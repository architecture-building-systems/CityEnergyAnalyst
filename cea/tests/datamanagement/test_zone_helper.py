import math
import os

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from geopandas.testing import assert_geodataframe_equal
from osmnx._errors import InsufficientResponseError
from shapely import GeometryCollection, LineString, MultiPolygon, Point, Polygon, box

import cea.config
from cea.datamanagement import zone_helper
from cea.datamanagement.databases_verification import COLUMNS_ZONE, MINIMUM_STOREY_HEIGHT_M
from cea.datamanagement.utils import VOID_HEIGHT_COLUMN
from cea.demand import constants
from cea.inputlocator import InputLocator
from cea.tests.datamanagement.fakes import fake_features_from_polygon, osm_buildings

SITE_WGS84 = box(8.5130, 47.1755, 8.5155, 47.1780)
BUILDING_A = box(8.5135, 47.1760, 8.5138, 47.1763)
BUILDING_B = box(8.5141, 47.1760, 8.5144, 47.1763)
BUILDING_C = box(8.5147, 47.1760, 8.5150, 47.1763)


# fix_overlapping_geoms edits geometries through chained assignment, which pandas 3 silently drops
OVERLAP_NOOP = pytest.mark.xfail(strict=True, reason="overlapping geometries are never cut, see #4104")


def _osm(geometries, **columns):
    return osm_buildings(geometries, **columns)


def _assign(shapefile, height=None, floors=None, height_bg=3.0, floors_bg=1):
    return zone_helper.assign_attributes(shapefile, height, floors, height_bg, floors_bg, key="B")


class TestCleanGeometries:
    def test_clean_geometries(self):
        raw_geometries = gpd.GeoDataFrame({"geometry": [Point(0, 0), Polygon([(0, 0), (0, 1), (1, 0)])]})
        expected_output = gpd.GeoDataFrame({"geometry": [Polygon([(0, 0), (0, 1), (1, 0)])]})
        output = zone_helper.clean_geometries(raw_geometries).reset_index(drop=True)
        assert_geodataframe_equal(output, expected_output)

    def test_drops_null_geometries(self):
        raw_geometries = gpd.GeoDataFrame({"geometry": [None, box(0, 0, 1, 1)]})
        assert len(zone_helper.clean_geometries(raw_geometries)) == 1

    def test_explodes_multipolygons_and_geometry_collections(self):
        raw_geometries = gpd.GeoDataFrame({"geometry": [
            MultiPolygon([box(0, 0, 1, 1), box(5, 5, 6, 6)]),
            GeometryCollection([box(10, 10, 11, 11), LineString([(0, 0), (1, 1)])]),
        ]})
        output = zone_helper.clean_geometries(raw_geometries)
        assert len(output) == 3
        assert set(output.geometry.geom_type) == {"Polygon"}

    def test_flatten_geometries_drops_points_and_lines(self):
        raw_geometries = gpd.GeoDataFrame({"geometry": [Point(0, 0), LineString([(0, 0), (1, 1)]), box(0, 0, 1, 1)]})
        output = zone_helper.flatten_geometries(raw_geometries)
        assert list(output.geometry.geom_type) == ["Polygon"]


class TestParseBuildingFloors:
    @pytest.mark.parametrize("floors, expected", [
        ("3", 3.0),
        ("2.5", 2.5),
        ("3,5", 5.0),
        ("2;4", 4.0),
        ("1; 6", 6.0),
    ])
    def test_parses_numbers_and_lists(self, floors, expected):
        assert zone_helper.parse_building_floors(floors) == expected

    @pytest.mark.parametrize("floors", ["many", "", "3 and a half", "3,x"])
    def test_unparseable_is_nan(self, floors):
        assert math.isnan(zone_helper.parse_building_floors(floors))


