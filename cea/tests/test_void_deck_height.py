"""The void deck moves from whole floors (`void_deck`) to metres (`height_vd`).

A void deck is the open, unenclosed portion at the *bottom* of a building. Recording it as an
integer count of floors tied it to the storey grid; `height_vd` records it in metres so it can
sit anywhere.

The two columns count `floors_ag` differently, and that is deliberate:

- with `void_deck`, `floors_ag` spans the whole height, void storeys included
- with `height_vd`, `floors_ag` counts only the enclosed storeys, and the void sits beneath them

The second form is what lets a void deck be taller than a normal storey -- a 4.5 m void deck
under 2.8 m residential floors cannot be put on one uniform grid. `height_ag` means the same
thing in both: void deck plus enclosed solid.

`height_vd` is optional and `void_deck` is never removed, so a scenario that predates this
change keeps working untouched. The tests below pin that: the legacy column is converted at the
building's own storey height, which is the expression the geometry code always used, so legacy
results do not move.
"""

import contextlib
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Polygon

from cea.datamanagement.utils import (
    VOID_FLOORS_COLUMN,
    VOID_HEIGHT_COLUMN,
    enclosed_storey_height,
    enclosed_storey_height_for_row,
    resolve_enclosed_floors_ag,
    resolve_void_height,
    resolve_void_height_for_row,
)
from cea.resources.radiation.geometry_generator import calc_z_levels


@contextlib.contextmanager
def warnings_as_errors():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        yield


def zone(**cols):
    base = {"height_ag": [30.0], "floors_ag": [10]}
    base.update({k: [v] for k, v in cols.items()})
    return pd.DataFrame(base)


# --------------------------------------------------------------------------- resolution


def test_neither_column_means_no_void_deck():
    """Most scenarios have no void decks at all; that must not be an error."""
    assert resolve_void_height(zone()).tolist() == [0.0]


def test_the_legacy_column_converts_at_the_buildings_own_storey_height():
    # 30 m over 10 floors = 3 m storeys, so 2 floors of void is 6 m.
    assert resolve_void_height(zone(**{VOID_FLOORS_COLUMN: 2})).tolist() == [6.0]


def test_the_metre_column_is_used_as_given():
    assert resolve_void_height(zone(**{VOID_HEIGHT_COLUMN: 4.5})).tolist() == [4.5]


def test_the_metre_column_wins_when_both_are_present():
    df = zone(**{VOID_HEIGHT_COLUMN: 4.5, VOID_FLOORS_COLUMN: 2})
    with pytest.warns(RuntimeWarning, match="disagree"):
        assert resolve_void_height(df).tolist() == [4.5]


def test_a_consistent_pair_of_columns_does_not_warn():
    """void_deck=2 at 3 m storeys is 6 m -- agreeing, so there is nothing to report."""
    df = zone(**{VOID_HEIGHT_COLUMN: 6.0, VOID_FLOORS_COLUMN: 2})
    with warnings_as_errors():
        assert resolve_void_height(df).tolist() == [6.0]


def test_blank_cells_mean_no_void_deck_rather_than_nan():
    """A NaN would silently poison every downstream area calculation."""
    df = pd.DataFrame({VOID_HEIGHT_COLUMN: [np.nan], "height_ag": [30.0], "floors_ag": [10]})
    assert resolve_void_height(df).tolist() == [0.0]


@pytest.mark.parametrize("cols", [
    {},
    {VOID_FLOORS_COLUMN: 2},
    {VOID_HEIGHT_COLUMN: 4.5},
    {VOID_HEIGHT_COLUMN: 4.5, VOID_FLOORS_COLUMN: 2},   # both, disagreeing
    {VOID_HEIGHT_COLUMN: 6.0, VOID_FLOORS_COLUMN: 2},   # both, agreeing
    {VOID_HEIGHT_COLUMN: np.nan},                       # column there, cell blank
    {VOID_HEIGHT_COLUMN: np.nan, VOID_FLOORS_COLUMN: 2},  # blank cell, legacy present
    {VOID_FLOORS_COLUMN: np.nan},
    {VOID_HEIGHT_COLUMN: 0.0, VOID_FLOORS_COLUMN: 0},
])
def test_the_row_resolver_matches_the_frame_resolver(cols):
    """`BuildingGeometry[name]` hands back a dict, so the two must not drift apart.

    The blank-cell-with-legacy-column case is the one that matters: a second implementation
    of the precedence rule got it wrong (falling back to `void_deck` where the frame resolver
    treats the present column as authoritative), and no test covered it.
    """
    df = zone(**cols)
    row = df.iloc[0].to_dict()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert resolve_void_height_for_row(row) == pytest.approx(resolve_void_height(df).iloc[0])
        assert enclosed_storey_height_for_row(row) == pytest.approx(
            enclosed_storey_height(df).iloc[0])


