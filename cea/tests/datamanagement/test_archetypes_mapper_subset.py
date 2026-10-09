"""`archetypes_mapper` must not delete the buildings it was not asked to map.

Each mapper builds its frame from `building_typology_df`, which `archetypes_mapper` has already
filtered to `list_buildings`. Writing that frame straight out replaced the whole file with the
subset: mapping one building of fifteen left a one-row file and silently removed the other
fourteen, across all five derived tables.

Reachable from the CLI and the dashboard through `archetypes-mapper:buildings`, and from
Archetype Lock whenever a building's archetype changes.
"""

import os
import shutil
import tempfile

import geopandas as gpd
import pandas as pd
import pytest

from cea.datamanagement.archetypes_mapper import archetypes_mapper


@pytest.fixture(scope="module")
def locator():
    from cea.inputlocator import ReferenceCaseOpenLocator

    return ReferenceCaseOpenLocator()


def fresh_locator():
    """An isolated copy of the reference case, for tests that must not affect the others.

    The shared `locator` fixture is mutated in place across every test in this module in
    sequence; a test that removes a building from the zone or corrupts a CSV's schema would
    otherwise leak that damage into every test that runs after it.
    """
    from cea.inputlocator import InputLocator, ReferenceCaseOpenLocator

    scenario = os.path.join(tempfile.mkdtemp(), "baseline")
    shutil.copytree(ReferenceCaseOpenLocator().scenario, scenario)
    return InputLocator(scenario)


def map_buildings(locator, buildings, *, update_schedule_operation_cea=False):
    archetypes_mapper(
        locator=locator,
        update_architecture_dbf=True,
        update_air_conditioning_systems_dbf=True,
        update_indoor_comfort_dbf=True,
        update_internal_loads_dbf=True,
        update_supply_systems_dbf=True,
        # Per-building schedule files never truncated (one file per building); the district
        # MONTHLY_MULTIPLIERS.csv did, before `calc_mixed_schedule` learned to merge -- see
        # `test_mapping_a_subset_keeps_every_other_buildings_monthly_multipliers` below.
        update_schedule_operation_cea=update_schedule_operation_cea,
        list_buildings=list(buildings),
    )


def derived_paths(locator):
    return {
        "envelope": locator.get_building_architecture(),
        "hvac": locator.get_building_air_conditioning(),
        "indoor_comfort": locator.get_building_comfort(),
        "internal_loads": locator.get_building_internal(),
        "supply": locator.get_building_supply(),
    }


def test_mapping_a_subset_keeps_every_other_building(locator):
    paths = derived_paths(locator)
    before = {name: list(pd.read_csv(path)["name"]) for name, path in paths.items()}
    assert all(len(names) > 1 for names in before.values()), "need several buildings to detect this"

    map_buildings(locator, ["B1000"])

    for name, path in paths.items():
        after = list(pd.read_csv(path)["name"])
        assert after == before[name], f"{name} lost or reordered buildings"


def test_mapping_a_subset_does_not_change_the_other_buildings_values(locator):
    """Values, not layout.

    The mapper writes its own column order, so a file that arrived from the CEA-3 migration
    comes back reordered -- that is pre-existing and cosmetic, and a full-district run has
    always done it. Compare on a stable column order so the test is about the data.
    """
    path = locator.get_building_architecture()
    before = pd.read_csv(path).set_index("name").sort_index(axis=1)

    map_buildings(locator, ["B1000"])

    after = pd.read_csv(path).set_index("name").sort_index(axis=1)
    untouched = [b for b in before.index if b != "B1000"]
    pd.testing.assert_frame_equal(before.loc[untouched], after.loc[untouched])


def test_mapping_a_subset_is_idempotent(locator):
    path = locator.get_building_architecture()
    map_buildings(locator, ["B1000"])
    once = pd.read_csv(path)

    map_buildings(locator, ["B1000"])

    pd.testing.assert_frame_equal(once, pd.read_csv(path))


def test_a_full_run_still_writes_every_building(locator):
    """The merge must not change what a whole-district run produces."""
    path = locator.get_building_architecture()
    everyone = list(pd.read_csv(path)["name"])

    map_buildings(locator, everyone)

    assert list(pd.read_csv(path)["name"]) == everyone


