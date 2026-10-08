import os

import geopandas as gpd
import numpy as np
import pytest
from shapely import box

import cea.config
from cea.datamanagement import surroundings_helper
from cea.demand import constants
from cea.inputlocator import InputLocator
from cea.tests.datamanagement.fakes import fake_features_from_polygon, osm_buildings
from cea.utilities.standardize_coordinates import get_projected_coordinate_system

UTM32N = get_projected_coordinate_system(47.1767, 8.5143)
ZONE_WGS84 = box(8.5135, 47.1755, 8.5150, 47.1780)
# a few tens of metres east of the zone
NEIGHBOUR_WGS84 = box(8.5152, 47.1760, 8.5156, 47.1764)
FAR_AWAY_WGS84 = box(8.6000, 47.2500, 8.6004, 47.2504)


def _scenario(tmp_path, zone_crs="EPSG:4326"):
    config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    config.project = str(tmp_path)
    config.scenario_name = "baseline"
    locator = InputLocator(config.scenario)
    os.makedirs(locator.get_building_geometry_folder(), exist_ok=True)
    zone = gpd.GeoDataFrame({"name": ["B1001"]}, geometry=[ZONE_WGS84], crs="EPSG:4326").to_crs(zone_crs)
    zone.to_file(locator.get_zone_geometry())
    return config, locator


def test_generate_empty_surroundings_has_expected_columns_and_crs():
    empty = surroundings_helper.generate_empty_surroundings("EPSG:32632")
    assert list(empty.columns) == ["name", "height_ag", "floors_ag", "geometry"]
    assert empty.empty
    assert empty.crs.to_epsg() == 32632


def test_calc_surrounding_area_buffers_single_polygon():
    zone = gpd.GeoDataFrame(geometry=[box(0, 0, 10, 10)], crs="EPSG:32632")
    area = surroundings_helper.calc_surrounding_area(zone, 5)
    assert area.crs == zone.crs
    minx, miny, maxx, maxy = area.total_bounds
    assert (minx, miny, maxx, maxy) == pytest.approx((-5, -5, 15, 15))


def test_calc_surrounding_area_uses_convex_hull_for_disjoint_buildings():
    zone = gpd.GeoDataFrame(geometry=[box(0, 0, 10, 10), box(100, 0, 110, 10)], crs="EPSG:32632")
    area = surroundings_helper.calc_surrounding_area(zone, 1)
    # The gap between the two buildings is covered, which a plain buffer of the union would not do
    assert area.geometry.iloc[0].contains(box(40, 2, 60, 8))


def test_clean_attributes_assumes_floors_when_levels_missing():
    shapefile = gpd.GeoDataFrame({"building": ["yes", "yes"]}, geometry=[box(0, 0, 1, 1), box(2, 0, 3, 1)])
    result = surroundings_helper.clean_attributes(shapefile, key="CEA")
    assert list(result["name"]) == ["CEA1000", "CEA1001"]
    assert set(result["REFERENCE"]) == {"CEA - assumption"}
    assert list(result["floors_ag"]) == [3, 3]
    assert list(result["height_ag"]) == [3 * constants.H_F] * 2
    assert list(result.columns) == ["name", "height_ag", "floors_ag", "description", "category", "geometry",
                                    "REFERENCE"]


def test_clean_attributes_assumes_floors_when_all_levels_null():
    shapefile = gpd.GeoDataFrame({"building": ["yes"], "building:levels": [np.nan]}, geometry=[box(0, 0, 1, 1)])
    result = surroundings_helper.clean_attributes(shapefile, key="CEA")
    assert result["REFERENCE"].iloc[0] == "CEA - assumption"
    assert result["floors_ag"].iloc[0] == 3


def test_clean_attributes_uses_osm_levels_and_roof_levels_with_median_fill():
    shapefile = gpd.GeoDataFrame(
        {
            "building": ["yes"] * 3,
            "building:levels": ["4", "6", np.nan],
            "roof:levels": [1, np.nan, np.nan],
        },
        geometry=[box(0, 0, 1, 1), box(2, 0, 3, 1), box(4, 0, 5, 1)],
    )
    result = surroundings_helper.clean_attributes(shapefile, key="S")
    # 4 + 1 roof level, 6, and a building without levels that takes the median (ceil(5.5) = 6)
    assert list(result["floors_ag"]) == [5, 6, 6]
    assert list(result["height_ag"]) == [floors * constants.H_F for floors in (5, 6, 6)]
    assert list(result["REFERENCE"]) == ["OSM - as it is", "OSM - as it is", "OSM - median"]