def test_the_optional_column_survives_the_zone_column_selection():
    """`BuildingGeometry` selects an explicit column list from zone.shp.

    An optional column left out of that list is dropped before the resolver runs, and every
    void deck silently becomes zero in the demand calculation -- no error, just wrong areas.
    """
    from cea.datamanagement.databases_verification import (
        COLUMNS_ZONE_GEOMETRY,
        OPTIONAL_COLUMNS_ZONE_GEOMETRY,
    )

    assert VOID_HEIGHT_COLUMN in OPTIONAL_COLUMNS_ZONE_GEOMETRY
    assert VOID_HEIGHT_COLUMN not in COLUMNS_ZONE_GEOMETRY, "must stay optional, never required"

    zone_gdf = pd.DataFrame({
        "name": ["B1"], "floors_bg": [0], "floors_ag": [10], VOID_FLOORS_COLUMN: [0],
        "height_bg": [0.0], "height_ag": [30.0], VOID_HEIGHT_COLUMN: [4.5],
    })
    optional = [c for c in OPTIONAL_COLUMNS_ZONE_GEOMETRY if c in zone_gdf.columns]
    selected = zone_gdf[COLUMNS_ZONE_GEOMETRY + optional]

    assert resolve_void_height(selected).tolist() == [4.5]


def test_a_legacy_zone_without_the_optional_column_still_selects():
    """The selection must not demand a column that old scenarios do not have."""
    from cea.datamanagement.databases_verification import (
        COLUMNS_ZONE_GEOMETRY,
        OPTIONAL_COLUMNS_ZONE_GEOMETRY,
    )

    zone_gdf = pd.DataFrame({
        "name": ["B1"], "floors_bg": [0], "floors_ag": [10], VOID_FLOORS_COLUMN: [2],
        "height_bg": [0.0], "height_ag": [30.0],
    })
    optional = [c for c in OPTIONAL_COLUMNS_ZONE_GEOMETRY if c in zone_gdf.columns]
    selected = zone_gdf[COLUMNS_ZONE_GEOMETRY + optional]

    assert resolve_void_height(selected).tolist() == [6.0]


# --------------------------------------------------------------------------- floors_ag


def test_floors_ag_spans_the_void_with_the_legacy_column():
    """void_deck=2 of floors_ag=5 leaves 3 enclosed storeys above a 2-storey void."""
    df = pd.DataFrame({"height_ag": [15.0], "floors_ag": [5], VOID_FLOORS_COLUMN: [2]})
    assert resolve_void_height(df).tolist() == [6.0]
    assert resolve_enclosed_floors_ag(df).tolist() == [3.0]
    assert enclosed_storey_height(df).tolist() == [3.0]


def test_floors_ag_counts_only_enclosed_storeys_with_the_metre_column():
    """The void deck sits beneath floors_ag, not among them."""
    df = pd.DataFrame({"height_ag": [15.0], "floors_ag": [3], VOID_HEIGHT_COLUMN: [6.0]})
    assert resolve_enclosed_floors_ag(df).tolist() == [3.0]
    assert enclosed_storey_height(df).tolist() == [3.0]


def test_both_forms_describe_the_same_building_identically():
    """The whole point of the conversion: writing it either way must give the same building."""
    legacy = pd.DataFrame({"height_ag": [15.0], "floors_ag": [5], VOID_FLOORS_COLUMN: [2]})
    metres = pd.DataFrame({"height_ag": [15.0], "floors_ag": [3], VOID_HEIGHT_COLUMN: [6.0]})

    for fn in (resolve_void_height, resolve_enclosed_floors_ag, enclosed_storey_height):
        assert fn(legacy).iloc[0] == pytest.approx(fn(metres).iloc[0]), fn.__name__

    assert calc_z_levels(*enclosed_of(legacy)) == pytest.approx(calc_z_levels(*enclosed_of(metres)))


def test_a_void_deck_taller_than_a_storey_is_represented_exactly():
    """The case the metre column exists for, and the one whole floors cannot express.

    An HDB-style block: a 4.5 m open void deck under four 2.8 m residential floors. On a single
    uniform storey grid neither the void nor the floors come out right; here both do.
    """
    df = pd.DataFrame({"height_ag": [4.5 + 4 * 2.8], "floors_ag": [4], VOID_HEIGHT_COLUMN: [4.5]})

    assert resolve_enclosed_floors_ag(df).iloc[0] == 4.0
    assert enclosed_storey_height(df).iloc[0] == pytest.approx(2.8)

    footprint = 500.0
    assert footprint * resolve_enclosed_floors_ag(df).iloc[0] == pytest.approx(2000.0)


