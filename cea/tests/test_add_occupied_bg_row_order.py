"""`add_occupied_bg` must keep the envelope rows in the order they were given.

It used to select the buildings that are also in the zone with `list(set(...))`, so the rows of the migrated
`envelope.csv` came out in an order that changed with every Python process (string hashing is randomised).
That is harmless for the calculations, which look buildings up by name, but the same input produced a
different file each run, which made outputs that depend on the row order (for example the order materials
are listed in the radiance material file) differ between machines and runs.

The test uses enough buildings that the order of a set of their names is, for practical purposes, never
the order they were given in.
"""

import os

import pandas as pd
import pytest

from cea.datamanagement.format_helper.cea4_migrate_db import add_occupied_bg
from cea.utilities.dbf import dataframe_to_dbf

NAMES = [f"B{i:04d}" for i in range(40)]


@pytest.fixture
def scenario(tmp_path):
    geometry_folder = tmp_path / "inputs" / "building-geometry"
    geometry_folder.mkdir(parents=True)
    zone = pd.DataFrame({"name": NAMES, "floors_ag": 3, "floors_bg": 1})
    dataframe_to_dbf(zone, os.path.join(str(geometry_folder), "zone.dbf"))
    return str(tmp_path)


def _envelope(names):
    return pd.DataFrame({"name": names, "Hs": 0.9, "Ns": 0.8, "occupied_bg": 0.0})


def test_rows_keep_their_input_order(scenario):
    result = add_occupied_bg(scenario, _envelope(NAMES))

    assert list(result["name"]) == NAMES


def test_rows_keep_a_non_alphabetical_input_order(scenario):
    shuffled = NAMES[::-1]

    result = add_occupied_bg(scenario, _envelope(shuffled))

    assert list(result["name"]) == shuffled


def test_buildings_missing_from_the_zone_are_still_dropped(scenario):
    result = add_occupied_bg(scenario, _envelope(NAMES + ["B9999"]))

    assert list(result["name"]) == NAMES
