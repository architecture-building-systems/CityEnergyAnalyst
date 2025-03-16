"""
This script creates:
a singapore planning-area map to visualise given data and upload the map to server(chartstudio).
"""


# import chart_studio
# import chart_studio.plotly as py
import plotly.express as px
import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import re


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025 (A/S) Architecture and Building Systems，(ITA) Institute of Technology in Architecture, Zurich - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "shi@arch.ethz.ch"
__status__ = "Production"


dict_surface_to_planning_area = {
    'AngMoKio - E': 'ANG MO KIO',
    'AngMoKio - N': 'ANG MO KIO',
    'AngMoKio - Roof': 'ANG MO KIO',
    'AngMoKio - S': 'ANG MO KIO',
    'AngMoKio - W': 'ANG MO KIO',
    'Bedok - E': 'BEDOK',
    'Bedok - N': 'BEDOK',
    'Bedok - Roof': 'BEDOK',
    'Bedok - S': 'BEDOK',
    'Bedok - W': 'BEDOK',
    'Bishan - E': 'BISHAN',
    'Bishan - N': 'BISHAN',
    'Bishan - Roof': 'BISHAN',
    'Bishan - S': 'BISHAN',
    'Bishan - W': 'BISHAN',
    'BoonLay - E': 'BOON LAY',
    'BoonLay - N': 'BOON LAY',
    'BoonLay - Roof': 'BOON LAY',
    'BoonLay - S': 'BOON LAY',
    'BoonLay - W': 'BOON LAY',
    'BukitBatok - E': 'BUKIT BATOK',
    'BukitBatok - N': 'BUKIT BATOK',
    'BukitBatok - Roof': 'BUKIT BATOK',
    'BukitBatok - S': 'BUKIT BATOK',
    'BukitBatok - W': 'BUKIT BATOK',
    'BukitMerah - E': 'BUKIT MERAH',
    'BukitMerah - N': 'BUKIT MERAH',
    'BukitMerah - Roof': 'BUKIT MERAH',
    'BukitMerah - S': 'BUKIT MERAH',
    'BukitMerah - W': 'BUKIT MERAH',
    'BukitPanjang - E': 'BUKIT PANJANG',
    'BukitPanjang - N': 'BUKIT PANJANG',
    'BukitPanjang - Roof': 'BUKIT PANJANG',
    'BukitPanjang - S': 'BUKIT PANJANG',
    'BukitPanjang - W': 'BUKIT PANJANG',
    'BukitTimah - E': 'BUKIT TIMAH',
    'BukitTimah - N': 'BUKIT TIMAH',
    'BukitTimah - Roof': 'BUKIT TIMAH',
    'BukitTimah - S': 'BUKIT TIMAH',
    'BukitTimah - W': 'BUKIT TIMAH',
    'CentralWaterCatchment - E': 'CENTRAL WATER CATCHMENT',
    'CentralWaterCatchment - N': 'CENTRAL WATER CATCHMENT',
    'CentralWaterCatchment - Roof': 'CENTRAL WATER CATCHMENT',
    'CentralWaterCatchment - S': 'CENTRAL WATER CATCHMENT',
    'CentralWaterCatchment - W': 'CENTRAL WATER CATCHMENT',
    'Changi - E': 'CHANGI',
    'Changi - N': 'CHANGI',
    'Changi - Roof': 'CHANGI',
    'Changi - S': 'CHANGI',
    'Changi - W': 'CHANGI',
    'ChangiBay - E': 'CHANGI BAY',
    'ChangiBay - N': 'CHANGI BAY',
    'ChangiBay - Roof': 'CHANGI BAY',
    'ChangiBay - S': 'CHANGI BAY',
    'ChangiBay - W': 'CHANGI BAY',
    'ChaoChuKang - E': 'CHAO CHU KANG',
    'ChaoChuKang - N': 'CHAO CHU KANG',
    'ChaoChuKang - Roof': 'CHAO CHU KANG',
    'ChaoChuKang - S': 'CHAO CHU KANG',
    'ChaoChuKang - W': 'CHAO CHU KANG',
    'Clementi - E': 'CLEMENTI',
    'Clementi - N': 'CLEMENTI',
    'Clementi - Roof': 'CLEMENTI',
    'Clementi - S': 'CLEMENTI',
    'Clementi - W': 'CLEMENTI',
    'DowntownCore - E': 'DOWNTOWN CORE',
    'DowntownCore - N': 'DOWNTOWN CORE',
    'DowntownCore - Roof': 'DOWNTOWN CORE',
    'DowntownCore - S': 'DOWNTOWN CORE',
    'DowntownCore - W': 'DOWNTOWN CORE',
    'Geylang - E': 'GEYLANG',
    'Geylang - N': 'GEYLANG',
    'Geylang - Roof': 'GEYLANG',
    'Geylang - S': 'GEYLANG',
    'Geylang - W': 'GEYLANG',
    'Hougang - E': 'HOUGANG',
    'Hougang - N': 'HOUGANG',
    'Hougang - Roof': 'HOUGANG',
    'Hougang - S': 'HOUGANG',
    'Hougang - W': 'HOUGANG',
    'JurongEast - E': 'JURONG EAST',
    'JurongEast - N': 'JURONG EAST',
    'JurongEast - Roof': 'JURONG EAST',
    'JurongEast - S': 'JURONG EAST',
    'JurongEast - W': 'JURONG EAST',
    'JurongWest - E': 'JURONG WEST',
    'JurongWest - N': 'JURONG WEST',
    'JurongWest - Roof': 'JURONG WEST',
    'JurongWest - S': 'JURONG WEST',
    'JurongWest - W': 'JURONG WEST',
    'Kallang - E': 'KALLANG',
    'Kallang - N': 'KALLANG',
    'Kallang - Roof': 'KALLANG',
    'Kallang - S': 'KALLANG',
    'Kallang - W': 'KALLANG',
    'LimChuKang - E': 'LIM CHU KANG',
    'LimChuKang - N': 'LIM CHU KANG',
    'LimChuKang - Roof': 'LIM CHU KANG',
    'LimChuKang - S': 'LIM CHU KANG',
    'LimChuKang - W': 'LIM CHU KANG',
    'MarinaEast - E': 'MARINA EAST',
    'MarinaEast - N': 'MARINA EAST',
    'MarinaEast - Roof': 'MARINA EAST',
    'MarinaEast - S': 'MARINA EAST',
    'MarinaEast - W': 'MARINA EAST',
    'MarinaParade - E': 'MARINA PARADE',
    'MarinaParade - N': 'MARINA PARADE',
    'MarinaParade - Roof': 'MARINA PARADE',
    'MarinaParade - S': 'MARINA PARADE',
    'MarinaParade - W': 'MARINA PARADE',
    'MarinaSouth - E': 'MARINA SOUTH',
    'MarinaSouth - N': 'MARINA SOUTH',
    'MarinaSouth - Roof': 'MARINA SOUTH',
    'MarinaSouth - S': 'MARINA SOUTH',
    'MarinaSouth - W': 'MARINA SOUTH',
    'Museum - E': 'MUSEUM',
    'Museum - N': 'MUSEUM',
    'Museum - Roof': 'MUSEUM',
    'Museum - S': 'MUSEUM',
    'Museum - W': 'MUSEUM',
    'Newton - E': 'NEWTON',
    'Newton - N': 'NEWTON',
    'Newton - Roof': 'NEWTON',
    'Newton - S': 'NEWTON',
    'Newton - W': 'NEWTON',
    'NorthEasternIslands - E': 'NORTH EASTERN ISLANDS',
    'NorthEasternIslands - N': 'NORTH EASTERN ISLANDS',
    'NorthEasternIslands - Roof': 'NORTH EASTERN ISLANDS',
    'NorthEasternIslands - S': 'NORTH EASTERN ISLANDS',
    'NorthEasternIslands - W': 'NORTH EASTERN ISLANDS',
    'Novena - E': 'NOVENA',
    'Novena - N': 'NOVENA',
    'Novena - Roof': 'NOVENA',
    'Novena - S': 'NOVENA',
    'Novena - W': 'NOVENA',
    'Orchard - E': 'ORCHARD',
    'Orchard - N': 'ORCHARD',
    'Orchard - Roof': 'ORCHARD',
    'Orchard - S': 'ORCHARD',
    'Orchard - W': 'ORCHARD',
    'Outram - E': 'OUTRAM',
    'Outram - N': 'OUTRAM',
    'Outram - Roof': 'OUTRAM',
    'Outram - S': 'OUTRAM',
    'Outram - W': 'OUTRAM',
    'PasirRis - E': 'PASIR RIS',
    'PasirRis - N': 'PASIR RIS',
    'PasirRis - Roof': 'PASIR RIS',
    'PasirRis - S': 'PASIR RIS',
    'PasirRis - W': 'PASIR RIS',
    'PayaLebar - E': 'PAYA LEBAR',
    'PayaLebar - N': 'PAYA LEBAR',
    'PayaLebar - Roof': 'PAYA LEBAR',
    'PayaLebar - S': 'PAYA LEBAR',
    'PayaLebar - W': 'PAYA LEBAR',
    'Pioneer - E': 'PIONEER',
    'Pioneer - N': 'PIONEER',
    'Pioneer - Roof': 'PIONEER',
    'Pioneer - S': 'PIONEER',
    'Pioneer - W': 'PIONEER',
    'Punggol - E': 'PUNGGOL',
    'Punggol - N': 'PUNGGOL',
    'Punggol - Roof': 'PUNGGOL',
    'Punggol - S': 'PUNGGOL',
    'Punggol - W': 'PUNGGOL',
    'Queenstown - E': 'QUEENSTOWN',
    'Queenstown - N': 'QUEENSTOWN',
    'Queenstown - Roof': 'QUEENSTOWN',
    'Queenstown - S': 'QUEENSTOWN',
    'Queenstown - W': 'QUEENSTOWN',
    'RiverValley - E': 'RIVER VALLEY',
    'RiverValley - N': 'RIVER VALLEY',
    'RiverValley - Roof': 'RIVER VALLEY',
    'RiverValley - S': 'RIVER VALLEY',
    'RiverValley - W': 'RIVER VALLEY',
    'Rochor - E': 'ROCHOR',
    'Rochor - N': 'ROCHOR',
    'Rochor - Roof': 'ROCHOR',
    'Rochor - S': 'ROCHOR',
    'Rochor - W': 'ROCHOR',
    'Seletar - E': 'SELETAR',
    'Seletar - N': 'SELETAR',
    'Seletar - Roof': 'SELETAR',
    'Seletar - S': 'SELETAR',
    'Seletar - W': 'SELETAR',
    'Sembawang - E': 'SEMBAWANG',
    'Sembawang - N': 'SEMBAWANG',
    'Sembawang - Roof': 'SEMBAWANG',
    'Sembawang - S': 'SEMBAWANG',
    'Sembawang - W': 'SEMBAWANG',
    'Sengkang - E': 'SENGKANG',
    'Sengkang - N': 'SENGKANG',
    'Sengkang - Roof': 'SENGKANG',
    'Sengkang - S': 'SENGKANG',
    'Sengkang - W': 'SENGKANG',
    'Serangoon - E': 'SERANGOON',
    'Serangoon - N': 'SERANGOON',
    'Serangoon - Roof': 'SERANGOON',
    'Serangoon - S': 'SERANGOON',
    'Serangoon - W': 'SERANGOON',
    'SingaporeRiver - E': 'SINGAPORE RIVER',
    'SingaporeRiver - N': 'SINGAPORE RIVER',
    'SingaporeRiver - Roof': 'SINGAPORE RIVER',
    'SingaporeRiver - S': 'SINGAPORE RIVER',
    'SingaporeRiver - W': 'SINGAPORE RIVER',
    'SouthernIslands - E': 'SOUTHERN ISLANDS',
    'SouthernIslands - N': 'SOUTHERN ISLANDS',
    'SouthernIslands - Roof': 'SOUTHERN ISLANDS',
    'SouthernIslands - S': 'SOUTHERN ISLANDS',
    'SouthernIslands - W': 'SOUTHERN ISLANDS',
    'SungeiKadut - E': 'SUNGEI KADUT',
    'SungeiKadut - N': 'SUNGEI KADUT',
    'SungeiKadut - Roof': 'SUNGEI KADUT',
    'SungeiKadut - S': 'SUNGEI KADUT',
    'SungeiKadut - W': 'SUNGEI KADUT',
    'Tampines - E': 'TAMPINES',
    'Tampines - N': 'TAMPINES',
    'Tampines - Roof': 'TAMPINES',
    'Tampines - S': 'TAMPINES',
    'Tampines - W': 'TAMPINES',
    'Tanglin - E': 'TANGLIN',
    'Tanglin - N': 'TANGLIN',
    'Tanglin - Roof': 'TANGLIN',
    'Tanglin - S': 'TANGLIN',
    'Tanglin - W': 'TANGLIN',
    'ToaPayoh - E': 'TOA PAYOH',
    'ToaPayoh - N': 'TOA PAYOH',
    'ToaPayoh - Roof': 'TOA PAYOH',
    'ToaPayoh - S': 'TOA PAYOH',
    'ToaPayoh - W': 'TOA PAYOH',
    'Tuas - E': 'TUAS',
    'Tuas - N': 'TUAS',
    'Tuas - Roof': 'TUAS',
    'Tuas - S': 'TUAS',
    'Tuas - W': 'TUAS',
    'WesternIslands - E': 'WESTERN ISLANDS',
    'WesternIslands - N': 'WESTERN ISLANDS',
    'WesternIslands - Roof': 'WESTERN ISLANDS',
    'WesternIslands - S': 'WESTERN ISLANDS',
    'WesternIslands - W': 'WESTERN ISLANDS',
    'WesternWaterCatchment - E': 'WESTERN WATER CATCHMENT',
    'WesternWaterCatchment - N': 'WESTERN WATER CATCHMENT',
    'WesternWaterCatchment - Roof': 'WESTERN WATER CATCHMENT',
    'WesternWaterCatchment - S': 'WESTERN WATER CATCHMENT',
    'WesternWaterCatchment - W': 'WESTERN WATER CATCHMENT',
    'Woodlands - E': 'WOODLANDS',
    'Woodlands - N': 'WOODLANDS',
    'Woodlands - Roof': 'WOODLANDS',
    'Woodlands - S': 'WOODLANDS',
    'Woodlands - W': 'WOODLANDS',
    'Yishun - E': 'YISHUN',
    'Yishun - N': 'YISHUN',
    'Yishun - Roof': 'YISHUN',
    'Yishun - S': 'YISHUN',
    'Yishun - W': 'YISHUN',
}


