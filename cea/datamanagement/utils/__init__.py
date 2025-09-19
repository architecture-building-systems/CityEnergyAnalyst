from __future__ import annotations
from typing import TYPE_CHECKING
import warnings

import pandas as pd
import geopandas as gpd

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


def migrate_void_deck_data(locator: InputLocator) -> None:
    """Check if void_deck exists in zone.shp and copy it from envelope.csv if necessary.

    :param locator: the input locator object.
    :type locator: cea.inputlocator.InputLocator
    """

    zone_gdf = gpd.read_file(locator.get_zone_geometry())
    isin_zone = "void_deck" in zone_gdf.columns

    if not isin_zone:
        envelope_df = pd.read_csv(locator.get_building_architecture())

        if "void_deck" in envelope_df.columns:
            # assign void_deck from envelope.csv to zone.shp and remove it from envelope.csv
            zone_gdf = zone_gdf.merge(
                envelope_df[["name", "void_deck"]], on="name", how="left"
            )
            zone_gdf["void_deck"] = zone_gdf["void_deck"].fillna(0)
            print("Migrated void_deck data from envelope.csv to zone.shp.")
            envelope_df.drop(columns=["void_deck"], inplace=True)
            envelope_df.to_csv(locator.get_building_architecture(), index=False)

        else:  # cannot find void_deck anywhere, just initialize it to 0
            zone_gdf["void_deck"] = 0
            warnings.warn(
                "No void_deck data found in envelope.csv, setting to 0 in zone.shp"
            )

    # Validate that floors_ag is larger than void_deck for each building
    actual_floors = zone_gdf["floors_ag"] - zone_gdf["void_deck"]
    invalid_floors = zone_gdf[actual_floors <= 0]
    if len(invalid_floors) > 0:
        invalid_buildings = invalid_floors["name"].tolist()
        warnings.warn(f"Some buildings have void_deck greater than floors_ag: {invalid_buildings}",
                      RuntimeWarning)


def generate_architecture_csv(locator: InputLocator, building_zone_df: gpd.GeoDataFrame):
    """
    Generate an architecture CSV file with geometric properties

    Includes:
    - Af_m2: Conditioned floor area [m2]
    - Aroof_m2: Roof area [m2]
    - GFA_m2: Gross floor area [m2]
    - Aocc_m2: Occupied floor area [m2]
    
    :param locator: InputLocator instance
    :param building_zone_df: GeoDataFrame containing building geometry data
    """
    # Get architecture database to access Hs, Ns, Es, occupied_bg values
    architecture_DB = pd.read_csv(locator.get_database_archetypes_construction_type())
    prop_architecture_df = building_zone_df.merge(architecture_DB, left_on='const_type', right_on='const_type')

    # Calculate architectural properties
    # Calculate areas based on geometry
    footprint = building_zone_df.geometry.area  # building footprint area
    floors_ag = building_zone_df['floors_ag']  # above-ground floors
    floors_bg = building_zone_df['floors_bg']  # below-ground floors
    void_deck = building_zone_df['void_deck']  # void deck floors

    # Get shares from architecture database
    Hs = prop_architecture_df['Hs']  # Share of GFA that is conditioned
    Ns = prop_architecture_df['Ns']  # Share of GFA that is occupied
    occupied_bg = prop_architecture_df['occupied_bg']  # Whether basement is occupied

    # Calculate GFA components using proper equations
    gfa_ag_m2 = footprint * (floors_ag - void_deck)  # Above-ground GFA
    gfa_bg_m2 = footprint * floors_bg  # Below-ground GFA
    gfa_m2 = gfa_ag_m2 + gfa_bg_m2  # Total GFA

    # Split shares between above and below ground areas
    # Using the same logic as in useful_areas.py split_above_and_below_ground_shares
    effective_floors_ag = floors_ag - void_deck
    denominator = effective_floors_ag + floors_bg * occupied_bg
    share_ag = effective_floors_ag / denominator
    # Handle division by zero case
    share_ag = share_ag.fillna(1.0).where(denominator > 0, 1.0)
    share_bg = 1 - share_ag

    Hs_ag = Hs * share_ag
    Hs_bg = Hs * share_bg
    Ns_ag = Ns * share_ag
    Ns_bg = Ns * share_bg

    # Calculate areas using proper equations from useful_areas.py
    af_m2 = gfa_ag_m2 * Hs_ag + gfa_bg_m2 * Hs_bg  # Conditioned floor area
    aocc_m2 = gfa_ag_m2 * Ns_ag + gfa_bg_m2 * Ns_bg  # Occupied floor area
    aroof_m2 = footprint  # Roof area equals footprint

    # Create DataFrame directly from vectorized calculations
    architecture_df = pd.DataFrame({
        'name': prop_architecture_df['name'],
        'Af_m2': af_m2,
        'Aroof_m2': aroof_m2,
        'GFA_m2': gfa_m2,
        'Aocc_m2': aocc_m2,
    })
    
    # Ensure parent folder exists
    locator.ensure_parent_folder_exists(locator.get_architecture_csv())
    
    # Save to CSV file
    architecture_df.to_csv(locator.get_architecture_csv(), index=False, float_format='%.3f')
    print(f"Architecture data generated and saved to: {locator.get_architecture_csv()}")