def test_gross_floor_area_is_always_whole_storeys():
    """Recording the void in metres must not turn the floor count fractional."""
    for void in (0.0, 1.0, 4.5, 5.3, 7.9):
        df = pd.DataFrame({"height_ag": [20.0], "floors_ag": [4], VOID_HEIGHT_COLUMN: [void]})
        assert resolve_enclosed_floors_ag(df).iloc[0] == 4.0


def enclosed_of(df):
    return (resolve_void_height(df).iloc[0],
            float(df["height_ag"].iloc[0]),
            resolve_enclosed_floors_ag(df).iloc[0])


def test_storey_height_excludes_the_void_deck():
    """`floor_height` feeds internal air volume (`Af x floor_height`), so it must be the
    storey height of the *enclosed* part.

    `height_ag / floors_ag` is only that for the legacy column, where `floors_ag` spans the
    void. Alongside `height_vd` it divides the full height by the enclosed floors and
    overstates the storey -- 5 m instead of 3 m for the building below, inflating air volume
    by two thirds.
    """
    from cea.demand.building_properties.building_properties_row import BuildingPropertiesRow

    legacy = {"height_ag": 15.0, "floors_ag": 5, VOID_FLOORS_COLUMN: 2}
    metres = {"height_ag": 15.0, "floors_ag": 3, VOID_HEIGHT_COLUMN: 6.0}
    none = {"height_ag": 15.0, "floors_ag": 5}

    assert BuildingPropertiesRow.get_floor_height(legacy) == pytest.approx(3.0)
    assert BuildingPropertiesRow.get_floor_height(metres) == pytest.approx(3.0)
    assert BuildingPropertiesRow.get_floor_height(none) == pytest.approx(3.0)


def test_the_old_riser_expression_only_worked_because_floors_ag_spanned_the_void():
    """The DHW riser runs the full height, void deck included.

    It used to be written `floors_ag x floor_height`. That equalled `height_ag` exactly while
    `floors_ag` spanned the whole height, so the pipe lengths were right by construction.
    Alongside `height_vd` it no longer does -- which is why those call sites now use
    `height_ag` directly, an identity for legacy scenarios and correct for both.
    """
    from cea.demand.building_properties.building_properties_row import BuildingPropertiesRow

    legacy = {"height_ag": 15.0, "floors_ag": 5, VOID_FLOORS_COLUMN: 2}
    metres = {"height_ag": 15.0, "floors_ag": 3, VOID_HEIGHT_COLUMN: 6.0}

    def old_expression(geometry):
        return geometry["floors_ag"] * BuildingPropertiesRow.get_floor_height(geometry)

    # Legacy: the old expression really was height_ag, so replacing it changed nothing.
    assert old_expression(legacy) == pytest.approx(legacy["height_ag"])

    # Metres: it would have under-counted the riser by the height of the void deck.
    assert old_expression(metres) == pytest.approx(9.0)
    assert old_expression(metres) < metres["height_ag"]


def test_embodied_emissions_run_end_to_end_and_exclude_the_void_deck():
    """The real `lca_embodied` on the bundled reference case, which has a void deck on B1014.

    Two things at once, because this is the only place both are exercised for real:

    - it runs at all on a database migrated from CEA-3, which has no `GHG_biogenic_*` columns
    - B1014's above-ground floor area is its 1 enclosed storey, not all 5
    """
    import pandas as pd

    from cea.analysis.lca.embodied import lca_embodied
    from cea.inputlocator import ReferenceCaseOpenLocator

    locator = ReferenceCaseOpenLocator()
    lca_embodied(2050, locator)

    import geopandas as gpd

    from cea.utilities.standardize_coordinates import (
        get_lat_lon_projected_shapefile,
        get_projected_coordinate_system,
    )

    results = pd.read_csv(locator.get_lca_embodied()).set_index("name")

    # Footprint from the geometry itself, never from the result under test.
    zone = gpd.read_file(locator.get_zone_geometry())
    lat, lon = get_lat_lon_projected_shapefile(zone)
    zone = zone.to_crs(get_projected_coordinate_system(float(lat), float(lon))).set_index("name")
    footprint = float(zone.loc["B1014"].geometry.area)

    enclosed = resolve_enclosed_floors_ag(zone).loc["B1014"]
    floors_ag = float(zone.loc["B1014", "floors_ag"])
    floors_bg = float(zone.loc["B1014", "floors_bg"])
    gfa = float(results.loc["B1014", "GFA_m2"])

    assert enclosed == 1.0 and floors_ag == 5.0, "B1014 has a 4-floor void deck under 5 storeys"
    assert gfa == pytest.approx(footprint * (enclosed + floors_bg), rel=1e-6)
    # And emphatically not the whole storey count, which is what it used to be.
    assert gfa != pytest.approx(footprint * (floors_ag + floors_bg), rel=1e-6)


