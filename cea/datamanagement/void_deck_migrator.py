import pandas as pd
import geopandas as gpd
import cea.inputlocator
import warnings


def migrate_void_deck_data(locator: cea.inputlocator.InputLocator) -> None:
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
        for idx, row in zone_gdf.iterrows():
            if row['floors_ag'] - row['void_deck'] <= 0:
                raise ValueError(f"floors_ag should be larger than void_deck, cannot be equal or smaller. Building: {row.get('name', idx)}, floors_ag: {row['floors_ag']}, void_deck: {row['void_deck']}")
        
        zone_gdf.to_file(locator.get_zone_geometry(), driver="ESRI Shapefile")

    else:
        for idx, row in zone_gdf.iterrows():
            if row['floors_ag'] - row['void_deck'] <= 0:
                raise ValueError(
                    f"floors_ag should be larger than void_deck, cannot be equal or smaller. Building: {row.get('name', idx)}, floors_ag: {row['floors_ag']}, void_deck: {row['void_deck']}")
