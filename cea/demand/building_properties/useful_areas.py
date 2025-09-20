from __future__ import annotations

from typing import TYPE_CHECKING

from cea.utilities.standardize_coordinates import get_lat_lon_projected_shapefile, get_projected_coordinate_system

if TYPE_CHECKING:
    import pandas as pd
    import geopandas as gpd

def calc_useful_areas(zone_df: gpd.GeoDataFrame, architecture_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate useful (electrified/conditioned/occupied) floor areas based on building properties
    and assumptions on how these are distributed in the building.

    Adds the following columns to the dataframe:
        - footprint: Footprint area of the building [m2]
        - GFA_ag_m2: Above-ground gross floor area [m2]
        - GFA_bg_m2: Below-ground gross floor area [m2]
        - GFA_m2: Gross floor area [m2]
        - Hs_ag: Share of above-ground gross floor area that is heated/cooled (conditioned)
        - Hs_bg: Share of below-ground gross floor area that is heated/cooled (conditioned)
        - Ns_ag: Share of above-ground gross floor area that is occupied
        - Ns_bg: Share of below-ground gross floor area that is occupied
        - Aocc: Occupied floor area [m2]
        - Af: Conditioned floor area [m2]
        - Aef: Electrified floor area [m2]
    """
    # Ensure void_deck data is only present in zone_df
    props = {}
    if "void_deck" in zone_df.columns and "void_deck" in architecture_df.columns:
        props['suffixes'] = ('', '_arch')

    # Merge zone data with architecture data to get building properties
    df = zone_df.merge(architecture_df, how='left', left_index=True, right_index=True, **props)

    # reproject to projected coordinate system (in meters) to calculate area
    lat, lon = get_lat_lon_projected_shapefile(zone_df)
    df = df.to_crs(get_projected_coordinate_system(float(lat), float(lon)))

    # Calculate gross floor areas
    df['footprint'] = df.area
    df['GFA_ag_m2'] = df['footprint'] * (df['floors_ag'] - df['void_deck'])
    df['GFA_bg_m2'] = df['footprint'] * df['floors_bg']
    df['GFA_m2'] = df['GFA_ag_m2'] + df['GFA_bg_m2']

    # Calculate share of above- and below-ground GFA that is conditioned/occupied (assume same share on all floors)
    df['Hs_ag'], df['Hs_bg'], df['Ns_ag'], df['Ns_bg'] = split_above_and_below_ground_shares(
        df['Hs'], df['Ns'], df['occupied_bg'], df['floors_ag'] - df['void_deck'], df['floors_bg'])
    # occupied floor area: all occupied areas in the building
    df['Aocc'] = df['GFA_ag_m2'] * df['Ns_ag'] + df['GFA_bg_m2'] * df['Ns_bg']
    # conditioned area: areas that are heated/cooled
    df['Af'] = df['GFA_ag_m2'] * df['Hs_ag'] + df['GFA_bg_m2'] * df['Hs_bg']
    # electrified area: share of gross floor area that is also electrified
    df['Aef'] = df['GFA_m2'] * df['Es']

    # TODO: Return only relevant columns
    return df


def split_above_and_below_ground_shares(Hs, Ns, occupied_bg, floors_ag, floors_bg):
    """
    Split conditioned (Hs) and occupied (Ns) shares of ground floor area based on whether the basement
    conditioned/occupied or not.
    For simplicity, the same share is assumed for all conditioned/occupied floors (whether above or below ground)
    """
    share_ag = floors_ag / (floors_ag + floors_bg * occupied_bg)
    share_bg = 1 - share_ag
    Hs_ag = Hs * share_ag
    Hs_bg = Hs * share_bg
    Ns_ag = Ns * share_ag
    Ns_bg = Ns * share_bg

    return Hs_ag, Hs_bg, Ns_ag, Ns_bg