def test_embodied_floor_area_excludes_the_void_deck():
    """A void deck is open: no partitions, no floor slab, no technical systems above it.

    `embodied.py` used `footprint x floors_ag`, counting void storeys as built floor area
    while the demand module excluded them -- the two disagreed for any building with a void
    deck. Both now use the enclosed count.
    """
    footprint = 500.0
    no_void = pd.DataFrame({"floors_ag": [5], "height_ag": [15.0]})
    legacy = pd.DataFrame({"floors_ag": [5], "height_ag": [15.0], VOID_FLOORS_COLUMN: [2]})
    metres = pd.DataFrame({"floors_ag": [3], "height_ag": [15.0], VOID_HEIGHT_COLUMN: [6.0]})

    assert footprint * resolve_enclosed_floors_ag(no_void).iloc[0] == pytest.approx(2500.0)
    assert footprint * resolve_enclosed_floors_ag(legacy).iloc[0] == pytest.approx(1500.0)
    assert footprint * resolve_enclosed_floors_ag(metres).iloc[0] == pytest.approx(1500.0)


# --------------------------------------------------------------------------- degenerate input


@pytest.mark.parametrize("cols", [
    {VOID_FLOORS_COLUMN: -1},
    {VOID_FLOORS_COLUMN: 10},   # equals floors_ag: no enclosed storey left
    {VOID_FLOORS_COLUMN: 11},
    {VOID_HEIGHT_COLUMN: -1.0},
    {VOID_HEIGHT_COLUMN: 30.0},  # equals height_ag
    {VOID_HEIGHT_COLUMN: 35.0},
    {VOID_HEIGHT_COLUMN: 29.5},  # leaves less than a metre
])
def test_a_void_deck_that_swallows_the_building_is_rejected(cols):
    """Every input that would leave no enclosed building must fail validation.

    `void_deck == floors_ag` used to pass: the check was `>` where the rest of the code had
    always called `>=` invalid. It leaves zero enclosed storeys, so there is no floor area,
    no storey height, and only a single face to extrude.
    """
    from cea.datamanagement.databases_verification import (
        assert_input_geometry_acceptable_values_floor_height,
        check_void_deck_values,
        check_void_height_values,
    )

    df = zone(**cols)
    df["name"] = ["B"]
    df["floors_bg"] = [0]
    df["height_bg"] = [0.0]

    # Whichever rule catches it, the scenario must not get through. They are all run by
    # `verify_input_geometry_zone`, and which one fires depends on how the void is expressed.
    def validate():
        if VOID_FLOORS_COLUMN in df.columns:
            check_void_deck_values(df.copy())
        check_void_height_values(df.copy())
        assert_input_geometry_acceptable_values_floor_height(df.copy())

    with pytest.raises(Exception) as raised:
        validate()

    # Guard against an unrelated crash counting as a pass.
    message = str(raised.value).lower()
    assert any(t in message for t in ("void", "floor", "height")), message


def test_a_squashed_enclosed_storey_is_rejected():
    """The storey-height rule measures the *enclosed* height, not `height_ag / floors_ag`.

    A void deck is part of `height_ag` but encloses nothing, so the gross figure can look
    healthy while the occupied storeys are squeezed into what is left. A 12 m void deck under
    3 storeys of a 15 m building gives a 1 m storey, and the gross check (15 / 3 = 5 m) waved
    it through.
    """
    from cea.datamanagement.databases_verification import (
        MINIMUM_STOREY_HEIGHT_M,
        assert_input_geometry_acceptable_values_floor_height,
    )

    squashed = pd.DataFrame({"name": ["B"], "floors_ag": [3], "floors_bg": [0],
                             "height_ag": [15.0], "height_bg": [0.0], VOID_HEIGHT_COLUMN: [12.0]})
    assert enclosed_storey_height(squashed).iloc[0] == pytest.approx(1.0)
    assert squashed["height_ag"].iloc[0] / squashed["floors_ag"].iloc[0] == 5.0  # gross looks fine

    with pytest.raises(Exception, match="height per"):
        assert_input_geometry_acceptable_values_floor_height(squashed)

    # Right at the limit it is accepted.
    ok = squashed.copy()
    ok[VOID_HEIGHT_COLUMN] = [15.0 - 3 * MINIMUM_STOREY_HEIGHT_M]
    assert enclosed_storey_height(ok).iloc[0] == pytest.approx(MINIMUM_STOREY_HEIGHT_M)
    assert_input_geometry_acceptable_values_floor_height(ok)


