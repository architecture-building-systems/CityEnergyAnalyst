"""A row with no footprint must not blank the whole map, and must say so clearly.

A `zone.shp` carrying one row with a null geometry made `get_lat_lon_projected_shapefile`
reject the entire file, so the Input Editor drew nothing at all -- every other building
included -- while the table beside it still listed them. The error said "invalid geometries
must be fixed", which points at a malformed polygon rather than a missing one.

Two different audiences, two different behaviours:

- simulation scripts call the validator directly and still refuse to run, because a building
  with no footprint cannot be simulated
- the editor draws what it can and reports the rest, because that is how the user finds and
  fixes the row
"""

import warnings

import geopandas as gpd
import pytest
from shapely.geometry import Polygon

from cea.utilities.standardize_coordinates import validate_geometries_before_crs_transform


def zone(geometries, names=None):
    names = names or [f"B{i}" for i in range(len(geometries))]
    return gpd.GeoDataFrame({"name": names, "geometry": geometries}, crs="EPSG:4326")


SQUARE = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
BOWTIE = Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])  # self-intersecting


# --------------------------------------------------------------------------- the message


def test_a_missing_geometry_is_reported_as_missing_not_invalid():
    """"Invalid" sends people looking for a broken polygon; the fix here is different."""
    with pytest.raises(ValueError) as raised:
        validate_geometries_before_crs_transform(zone([SQUARE, None], ["B1000", "B1000_V"]))

    message = str(raised.value)
    assert "no geometry at all" in message
    assert "B1000_V" in message
    assert "delete the row" in message, "the message should say what to do about it"
    assert "B1000" in message  # the offending row is named


def test_a_malformed_geometry_is_still_reported_as_malformed():
    with pytest.raises(ValueError) as raised:
        validate_geometries_before_crs_transform(zone([SQUARE, BOWTIE], ["ok", "bowtie"]))

    message = str(raised.value)
    assert "malformed" in message
    assert "bowtie" in message
    assert "no geometry at all" not in message


def test_both_kinds_are_reported_together():
    """One run should tell you about everything wrong, not just the first thing."""
    with pytest.raises(ValueError) as raised:
        validate_geometries_before_crs_transform(
            zone([SQUARE, None, BOWTIE], ["ok", "nogeom", "bowtie"]))

    message = str(raised.value)
    assert "nogeom" in message and "bowtie" in message
    assert "no geometry at all" in message and "malformed" in message


def test_a_clean_file_raises_nothing():
    validate_geometries_before_crs_transform(zone([SQUARE, SQUARE]))


# --------------------------------------------------------------------------- the editor


def test_the_editor_draws_the_buildings_it_can(tmp_path):
    """One null row used to blank the map entirely."""
    from cea.interfaces.dashboard.api.inputs import df_to_json

    path = tmp_path / "zone.shp"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        zone([SQUARE, None], ["B1000", "B1000_V"]).to_file(path)

    geojson, crs = df_to_json(str(path))

    assert geojson is not None, "a null row must not blank the map"
    assert [f["properties"]["name"] for f in geojson["features"]] == ["B1000"]
    assert crs is not None


def test_the_editor_names_the_rows_it_skipped(tmp_path, caplog):
    """The row stays in the table, so the user needs telling which one to fix."""
    import logging

    from cea.interfaces.dashboard.api.inputs import df_to_json

    path = tmp_path / "zone.shp"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        zone([SQUARE, None], ["B1000", "B1000_V"]).to_file(path)

    with caplog.at_level(logging.WARNING):
        df_to_json(str(path))

    assert any("B1000_V" in record.message for record in caplog.records)


def test_a_malformed_geometry_still_stops_the_editor(tmp_path):
    """Only *missing* geometry is skipped.

    A self-intersecting polygon is a real problem with a shape that does exist; silently
    dropping it would hide a building the user believes is there.
    """
    from cea.interfaces.dashboard.api.inputs import df_to_json

    path = tmp_path / "zone.shp"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        zone([SQUARE, BOWTIE], ["ok", "bowtie"]).to_file(path)

    geojson, _ = df_to_json(str(path))
    assert geojson is None


def test_the_editor_can_tell_which_rows_have_no_geometry(tmp_path):
    """The Input Editor highlights these rows without asking the server anything extra.

    It already holds both halves: the table lists every row, the geojson only the ones that
    could be drawn. The difference is exactly the set with no footprint. That keeps the marker
    honest -- it is derived from what was actually rendered, not from a separate flag that
    could go stale.
    """
    from cea.interfaces.dashboard.api.inputs import df_to_json

    path = tmp_path / "zone.shp"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        zone([SQUARE, None, SQUARE], ["B1000", "B1000_V", "B1001"]).to_file(path)

    geojson, _ = df_to_json(str(path))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        table_rows = list(gpd.read_file(path)["name"])

    drawn = {feature["properties"]["name"] for feature in geojson["features"]}
    highlighted = [name for name in table_rows if name not in drawn]

    assert highlighted == ["B1000_V"]
    assert set(drawn) == {"B1000", "B1001"}, "the good buildings still draw"
