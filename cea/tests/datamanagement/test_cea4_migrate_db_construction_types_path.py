"""`hs_bg_in_db` / `add_occupied_bg_db` must agree with `path_to_db_file_4` on where
`CONSTRUCTION_TYPES.csv` lives.

They used to hardcode `inputs/database/archetypes/CONSTRUCTION/...` (lowercase
`archetypes`) while `path_to_db_file_4` -- the function that actually writes the file during
migration -- puts it under `ARCHETYPES` (uppercase). The two paths are the same file on a
case-insensitive filesystem (macOS, Windows), so this went unnoticed there; on a
case-sensitive one (Linux, every `ubuntu-latest` CI run) the lowercase path never existed, so
`hs_bg_in_db` always read `False` and the `Hs_ag`/`Hs_bg` -> `Hs`/`occupied_bg` rename this
gates never ran, leaving `archetypes_mapper` unable to find those columns afterwards.

This test does not need a case-sensitive filesystem to be meaningful: it asserts the two
functions resolve to the exact same path `path_to_db_file_4` returns, which is the actual
invariant that broke -- not merely "does this happen to work on the machine running it".
"""

import os
import shutil
import tempfile

import pandas as pd
import pytest

from cea.datamanagement.format_helper.cea4_migrate_db import (
    add_occupied_bg_db,
    hs_bg_in_db,
)
from cea.datamanagement.format_helper.cea4_verify_db import path_to_db_file_4


@pytest.fixture
def scenario():
    root = tempfile.mkdtemp()
    yield os.path.join(root, "baseline")
    shutil.rmtree(root, ignore_errors=True)


def write_construction_types(scenario, **columns):
    path = path_to_db_file_4(scenario, "CONSTRUCTION_TYPES")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pd.DataFrame({"const_type": ["STANDARD1"], **columns}).set_index("const_type").to_csv(path)
    return path


def test_hs_bg_in_db_finds_the_file_path_to_db_file_4_writes(scenario):
    write_construction_types(scenario, Hs_ag=[0.9], Hs_bg=[0.0])

    assert hs_bg_in_db(scenario) is True


def test_hs_bg_in_db_is_false_when_already_migrated(scenario):
    write_construction_types(scenario, Hs=[0.9], occupied_bg=[False])

    assert hs_bg_in_db(scenario) is False


def test_add_occupied_bg_db_renames_the_columns_in_place(scenario):
    path = write_construction_types(scenario, Hs_ag=[0.9], Hs_bg=[0.3])

    add_occupied_bg_db(scenario)

    result = pd.read_csv(path, index_col=0)
    assert list(result.columns) == ["Hs", "occupied_bg"]
    assert result["occupied_bg"].tolist() == [True]
