import os

import geopandas as gpd
import pandas as pd

import fiona

fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'

URL_LIST = [
    "https://climate.onebuilding.org/WMO_Region_1_Africa/Region1_Africa_EPW_Processing_locations.kml",
    "https://climate.onebuilding.org/WMO_Region_2_Asia/Region2_Asia_EPW_Processing_locations.kml",
    "https://climate.onebuilding.org/WMO_Region_2_Asia/Region2_Region6_Russia_EPW_Processing_locations.kml",
    "https://climate.onebuilding.org/WMO_Region_3_South_America/Region3_South_America_EPW_Processing_locations.kml",
    "https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/Region4_Canada_EPW_Processing_locations.kml",
    "https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/Region4_USA_EPW_Processing_locations.kml",
    "https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/Region4_NA_CA_Caribbean_EPW_Processing_locations.kml",
    "https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/Region4_CaliforniaClimateZones_EPW_Processing_locations.kml",
    "https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/Region4_Canada_NRC_Future_TMY_Year_EPW_Processing_locations.kml",
    "https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/Region4_Canada_NRC_Future_Extreme_Warm_Year_EPW_Processing_locations.kml",
    "https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/Region4_Canada_NRC_Future_Extreme_Cold_Year_EPW_Processing_locations.kml",
    "https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/Region4_Canada_NRC_Future_Avg_Year_EPW_Processing_locations.kml",
    "https://climate.onebuilding.org/WMO_Region_5_Southwest_Pacific/Region5_Southwest_Pacific_EPW_Processing_locations.kml",
    "https://climate.onebuilding.org/WMO_Region_6_Europe/Region6_Europe_EPW_Processing_locations.kml",
    "https://climate.onebuilding.org/WMO_Region_6_Europe/Region2_Region6_Russia_EPW_Processing_locations.kml",
    "https://climate.onebuilding.org/WMO_Region_7_Antarctica/Region7_Antarctica_EPW_Processing_locations.kml"
]

WEATHER_DATA_LOCATION = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'weather.geojson')


def main():
    # Combine for global data
    kmls = [gpd.read_file(url) for url in URL_LIST]
    global_gdf = pd.concat(kmls)

    # Filter NA
    global_gdf = global_gdf[global_gdf['description'].notna()]
    # Filter for latest TMYx url
    latest_tmyx = global_gdf[global_gdf["description"].str.contains("TMYx.2007-2021")]
    latest_tmyx["url"] = latest_tmyx["description"].str.extract(r'https?://climate.onebuilding.org/([^ ]+\.zip)')

    latest_tmyx[["url", "geometry"]].to_file(WEATHER_DATA_LOCATION)


if __name__ == '__main__':
    main()
