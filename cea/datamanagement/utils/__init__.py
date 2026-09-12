from __future__ import annotations
from typing import TYPE_CHECKING
import warnings

import numpy as np
import pandas as pd
import geopandas as gpd

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


VOID_HEIGHT_COLUMN = "height_vd"
VOID_FLOORS_COLUMN = "void_deck"

# `height_vd`, not `height_void`: shapefile attribute names live in a DBF, which truncates at
# 10 characters, and the longer name silently becomes `height_voi` on write. Enforced by
# `test_the_column_name_survives_a_shapefile_round_trip`.

# Neither void-deck column is required. `height_vd` is what CEA writes for new scenarios;
# `void_deck` is the legacy form and is kept so existing scenarios keep working untouched. A
# zone carrying neither simply has no void decks. Verification must treat both as optional, or
# every scenario written before the other one existed reports as broken.
#
# Ordered by precedence, most authoritative first -- callers pick the first column a scenario
# carries. Do not reorder.
OPTIONAL_VOID_DECK_COLUMNS = [VOID_HEIGHT_COLUMN, VOID_FLOORS_COLUMN]


def _legacy_storey_height(df) -> "pd.Series":
    """Storey height in metres across the full above-ground height, void deck included.

    Only correct for the legacy `void_deck` column, where `floors_ag` spans the whole height,
    which is why it is private: `enclosed_storey_height` is the one callers want.
    """
    return df["height_ag"].astype(float) / df["floors_ag"].astype(float)


def resolve_enclosed_floors_ag(df):
    """Number of enclosed (non-void) storeys above ground.

    The two void-deck columns count `floors_ag` differently, and this is the only place that
    difference is resolved:

    - `void_deck` (legacy): `floors_ag` spans the whole height, void storeys included, so the
      enclosed count is `floors_ag - void_deck`.
    - `height_vd`: `floors_ag` counts the enclosed storeys only; the void deck sits beneath
      them and is measured in metres, so it is independent of the storey grid.

    The second form is what lets a void deck be taller (or shorter) than a normal storey -- a
    4.5 m void deck under 2.8 m residential floors cannot be expressed on one uniform grid.

    :return: enclosed storey count, aligned to `df`, as float. Whole numbers in both forms.
    """
    floors_ag = df["floors_ag"].astype(float)
    has_height = VOID_HEIGHT_COLUMN in df.columns
    has_floors = VOID_FLOORS_COLUMN in df.columns

    if not has_floors:
        return floors_ag

    void_floors = pd.to_numeric(df[VOID_FLOORS_COLUMN], errors="coerce").fillna(0.0)

    if not has_height:
        return floors_ag - void_floors

    # Both columns exist, so decide per building on the value, not on the column. An empty
    # `height_vd` cell alongside a populated `void_deck` is the common shape -- the input
    # editor shows every schema column, so an older scenario can acquire a blank `height_vd`
    # -- and treating the blank column as authoritative would silently drop the void deck.
    uses_metres = pd.to_numeric(df[VOID_HEIGHT_COLUMN], errors="coerce").notna()
    return floors_ag.where(uses_metres, floors_ag - void_floors)


def enclosed_storey_height(df):
    """Storey height in metres of the enclosed part of the building.

    `(height_ag - void height) / enclosed floors` -- one expression correct for both column
    forms, because `height_ag` always spans the void deck plus the enclosed solid.

    The denominator is the subtle part: it is `floors_ag` itself alongside `height_vd`, but
    `floors_ag - void_deck` alongside the legacy column. `resolve_enclosed_floors_ag` resolves
    that. Writing `height_ag / floors_ag` instead is only right for the legacy form and
    overstates the storey height -- and with it the internal air volume -- for the other.
    """
    enclosed_height = df["height_ag"].astype(float) - resolve_void_height(df, warn_on_conflict=False)
    enclosed_floors = resolve_enclosed_floors_ag(df)

    # A building whose void deck spans every storey has no enclosed floor. Validation rejects
    # that, but this must not hand back NaN if one slips past -- it would propagate silently
    # into internal air volume and pipe lengths rather than failing where it is introduced.
    return (enclosed_height / enclosed_floors).where(enclosed_floors > 0, 0.0)