def test_the_resolvers_never_return_nan_or_infinity():
    """A NaN storey height propagates silently into air volume and pipe lengths.

    Validation rejects the inputs that could cause one, but the resolvers must fail loudly or
    return something finite rather than poisoning arithmetic far downstream.
    """
    degenerate = [
        {"floors_ag": [0], "height_ag": [9.0]},
        {"floors_ag": [3], "height_ag": [0.0]},
        {"floors_ag": [3], "height_ag": [9.0], VOID_FLOORS_COLUMN: [3]},
        {"floors_ag": [3], "height_ag": [9.0], VOID_HEIGHT_COLUMN: [9.0]},
        {"floors_ag": [3], "height_ag": [9.0], VOID_HEIGHT_COLUMN: ["not a number"]},
    ]
    for cols in degenerate:
        df = pd.DataFrame(cols)
        for fn in (resolve_void_height, resolve_enclosed_floors_ag, enclosed_storey_height):
            value = fn(df).iloc[0]
            assert np.isfinite(value), f"{fn.__name__} returned {value} for {cols}"


# --------------------------------------------------------------------------- geometry


def legacy_z_levels(void_deck, height_ag, floors_ag):
    """What `calc_solid` was fed before this change: floor indices x storey height."""
    floor_to_floor = height_ag / floors_ag
    return [f * floor_to_floor for f in range(void_deck, floors_ag + 1)]



@pytest.mark.parametrize("floors_ag", [1, 2, 3, 5, 10, 40])
@pytest.mark.parametrize("void_deck", [0, 1, 2, 5])
def test_legacy_scenarios_produce_the_same_building_solid(void_deck, floors_ag):
    """The guarantee that makes this change safe: existing scenarios do not move."""
    if void_deck >= floors_ag:
        pytest.skip("a void deck cannot swallow the whole building")

    height_ag = floors_ag * 3.2
    df = pd.DataFrame({VOID_FLOORS_COLUMN: [void_deck], "height_ag": [height_ag],
                       "floors_ag": [floors_ag]})
    void_height = resolve_void_height(df).iloc[0]
    enclosed_floors = resolve_enclosed_floors_ag(df).iloc[0]

    assert calc_z_levels(void_height, height_ag, enclosed_floors) == pytest.approx(
        legacy_z_levels(void_deck, height_ag, floors_ag)
    )


def test_the_first_level_is_the_underside_and_the_last_is_the_roof():
    levels = calc_z_levels(4.5, 30.0, 9)
    assert levels[0] == 4.5
    assert levels[-1] == 30.0


def test_the_roof_is_pinned_to_the_reported_height():
    """floors x storey height accumulates float error; the roof must match height_ag exactly."""
    height_ag = 10.0
    assert calc_z_levels(0.0, height_ag, 3)[-1] == height_ag


def test_a_void_deck_landing_on_a_storey_line_does_not_produce_a_zero_height_segment():
    """Two faces at the same height loft into a degenerate solid that may not close."""
    levels = calc_z_levels(6.0, 9.0, 1)
    assert levels == [6.0, 9.0]
    assert all(b > a for a, b in zip(levels, levels[1:]))


def test_a_void_deck_just_below_a_storey_line_collapses_into_it():
    levels = calc_z_levels(6.0 - 1e-9, 9.0, 1)
    assert all(b - a > 1e-7 for a, b in zip(levels, levels[1:]))


def test_levels_are_strictly_ascending_for_arbitrary_void_heights():
    height_ag, enclosed_floors = 30.0, 10
    for void in np.linspace(0.0, height_ag - 0.01, 200):
        levels = calc_z_levels(void, height_ag, enclosed_floors)
        assert all(b > a for a, b in zip(levels, levels[1:])), f"not ascending at {void}"
        assert levels[-1] == pytest.approx(height_ag)


def test_a_void_deck_is_always_at_the_bottom():
    """Every storey line at or below the void is dropped -- CEA models no mid-building void."""
    levels = calc_z_levels(12.0, 30.0, 6)
    assert min(levels) == 12.0


