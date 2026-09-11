"""A geometry that fails to load must not surface as a 500 on the next save.

`GET /inputs/all-inputs` builds `tables` and `geojsons` from two independent reads of the same
files. `df_to_json` additionally applies `secure_path`, reprojects, and catches *every*
exception into `None`, so a table can arrive populated with no geometry beside it.

The editor sends back what it was given, and the save then did:

    geojsons[db]['features']        # None -> TypeError, reported as a 500 on PUT

The report points at the save; the fault was at load time, and `df_to_json` printed its reason
to stdout rather than the log, so it was not in the server log either.
"""

import asyncio
import warnings

import pytest

from cea.interfaces.dashboard.api.inputs import (
    InputForm,
    get_all_inputs,
    save_all_inputs,
)


@pytest.fixture(scope="module")
def locator():
    from cea.inputlocator import ReferenceCaseOpenLocator

    return ReferenceCaseOpenLocator()


def load(scenario):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return asyncio.run(get_all_inputs(scenario))


def save(scenario, form):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return asyncio.run(save_all_inputs(scenario, form))


def test_a_table_sent_without_its_geometry_does_not_raise(locator):
    """The exact shape reported: zone rows present, zone geojson null."""
    store = load(locator.scenario)
    assert store["tables"]["zone"], "the fixture must have zone rows for this to mean anything"

    form = InputForm(
        tables=store["tables"],
        geojsons={**store["geojsons"], "zone": None},
        crs=store["crs"],
        schedules={},
    )

    result = save(locator.scenario, form)  # must not raise TypeError
    assert result is not None


def test_the_untouched_geometry_is_left_on_disk(locator):
    """Skipping is only safe if it does not also wipe the file.

    The rows are handed back so the editor keeps showing them, but nothing is written -- the
    geometry needed to write a shapefile is precisely what is missing.
    """
    import geopandas as gpd

    store = load(locator.scenario)
    before = len(gpd.read_file(locator.get_zone_geometry()))

    form = InputForm(
        tables=store["tables"],
        geojsons={**store["geojsons"], "zone": None},
        crs=store["crs"],
        schedules={},
    )
    result = save(locator.scenario, form)

    assert len(gpd.read_file(locator.get_zone_geometry())) == before
    assert len(result["tables"]["zone"]) == before, "the rows are returned, not dropped"


def test_an_empty_feature_list_is_treated_the_same_as_none(locator):
    """`{'features': []}` cannot build a shapefile either, and must not be written."""
    store = load(locator.scenario)

    form = InputForm(
        tables=store["tables"],
        geojsons={**store["geojsons"], "zone": {"type": "FeatureCollection", "features": []}},
        crs=store["crs"],
        schedules={},
    )
    result = save(locator.scenario, form)
    assert result is not None


def test_a_normal_save_is_unaffected(locator):
    store = load(locator.scenario)
    form = InputForm(tables=store["tables"], geojsons=store["geojsons"],
                     crs=store["crs"], schedules={})

    result = save(locator.scenario, form)

    assert len(result["tables"]["zone"]) == len(store["tables"]["zone"])


def test_df_to_json_reports_why_it_failed(locator, caplog):
    """It used to `print()` the reason, so it never reached the server log.

    Without it the only evidence is a TypeError raised somewhere else entirely.
    """
    import logging

    from cea.interfaces.dashboard.api.inputs import df_to_json

    with caplog.at_level(logging.WARNING):
        result, crs = df_to_json("/nonexistent/does_not_exist.shp")

    assert result is None and crs is None
    assert any("does_not_exist.shp" in record.message for record in caplog.records), (
        "the failing file must be named in the log")