class TestAssignAttributesUserValues:
    def test_height_only_derives_floors(self):
        result = _assign(_osm([BUILDING_A, BUILDING_B]), height=10.0)
        assert list(result["height_ag"]) == [10.0, 10.0]
        assert list(result["floors_ag"]) == [int(10.0 // constants.H_F)] * 2
        assert set(result["reference"]) == {"User - assumption"}

    def test_floors_only_derives_height(self):
        result = _assign(_osm([BUILDING_A]), floors=4)
        assert list(result["floors_ag"]) == [4]
        assert list(result["height_ag"]) == [4 * constants.H_F]

    def test_height_and_floors_are_taken_as_given(self):
        result = _assign(_osm([BUILDING_A]), height=20.0, floors=5)
        assert (result["height_ag"].iloc[0], result["floors_ag"].iloc[0]) == (20.0, 5)

    def test_below_ground_values_are_applied(self):
        result = _assign(_osm([BUILDING_A]), floors=2, height_bg=6.0, floors_bg=2)
        assert (result["height_bg"].iloc[0], result["floors_bg"].iloc[0]) == (6.0, 2)

    def test_sub_storey_height_becomes_one_plausible_storey(self):
        result = _assign(_osm([BUILDING_A]), height=1.0)
        assert result["floors_ag"].iloc[0] == 1
        assert result["height_ag"].iloc[0] == constants.H_F

    def test_names_start_at_1000(self):
        result = _assign(_osm([BUILDING_A, BUILDING_B]), floors=2)
        assert list(result["name"]) == ["B1000", "B1001"]


class TestAssignAttributesFromOsm:
    def test_without_levels_or_height_uses_cea_assumption(self):
        result = _assign(_osm([BUILDING_A, BUILDING_B]))
        assert set(result["reference"]) == {"CEA Assumption"}
        assert list(result["floors_ag"]) == [3, 3]
        assert list(result["height_ag"]) == [3 * constants.H_F] * 2
        assert list(result[VOID_HEIGHT_COLUMN]) == [0.0, 0.0]

    def test_levels_only(self):
        result = _assign(_osm([BUILDING_A, BUILDING_B], **{"building:levels": ["4", "6"]}))
        assert list(result["floors_ag"]) == [4, 6]
        assert list(result["height_ag"]) == [4 * constants.H_F, 6 * constants.H_F]
        assert set(result["reference"]) == {"OSM - as it is"}

    def test_roof_levels_add_to_floors(self):
        result = _assign(_osm([BUILDING_A], **{"building:levels": ["4"], "roof:levels": ["1"]}))
        assert result["floors_ag"].iloc[0] == 5

    def test_levels_and_height_are_both_taken_from_osm(self):
        result = _assign(_osm([BUILDING_A], **{"building:levels": ["4"], "height": ["14"]}))
        assert (result["floors_ag"].iloc[0], result["height_ag"].iloc[0]) == (4, 14.0)
        assert result["reference"].iloc[0] == "OSM - as it is"

    def test_height_only_derives_floors_from_height(self):
        result = _assign(_osm([BUILDING_A], height=["12"]))
        assert result["reference"].iloc[0] == "CEA Assumption"
        assert result["floors_ag"].iloc[0] == 4
        assert result["height_ag"].iloc[0] == pytest.approx(12.0)

    def test_zero_height_is_replaced_by_floor_based_height(self):
        result = _assign(_osm([BUILDING_A], **{"building:levels": ["2"], "height": ["0"]}))
        assert result["height_ag"].iloc[0] == 2 * constants.H_F

    def test_height_that_cannot_fit_the_floors_is_rebuilt(self):
        result = _assign(_osm([BUILDING_A], **{"building:levels": ["10"], "height": ["5"]}))
        assert result["floors_ag"].iloc[0] == 10
        assert result["height_ag"].iloc[0] >= 10 * MINIMUM_STOREY_HEIGHT_M
        assert result["height_ag"].iloc[0] == 10 * constants.H_F

    def test_non_numeric_osm_values_are_coerced(self):
        result = _assign(_osm([BUILDING_A, BUILDING_B], **{"building:levels": ["3", "lots"]}))
        assert result["floors_ag"].iloc[0] == 3
        assert result["floors_ag"].iloc[1] >= 1

    @pytest.mark.parametrize("columns, expected", [
        ({"description": ["school"], "addr:housename": ["house"], "amenity": ["cafe"]}, "school"),
        ({"addr:housename": ["house"], "amenity": ["cafe"]}, "house"),
        ({"amenity": ["cafe"]}, "cafe"),
        ({}, None),
    ])
    def test_description_precedence(self, columns, expected):
        description = _assign(_osm([BUILDING_A], **columns))["description"].iloc[0]
        if expected is None:
            assert pd.isna(description)
        else:
            assert description == expected

    def test_amenity_assigns_use_type(self):
        result = _assign(_osm([BUILDING_A, BUILDING_B], amenity=["school", "cafe"]))
        assert result["use_type1"].iloc[0] == "SCHOOL"
        assert result["category"].iloc[0] == "yes"

    def test_minimum_level_columns_are_accepted(self):
        result = _assign(_osm([BUILDING_A], **{"building:levels": ["3"], "building:min_level": ["1"],
                                                "min_height": ["2"]}))
        assert result["floors_ag"].iloc[0] == 3
        assert {"height_bg", "floors_bg"} <= set(result.columns)


class TestAssignAttributesAdditional:
    def test_missing_address_columns_are_created_empty(self):
        result = zone_helper.assign_attributes_additional(_osm([BUILDING_A]))
        for column in ["house_no", "street", "postcode", "house_name", "resi_type", "city", "country"]:
            assert result[column].iloc[0] == ""

    def test_present_address_columns_are_mapped(self):
        result = zone_helper.assign_attributes_additional(_osm(
            [BUILDING_A], **{"addr:housenumber": ["7"], "addr:street": ["Bahnhofstrasse"], "addr:postcode": ["6300"],
                             "addr:housename": ["Haus"], "residential": ["hdb"], "addr:city": ["Zug"],
                             "addr:country": ["CH"]}))
        row = result.iloc[0]
        assert (row["house_no"], row["street"], row["postcode"], row["house_name"], row["resi_type"], row["city"],
                row["country"]) == ("7", "Bahnhofstrasse", "6300", "Haus", "hdb", "Zug", "CH")


class TestFixOverlappingGeoms:
    @staticmethod
    def _buildings(geometries, heights, references=None, **columns):
        buildings = gpd.GeoDataFrame(
            {"height_ag": heights, "height_bg": [0.0] * len(geometries),
             "reference": references or ["CEA Assumption"] * len(geometries), **columns},
            geometry=geometries, crs="EPSG:4326")
        return buildings

    @staticmethod
    def _zone():
        return gpd.GeoDataFrame(geometry=[SITE_WGS84], crs="EPSG:4326")

    def test_non_overlapping_buildings_are_unchanged(self):
        buildings = self._buildings([BUILDING_A, BUILDING_B], [9.0, 9.0])
        result = zone_helper.fix_overlapping_geoms(buildings.copy(), self._zone())
        assert result.geometry.equals(buildings.geometry)

    @OVERLAP_NOOP
    def test_taller_building_cuts_the_lower_one(self):
        low = box(8.5135, 47.1760, 8.5140, 47.1763)
        tall = box(8.5138, 47.1760, 8.5143, 47.1763)
        result = zone_helper.fix_overlapping_geoms(self._buildings([low, tall], [6.0, 30.0]), self._zone())
        assert result.geometry.iloc[1].equals(tall)
        assert result.geometry.iloc[0].area < low.area
        assert not result.geometry.iloc[0].intersects(tall.buffer(-1e-9))

    @OVERLAP_NOOP
    def test_osm_building_takes_priority_over_assumed_one(self):
        first = box(8.5135, 47.1760, 8.5140, 47.1763)
        second = box(8.5138, 47.1760, 8.5143, 47.1763)
        # The OSM building is the lower of the two, but still wins the overlap
        result = zone_helper.fix_overlapping_geoms(
            self._buildings([first, second], [6.0, 30.0], ["OSM - as it is", "CEA Assumption"]), self._zone())
        assert result.geometry.iloc[0].equals(first)
        assert result.geometry.iloc[1].area < second.area

    @OVERLAP_NOOP
    def test_osm_priority_works_in_either_order(self):
        first = box(8.5135, 47.1760, 8.5140, 47.1763)
        second = box(8.5138, 47.1760, 8.5143, 47.1763)
        result = zone_helper.fix_overlapping_geoms(
            self._buildings([first, second], [30.0, 6.0], ["CEA Assumption", "OSM - as it is"]), self._zone())
        assert result.geometry.iloc[1].equals(second)
        assert result.geometry.iloc[0].area < first.area

    def test_buildings_without_vertical_overlap_are_both_kept_whole(self):
        underground = box(8.5135, 47.1760, 8.5140, 47.1763)
        high_up = box(8.5138, 47.1760, 8.5143, 47.1763)
        buildings = self._buildings([underground, high_up], [5.0, 20.0])
        buildings["height_bg"] = [0.0, -10.0]
        result = zone_helper.fix_overlapping_geoms(buildings, self._zone())
        assert result.geometry.iloc[0].equals(underground)
        assert result.geometry.iloc[1].equals(high_up)

    def test_missing_use_information_takes_the_mode_of_overlapping_buildings(self):
        a = box(8.5135, 47.1760, 8.5140, 47.1763)
        b = box(8.5138, 47.1760, 8.5143, 47.1763)
        c = box(8.5139, 47.1760, 8.5144, 47.1763)
        buildings = self._buildings([a, b, c], [9.0, 9.0, 9.0], building=["office", None, "office"])
        result = zone_helper.fix_overlapping_geoms(buildings, self._zone())
        assert result["building"].iloc[1] == "office"


class TestParseYear:
    @pytest.mark.parametrize("year, expected", [
        ("C19", 1900), ("late 1920s", 1920), ("1860", 1860), ("1999-05-01", 1999), ("1950", 1950), (1975, 1975),
    ])
    def test_formats(self, year, expected):
        assert zone_helper.parse_year(year) == expected

    def test_invalid_year_raises(self):
        with pytest.raises(ValueError):
            zone_helper.parse_year("sometime")


class TestCalculateAge:
    def test_explicit_year_is_applied_to_every_building(self):
        result = zone_helper.calculate_age(_osm([BUILDING_A, BUILDING_B]), 1985)
        assert list(result["year"]) == [1985, 1985]

    def test_start_dates_from_osm_with_median_fill(self):
        zone_df = _osm([BUILDING_A, BUILDING_B, BUILDING_C], start_date=["1950", "C19", np.nan])
        result = zone_helper.calculate_age(zone_df, None)
        assert list(result["year"][:2]) == [1950, 1900]
        assert result["year"].iloc[2] == 1925

    def test_missing_start_dates_default_to_2000(self):
        result = zone_helper.calculate_age(_osm([BUILDING_A]), None)
        assert result["year"].iloc[0] == 2000


class TestCalcCategory:
    STANDARDS = pd.DataFrame({
        "year_start": [0, 1950, 2000], "year_end": [1949, 1999, 2100], "const_type": ["STANDARD1", "STANDARD2", "STANDARD3"],
    })

    def test_matches_the_year_range(self):
        assert list(zone_helper.calc_category(self.STANDARDS, [1900, 1960, 2010])) == [
            "STANDARD1", "STANDARD2", "STANDARD3"]

    def test_falls_back_to_the_first_standard_outside_all_ranges(self):
        assert list(zone_helper.calc_category(self.STANDARDS, [3000])) == ["STANDARD1"]


@pytest.fixture
def scenario(tmp_path):
    config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    config.project = str(tmp_path)
    config.scenario_name = "baseline"
    locator = InputLocator(config.scenario)
    construction_csv = locator.get_database_archetypes_construction_type()
    os.makedirs(os.path.dirname(construction_csv), exist_ok=True)
    pd.DataFrame({"year_start": [0, 2000], "year_end": [1999, 2100], "const_type": ["STANDARD1", "STANDARD2"]}
                 ).to_csv(construction_csv, index=False)
    os.makedirs(locator.get_building_geometry_folder(), exist_ok=True)
    gpd.GeoDataFrame({"name": ["site"]}, geometry=[SITE_WGS84], crs="EPSG:4326").to_file(locator.get_site_polygon())
    return config, locator


class TestCalculateTypologyFile:
    def test_use_types_from_osm_categories_and_amenities(self, scenario):
        _, locator = scenario
        zone_df = _assign(_osm([BUILDING_A, BUILDING_B, BUILDING_C],
                               building=["house", "yes", "warehouse"], amenity=[None, "school", None]), floors=2)
        result = zone_helper.calculate_typology_file(locator, zone_df, 1980, "Get it from open street maps")
        assert list(result["use_type1"]) == ["SINGLE_RES", "SCHOOL", "PARKING"]
        assert set(result["const_type"]) == {"STANDARD1"}
        assert list(result["use_type1r"]) == [1.0] * 3

    def test_unknown_categories_take_the_most_common_use_type(self, scenario):
        _, locator = scenario
        zone_df = _assign(_osm([BUILDING_A, BUILDING_B, BUILDING_C], building=["office", "office", "yes"]), floors=2)
        result = zone_helper.calculate_typology_file(locator, zone_df, 2010, "Get it from open street maps")
        assert list(result["use_type1"]) == ["OFFICE", "OFFICE", "OFFICE"]
        assert set(result["const_type"]) == {"STANDARD2"}

    def test_no_classifiable_buildings_default_to_multi_res(self, scenario):
        _, locator = scenario
        zone_df = _assign(_osm([BUILDING_A]), floors=2)
        result = zone_helper.calculate_typology_file(locator, zone_df, 2010, "Get it from open street maps")
        assert list(result["use_type1"]) == ["MULTI_RES"]

    def test_explicit_occupancy_type_is_applied_to_all(self, scenario):
        _, locator = scenario
        zone_df = _assign(_osm([BUILDING_A, BUILDING_B], building=["house", "office"]), floors=2)
        result = zone_helper.calculate_typology_file(locator, zone_df, 2010, "HOTEL")
        assert list(result["use_type1"]) == ["HOTEL", "HOTEL"]
        assert list(result["use_type2"]) == ["NONE", "NONE"]


class TestPolygonToZone:
    @staticmethod
    def _polygon():
        return gpd.GeoDataFrame(geometry=[SITE_WGS84], crs="EPSG:4326")

    def test_building_parts_are_merged_and_force_overlap_fixing(self, monkeypatch):
        buildings = _osm([BUILDING_A], **{"building:levels": ["4"]})
        parts = _osm([box(8.5136, 47.1761, 8.5137, 47.1762)], building=["part"], **{"building:levels": ["6"]})
        monkeypatch.setattr(zone_helper.osmnx, "features_from_polygon", fake_features_from_polygon([buildings, parts]))

        zone = zone_helper.polygon_to_zone(None, 1, None, 3.0, False, True, self._polygon())

        assert len(zone) == 2
        assert list(zone["name"]) == ["B1000", "B1001"]

    def test_missing_building_parts_are_ignored(self, monkeypatch):
        buildings = _osm([BUILDING_A, BUILDING_B])
        monkeypatch.setattr(zone_helper.osmnx, "features_from_polygon", fake_features_from_polygon(
            [buildings, InsufficientResponseError("no building parts")]))

        zone = zone_helper.polygon_to_zone(None, 1, None, 3.0, False, True, self._polygon())

        assert len(zone) == 2

    def test_overlap_fixing_can_be_requested_without_parts(self, monkeypatch):
        buildings = _osm([box(8.5135, 47.1760, 8.5140, 47.1763), box(8.5138, 47.1760, 8.5143, 47.1763)],
                         **{"building:levels": ["2", "8"]})
        monkeypatch.setattr(zone_helper.osmnx, "features_from_polygon", fake_features_from_polygon([buildings]))

        zone = zone_helper.polygon_to_zone(None, 1, None, 3.0, True, False, self._polygon())

        assert len(zone) == 2
        assert not zone.geometry.is_empty.any()


class TestMain:
    def test_writes_zone_shapefile_with_all_required_columns(self, scenario, monkeypatch):
        config, locator = scenario
        config.zone_helper.include_building_parts = False
        config.zone_helper.fix_overlapping_geometries = False
        buildings = _osm([BUILDING_A, BUILDING_B, BUILDING_C], building=["house", "office", "office"],
                         **{"building:levels": ["3", "5", "8"], "start_date": ["1960", "2005", "1999"]})
        monkeypatch.setattr(zone_helper.osmnx, "features_from_polygon", fake_features_from_polygon([buildings]))

        zone_helper.main(config)

        zone = gpd.read_file(locator.get_zone_geometry())
        assert set(COLUMNS_ZONE) - {"geometry"} <= set(zone.columns)
        assert len(zone) == 3
        assert zone.crs.to_epsg() == 32632
        assert list(zone["use_type1"]) == ["SINGLE_RES", "OFFICE", "OFFICE"]
        assert list(zone["const_type"]) == ["STANDARD1", "STANDARD2", "STANDARD1"]
        assert list(zone["floors_ag"]) == [3, 5, 8]

    @pytest.mark.xfail(strict=True, reason="height_vd is not written for user-supplied heights, see #4103")
    def test_user_assumptions_override_osm_attributes(self, scenario, monkeypatch):
        config, locator = scenario
        config.zone_helper.include_building_parts = False
        config.zone_helper.fix_overlapping_geometries = False
        config.zone_helper.floors_ag = 2
        config.zone_helper.year_construction = 2015
        config.zone_helper.occupancy_type = "OFFICE"
        buildings = _osm([BUILDING_A, BUILDING_B], **{"building:levels": ["9", "9"]})
        monkeypatch.setattr(zone_helper.osmnx, "features_from_polygon", fake_features_from_polygon([buildings]))

        zone_helper.main(config)

        zone = gpd.read_file(locator.get_zone_geometry())
        assert set(zone["floors_ag"]) == {2}
        assert set(zone["year"]) == {2015}
        assert set(zone["use_type1"]) == {"OFFICE"}

    def test_requires_existing_scenario(self, tmp_path):
        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.project = str(tmp_path)
        config.scenario_name = "does-not-exist"
        with pytest.raises(AssertionError):
            zone_helper.main(config)
