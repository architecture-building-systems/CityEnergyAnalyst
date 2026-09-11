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

    if VOID_HEIGHT_COLUMN in df.columns:
        return floors_ag

    if VOID_FLOORS_COLUMN in df.columns:
        void_floors = pd.to_numeric(df[VOID_FLOORS_COLUMN], errors="coerce").fillna(0.0)
        return floors_ag - void_floors

    return floors_ag


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

    `height_vd` is authoritative when present. `void_deck` is the legacy form and is converted
    at the building's own storey height -- the same expression the geometry code has always
    used -- so a scenario that only carries `void_deck` produces identical results to before.

    Neither column is required: a scenario with neither has no void decks.

    :param df: any frame carrying the zone geometry columns. Converting the legacy column
        needs `height_ag` and `floors_ag`, both of which are in `COLUMNS_ZONE_GEOMETRY`.
    :param warn_on_conflict: warn when both columns are present and disagree. The legacy
        column is ignored either way; the warning stops that being silent.
    :return: void height in metres, aligned to `df`, as float. Never NaN -- a blank cell
        means "no void deck", which is the assumption CEA made before the column existed.
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

    height = pd.to_numeric(df[VOID_HEIGHT_COLUMN], errors="coerce").fillna(0.0).astype(float)

    if has_floors and warn_on_conflict:
        # Only complain where the two actually disagree; a scenario carrying a consistent
        # pair is not doing anything wrong.
        disagrees = ~np.isclose(height, legacy_height, rtol=1e-6, atol=1e-9)
        if disagrees.any():
            names = df.index[disagrees].tolist() if df.index.name == "name" else None
            where = f" for {names}" if names else ""
            warnings.warn(
                f"Both '{VOID_HEIGHT_COLUMN}' and '{VOID_FLOORS_COLUMN}' are present and "
                f"disagree{where}. Using '{VOID_HEIGHT_COLUMN}' (metres) and ignoring "
                f"'{VOID_FLOORS_COLUMN}' (floors).",
                RuntimeWarning,
            )

    return height


def _single_row_frame(row) -> "pd.DataFrame":
    """A one-row frame from a building mapping, for the frame-based resolvers.

    `BuildingGeometry[name]` hands back a plain dict. Rather than reimplement the column
    precedence for mappings -- two copies of a rule this subtle drift apart -- the row
    helpers below build a frame and defer. Only the columns the resolvers read are copied,
    and a key that is absent stays absent, so column presence still decides.
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
    """Check if void_deck exists in zone.shp and copy it from envelope.csv if necessary.

    :param locator: the input locator object.
    :type locator: cea.inputlocator.InputLocator
    """

    zone_gdf = gpd.read_file(locator.get_zone_geometry())

    # Both branches must reach disk: consumers re-read zone.shp (radiation's
    # geometry_generator indexes the column with no default), so an in-memory value alone
    # is invisible to them.
    if "void_deck" not in zone_gdf.columns:
        envelope_df = pd.read_csv(locator.get_building_architecture())

        if "void_deck" in envelope_df.columns:
            # assign void_deck from envelope.csv to zone.shp and remove it from envelope.csv
            zone_gdf = zone_gdf.merge(
                envelope_df[["name", "void_deck"]], on="name", how="left"
            )
            zone_gdf["void_deck"] = zone_gdf["void_deck"].fillna(0)
            zone_gdf.to_file(locator.get_zone_geometry())

            print("Migrated void_deck data from envelope.csv to zone.shp.")
            # Drop the source only once the destination is on disk.
            envelope_df.drop(columns=["void_deck"], inplace=True)
            envelope_df.to_csv(locator.get_building_architecture(), index=False)

        else:  # cannot find void_deck anywhere, just initialize it to 0
            zone_gdf["void_deck"] = 0
            zone_gdf.to_file(locator.get_zone_geometry())
            warnings.warn(
                "No void_deck data found in envelope.csv, setting to 0 in zone.shp"
            )

    # Validate that floors_ag is larger than void_deck for each building
    actual_floors = zone_gdf["floors_ag"] - zone_gdf["void_deck"]
    invalid_floors = zone_gdf[actual_floors <= 0]
    if len(invalid_floors) > 0:
        invalid_buildings = invalid_floors["name"].tolist()
        warnings.warn(f"Some buildings have void_deck greater than or equal to floors_ag: {invalid_buildings}",
                      RuntimeWarning)
