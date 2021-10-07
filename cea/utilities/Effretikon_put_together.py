import pandas as pd
import os
from geopandas import GeoDataFrame as gdf




DIR_PROJECT = r"C:\Users\jfo\OneDrive - EBP\Dokumente\1_Projekte\22-Efreetikon-PV\Effretikon_PV"
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
             "Verwaltung_dezentral_cluster",
             "Bachtelstrasse_10_illnau",
             "Bannhaldenstrasse_8_effretikon",
             "Dorfstrasse_32_effretikon",
             "Rappenstrasse_13a_effretikon"]

data = {}
projects = [r"C:\Users\jfo\OneDrive - EBP\Dokumente\1_Projekte\22-Efreetikon-PV\Effretikon_PV",
            r"C:\Users\jfo\OneDrive - EBP\Dokumente\1_Projekte\22-Efreetikon-PV\Effretikon_PV_saniert"]
cases = ["heute_zustand",
         "zukunft_saniert"]
for project, case in zip(projects, cases):
    for scenario in SCENARIOS:
        path = os.path.join(project,scenario,PATH_NAMES_ADDRESS_FILE)
        dbf = gdf.from_file(path)
        names = dbf.Name.values
        address = dbf.address.values
        data_scenario_strom_APPL = pd.DataFrame()
        data_scenario_thermal = pd.DataFrame()
        data_scenario_strom_WP = pd.DataFrame()
        for name, address in zip(names, address):
            path_demand_folder = os.path.join(project, scenario, PATH_FOLDER_DEMAND, name + ".csv")
            data_demand = pd.read_csv(path_demand_folder)
            strom_APPL = (data_demand["GRID_kWh"] - data_demand["GRID_ww_kWh"].values - data_demand["GRID_hs_kWh"]).values
            thermal = (data_demand["Qhs_sys_kWh"] + data_demand["Qww_sys_kWh"]).values
            strom_WP = (data_demand["GRID_ww_kWh"].values + data_demand["GRID_hs_kWh"]).values
            data_scenario_strom_APPL = pd.concat([data_scenario_strom_APPL, pd.DataFrame({address:strom_APPL})], axis =1)
            data_scenario_thermal = pd.concat([data_scenario_thermal, pd.DataFrame({address:thermal})], axis =1)
            data_scenario_strom_WP = pd.concat([data_scenario_strom_WP, pd.DataFrame({address:strom_WP})], axis =1)

        path_result = os.path.join(project, RESULTS_FOLDER, scenario+"_"+case+".xlsx")
        #create a Pandas Excel writer using XlsxWriter as the engine
        writer = pd.ExcelWriter(path_result, engine='xlsxwriter')
        data_scenario_strom_APPL.to_excel(writer, sheet_name='STROM_LICHT_USW_OHNE_WP_KWH')
        data_scenario_thermal.to_excel(writer, sheet_name='WAERMEVERBRAUCH_KWH')
        data_scenario_strom_WP.to_excel(writer, sheet_name='STROM_NUR_WP_UND_OFEN_KWH')

        #close the Pandas Excel writer and output the Excel file
        writer.save()