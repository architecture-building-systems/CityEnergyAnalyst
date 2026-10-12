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


# The storey-height rule runs before the void-deck-specific ones, so a void deck that leaves no
# room for the floors is reported by it; the column rules catch the rest.
STOREY_RULE = r"less than 2\.0 m of height per enclosed floor"


@pytest.mark.parametrize("extra, message", [
    ({VOID_FLOORS_COLUMN: [1.5, 0]}, "no decimals"),
    ({VOID_FLOORS_COLUMN: [-1, 0]}, "negative values"),
    ({VOID_FLOORS_COLUMN: [4, 0]}, STOREY_RULE),
    ({VOID_FLOORS_COLUMN: ["a", "b"]}, "integer type"),
    # Not superseded for B2, where height_vd is blank, so the legacy rule still applies there.
    ({VOID_FLOORS_COLUMN: [1, 4], VOID_HEIGHT_COLUMN: [3.0, NAN]}, STOREY_RULE),
    ({VOID_HEIGHT_COLUMN: [-1.0, 0.0]}, "negative values"),
    ({VOID_HEIGHT_COLUMN: [12.0, 0.0]}, STOREY_RULE),
], ids=["fractional", "negative", "swallows building", "text", "legacy applies where blank",
        "negative metres", "metres swallow building"])
def test_verification_still_rejects_genuinely_bad_values(extra, message):
    with pytest.raises(Exception, match=message):
        verify_input_geometry_zone(make_zone(extra))


def test_the_void_column_rules_reject_a_void_deck_swallowing_the_building_on_their_own():
    """Unreachable through `verify_input_geometry_zone` (the storey rule fires first), but the
    column checks are public and must not depend on running after it."""
    from cea.datamanagement.databases_verification import check_void_deck_values, check_void_height_values

    with pytest.raises(ValueError, match="greater than or equal"):
        check_void_deck_values(make_zone({VOID_FLOORS_COLUMN: [4, 0]}))
    with pytest.raises(ValueError, match="nothing enclosed"):
        check_void_height_values(make_zone({VOID_HEIGHT_COLUMN: [12.0, 0.0]}))


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


# --------------------------------------------------------------------------- input editor save


class _NoChoices(dict):
    def __missing__(self, key):
        return "", []


@pytest.fixture
def editor(tmp_path, monkeypatch):
    """A scenario on disk plus helpers that act as the input editor: GET, edit, PUT."""
    import asyncio
    import copy

    from fastapi import HTTPException

    from cea.inputlocator import InputLocator
    from cea.interfaces.dashboard.api import inputs

    # Choice lists come from the construction database, which is not what is under test.
    monkeypatch.setattr(inputs, "_build_choices_cache", lambda locator: _NoChoices())

    scenario = str(tmp_path / "scenario")
    locator = InputLocator(scenario)

    class Editor:
        scenario_path = scenario
        zone_path = locator.get_zone_geometry()

        def write(self, extra=None):
            locator.ensure_parent_folder_exists(self.zone_path)
            zone = make_zone(extra)
            zone["year"], zone["const_type"] = 2000, "MULTI_RES"
            for i in (1, 2, 3):
                zone[f"use_type{i}"] = "MULTI_RES" if i == 1 else "NONE"
                zone[f"use_type{i}r"] = 1.0 if i == 1 else 0.0
            zone.to_file(self.zone_path)

        def load(self):
            store = inputs.get_building_properties(scenario)
            geojson, crs = inputs.df_to_json(self.zone_path, root=scenario)
            return {"tables": {"zone": store["tables"]["zone"]},
                    "geojsons": {"zone": geojson}, "crs": {"zone": crs}}

        def save(self, form):
            """Returns None on success, or the list of problems the 400 carried."""
            try:
                asyncio.run(inputs.save_all_inputs(scenario, inputs.InputForm(**copy.deepcopy(form))))
            except HTTPException as e:
                return e.detail["problems"]
            return None

        @staticmethod
        def edit(form, name, **values):
            """Change cells as the editor does: in the table and on the map feature."""
            form["tables"]["zone"][name].update(values)
            for feature in form["geojsons"]["zone"]["features"]:
                if feature["properties"]["name"] == name:
                    feature["properties"].update(values)

        def stored(self):
            return gpd.read_file(self.zone_path).drop(columns="geometry")

    return Editor()


def test_a_valid_zone_saves(editor):
    editor.write()
    form = editor.load()
    editor.edit(form, "B1", floors_ag=3)

    assert editor.save(form) is None
    assert editor.stored().set_index("name").loc["B1", "floors_ag"] == 3


@pytest.mark.parametrize("extra", [s[1] for s in VALID_SHAPES], ids=[s[0] for s in VALID_SHAPES])
def test_every_valid_void_deck_shape_saves(editor, extra):
    """#4109: a zone with no or blank void columns must not be refused, or rewritten wrongly."""
    editor.write(extra)
    form = editor.load()

    assert editor.save(form) is None
    assert set(editor.stored().columns) >= {"name", "floors_ag", "height_ag"}


