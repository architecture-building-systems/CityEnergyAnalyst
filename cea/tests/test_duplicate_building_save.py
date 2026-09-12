"""Saving a duplicated building gives it a full set of archetype-derived rows.

The input editor's duplicate copies the `zone` row and its footprint and nothing else -- no
envelope, HVAC, comfort, loads, supply or schedule. Those are owed by the server, which spots
the new name through `archetype_lock.buildings_added` and runs `archetypes_mapper` for it on
save. That is the whole reason the button is only offered while the scenario is locked, so it
is worth proving rather than assuming: a duplicate that saved without its derived rows would
leave a building that every downstream script reads as missing data.
"""

import json
import os
import shutil
import warnings

import geopandas as gpd
import pandas as pd
import pytest

from cea.datamanagement.archetype_lock import (
    ARCHETYPE_DERIVED_TABS,
    derived_signature,
    write_lock,
)
from cea.inputlocator import InputLocator

SOURCE = "B1000"
COPY = "B1000_"


def fresh_scenario():
    """A throwaway copy of the reference case, as shipped.

    Always copied from the reference case rather than from another test's scenario: tests here
    re-map buildings, and a copy taken after that would no longer show the divergence between
    stored and archetype values that one of them depends on.

    The duplicate adds a building, so nothing may run against the shared reference case
    directly -- it would leave that building there for the rest of the session.
    """
    import tempfile

    from cea.inputlocator import ReferenceCaseOpenLocator

    scenario = os.path.join(tempfile.mkdtemp(), "baseline")
    shutil.copytree(ReferenceCaseOpenLocator().scenario, scenario)
    return InputLocator(scenario)


@pytest.fixture(scope="module")
def locator():
    return fresh_scenario()


def save_with_duplicate(locator, source, copy):
    """Drive `save_all_inputs` with exactly what the editor sends after a duplicate."""
    import asyncio

    from cea.interfaces.dashboard.api.inputs import (
        InputForm,
        get_building_properties,
        save_all_inputs,
    )

    scenario = locator.scenario
    store = get_building_properties(scenario)

    # While locked the derived tables are skipped by the server anyway, and the editor holds
    # them only to display -- mirroring the payload keeps the test honest about what arrives.
    payload = {k: (v if k in ("zone", "envelope") else None)
               for k, v in store["tables"].items()}
    payload["zone"][copy] = dict(payload["zone"][source])

    zone_shp = gpd.read_file(locator.get_zone_geometry())
    geojson = json.loads(zone_shp.to_crs("EPSG:4326").to_json())
    source_feature = next(f for f in geojson["features"]
                          if f["properties"]["name"] == source)
    duplicate_feature = json.loads(json.dumps(source_feature))
    duplicate_feature["properties"]["name"] = copy
    geojson["features"].append(duplicate_feature)

    form = InputForm(tables=payload, geojsons={"zone": geojson},
                     crs={"zone": zone_shp.crs.to_proj4()}, schedules={})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return asyncio.run(save_all_inputs(scenario, form))


@pytest.fixture(scope="module")
def saved(locator):
    write_lock(locator, locked=True, signature=derived_signature(locator))
    return save_with_duplicate(locator, SOURCE, COPY)


def remap(locator, buildings):
    """Re-derive the named buildings, so a comparison is archetype-against-archetype."""
    from cea.datamanagement.archetypes_mapper import archetypes_mapper

    archetypes_mapper(
        locator=locator,
        update_architecture_dbf=True,
        update_air_conditioning_systems_dbf=True,
        update_indoor_comfort_dbf=True,
        update_internal_loads_dbf=True,
        update_supply_systems_dbf=True,
        update_schedule_operation_cea=False,
        list_buildings=list(buildings),
    )


def derived_table(locator, tab):
    paths = {
        "envelope": locator.get_building_architecture,
        "hvac": locator.get_building_air_conditioning,
        "indoor-comfort": locator.get_building_comfort,
        "internal-loads": locator.get_building_internal,
        "supply": locator.get_building_supply,
    }
    return pd.read_csv(paths[tab]()).set_index("name")


def test_the_duplicate_reaches_the_zone_shapefile(locator, saved):
    zone = gpd.read_file(locator.get_zone_geometry()).set_index("name")

    assert COPY in zone.index
    assert SOURCE in zone.index, "duplicating must not consume the original"


def test_the_duplicate_keeps_the_original_footprint(locator, saved):
    zone = gpd.read_file(locator.get_zone_geometry()).set_index("name")

    # Copied, not approximated -- the editor offers no way to move it afterwards.
    assert zone.loc[COPY].geometry.equals(zone.loc[SOURCE].geometry)


def test_the_save_reports_the_duplicate_as_remapped(saved):
    assert saved.get("remapped_buildings") == [COPY]


@pytest.mark.parametrize("tab", sorted(ARCHETYPE_DERIVED_TABS))
def test_every_derived_table_gains_a_row_for_the_duplicate(locator, saved, tab):
    if tab == "schedules":
        pytest.skip("schedules are per-building files, covered separately")

    table = derived_table(locator, tab)
    assert COPY in table.index, f"{tab} has no row for the duplicate"


@pytest.mark.parametrize("tab", ["envelope", "hvac", "indoor-comfort",
                                 "internal-loads", "supply"])
def test_the_duplicate_takes_its_values_from_the_archetype(locator, saved, tab):
    """Same archetype key in, same derived values out.

    Compared against a freshly mapped original rather than against whatever the original holds
    on disk. Those are not the same thing: a scenario can carry derived values that no longer
    match its archetype -- the reference case itself ships `B1000` with SUPPLY_COOLING_AS3
    where its archetype gives AS0 -- and the duplicate gets the archetype's answer, not the
    stored one. See `test_the_duplicate_does_not_copy_values_that_diverge_from_the_archetype`.
    """
    remap(locator, [SOURCE])
    table = derived_table(locator, tab)

    pd.testing.assert_series_equal(
        table.loc[COPY], table.loc[SOURCE], check_names=False)


def test_the_duplicate_does_not_copy_values_that_diverge_from_the_archetype():
    """Duplicating re-derives; it does not clone the row.

    A building whose derived values were hand-edited while unlocked produces a copy carrying
    the archetype defaults instead of those edits. That follows from CEA owning the derived
    tables while locked, but it is the surprising half of the feature, so it is pinned here
    rather than left to be discovered.
    """
    fresh = fresh_scenario()
    write_lock(fresh, locked=True, signature=derived_signature(fresh))

    stored = pd.read_csv(fresh.get_building_supply()).set_index("name").loc[SOURCE]
    save_with_duplicate(fresh, SOURCE, COPY)
    copied = pd.read_csv(fresh.get_building_supply()).set_index("name").loc[COPY]

    assert stored["supply_type_cs"] != copied["supply_type_cs"], (
        "the reference case must ship a building whose stored supply differs from its "
        "archetype for this test to mean anything")


def test_the_duplicate_gets_a_schedule_file(locator, saved):
    assert os.path.isfile(locator.get_building_weekly_schedules(COPY))


def test_the_other_buildings_are_left_alone(locator, saved):
    """The mapper runs for the duplicate only.

    `archetypes_mapper` filters to `list_buildings`, and writing that frame straight out used
    to replace the whole file -- one mapped building leaving a one-row table.
    """
    zone = gpd.read_file(locator.get_zone_geometry()).set_index("name")
    envelope = derived_table(locator, "envelope")

    assert set(envelope.index) == set(zone.index)
    assert len(envelope) > 2, "the fixture needs several buildings for this to mean anything"