def test_a_blank_metre_cell_falls_back_to_the_legacy_column():
    """An older scenario can end up carrying a blank `height_vd` column.

    The input editor renders every column in the schema, so opening an old scenario shows
    `height_vd` as an empty column next to a populated `void_deck`. If that shape is ever
    saved, the columns coexist with only the legacy one filled in.

    Precedence is therefore per *value*, not per column: a blank cell falls back to
    `void_deck` instead of reading as "no void deck", which would silently drop the void deck
    and inflate floor area with no error anywhere.
    """
    df = pd.DataFrame({"name": ["B1014"], "floors_ag": [5], "height_ag": [15.0],
                       VOID_FLOORS_COLUMN: [4], VOID_HEIGHT_COLUMN: [np.nan]})

    assert resolve_void_height(df).iloc[0] == pytest.approx(12.0)
    assert resolve_enclosed_floors_ag(df).iloc[0] == 1.0
    assert enclosed_storey_height(df).iloc[0] == pytest.approx(3.0)


def test_an_explicit_zero_still_removes_the_void_deck():
    """0 is a value, not a blank -- it is how a user clears a void deck in the editor."""
    df = pd.DataFrame({"name": ["B"], "floors_ag": [5], "height_ag": [15.0],
                       VOID_FLOORS_COLUMN: [4], VOID_HEIGHT_COLUMN: [0.0]})

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert resolve_void_height(df).iloc[0] == 0.0
        assert resolve_enclosed_floors_ag(df).iloc[0] == 5.0


def test_precedence_is_decided_per_building_not_per_column():
    """One scenario can hold both shapes at once, building by building."""
    df = pd.DataFrame({
        "name": ["legacy", "metres"],
        "floors_ag": [5, 5],
        "height_ag": [15.0, 15.0],
        VOID_FLOORS_COLUMN: [4, 0],
        VOID_HEIGHT_COLUMN: [np.nan, 6.0],
    })

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert resolve_void_height(df).tolist() == [12.0, 6.0]
        assert resolve_enclosed_floors_ag(df).tolist() == [1.0, 5.0]


# --------------------------------------------------------------------------- optional-ness


def test_neither_void_column_is_required_by_the_schema_check():
    """Verification is driven by schemas.yml, so adding a column there makes every existing
    scenario report it as missing unless it is explicitly optional.

    Both columns must be optional: `height_vd` postdates older scenarios, and `void_deck`
    predates the ones CEA writes now.
    """
    from cea.datamanagement.utils import OPTIONAL_VOID_DECK_COLUMNS
    from cea.schemas import schemas

    columns = schemas(plugins=[])["get_zone_geometry"]["schema"]["columns"]

    for label, absent in [
        ("legacy", {"geometry", VOID_HEIGHT_COLUMN}),
        ("current", {"geometry", VOID_FLOORS_COLUMN}),
        ("no void decks", {"geometry", VOID_HEIGHT_COLUMN, VOID_FLOORS_COLUMN}),
    ]:
        present = [c for c in columns if c not in absent]
        missing = [c for c in columns if c not in present]
        missing = [c for c in missing if c.lower() not in ("geometry", "reference")]
        missing = [c for c in missing if c not in OPTIONAL_VOID_DECK_COLUMNS]
        assert missing == [], f"{label} scenario reports missing columns: {missing}"


def test_a_new_scenario_is_given_an_editable_void_deck_column():
    """CEA writes `height_vd` for new scenarios so the field exists to be edited.

    Without it a user wanting a void deck would have to add the column by hand in GIS.
    """
    from cea.datamanagement.databases_verification import COLUMNS_ZONE

    assert VOID_HEIGHT_COLUMN in COLUMNS_ZONE
    assert VOID_FLOORS_COLUMN not in COLUMNS_ZONE, "new scenarios should not be given the legacy column"


def test_a_zone_carrying_only_the_new_column_can_be_read():
    """`void_deck` must no longer be required, or a scenario CEA itself just wrote fails."""
    from cea.datamanagement.databases_verification import (
        COLUMNS_ZONE_GEOMETRY,
        OPTIONAL_COLUMNS_ZONE_GEOMETRY,
    )

    assert VOID_FLOORS_COLUMN not in COLUMNS_ZONE_GEOMETRY
    assert VOID_FLOORS_COLUMN in OPTIONAL_COLUMNS_ZONE_GEOMETRY

    zone_gdf = pd.DataFrame({
        "name": ["B1"], "floors_bg": [0], "floors_ag": [10],
        "height_bg": [0.0], "height_ag": [30.0], VOID_HEIGHT_COLUMN: [0.0],
    })
    optional = [c for c in OPTIONAL_COLUMNS_ZONE_GEOMETRY if c in zone_gdf.columns]
    selected = zone_gdf[COLUMNS_ZONE_GEOMETRY + optional]

    assert resolve_void_height(selected).tolist() == [0.0]


