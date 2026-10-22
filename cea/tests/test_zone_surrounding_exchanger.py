"""Zone-surroundings exchanger: moving buildings between `zone.shp` and `surroundings.shp`.

Moving a building invalidates results, so the tool refuses to run until `delete-outputs` is
true, then deletes everything under `outputs/` and `export/` except saved canvases and solar
radiation (minus the radiation of buildings moved out). With Archetype Lock on, buildings moved
in get their properties from the mapper; with it off, only `zone.shp` changes.
"""

import os
import shutil

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point, box

import cea.config
from cea.datamanagement import archetype_lock
from cea.datamanagement.zone_surrounding_exchanger import (
    MOVED_TO_ZONE_REFERENCE,
    check_archetypes,
    delete_outputs,
    exchange,
    validate,
    zone_surrounding_exchanger,
)
from cea.inputlocator import InputLocator

CRS = "EPSG:32632"
CONSTRUCTION_TYPES = pd.DataFrame({
    "const_type": ["OLD", "NEW"], "year_start": [0, 2000], "year_end": [1999, 2100]})


def _zone(names=("B1", "B2", "B3"), years=(1990, 2000, 2010)):
    return gpd.GeoDataFrame({
        "name": list(names),
        "floors_bg": 1, "floors_ag": 3, "height_vd": 0.0, "height_bg": 3.0, "height_ag": 9.0,
        "reference": "OSM",
        "year": list(years), "const_type": "OLD",
        "use_type1": ["OFFICE", "OFFICE", "RETAIL"], "use_type1r": 1.0,
        "use_type2": "NONE", "use_type2r": 0.0, "use_type3": "NONE", "use_type3r": 0.0,
        "street": "Main St", "city": "Zurich", "country": "CH",
    }, geometry=[box(i * 20, 0, i * 20 + 10, 10) for i in range(len(names))], crs=CRS)


def _surroundings(names=("S1", "S2"), categories=("apartments", "yes")):
    return gpd.GeoDataFrame({
        "name": list(names), "height_ag": 12.0, "floors_ag": 4, "category": list(categories),
        "REFERENCE": "OSM - as it is",
    }, geometry=[box(i * 20, 50, i * 20 + 10, 60) for i in range(len(names))], crs=CRS)


# --------------------------------------------------------------------------- exchange


def test_zone_to_surroundings_keeps_only_what_surroundings_describe():
    zone, surroundings, renamed = exchange(_zone(), _surroundings(), ["B2"], [])

    assert list(zone["name"]) == ["B1", "B3"]
    moved = surroundings.set_index("name").loc["B2"]
    assert (moved["height_ag"], moved["floors_ag"], moved["REFERENCE"]) == (9.0, 3, "OSM")
    assert "use_type1" not in surroundings.columns
    assert renamed == {}


def test_surroundings_to_zone_copies_the_template_but_not_its_address():
    zone, surroundings, _ = exchange(_zone(), _surroundings(), [], ["S1"], template="B3")

    assert list(surroundings["name"]) == ["S2"]
    moved = zone.set_index("name").loc["S1"]
    assert (moved["year"], moved["use_type1"]) == (2010, "RETAIL")
    assert (moved["street"], moved["city"], moved["country"]) == ("", "", "")
    assert (moved["height_ag"], moved["floors_ag"]) == (12.0, 4)
    assert (moved["floors_bg"], moved["height_bg"], moved["height_vd"]) == (0, 0.0, 0)
    assert moved["reference"] == MOVED_TO_ZONE_REFERENCE


def test_surroundings_to_zone_defaults_follow_zone_helper():
    zone, _, _ = exchange(_zone(), _surroundings(), [], ["S1", "S2"],
                          construction_types=CONSTRUCTION_TYPES)
    moved = zone.set_index("name")

    assert moved.loc["S1", "use_type1"] == "MULTI_RES", "OSM 'apartments' maps to a CEA use type"
    assert moved.loc["S2", "use_type1"] == "OFFICE", "unknown category falls back to the zone's mode"
    assert moved.loc["S1", "year"] == 2000, "the zone's median year"
    assert moved.loc["S1", "const_type"] == "NEW"


