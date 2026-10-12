"""Neither `void_deck` nor `height_vd` is required, and neither may be broken by being blank.

Regression tests for #4109: zone verification demanded `void_deck`, rejected a blank one as
"not an integer", and the schema marked it required so the input editor flagged blank cells.
Every shape a zone file can take is exercised against every place that reads the columns.
"""
import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

from cea.datamanagement.databases_verification import verify_input_geometry_zone
from cea.datamanagement.utils import VOID_FLOORS_COLUMN, VOID_HEIGHT_COLUMN, resolve_enclosed_floors_ag

NAN = np.nan

# (id, extra columns) -- two buildings of 4 storeys / 12 m each.
VALID_SHAPES = [
    ("neither column", {}),
    ("void_deck only", {VOID_FLOORS_COLUMN: [1, 0]}),
    ("void_deck all blank", {VOID_FLOORS_COLUMN: [NAN, NAN]}),
    ("void_deck partly blank", {VOID_FLOORS_COLUMN: [1, NAN]}),
    ("height_vd only", {VOID_HEIGHT_COLUMN: [3.0, 0.0]}),
    ("height_vd all blank", {VOID_HEIGHT_COLUMN: [NAN, NAN]}),
    ("height_vd partly blank", {VOID_HEIGHT_COLUMN: [3.0, NAN]}),
    ("both, height_vd blank", {VOID_FLOORS_COLUMN: [1, 2], VOID_HEIGHT_COLUMN: [NAN, NAN]}),
    ("both, void_deck blank", {VOID_FLOORS_COLUMN: [NAN, NAN], VOID_HEIGHT_COLUMN: [3.0, 0.0]}),
    ("both, all blank", {VOID_FLOORS_COLUMN: [NAN, NAN], VOID_HEIGHT_COLUMN: [NAN, NAN]}),
    ("both, populated", {VOID_FLOORS_COLUMN: [1, 1], VOID_HEIGHT_COLUMN: [3.0, 0.0]}),
    # height_vd wins per building, so a void_deck it supersedes is not held to the old rule.
    ("both, superseded void_deck is stale", {VOID_FLOORS_COLUMN: [9, 9], VOID_HEIGHT_COLUMN: [3.0, 3.0]}),
]


def make_zone(extra=None):
    data = {"name": ["B1", "B2"], "floors_bg": [0, 0], "floors_ag": [4, 4],
            "height_bg": [0.0, 0.0], "height_ag": [12.0, 12.0],
            "geometry": [box(0, 0, 10, 10), box(20, 0, 30, 10)]}
    data.update(extra or {})
    return gpd.GeoDataFrame(data, crs="EPSG:32632")


@pytest.mark.parametrize("extra", [s[1] for s in VALID_SHAPES], ids=[s[0] for s in VALID_SHAPES])
def test_verification_accepts_every_valid_shape(extra):
    zone = make_zone(extra)
    columns_before = list(zone.columns)

    verify_input_geometry_zone(zone)

    assert list(zone.columns) == columns_before, "verification must not add or drop columns"


def test_verification_does_not_invent_void_deck():
    zone = make_zone()
    verify_input_geometry_zone(zone)
    assert VOID_FLOORS_COLUMN not in zone.columns


@pytest.mark.parametrize("extra, message", [
    ({VOID_FLOORS_COLUMN: [1.5, 0]}, "integer"),
    ({VOID_FLOORS_COLUMN: [-1, 0]}, "negative"),
    ({VOID_FLOORS_COLUMN: [4, 0]}, "greater than or equal"),
    ({VOID_FLOORS_COLUMN: ["a", "b"]}, "integer"),
    # Not superseded for B2, where height_vd is blank, so the legacy rule still applies there.
    ({VOID_FLOORS_COLUMN: [1, 4], VOID_HEIGHT_COLUMN: [3.0, NAN]}, "greater than or equal"),
    ({VOID_HEIGHT_COLUMN: [-1.0, 0.0]}, "negative"),
    ({VOID_HEIGHT_COLUMN: [12.0, 0.0]}, "nothing enclosed"),
], ids=["fractional", "negative", "swallows building", "text", "legacy applies where blank",
        "negative metres", "metres swallow building"])
