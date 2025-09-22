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
            zone_gdf.to_file(locator.get_zone_geometry())

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