def test_the_cea3_migration_keeps_the_void_deck_on_the_legacy_column():
    """CEA-3 stored the void deck in architecture.dbf as whole floors.

    The CEA-4 migration carries it across unchanged rather than converting it to `height_vd`.
    Converting would mean redefining `floors_ag` to the enclosed count, and `floors_ag` is read
    elsewhere as the total above-ground storey count -- `cea4_migrate_db` rescales `Ns` by
    `(floors_ag + floors_bg) / floors_ag`. Rewriting it silently shifts occupied area and
    demand for every migrated building, so a CEA-3 scenario stays on the legacy column.

    The bundled reference case has a genuine 4-floor void deck on B1014, which is what makes
    any drift here detectable at all.
    """
    import geopandas as gpd

    from cea.inputlocator import ReferenceCaseOpenLocator

    locator = ReferenceCaseOpenLocator()
    zone = gpd.read_file(locator.get_zone_geometry()).set_index("name")
    building = zone.loc["B1014"]

    # Untouched by the migration: the CEA-3 values, exactly.
    assert VOID_FLOORS_COLUMN in zone.columns
    assert float(building[VOID_FLOORS_COLUMN]) == 4
    assert float(building["floors_ag"]) == 5

    # And they resolve to the same building the legacy code described.
    assert resolve_void_height(zone).loc["B1014"] == pytest.approx(4 * (15.0 / 5))
    assert resolve_enclosed_floors_ag(zone).loc["B1014"] == 1.0
    assert enclosed_storey_height(zone).loc["B1014"] == pytest.approx(3.0)


# --------------------------------------------------------------------------- naming