def test_the_merge_matches_on_columns_regardless_of_their_order(locator):
    """The file on disk stores these columns in a different order from the mapper's `fields`.

    A first attempt compared the two as ordered lists, so the merge never ran and the
    truncation survived the fix.
    """
    path = locator.get_building_architecture()
    on_disk = list(pd.read_csv(path).columns)
    shuffled = [on_disk[0]] + list(reversed(on_disk[1:]))
    pd.read_csv(path)[shuffled].to_csv(path, index=False)

    before = set(pd.read_csv(path)["name"])
    map_buildings(locator, ["B1000"])

    assert set(pd.read_csv(path)["name"]) == before, "column order must not defeat the merge"


def test_a_full_run_drops_a_building_removed_from_the_zone():
    """A full-district run is authoritative over the whole zone -- a building deleted from
    `zone.shp` must not survive as an orphan row in the derived tables just because nothing
    ever explicitly asked to remove it.
    """
    isolated = fresh_locator()
    zone = gpd.read_file(isolated.get_zone_geometry())
    assert "B1000" in set(zone["name"]), "fixture assumption: B1000 exists in the zone"

    remaining = zone[zone["name"] != "B1000"]
    remaining.to_file(isolated.get_zone_geometry())

    map_buildings(isolated, list(remaining["name"]))

    for path in derived_paths(isolated).values():
        assert "B1000" not in set(pd.read_csv(path)["name"]), (
            f"{path} kept a row for a building no longer in the zone")


def test_mapping_a_subset_keeps_every_other_buildings_monthly_multipliers():
    """The district MONTHLY_MULTIPLIERS.csv must not be replaced with just the mapped subset.

    `calc_mixed_schedule` builds `lists_monthly_multiplier` from the (already-filtered)
    `building_typology_df` and used to write it straight out via `save_cea_monthly_multipliers`,
    silently deleting every other building's row -- the same failure mode `write_building_properties`
    was introduced to fix for the other five derived tables, but this file went through a
    different write path that never got the same treatment.
    """
    isolated = fresh_locator()
    zone_buildings = set(gpd.read_file(isolated.get_zone_geometry())["name"])
    path = isolated.get_building_weekly_schedules_monthly_multiplier_csv()
    # Restrict to buildings actually in the zone: like `write_building_properties`, the merge
    # also drops any pre-existing row for a building no longer in `zone.shp`, so a fixture with
    # such a row is not a case this assertion is about.
    before = [b for b in pd.read_csv(path)["name"] if b in zone_buildings]
    assert len(before) > 1, "need several buildings to detect this"

    map_buildings(isolated, ["B1000"], update_schedule_operation_cea=True)

    assert list(pd.read_csv(path)["name"]) == before


def test_a_subset_run_refuses_to_merge_into_a_differently_shaped_file():
    """A subset run cannot safely blend into a file from an older/different CEA schema.

    Overwriting silently would keep only the mapped subset and delete every other building's
    row; the correct outcome is to stop before writing anything.
    """
    isolated = fresh_locator()
    path = isolated.get_building_architecture()
    before = pd.read_csv(path)
    mismatched = before.drop(columns=[before.columns[-1]])
    mismatched.to_csv(path, index=False)

    with pytest.raises(ValueError):
        map_buildings(isolated, ["B1000"])

    # Nothing was written -- the file other buildings depend on is exactly as this test left it.
    after = pd.read_csv(path)
    pd.testing.assert_frame_equal(mismatched, after)


def test_a_monthly_multiplier_subset_run_refuses_to_merge_into_a_differently_shaped_file():
    """Same failure mode as `test_a_subset_run_refuses_to_merge_into_a_differently_shaped_file`,
    for `save_cea_monthly_multipliers` -- a separate write path that went through the same bug
    (see its module-level test above) but is not `write_building_properties` itself, so its own
    fix needs its own regression test.
    """
    isolated = fresh_locator()
    path = isolated.get_building_weekly_schedules_monthly_multiplier_csv()
    before = pd.read_csv(path)
    mismatched = before.drop(columns=[before.columns[-1]])
    mismatched.to_csv(path, index=False)

    with pytest.raises(ValueError):
        map_buildings(isolated, ["B1000"], update_schedule_operation_cea=True)

    # Nothing was written -- the file other buildings depend on is exactly as this test left it.
    after = pd.read_csv(path)
    pd.testing.assert_frame_equal(mismatched, after)
