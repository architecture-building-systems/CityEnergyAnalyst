"""`archetypes_mapper` must not delete the buildings it was not asked to map.

Each mapper builds its frame from `building_typology_df`, which `archetypes_mapper` has already
filtered to `list_buildings`. Writing that frame straight out replaced the whole file with the
subset: mapping one building of fifteen left a one-row file and silently removed the other
fourteen, across all five derived tables.

Reachable from the CLI and the dashboard through `archetypes-mapper:buildings`, and from
Archetype Lock whenever a building's archetype changes.
"""

import pandas as pd
import pytest

from cea.datamanagement.archetypes_mapper import archetypes_mapper


@pytest.fixture(scope="module")
def locator():
    from cea.inputlocator import ReferenceCaseOpenLocator

    return ReferenceCaseOpenLocator()


def map_buildings(locator, buildings):
    archetypes_mapper(
        locator=locator,
        update_architecture_dbf=True,
        update_air_conditioning_systems_dbf=True,
        update_indoor_comfort_dbf=True,
        update_internal_loads_dbf=True,
        update_supply_systems_dbf=True,
        update_schedule_operation_cea=False,  # per-building files; they never truncated
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