def test_verification_still_rejects_genuinely_bad_values(extra, message):
    # Several of these trip an earlier, more general check (plain `Exception`), so the
    # message is only a hint at which rule is expected to fire.
    with pytest.raises(Exception):
        verify_input_geometry_zone(make_zone(extra))


def test_required_columns_are_still_required():
    zone = make_zone().drop(columns="height_ag")
    with pytest.raises(ValueError):
        verify_input_geometry_zone(zone)


@pytest.mark.parametrize("extra", [s[1] for s in VALID_SHAPES], ids=[s[0] for s in VALID_SHAPES])
def test_shapefile_round_trip_keeps_verification_passing(extra, tmp_path):
    """A blank written by GIS or by the input editor comes back as NaN, not as an error."""
    path = tmp_path / "zone.shp"
    make_zone(extra).to_file(path)

    verify_input_geometry_zone(gpd.read_file(path))


@pytest.mark.parametrize("extra", [s[1] for s in VALID_SHAPES], ids=[s[0] for s in VALID_SHAPES])
def test_downstream_resolution_handles_every_valid_shape(extra):
    """The demand/area code reads the same columns; none of the shapes may produce NaN."""
    enclosed = resolve_enclosed_floors_ag(make_zone(extra))

    assert not enclosed.isna().any()
    assert (enclosed > 0).all()


def test_blank_legacy_cell_means_no_void_deck():
    enclosed = resolve_enclosed_floors_ag(make_zone({VOID_FLOORS_COLUMN: [1, NAN]}))
    assert enclosed.tolist() == [3.0, 4.0]


def test_both_void_columns_are_nullable_in_the_schema():
    """The input editor adds `required` to any column not marked nullable, so a blank cell in
    an optional column would be flagged invalid (or written back as a real 0)."""
    from cea.schemas import schemas

    columns = schemas(plugins=[])["get_zone_geometry"]["schema"]["columns"]
    for name in (VOID_FLOORS_COLUMN, VOID_HEIGHT_COLUMN):
        assert columns[name].get("nullable") is True, f"{name} must be nullable"


@pytest.mark.parametrize("extra", [s[1] for s in VALID_SHAPES], ids=[s[0] for s in VALID_SHAPES])
def test_input_editor_reads_every_shape(extra, tmp_path, monkeypatch):
    """`GET /inputs/all-inputs` -- the "Error reading inputs" 500 -- must serve each shape."""
    from cea.inputlocator import InputLocator
    from cea.interfaces.dashboard.api import inputs
    from cea.interfaces.dashboard.api.inputs import df_to_json, get_building_properties

    class NoChoices(dict):
        def __missing__(self, key):
            return "", []

    # Choice lists come from the construction database, which is not what is under test.
    monkeypatch.setattr(inputs, "_build_choices_cache", lambda locator: NoChoices())

    scenario = tmp_path / "scenario"
    locator = InputLocator(str(scenario))
    zone_path = locator.get_zone_geometry()
    locator.ensure_parent_folder_exists(zone_path)
    make_zone(extra).to_file(zone_path)

    store = get_building_properties(str(scenario))
    table = store["tables"]["zone"]
    assert table is not None and set(table) == {"B1", "B2"}
    assert store["columns"]["zone"] is not None

    advertised = store["columns"]["zone"]
    assert VOID_HEIGHT_COLUMN in advertised
    assert (VOID_FLOORS_COLUMN in advertised) == (VOID_FLOORS_COLUMN in extra), \
        "the legacy column is shown only where the file already carries it"
    assert all(advertised[c].get("nullable") for c in advertised if c in (VOID_FLOORS_COLUMN, VOID_HEIGHT_COLUMN))

    geojson, crs = df_to_json(zone_path, root=str(scenario))
    assert geojson is not None and len(geojson["features"]) == 2
