"""`save_all_inputs`'s response must fully describe every table the save touched.

The input editor used to refetch `GET /all-inputs` after every save; it now merges the PUT
response straight into its cache instead (`useSaveInputs.js`), because `save_all_inputs`
already re-reads whatever it wrote -- refetching just repeated that work. A response key
silently absent for a table this save did touch reads as "unchanged" to that merge, leaving
stale, non-empty data in the client's cache.

`surroundings` was always reported as `[]` when cleared; every other table was not reported
at all in the same situation -- the file was deleted on disk, but the response said nothing.
"""

import asyncio
import os
import shutil
import tempfile
import warnings

import pytest


def fresh_locator():
    """An isolated copy of the reference case -- these tests delete/empty tables, which must
    not leak into any other test.
    """
    from cea.inputlocator import InputLocator, ReferenceCaseOpenLocator

    scenario = os.path.join(tempfile.mkdtemp(), "baseline")
    shutil.copytree(ReferenceCaseOpenLocator().scenario, scenario)
    return InputLocator(scenario)


def save(locator, tables, geojsons=None):
    """Drive `save_all_inputs` with a minimal payload -- only the tables under test."""
    from cea.interfaces.dashboard.api.inputs import InputForm, save_all_inputs

    form = InputForm(tables=tables, geojsons=geojsons or {}, crs={}, schedules={})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return asyncio.run(save_all_inputs(locator.scenario, form))


def test_clearing_a_csv_table_reports_it_as_empty():
    """`internal-loads` is a plain CSV, not `surroundings` -- the table this bug skipped."""
    locator = fresh_locator()
    assert os.path.isfile(locator.get_building_internal()), (
        "fixture assumption: internal-loads starts out present")

    result = save(locator, {"internal-loads": {}})

    assert result["tables"]["internal-loads"] == {}, (
        "a cleared table must appear in the response, not be silently absent")
    assert not os.path.isfile(locator.get_building_internal())


def test_clearing_a_shapefile_table_reports_it_as_empty():
    """`trees` is shapefile-backed, so both `tables` and `geojsons` must report it."""
    locator = fresh_locator()

    result = save(
        locator,
        {"trees": {}},
        geojsons={"trees": {"type": "FeatureCollection", "features": []}},
    )

    assert result["tables"]["trees"] == {}
    assert result["geojsons"]["trees"] == {}


def test_a_table_untouched_by_the_save_is_not_mentioned():
    """The absence of a key must still mean "this save did not touch it" -- only a table
    actually present (even if empty) in the payload should appear in the response.
    """
    locator = fresh_locator()

    result = save(locator, {"internal-loads": {}})

    assert "zone" not in result["tables"]
    assert "envelope" not in result["tables"]


@pytest.mark.parametrize("db", ["internal-loads", "indoor-comfort", "hvac", "supply"])
def test_every_non_surroundings_csv_table_reports_clearing(db):
    """Not just `internal-loads` -- every derived CSV table had the same gap."""
    locator = fresh_locator()

    result = save(locator, {db: {}})

    assert result["tables"][db] == {}