def resolve_void_height(df, *, warn_on_conflict: bool = True):
    """Void-deck height in metres, from whichever column the scenario carries.

    A void deck is the open, unenclosed portion at the *bottom* of a building. It used to be
    recorded as `void_deck`, an integer count of floors, which tied the void to the storey
    grid. `height_vd` records it directly in metres, so it can sit anywhere.

    Precedence is per building, on the *value*, not on which columns exist:

    - a `height_vd` cell holding a number wins, including an explicit 0 -- that is how a user
      removes a void deck
    - a blank `height_vd` cell falls back to `void_deck`, converted at the building's own
      storey height. The input editor renders every schema column, so an older scenario can
      acquire a blank `height_vd` beside a populated `void_deck`; treating the column as
      authoritative would silently drop the void deck
    - neither column, or neither holding a value, means no void deck

    Deciding per column instead would make a scenario's areas depend on whether a blank
    column had ever been written to it.

    :param df: any frame carrying the zone geometry columns. Converting the legacy column
        needs `height_ag` and `floors_ag`, both of which are in `COLUMNS_ZONE_GEOMETRY`.
    :param warn_on_conflict: warn where a building's two columns both hold values and those
        values disagree. The legacy one is ignored there; the warning stops that being silent.
    :return: void height in metres, aligned to `df`, as float. Never NaN.
    """
    has_height = VOID_HEIGHT_COLUMN in df.columns
    has_floors = VOID_FLOORS_COLUMN in df.columns

    if not has_height and not has_floors:
        return pd.Series(0.0, index=df.index, dtype=float)

    if has_floors:
        legacy = pd.to_numeric(df[VOID_FLOORS_COLUMN], errors="coerce").fillna(0.0)
        legacy_height = legacy.astype(float) * _legacy_storey_height(df)

    if not has_height:
        return legacy_height

    height = pd.to_numeric(df[VOID_HEIGHT_COLUMN], errors="coerce").astype(float)

    if not has_floors:
        return height.fillna(0.0)

    # A usable `height_vd` wins; a blank cell falls back to the legacy column rather than
    # reading as "no void deck". An explicit 0 is a value, so it still wins -- that is how a
    # user removes a void deck.
    resolved = height.where(height.notna(), legacy_height).fillna(0.0)

    if warn_on_conflict:
        # Only where `height_vd` holds a value and the two actually differ. A blank cell is a
        # fallback, not a disagreement, and a consistent pair is not doing anything wrong.
        disagrees = height.notna() & ~np.isclose(height.fillna(0.0), legacy_height,
                                                 rtol=1e-6, atol=1e-9)
        if disagrees.any():
            names = df.index[disagrees].tolist() if df.index.name == "name" else None
            where = f" for {names}" if names else ""
            warnings.warn(
                f"Both '{VOID_HEIGHT_COLUMN}' and '{VOID_FLOORS_COLUMN}' are present and "
                f"disagree{where}. Using '{VOID_HEIGHT_COLUMN}' (metres) and ignoring "
                f"'{VOID_FLOORS_COLUMN}' (floors).",
                RuntimeWarning,
            )

    return resolved


def _single_row_frame(row) -> "pd.DataFrame":
    """A one-row frame from a building mapping, for the frame-based resolvers.

    `BuildingGeometry[name]` hands back a plain dict. Rather than reimplement the precedence
    for mappings -- two copies of a rule this subtle drift apart, and did -- the row helpers
    below build a frame and defer. Only the columns the resolvers read are copied, and a key
    that is absent stays absent, so the frame sees exactly what the mapping carried.
    """
    fields = (VOID_HEIGHT_COLUMN, VOID_FLOORS_COLUMN, "height_ag", "floors_ag")
    return pd.DataFrame([{f: row[f] for f in fields if f in row}])


def resolve_void_height_for_row(row) -> float:
    """`resolve_void_height` for a single building held as a mapping."""
    return float(resolve_void_height(_single_row_frame(row), warn_on_conflict=False).iloc[0])


def enclosed_storey_height_for_row(row) -> float:
    """`enclosed_storey_height` for a single building held as a mapping."""
    return float(enclosed_storey_height(_single_row_frame(row)).iloc[0])


def migrate_void_deck_data(locator: InputLocator) -> None:
    """Move a CEA-3-era `void_deck` column from envelope.csv into zone.shp.

    CEA-3 recorded the void deck in the architecture/envelope table. This lifts it into the
    zone geometry, where CEA-4 keeps it, and drops the stale source column.

    Does nothing when the scenario already expresses its void decks -- with either
    `height_vd` or `void_deck` in zone.shp -- and nothing when envelope.csv has no
    `void_deck` either. In particular it must not *invent* a `void_deck` column: a scenario
    CEA created today carries `height_vd`, and adding the legacy column back would put two
    columns for one concept in front of the user, in a file that never had one.

    :param locator: the input locator object.
    """
    zone_gdf = gpd.read_file(locator.get_zone_geometry())

    if any(c in zone_gdf.columns for c in OPTIONAL_VOID_DECK_COLUMNS):
        return  # already expressed, nothing to migrate

    envelope_df = pd.read_csv(locator.get_building_architecture())
    if VOID_FLOORS_COLUMN not in envelope_df.columns:
        return  # no void-deck data anywhere: the scenario simply has none

    # Reaching disk matters: consumers re-read zone.shp, so an in-memory value is invisible.
    zone_gdf = zone_gdf.merge(
        envelope_df[["name", VOID_FLOORS_COLUMN]], on="name", how="left"
    )
    zone_gdf[VOID_FLOORS_COLUMN] = zone_gdf[VOID_FLOORS_COLUMN].fillna(0)
    zone_gdf.to_file(locator.get_zone_geometry())
    print(f"Migrated {VOID_FLOORS_COLUMN} data from envelope.csv to zone.shp.")

    # Drop the source only once the destination is on disk.
    envelope_df.drop(columns=[VOID_FLOORS_COLUMN], inplace=True)
    envelope_df.to_csv(locator.get_building_architecture(), index=False)

    # A void deck spanning every storey leaves no enclosed floor. Verification rejects it;
    # warn here too, because this runs before verification on most entry points.
    enclosed = resolve_enclosed_floors_ag(zone_gdf)
    invalid = zone_gdf.loc[enclosed <= 0, "name"].tolist()
    if invalid:
        warnings.warn(
            f"Some buildings have {VOID_FLOORS_COLUMN} greater than or equal to floors_ag: "
            f"{invalid}",
            RuntimeWarning,
        )
