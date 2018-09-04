"""
Electricity imports and exports script

This file takes in the values of the electricity activation pattern (which is only considering buildings present in
network and corresponding district energy systems) and adds in the electricity requirement of decentralized buildings
and recalculates the imports from grid and exports to the grid
"""
from __future__ import division
from __future__ import print_function

import os
import pandas as pd
import numpy as np
import cea.config
import cea.inputlocator
from cea.optimization.lca_calculations import lca_calculations

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def electricity_main(DHN_barcode, DCN_barcode, locator, master_to_slave_vars, ntwFeat, gv, prices, lca, config):

    # if not config.optimization.isheating:
    #     if PV_barcode.count("1") > 0:
    #         df1 = pd.DataFrame({'A': []})
    #         for (i, index) in enumerate(PV_barcode):
    #             if index == str(1):
    #                 if df1.empty:
    #                     data = pd.read_csv(locator.PV_results(buildList[i]))
    #                     df1 = data
    #                 else:
    #                     data = pd.read_csv(locator.PV_results(buildList[i]))
    #                     df1 = df1 + data
    #         if not df1.empty:
    #             df1.to_csv(locator.PV_network(PV_barcode), index=True, float_format='%.2f')
    #
    #         solar_data = pd.read_csv(locator.PV_network(PV_barcode), usecols=['E_PV_gen_kWh', 'Area_PV_m2'], nrows=8760)
    #         E_PV_sum_kW = np.sum(solar_data['E_PV_gen_kWh'])
    #         E_PV_W = solar_data['E_PV_gen_kWh'] * 1000
    #         Area_AvailablePV_m2 = np.max(solar_data['Area_PV_m2'])
    #         Q_PowerPeakAvailablePV_kW = Area_AvailablePV_m2 * ETA_AREA_TO_PEAK
    #         KEV_RpPerkWhPV = calc_Crem_pv(Q_PowerPeakAvailablePV_kW * 1000.0)
    #         KEV_total = KEV_RpPerkWhPV / 100 * np.sum(E_PV_sum_kW)
    #
    #         addcosts_Capex_a = addcosts_Capex_a - KEV_total
    #         addCO2 = addCO2 - (E_PV_sum_kW * 1000 * (lca.EL_PV_TO_CO2 - lca.EL_TO_CO2_GREEN) * WH_TO_J / 1.0E6)
    #         addPrim = addPrim - (E_PV_sum_kW * 1000 * (lca.EL_PV_TO_OIL_EQ - lca.EL_TO_OIL_EQ_GREEN) * WH_TO_J / 1.0E6)
    #
    #         cost_PV_disconnected = KEV_total
    #         CO2_PV_disconnected = (E_PV_sum_kW * 1000 * (lca.EL_PV_TO_CO2 - lca.EL_TO_CO2_GREEN) * WH_TO_J / 1.0E6)
    #         Eprim_PV_disconnected = (E_PV_sum_kW * 1000 * (lca.EL_PV_TO_OIL_EQ - lca.EL_TO_OIL_EQ_GREEN) * WH_TO_J / 1.0E6)
    #
    #         network_data = pd.read_csv(
    #             locator.get_optimization_network_data_folder(master_to_slave_vars.network_data_file_cooling))
    #
    #         E_total_req_W = np.array(network_data['Electr_netw_total_W'])
    #         cooling_data = pd.read_csv(locator.get_optimization_slave_cooling_activation_pattern(master_to_slave_vars.individual_number,
    #                                                                                  master_to_slave_vars.generation_number))
    #
    #         E_from_CHP_W = np.array(cooling_data['E_gen_CCGT_associated_with_absorption_chillers_W'])
    #         E_CHP_to_directload_W = np.zeros(8760)
    #         E_CHP_to_grid_W = np.zeros(8760)
    #         E_PV_to_directload_W = np.zeros(8760)
    #         E_PV_to_grid_W = np.zeros(8760)
    #         E_from_grid_W = np.zeros(8760)
    #
    #         for hour in range(8760):
    #             E_hour_W = E_total_req_W[hour]
    #             if E_hour_W > 0:
    #                 if E_PV_W[hour] > E_hour_W:
    #                     E_PV_to_directload_W[hour] = E_hour_W
    #                     E_PV_to_grid_W[hour] = E_PV_W[hour] - E_total_req_W[hour]
    #                     E_hour_W = 0
    #                 else:
    #                     E_hour_W = E_hour_W - E_PV_W[hour]
    #                     E_PV_to_directload_W[hour] = E_PV_W[hour]
    #
    #                 if E_from_CHP_W[hour] > E_hour_W:
    #                     E_CHP_to_directload_W[hour] = E_hour_W
    #                     E_CHP_to_grid_W[hour] = E_from_CHP_W[hour] - E_hour_W
    #                     E_hour_W = 0
    #                 else:
    #                     E_hour_W = E_hour_W - E_from_CHP_W[hour]
    #                     E_CHP_to_directload_W[hour] = E_from_CHP_W[hour]
    #
    #                 E_from_grid_W[hour] = E_hour_W
    #
    #
    #         date = network_data.DATE.values
    #         results = pd.DataFrame({"DATE": date,
    #                                 "E_total_req_W": E_total_req_W,
    #                                 "E_PV_W": solar_data['E_PV_gen_kWh'] * 1000,
    #                                 "Area_PV_m2": solar_data['Area_PV_m2'],
    #                                 "KEV": KEV_RpPerkWhPV/100 * solar_data['E_PV_gen_kWh'],
    #                                 "E_from_grid_W": E_from_grid_W,
    #                                 "E_PV_to_directload_W": E_PV_to_directload_W,
    #                                 "E_CHP_to_directload_W": E_CHP_to_directload_W,
    #                                 "E_CHP_to_grid_W": E_CHP_to_grid_W,
    #                                 "E_PV_to_grid_W": E_PV_to_grid_W
    #                                 })

    # Electricity Requirement of the Buildings
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values

    E_appliances_total_W = np.zeros(8760)
    E_data_center_total_W = np.zeros(8760)
    E_industrial_processes_total_W = np.zeros(8760)
    E_auxiliary_units_total_W = np.zeros(8760)
    E_hotwater_total_W = np.zeros(8760)
    E_space_heating_total_W = np.zeros(8760)
    E_space_cooling_total_W = np.zeros(8760)

    for name in building_names: # adding the electricity demand of
        building_demand = pd.read_csv(locator.get_demand_results_folder() + '//' + name + ".csv",
                                      usecols=['Eal_kWh', 'Edata_kWh', 'Epro_kWh', 'Eaux_kWh', 'E_ww_kWh', 'E_hs_kWh', 'E_cs_kWh'])
        E_appliances_total_W += building_demand['Eal_kWh'] * 1000
        E_data_center_total_W += building_demand['Edata_kWh'] * 1000
        E_industrial_processes_total_W += building_demand['Epro_kWh'] * 1000
        E_auxiliary_units_total_W += building_demand['Eaux_kWh'] * 1000
        E_hotwater_total_W += building_demand['E_ww_kWh'] * 1000

    for i, name in zip(DHN_barcode, building_names):  # adding the electricity corresponding to space heating of decentralized buildings
        if i is '0':
            building_demand = pd.read_csv(locator.get_demand_results_folder() + '//' + name + ".csv",
                                          usecols=['E_hs_kWh'])
            E_space_heating_total_W += building_demand['E_hs_kWh'] * 1000

    for i, name in zip(DCN_barcode, building_names):  # adding the electricity corresponding to space cooling of decentralized buildings
        if i is '0':
            building_demand = pd.read_csv(locator.get_demand_results_folder() + '//' + name + ".csv",
                                          usecols=['E_cs_kWh'])
            E_space_cooling_total_W += building_demand['E_cs_kWh'] * 1000



    total_electricity_demand_W = E_appliances_total_W + E_data_center_total_W + E_industrial_processes_total_W + \
                                 E_auxiliary_units_total_W + E_hotwater_total_W + E_space_heating_total_W + E_space_cooling_total_W


    # Solar data
    centralized_plant_data = pd.read_csv(
        locator.get_optimization_slave_storage_operation_data(master_to_slave_vars.individual_number,
                                                              master_to_slave_vars.generation_number))
    E_aux_ch_W = np.array(centralized_plant_data['E_aux_ch_W'])
    E_aux_dech_W = np.array(centralized_plant_data['E_aux_dech_W'])
    E_PV_gen_W = np.array(centralized_plant_data['E_PV_Wh'])
    E_PVT_gen_W = np.array(centralized_plant_data['E_PVT_Wh'])
    E_aux_solar_and_heat_recovery_W = np.array(centralized_plant_data['E_aux_solar_and_heat_recovery_Wh'])

    total_electricity_demand_W = total_electricity_demand_W.add(E_aux_ch_W)
    total_electricity_demand_W = total_electricity_demand_W.add(E_aux_dech_W)
    total_electricity_demand_W = total_electricity_demand_W.add(E_aux_solar_and_heat_recovery_W)

    # Electricity of Energy Systems
    if config.optimization.iscooling:

        data_cooling = pd.read_csv(locator.get_optimization_slave_cooling_activation_pattern(master_to_slave_vars.individual_number,
                                                              master_to_slave_vars.generation_number))

        E_used_Lake_W = data_cooling['E_used_Lake_W']
        E_used_VCC_W = data_cooling['E_used_VCC_W']
        E_used_VCC_backup_W = data_cooling['E_used_VCC_backup_W']
        E_used_ACH_W = data_cooling['E_used_ACH_W']
        E_used_CT_W = data_cooling['E_used_CT_W']
        total_electricity_demand_W = total_electricity_demand_W.add(E_used_Lake_W)
        total_electricity_demand_W = total_electricity_demand_W.add(E_used_VCC_W)
        total_electricity_demand_W = total_electricity_demand_W.add(E_used_VCC_backup_W)
        total_electricity_demand_W = total_electricity_demand_W.add(E_used_ACH_W)
        total_electricity_demand_W = total_electricity_demand_W.add(E_used_CT_W)


        E_from_CHP_W = data_cooling['E_gen_CCGT_associated_with_absorption_chillers_W']
        E_from_PV_W = E_PV_gen_W
        E_from_PVT_W = E_PVT_gen_W


        E_CHP_to_directload_W = np.zeros(8760)
        E_CHP_to_grid_W = np.zeros(8760)
        E_PV_to_directload_W = np.zeros(8760)
        E_PV_to_grid_W = np.zeros(8760)
        E_from_grid_W = np.zeros(8760)

        for hour in range(8760):
            E_hour_W = total_electricity_demand_W[hour]
            if E_hour_W > 0:
                if E_from_PV_W[hour] > E_hour_W:
                    E_PV_to_directload_W[hour] = E_hour_W
                    E_PV_to_grid_W[hour] = E_from_PV_W[hour] - total_electricity_demand_W[hour]
                    E_hour_W = 0
                else:
                    E_hour_W = E_hour_W - E_from_PV_W[hour]
                    E_PV_to_directload_W[hour] = E_from_PV_W[hour]

                if E_from_CHP_W[hour] > E_hour_W:
                    E_CHP_to_directload_W[hour] = E_hour_W
                    E_CHP_to_grid_W[hour] = E_from_CHP_W[hour] - E_hour_W
                    E_hour_W = 0
                else:
                    E_hour_W = E_hour_W - E_from_CHP_W[hour]
                    E_CHP_to_directload_W[hour] = E_from_CHP_W[hour]

                E_from_grid_W[hour] = E_hour_W

        date = data_network_electricity.DATE.values

        results = pd.DataFrame({"DATE": date,
                                "E_total_req_W": total_electricity_demand_W,
                                "E_from_grid_W": E_from_grid_W,
                                "E_VCC_W": E_used_VCC_W,
                                "E_VCC_backup_W": E_used_VCC_backup_W,
                                "E_ACH_W": E_used_ACH_W,
                                "E_CT_W": E_used_CT_W,
                                "E_PV_to_directload_W": E_PV_to_directload_W,
                                "E_CHP_to_directload_W": E_CHP_to_directload_W,
                                "E_CHP_to_grid_W": E_CHP_to_grid_W,
                                "E_PV_to_grid_W": E_PV_to_grid_W,
                                "E_for_hot_water_demand_W": E_for_hot_water_demand_W,
                                "E_decentralized_appliances_W": E_decentralized_appliances_W,
                                "E_appliances_total_W": E_appliances_total_W,
                                "E_total_to_grid_W_negative": - E_PV_to_grid_W - E_CHP_to_grid_W}) #let's keep this negative so it is something exported, we can use it in the graphs of likelihood

        results.to_csv(
            locator.get_optimization_slave_electricity_activation_pattern_processed(individual, generation), index=False)

    return results

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    generation = 25
    individual = 10
    print("Calculating imports and exports of individual" + str(individual) + " of generation " + str(generation))

    electricity_main(generation, individual, locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())