#
# chart_studio.tools.set_credentials_file(username='zhongming.shi'
#                                         , api_key='Zq5BDft589LLGA49ZJb0'
#                                         )
# chart_studio.tools.set_config_file(world_readable=True, sharing='public')


# Load the datasets
geojson_path = "/Users/zshi/Documents/GitHub/cea-user-visual/sg/MasterPlan2019PlanningAreaBoundaryNoSea.geojson"
csv_path = "/Users/zshi/Documents/GitHub/cea-user-visual/sg/surface/SGP_BIA_metrics_AmaranthRed.csv"

gdf = gpd.read_file(geojson_path)
df = pd.read_csv(csv_path)

# Extract 'PLN_AREA_N' from 'Description' using regex
def extract_pln_area(description):
    match = re.search(r"<th>PLN_AREA_N<\/th>\s*<td>(.*?)<\/td>", description)
    return match.group(1) if match else None

gdf["PLN_AREA_N"] = gdf["Description"].apply(extract_pln_area)

# Map 'srf_index' to 'PLN_AREA_N'
df["PLN_AREA_N"] = df["srf_index"].map(dict_surface_to_planning_area)

# Aggregate sum of 'yield_kg_per_year' per planning area
df_agg = df.groupby("PLN_AREA_N")["yield_kg_per_year"].sum().reset_index()