@pytest.mark.parametrize("columns, expected", [
    ({"description": ["school"], "addr:housename": ["house"], "amenity": ["cafe"]}, "school"),
    ({"addr:housename": ["house"], "amenity": ["cafe"]}, "house"),
    ({"amenity": ["cafe"]}, "cafe"),
    ({}, None),
])
def test_clean_attributes_description_precedence(columns, expected):
    shapefile = gpd.GeoDataFrame({"building": ["yes"], **columns}, geometry=[box(0, 0, 1, 1)])
    description = surroundings_helper.clean_attributes(shapefile, key="CEA")["description"].iloc[0]
    if expected is None:
        assert description != description  # NaN
    else:
        assert description == expected


def test_erase_no_surrounding_areas_keeps_only_buildings_around_the_zone():
    zone = gpd.GeoDataFrame(geometry=[box(0, 0, 10, 10)], crs="EPSG:32632")
    area_with_buffer = gpd.GeoDataFrame(geometry=[box(-20, -20, 30, 30)], crs="EPSG:32632")
    candidates = gpd.GeoDataFrame(
        {"building": ["inside zone", "overlaps zone", "ring", "outside buffer"]},
        geometry=[box(2, 2, 4, 4), box(8, 8, 15, 15), box(15, 0, 20, 5), box(200, 200, 210, 210)],
        crs="EPSG:32632",
    )
    result = surroundings_helper.erase_no_surrounding_areas(candidates, zone, area_with_buffer)
    assert list(result["building"]) == ["ring"]


def test_get_zone_and_surr_in_projected_crs_reprojects_and_rewrites(tmp_path):
    _, locator = _scenario(tmp_path)
    gpd.GeoDataFrame({"name": ["CEA1000"]}, geometry=[NEIGHBOUR_WGS84], crs="EPSG:4326").to_file(
        locator.get_surroundings_geometry())

    zone, surroundings = surroundings_helper.get_zone_and_surr_in_projected_crs(locator)

    assert zone.crs.to_epsg() == 32632
    assert surroundings.crs.to_epsg() == 32632
    assert gpd.read_file(locator.get_zone_geometry()).crs.to_epsg() == 32632
    assert gpd.read_file(locator.get_surroundings_geometry()).crs.to_epsg() == 32632


def test_get_zone_and_surr_in_projected_crs_leaves_matching_crs_alone(tmp_path):
    _, locator = _scenario(tmp_path, zone_crs=UTM32N)
    gpd.GeoDataFrame({"name": ["CEA1000"]}, geometry=[NEIGHBOUR_WGS84], crs="EPSG:4326").to_crs(UTM32N).to_file(
        locator.get_surroundings_geometry())
    modified_before = os.path.getmtime(locator.get_zone_geometry())

    zone, surroundings = surroundings_helper.get_zone_and_surr_in_projected_crs(locator)

    assert zone.crs == surroundings.crs
    assert os.path.getmtime(locator.get_zone_geometry()) == modified_before


def test_main_writes_surroundings_around_the_zone(tmp_path, monkeypatch):
    config, locator = _scenario(tmp_path, zone_crs=UTM32N)
    config.surroundings_helper.buffer = 200
    osm = osm_buildings(
        [ZONE_WGS84, NEIGHBOUR_WGS84, FAR_AWAY_WGS84],
        **{"building:levels": ["2", "5", "9"]},
    )
    monkeypatch.setattr(surroundings_helper.osmnx, "features_from_polygon", fake_features_from_polygon([osm]))

    surroundings_helper.main(config)

    result = gpd.read_file(locator.get_surroundings_geometry())
    assert result.crs.to_epsg() == 32632
    assert list(result["name"]) == ["CEA1000"]
    assert list(result["floors_ag"]) == [5]


def test_main_writes_empty_surroundings_when_nothing_is_nearby(tmp_path, monkeypatch):
    config, locator = _scenario(tmp_path, zone_crs=UTM32N)
    osm = osm_buildings([ZONE_WGS84])
    monkeypatch.setattr(surroundings_helper.osmnx, "features_from_polygon", fake_features_from_polygon([osm]))

    surroundings_helper.main(config)

    result = gpd.read_file(locator.get_surroundings_geometry())
    assert result.empty
    assert result.crs.to_epsg() == 32632


def test_main_requires_existing_scenario(tmp_path):
    config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    config.project = str(tmp_path)
    config.scenario_name = "does-not-exist"
    with pytest.raises(AssertionError):
        surroundings_helper.main(config)
