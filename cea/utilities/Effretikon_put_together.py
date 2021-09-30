import pandas as pd
import os
from geopandas import GeoDataFrame as gdf


DIR_PROJECT = r"C:\Users\jfo\OneDrive - EBP\Dokumente\1_Projekte\22-Efreetikon-PV\Effretikon_PV_saniert"
RESULTS_FOLDER = "Resultaten"
PATH_NAMES_ADDRESS_FILE = "inputs/building-geometry/zone.dbf"
PATH_FOLDER_DEMAND = "outputs/data/demand"
SCENARIOS = ["Altersheim",
             "Chratz_cluster",
             "Gelbes_schulhaus",
             "Hauptstrasse_2_effretikon",
             "kyburg_cluster",
             "Schlimperg_cluster",
             "schulhausstrasse_12_Effretikon",
             "Verwaltung_dezentral_cluster"]

data = {}
for scenario in SCENARIOS:
    path = os.path.join(DIR_PROJECT,scenario,PATH_NAMES_ADDRESS_FILE)
    dbf = gdf.from_file(path)
    names = dbf.Name.values
    address = dbf.address.values
    data_scenario_elec = pd.DataFrame()
    data_scenario_thermal = pd.DataFrame()
    for name, address in zip(names, address):
        path_demand_folder = os.path.join(DIR_PROJECT, scenario, PATH_FOLDER_DEMAND, name + ".csv")
        data_demand = pd.read_csv(path_demand_folder)
        elec = data_demand["GRID_kWh"].values
        thermal = (data_demand["Qhs_sys_kWh"] + data_demand["Qww_sys_kWh"]).values
        data_scenario_elec = pd.concat([data_scenario_elec, pd.DataFrame({address:elec})], axis =1)
        data_scenario_thermal = pd.concat([data_scenario_thermal, pd.DataFrame({address:thermal})], axis =1)

    path_result = os.path.join(DIR_PROJECT, RESULTS_FOLDER, scenario+"saniert.xlsx")
    #create a Pandas Excel writer using XlsxWriter as the engine
    writer = pd.ExcelWriter(path_result, engine='xlsxwriter')
    data_scenario_elec.to_excel(writer, sheet_name='ELEKTRO_KWH')
    data_scenario_thermal.to_excel(writer, sheet_name='HEIZUNG_KWH')

    #close the Pandas Excel writer and output the Excel file
    writer.save()