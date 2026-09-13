"""A MATERIALS.csv written before the end-of-life column rename gets an actionable message.

The columns were `*_recycling` before being corrected to `*_disposal`. Such a file reports
seven missing columns, which says what is absent but not why; the verifier adds a pointer.
Deliberately a hint, not a silent fixup -- nothing rewrites the user's file.
"""

import os
import shutil

import pandas as pd
import pytest

import cea.config
from cea.datamanagement.format_helper.cea4_verify_db import cea4_verify_db
from cea.inputlocator import InputLocator
from cea.tests import paths

PRE_RENAME = {
    "ID_disposal": "ID_recycling",
    "disposal_method": "recycling_method",
    "UBP_disposal": "UBP_recycling",
    "overall_disposal": "overall_recycling",
    "renewable_disposal": "renewable_recycling",
    "unrenewable_disposal": "unrenewable_recycling",
    "GHG_emission_disposal": "GHG_emission_recycling",
}


@pytest.fixture
def ch_scenario(tmp_path):
    """A scenario holding a copy of the shipped CH database, safe to mutate."""
    config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    config.project = str(tmp_path)
    config.scenario_name = "s"
    locator = InputLocator(config.scenario)
    shutil.copytree(
        os.path.join(str(paths.REPO_ROOT), "cea", "databases", "CH"),
        os.path.join(config.scenario, "inputs", "database"),
        dirs_exist_ok=True,
    )
    return locator, config.scenario


def _materials_report(scenario):
    return [
        entry
        for entry in cea4_verify_db(scenario, verbose=False).get("MATERIALS", [])
        if isinstance(entry, str)
    ]


def _hint(report):
    return [entry for entry in report if "pre-rename" in entry]


def test_a_healthy_database_reports_nothing(ch_scenario):
    _locator, scenario = ch_scenario

    assert _materials_report(scenario) == []


def test_a_pre_rename_database_gets_a_pointer(ch_scenario):
    locator, scenario = ch_scenario
    path = locator.get_database_components_materials()
    df = pd.read_csv(path)
    df.rename(columns=PRE_RENAME).to_csv(path, index=False)

    report = _materials_report(scenario)

    hint = _hint(report)
    assert len(hint) == 1, report
    assert "GHG_emission_recycling" in hint[0]
    assert "Re-import" in hint[0]
    # The plain missing-column report is kept as well: the hint explains it, not replaces it.
    assert "GHG_emission_disposal" in report


def test_a_merely_incomplete_database_gets_no_migration_hint(ch_scenario):
    """Columns absent for any other reason must not be blamed on the rename."""
    locator, scenario = ch_scenario
    path = locator.get_database_components_materials()
    df = pd.read_csv(path)
    df.drop(columns=list(PRE_RENAME)).to_csv(path, index=False)

    report = _materials_report(scenario)

    assert _hint(report) == [], report
    assert "GHG_emission_disposal" in report


def test_the_file_is_never_rewritten(ch_scenario):
    """The hint is advice; migrating shipped data is `cea4_migrate_db`'s job, not a side
    effect of verifying."""
    locator, scenario = ch_scenario
    path = locator.get_database_components_materials()
    df = pd.read_csv(path)
    df.rename(columns=PRE_RENAME).to_csv(path, index=False)
    before = open(path, encoding="utf-8").read()

    _materials_report(scenario)

    assert open(path, encoding="utf-8").read() == before