def test_the_column_name_survives_a_shapefile_round_trip(tmp_path):
    """zone.shp stores attributes in a DBF, which truncates field names at 10 characters.

    `height_void` would silently become `height_voi` on write, so the length is a hard
    constraint on the name, not a style preference.
    """
    assert len(VOID_HEIGHT_COLUMN) <= 10

    gdf = gpd.GeoDataFrame(
        {"name": ["B1"], VOID_HEIGHT_COLUMN: [4.5],
         "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]},
        crs="EPSG:4326",
    )
    path = tmp_path / "zone.shp"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        gdf.to_file(path)
    assert VOID_HEIGHT_COLUMN in gpd.read_file(path).columns



# --------------------------------------------------------------------------- OSM import


def test_an_implausible_osm_height_is_rebuilt_from_the_assumed_storey_height():
    """OSM tags `height` and `building:levels` independently and they often disagree.

    `zone_helper` used to repair that by setting `height_ag = floors_ag` -- exactly 1 m per
    floor. That satisfied the old "at least 1 m" check while describing a building nobody
    could occupy, and it is why OSM imports were full of 1 m storeys. The repair now rebuilds
    the height from CEA's assumed storey height, as the three neighbouring repairs already do.
    """
    from cea.datamanagement.databases_verification import (
        MINIMUM_STOREY_HEIGHT_M,
        assert_input_geometry_acceptable_values_floor_height,
    )
    from cea.demand import constants

    def repair(osm_height, floors_ag):
        df = pd.DataFrame({"height_ag": [float(osm_height)], "floors_ag": [floors_ag]})
        implausible = df["height_ag"] < df["floors_ag"] * MINIMUM_STOREY_HEIGHT_M
        df.loc[implausible, "height_ag"] = (
            df.loc[implausible, "floors_ag"].astype(float) * constants.H_F)
        return float(df["height_ag"].iloc[0])

    # Implausible input is rebuilt, and never to 1 m per floor.
    for osm_height, floors in [(3.0, 10), (15.0, 10), (0.5, 1), (2.0, 3)]:
        repaired = repair(osm_height, floors)
        assert repaired / floors == pytest.approx(constants.H_F)
        assert repaired / floors > MINIMUM_STOREY_HEIGHT_M

    # Plausible input is left exactly as OSM reported it.
    for osm_height, floors in [(30.0, 10), (54.0, 18), (6.0, 2)]:
        assert repair(osm_height, floors) == osm_height

    # Whatever it emits must satisfy CEA's own validation -- the generator and the verifier
    # disagreeing is how a scenario CEA just created fails to open.
    for osm_height, floors in [(3.0, 10), (15.0, 10), (0.5, 1), (30.0, 10)]:
        zone_row = pd.DataFrame({"name": ["B"], "floors_ag": [floors], "floors_bg": [0],
                                 "height_ag": [repair(osm_height, floors)], "height_bg": [0.0]})
        assert_input_geometry_acceptable_values_floor_height(zone_row)


def test_the_zone_helper_cannot_create_a_scenario_that_will_not_open():
    """Whatever the Zone Helper emits must satisfy CEA's own geometry verification.

    Both creation branches can otherwise produce a building CEA then refuses to open:

    - OSM: `height` and `building:levels` are tagged independently and often disagree
    - user assumptions: `floor(height_ag / H_F)` is 0 for anything under one storey, and a
      conflicting height/floors pair entered by hand is not repaired at all

    A scenario failing verification immediately after the Helper created it is the worst
    possible first experience, so the repair runs for both branches.
    """
    import math

    from cea.datamanagement.databases_verification import (
        MINIMUM_STOREY_HEIGHT_M,
        assert_input_geometry_acceptable_values_floor_height,
    )
    from cea.demand import constants

    def create(height=None, floors=None, osm_height=None, osm_levels=None):
        if osm_levels is not None:
            n = osm_levels
            h = osm_height if osm_height is not None else osm_levels * constants.H_F
        elif height is None and floors is not None:
            n, h = floors, floors * constants.H_F
        elif height is not None and floors is None:
            h, n = height, int(math.floor(height / constants.H_F))
        else:
            h, n = height, floors

        df = pd.DataFrame({"floors_ag": [n], "height_ag": [float(h)]})
        df["floors_ag"] = df["floors_ag"].clip(lower=1).astype(int)          # at least one storey
        implausible = df["height_ag"] < df["floors_ag"] * MINIMUM_STOREY_HEIGHT_M
        df.loc[implausible, "height_ag"] = (
            df.loc[implausible, "floors_ag"].astype(float) * constants.H_F)   # plausible storey
        return df

    inputs = [
        dict(floors=5), dict(height=9.0), dict(height=2.5), dict(height=1.0), dict(height=0.1),
        dict(height=15.0, floors=5), dict(height=5.0, floors=10), dict(height=15.0, floors=10),
        dict(osm_height=3.0, osm_levels=10), dict(osm_height=54.0, osm_levels=18),
        dict(osm_levels=0), dict(osm_levels=1),
    ]
    for kwargs in inputs:
        created = create(**kwargs)
        zone_row = pd.DataFrame({
            "name": ["B"], "floors_ag": created["floors_ag"], "floors_bg": [1],
            "height_ag": created["height_ag"], "height_bg": [3.0],
        })
        # Must not raise -- this is the whole point.
        assert_input_geometry_acceptable_values_floor_height(zone_row)
        assert int(created["floors_ag"].iloc[0]) >= 1, kwargs


def test_the_envelope_migration_never_invents_a_legacy_column(tmp_path):
    """`migrate_void_deck_data` runs at the top of eight entry points.

    Its job is lifting a CEA-3 `void_deck` out of envelope.csv. It used to *create* the column
    when it found none anywhere, which meant the first tool run on a scenario CEA had just
    created added the legacy column back beside `height_vd` -- two columns for one concept, in
    a file that never had one.
    """
    from cea.datamanagement.utils import migrate_void_deck_data
    from cea.inputlocator import InputLocator

    def scenario(name, zone_cols, envelope_cols):
        root = tmp_path / name
        (root / "inputs" / "building-geometry").mkdir(parents=True)
        (root / "inputs" / "building-properties").mkdir(parents=True)
        gpd.GeoDataFrame(
            [{"name": "B1", "floors_ag": 5, "floors_bg": 1, "height_ag": 15.0,
              "height_bg": 3.0, **zone_cols,
              "geometry": Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])}],
            crs="EPSG:4326",
        ).to_file(root / "inputs" / "building-geometry" / "zone.shp")
        pd.DataFrame([{"name": "B1", "Hs": 0.8, **envelope_cols}]).to_csv(
            root / "inputs" / "building-properties" / "envelope.csv", index=False)
        return InputLocator(str(root))

    def void_columns(locator):
        cols = gpd.read_file(locator.get_zone_geometry()).columns
        return [c for c in (VOID_HEIGHT_COLUMN, VOID_FLOORS_COLUMN) if c in cols]

    # A scenario CEA created today is left exactly as it was.
    locator = scenario("new", {VOID_HEIGHT_COLUMN: 0.0}, {})
    migrate_void_deck_data(locator)
    assert void_columns(locator) == [VOID_HEIGHT_COLUMN]

    # A scenario with no void-deck data anywhere does not acquire a column.
    locator = scenario("empty", {}, {})
    migrate_void_deck_data(locator)
    assert void_columns(locator) == []

    # The migration it actually exists for still happens.
    locator = scenario("cea3", {}, {VOID_FLOORS_COLUMN: 4})
    migrate_void_deck_data(locator)
    assert void_columns(locator) == [VOID_FLOORS_COLUMN]
    assert VOID_FLOORS_COLUMN not in pd.read_csv(locator.get_building_architecture()).columns