def test_a_taken_name_gets_a_suffix():
    zone, _, renamed = exchange(_zone(names=("B1", "B1_1", "B2")), _surroundings(names=("B1", "S2")),
                                [], ["B1"], template="B2")

    assert renamed == {"B1": "B1_2"}
    assert list(zone["name"]).count("B1") == 1 and "B1_2" in set(zone["name"])


def test_swapping_names_needs_no_suffix():
    zone, surroundings, renamed = exchange(_zone(), _surroundings(names=("B1", "S2")), ["B1"], ["B1"],
                                           template="B2")

    assert renamed == {}
    assert zone.set_index("name").loc["B1", "reference"] == MOVED_TO_ZONE_REFERENCE
    assert surroundings.set_index("name").loc["B1", "REFERENCE"] == "OSM"


def test_moved_buildings_take_the_destination_crs():
    surroundings = _surroundings().to_crs("EPSG:4326")
    zone, _, _ = exchange(_zone(), surroundings, [], ["S1"], template="B1")

    moved = zone.set_index("name").loc["S1", "geometry"]
    assert zone.crs == CRS
    assert moved.centroid.distance(Point(5, 55)) < 0.01


def test_a_building_too_short_for_its_floors_cannot_join_the_zone():
    surroundings = _surroundings()
    surroundings["height_ag"] = 3.0  # 4 floors in 3 m
    with pytest.raises(Exception, match="height per"):
        exchange(_zone(), surroundings, [], ["S1"], template="B1")


# --------------------------------------------------------------------------- validate


@pytest.mark.parametrize("to_surroundings, to_zone, template, confirmed, message", [
    (["B1"], [], None, False, "delete-outputs"),
    ([], [], None, True, "at least one building"),
    (["B1"], ["B1"], None, True, "both ways"),
    (["B9"], [], None, True, "Not found in the zone"),
    ([], ["S9"], None, True, "Not found in the surroundings"),
    (["B1", "B2", "B3"], [], None, True, "at least one building"),
    ([], ["S1"], "B9", True, "not in the zone"),
    (["B1"], ["S1"], "B1", True, "cannot also be moved"),
])
def test_validate_refuses(to_surroundings, to_zone, template, confirmed, message):
    with pytest.raises(ValueError, match=message):
        validate(_zone(), _surroundings(), to_surroundings, to_zone, template, confirmed)


def test_types_missing_from_the_database_are_refused():
    zone, _, _ = exchange(_zone(), _surroundings(), [], ["S1"], construction_types=CONSTRUCTION_TYPES)
    moved = zone[zone["name"] == "S1"]

    check_archetypes(moved, CONSTRUCTION_TYPES, pd.DataFrame({"use_type": ["MULTI_RES"]}))
    with pytest.raises(ValueError, match="MULTI_RES"):
        check_archetypes(moved, CONSTRUCTION_TYPES, pd.DataFrame({"use_type": ["OFFICE"]}))


def test_validate_refuses_an_ambiguous_name():
    with pytest.raises(ValueError, match="more than once"):
        validate(_zone(), _surroundings(names=("S1", "S1")), [], ["S1"], None, True)


# --------------------------------------------------------------------------- scenario


@pytest.fixture(scope="module")
def reference_scenario():
    from cea.inputlocator import ReferenceCaseOpenLocator

    return ReferenceCaseOpenLocator().scenario


@pytest.fixture
def locator(reference_scenario, tmp_path):
    scenario = tmp_path / "baseline"
    shutil.copytree(reference_scenario, scenario)
    return InputLocator(str(scenario))


def _touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").close()


def test_delete_outputs_keeps_canvas_and_radiation_but_not_the_moved_buildings(locator):
    output = locator.get_output_folder()
    keep = [os.path.join(output, "canvas", "board", "canvas.yml"),
            locator.get_radiation_building("B1001")]
    delete = [os.path.join(output, "data", "demand", "Total_demand.csv"),
              os.path.join(output, "pathways", "p1", "district_pathway_log.yml"),
              os.path.join(output, "data", "thermal-network", "DH", "layout.shp"),
              os.path.join(output, "kpis", "kpi_status.json"),
              os.path.join(locator.get_export_folder(), "rhino", "zone.csv"),
              locator.get_radiation_building("B1000"),
              locator.get_radiation_building_sensors("B1000")]
    for path in keep + delete:
        _touch(path)

    delete_outputs(locator, ["B1000"])

    assert all(os.path.exists(p) for p in keep)
    assert not any(os.path.exists(p) for p in delete)
    assert not os.path.exists(locator.get_export_folder())