@pytest.mark.parametrize("edit, fragment", [
    ({"floors_ag": 20}, "B1"),                       # 12 m over 20 storeys: 0.6 m each
    ({"floors_ag": 0}, "floor"),
    ({"floors_bg": 2}, "B1"),                        # basement floors without a depth
    ({"height_ag": -3.0}, "negative"),
], ids=["too many floors", "no floors", "basement without depth", "negative height"])
def test_an_inconsistent_zone_is_refused_and_nothing_is_written(editor, edit, fragment):
    editor.write()
    before = editor.stored()
    form = editor.load()
    editor.edit(form, "B1", **edit)

    problems = editor.save(form)

    assert problems and any(fragment in p for p in problems), problems
    pd.testing.assert_frame_equal(editor.stored(), before)


@pytest.mark.parametrize("edit", [
    {VOID_HEIGHT_COLUMN: 12.0},                       # void deck swallows the building
    {VOID_HEIGHT_COLUMN: -1.0},
    {VOID_FLOORS_COLUMN: 4},                          # void_deck == floors_ag
    {VOID_FLOORS_COLUMN: 2.5},
], ids=["metres swallow building", "negative metres", "legacy swallows building", "fractional legacy"])
def test_a_bad_void_deck_is_refused(editor, edit):
    editor.write({VOID_FLOORS_COLUMN: [0, 0], VOID_HEIGHT_COLUMN: [NAN, NAN]})
    form = editor.load()
    editor.edit(form, "B1", **edit)

    assert editor.save(form)


@pytest.mark.parametrize("column", [VOID_FLOORS_COLUMN, VOID_HEIGHT_COLUMN])
def test_text_in_a_void_deck_cell_is_refused_not_blanked(editor, column):
    """Text must not be read as a blank (= no void deck) and then written to the shapefile."""
    editor.write({column: [NAN, NAN]})
    form = editor.load()
    editor.edit(form, "B1", **{column: "abc"})

    assert editor.save(form)


def test_clearing_a_void_deck_cell_saves(editor):
    editor.write({VOID_FLOORS_COLUMN: [1, 1], VOID_HEIGHT_COLUMN: [3.0, 3.0]})
    form = editor.load()
    editor.edit(form, "B1", **{VOID_HEIGHT_COLUMN: None, VOID_FLOORS_COLUMN: None})

    assert editor.save(form) is None
    stored = editor.stored().set_index("name")
    assert pd.isna(stored.loc["B1", VOID_HEIGHT_COLUMN]) and pd.isna(stored.loc["B1", VOID_FLOORS_COLUMN])


def test_a_row_without_a_footprint_is_not_refused_for_it(editor):
    """The editor keeps such rows so they can be fixed; attribute checks must not reject them."""
    editor.write()
    form = editor.load()
    form["geojsons"]["zone"]["features"].pop(1)   # B2 drawn nowhere, still in the table

    assert editor.save(form) is None
    assert set(editor.stored()["name"]) == {"B1", "B2"}


def test_attribute_verification_ignores_geometry():
    from shapely.geometry import Point
    from cea.datamanagement.databases_verification import verify_zone_attributes

    zone = make_zone()
    zone["geometry"] = [Point(0, 0), None]

    verify_zone_attributes(zone)
    with pytest.raises(Exception):
        verify_input_geometry_zone(zone)


# --------------------------------------------------------------------------- schema -> editor contract


ALWAYS_SENT_KEYS = {"type", "description", "unit"}
# Sent transformed (`choice` -> `path` + `choices`) or meaningless to the editor.
NOT_FORWARDED_KEYS = {"choice", "primary", "foreign_key", "used_by"}


def test_every_schema_column_key_is_classified():
    """A rule added to schemas.yml reaches the input editor only if its key is forwarded.

    Failing here means a new column key was added: decide whether the editor should enforce it
    (add to `FORWARDED_COLUMN_KEYS`, and teach the GUI) or not (add to `NOT_FORWARDED_KEYS`).
    """
    from cea.interfaces.dashboard.api.inputs import FORWARDED_COLUMN_KEYS, INPUTS

    used = {key for db in INPUTS.values() for column in db["columns"].values() for key in column}
    unclassified = used - set(FORWARDED_COLUMN_KEYS) - ALWAYS_SENT_KEYS - NOT_FORWARDED_KEYS

    assert not unclassified, f"schema keys the input editor never receives: {sorted(unclassified)}"


def test_the_editor_receives_numeric_bounds(editor):
    from cea.interfaces.dashboard.api import inputs

    editor.write({VOID_FLOORS_COLUMN: [0, 0]})
    columns = inputs.get_building_properties(editor.scenario_path)["columns"]["zone"]

    assert columns["floors_ag"]["min"] == 1
    assert columns["height_ag"]["min"] == 2.0
    assert columns["use_type1r"]["max"] == 1.0
    assert columns[VOID_FLOORS_COLUMN]["nullable"] and columns[VOID_HEIGHT_COLUMN]["nullable"]