# Merge with GeoDataFrame
gdf = gdf.merge(df_agg, on="PLN_AREA_N", how="left")

# Ensure the CRS is projected (convert from latitude/longitude if needed)
if gdf.crs is None or gdf.crs.to_string() == "EPSG:4326":
    gdf = gdf.to_crs(epsg=3857)  # Convert to meters (Web Mercator)

# Calculate area in square meters
gdf["area_m2"] = gdf["geometry"].area

# Normalize yield by area
gdf["yield_kg_per_m2"] = gdf["yield_kg_per_year"] / gdf["area_m2"]

# Plot the map with color based on normalized yield
fig, ax = plt.subplots(figsize=(12, 8))
cbar = gdf.plot(column="yield_kg_per_m2", cmap="OrRd", legend=True, edgecolor="white", linewidth=0.6, ax=ax)

# Remove axis labels, ticks, and borders
ax.set_xticks([])
ax.set_yticks([])
ax.set_xticklabels([])
ax.set_yticklabels([])
ax.set_frame_on(False)
plt.grid(False)

# Add title
ax.set_title("Annual Red amaranth yield normalised by land area of each Planning area of Singapore (kg/m²/year)", fontsize=11)

# Customize legend: Move below the map and make smaller
cbar_legend = ax.get_legend()
if cbar_legend:
    cbar_legend.set_bbox_to_anchor((5, -0.1))  # Move below
    cbar_legend.set_frame_on(False)  # Remove box around legend
    cbar_legend.set_title("Yield (kg/m²/year)", prop={'size': 5})  # Reduce title font
    for text in cbar_legend.get_texts():
        text.set_fontsize(5)  # Reduce tick font size

# Show the map
plt.show()