def _run(locator, to_surroundings, to_zone, template=None):
    zone_surrounding_exchanger(locator, to_surroundings, to_zone, template, delete_outputs_confirmed=True)


def _names(path):
    return set(pd.read_csv(path)["name"])


def test_with_the_lock_on_buildings_moved_in_get_their_properties(locator):
    archetype_lock.remap_and_relock(locator, locator.get_zone_building_names())
    moved_in = locator.get_surroundings_building_names()[0]

    _run(locator, ["B1000"], [moved_in])

    assert moved_in in set(locator.get_zone_building_names())
    assert "B1000" in set(locator.get_surroundings_building_names())
    for table in (locator.get_building_architecture(), locator.get_building_air_conditioning(),
                  locator.get_building_comfort(), locator.get_building_internal(),
                  locator.get_building_supply(),
                  locator.get_building_weekly_schedules_monthly_multiplier_csv()):
        assert moved_in in _names(table)
        assert "B1000" not in _names(table)
    assert os.path.isfile(locator.get_building_weekly_schedules(moved_in))
    assert not os.path.isfile(locator.get_building_weekly_schedules("B1000"))
    lock = archetype_lock.read_lock(locator)
    assert moved_in in lock.mapped_use_types and "B1000" not in lock.mapped_use_types


def test_with_the_lock_on_moving_out_only_keeps_mapped_at(locator):
    before = archetype_lock.remap_and_relock(locator, locator.get_zone_building_names())

    _run(locator, ["B1000"], [])

    assert "B1000" not in _names(locator.get_building_architecture())
    assert not os.path.isfile(locator.get_building_weekly_schedules("B1000"))
    after = archetype_lock.read_lock(locator)
    assert after.mapped_at == before.mapped_at
    assert "B1000" not in after.mapped_use_types


def test_with_the_lock_off_only_the_zone_changes(locator):
    archetype_lock.write_lock(locator, locked=False)
    envelope_before = pd.read_csv(locator.get_building_architecture())
    moved_in = locator.get_surroundings_building_names()[0]

    _run(locator, ["B1000"], [moved_in], template="B1001")

    assert moved_in in set(locator.get_zone_building_names())
    pd.testing.assert_frame_equal(pd.read_csv(locator.get_building_architecture()), envelope_before)


def test_a_failed_check_touches_nothing(locator):
    zone_before = gpd.read_file(locator.get_zone_geometry())
    radiation = locator.get_radiation_building("B1001")
    _touch(radiation)

    # A database without the moved-in building's use type.
    pd.DataFrame({"use_type": ["NOTHING"]}).to_csv(locator.get_database_archetypes_use_type(), index=False)

    with pytest.raises(ValueError, match="archetype database"):
        _run(locator, [], [locator.get_surroundings_building_names()[0]])

    assert os.path.exists(radiation)
    assert len(gpd.read_file(locator.get_zone_geometry())) == len(zone_before)


def test_stale_shapefile_sidecars_are_removed(locator):
    stale = os.path.splitext(locator.get_zone_geometry())[0] + ".sbn"
    _touch(stale)

    _run(locator, ["B1000"], [])

    assert not os.path.exists(stale)
    assert os.path.exists(os.path.splitext(locator.get_zone_geometry())[0] + ".dbf")


def test_surroundings_parameter_offers_surroundings_and_blank_means_none(locator):
    config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    config.scenario = locator.scenario
    parameter = config.sections["zone-surrounding-exchanger"].parameters["surroundings-to-zone"]

    assert parameter._choices == locator.get_surroundings_building_names()
    assert parameter.decode("") == []
    assert config.sections["zone-surrounding-exchanger"].parameters["zone-to-surroundings"].decode("") == []
