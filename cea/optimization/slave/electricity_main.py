"""
Electricity imports and exports script

This file takes in the values of the electricity activation pattern (which is only considering buildings present in
network and corresponding district energy systems) and adds in the electricity requirement of decentralized buildings
and recalculates the imports from grid and exports to the grid
"""
from __future__ import division
from __future__ import print_function
import pandas as pd
import numpy as np
import cea.config
import cea.inputlocator
from cea.constants import WH_TO_J

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def electricity_calculations_of_all_buildings(DHN_barcode, DCN_barcode, locator, master_to_slave_vars, ntwFeat, gv, prices, lca, config):

    # Electricity Requirement of the Buildings
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values

    costs_electricity_USD = 0
    GHG_electricity_tonCO2 = 0
    PEN_electricity_MJoil = 0


    # step 1: Get demand of all the district (tota
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


    # Step2. get solar potential data
    centralized_plant_data = pd.read_csv(
        locator.get_optimization_slave_storage_operation_data(master_to_slave_vars.individual_number,
                                                              master_to_slave_vars.generation_number))
    E_aux_ch_W = np.array(centralized_plant_data['E_aux_ch_W'])
    E_aux_dech_W = np.array(centralized_plant_data['E_aux_dech_W'])
    E_PV_gen_W = np.array(centralized_plant_data['E_PV_Wh'])
    E_PVT_gen_W = np.array(centralized_plant_data['E_PVT_Wh'])
    E_aux_solar_and_heat_recovery_W = np.array(centralized_plant_data['E_aux_solar_and_heat_recovery_Wh'])
    Q_SC_ET_gen_Wh = np.array(centralized_plant_data['Q_SC_ET_gen_Wh'])
    Q_SC_FP_gen_Wh = np.array(centralized_plant_data['Q_SC_FP_gen_Wh'])
    Q_PVT_gen_Wh = np.array(centralized_plant_data['Q_PVT_gen_Wh'])
    Q_SC_and_PVT_Wh = Q_SC_ET_gen_Wh + Q_SC_FP_gen_Wh + Q_PVT_gen_Wh

    total_electricity_demand_W = total_electricity_demand_W.add(E_aux_ch_W)
    total_electricity_demand_W = total_electricity_demand_W.add(E_aux_dech_W)
    total_electricity_demand_W = total_electricity_demand_W.add(E_aux_solar_and_heat_recovery_W)

    date = centralized_plant_data.DATE.values

    # Step3. Electricity of Energy Systems
    # if there is district cooling and at least one building is in the network
    if config.district_cooling_network and master_to_slave_vars.DCN_barcode.count("1") > 0:

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


        E_CHP_directload_W = np.zeros(8760)
        E_CHP_grid_W = np.zeros(8760)
        E_PV_directload_W = np.zeros(8760)
        E_PV_grid_W = np.zeros(8760)
        E_PVT_directload_W = np.zeros(8760)
        E_PVT_grid_W = np.zeros(8760)
        E_GRID_directload_W = np.zeros(8760)

        for hour in range(8760):
            E_hour_W = total_electricity_demand_W[hour]
            if E_hour_W > 0:
                if E_from_PV_W[hour] > E_hour_W:
                    E_PV_directload_W[hour] = E_hour_W
                    E_PV_grid_W[hour] = E_from_PV_W[hour] - total_electricity_demand_W[hour]
                    E_hour_W = 0
                else:
                    E_hour_W = E_hour_W - E_from_PV_W[hour]
                    E_PV_directload_W[hour] = E_from_PV_W[hour]

                if E_from_PVT_W[hour] > E_hour_W:
                    E_PVT_directload_W[hour] = E_hour_W
                    E_PVT_grid_W[hour] = E_from_PVT_W[hour] - total_electricity_demand_W[hour]
                    E_hour_W = 0
                else:
                    E_hour_W = E_hour_W - E_from_PVT_W[hour]
                    E_PVT_directload_W[hour] = E_from_PVT_W[hour]

                if E_from_CHP_W[hour] > E_hour_W:
                    E_CHP_directload_W[hour] = E_hour_W
                    E_CHP_grid_W[hour] = E_from_CHP_W[hour] - E_hour_W
                    E_hour_W = 0
                else:
                    E_hour_W = E_hour_W - E_from_CHP_W[hour]
                    E_CHP_directload_W[hour] = E_from_CHP_W[hour]

                E_GRID_directload_W[hour] = E_hour_W


        PEN_from_heat_used_SC_and_PVT_MJoil = Q_SC_and_PVT_Wh * lca.SOLARCOLLECTORS_TO_OIL * WH_TO_J / 1.0E6
        PEN_saved_from_electricity_sold_CHP_MJoil = E_from_CHP_W * (- lca.EL_TO_OIL_EQ) * WH_TO_J / 1.0E6
        PEN_saved_from_electricity_sold_Solar_MJoil = (np.add(E_PV_gen_W, E_PVT_gen_W)) * (lca.EL_PV_TO_OIL_EQ - lca.EL_TO_OIL_EQ) * WH_TO_J / 1.0E6
        PEN_HPSolarandHeatRecovery_MJoil = E_aux_solar_and_heat_recovery_W * lca.EL_TO_OIL_EQ * WH_TO_J / 1.0E6
        PEN_Lake_MJoil = E_used_Lake_W * lca.EL_TO_OIL_EQ * WH_TO_J / 1.0E6
        PEN_VCC_MJoil = E_used_VCC_W * lca.EL_TO_OIL_EQ * WH_TO_J / 1.0E6
        PEN_VCC_backup_MJoil = E_used_VCC_backup_W * lca.EL_TO_OIL_EQ * WH_TO_J / 1.0E6
        PEN_ACH_MJoil = E_used_ACH_W * lca.EL_TO_OIL_EQ * WH_TO_J / 1.0E6
        PEN_CT_MJoil = E_used_CT_W * lca.EL_TO_OIL_EQ * WH_TO_J / 1.0E6



        GHG_from_heat_used_SC_and_PVT_tonCO2 = Q_SC_and_PVT_Wh * lca.SOLARCOLLECTORS_TO_CO2 * WH_TO_J / 1.0E6
        GHG_saved_from_electricity_sold_CHP_tonCO2 = E_from_CHP_W * (- lca.EL_TO_CO2) * WH_TO_J / 1.0E6
        GHG_saved_from_electricity_sold_Solar_tonCO2 = (np.add(E_PV_gen_W, E_PVT_gen_W)) * (lca.EL_PV_TO_CO2 - lca.EL_TO_CO2) * WH_TO_J / 1.0E6
        GHG_HPSolarandHeatRecovery_tonCO2 = E_aux_solar_and_heat_recovery_W * lca.EL_TO_CO2 * WH_TO_J / 1E6
        GHG_Lake_MJoil = E_used_Lake_W * lca.EL_TO_CO2 * WH_TO_J / 1.0E6
        GHG_VCC_MJoil = E_used_VCC_W * lca.EL_TO_CO2 * WH_TO_J / 1.0E6
        GHG_VCC_backup_MJoil = E_used_VCC_backup_W * lca.EL_TO_CO2 * WH_TO_J / 1.0E6
        GHG_ACH_MJoil = E_used_ACH_W * lca.EL_TO_CO2 * WH_TO_J / 1.0E6
        GHG_CT_MJoil = E_used_CT_W * lca.EL_TO_CO2 * WH_TO_J / 1.0E6


        results = pd.DataFrame({"DATE": date,
                                "E_total_req_W": total_electricity_demand_W,
                                "E_used_Lake_W": E_used_Lake_W,
                                "E_used_VCC_W": E_used_VCC_W,
                                "E_used_VCC_backup_W": E_used_VCC_backup_W,
                                "E_used_ACH_W": E_used_ACH_W,
                                "E_used_CT_W": E_used_CT_W,
                                "E_from_CHP_W": E_from_CHP_W,
                                "E_from_PV_W": E_from_PV_W,
                                "E_from_PVT_W": E_from_PVT_W,
                                "E_CHP_directload_W": E_CHP_directload_W,
                                "E_CHP_grid_W": E_CHP_grid_W,
                                "E_PV_directload_W": E_PV_directload_W,
                                "E_PV_grid_W": E_PV_grid_W,
                                "E_PVT_directload_W": E_PVT_directload_W,
                                "E_PVT_grid_W": E_PVT_grid_W,
                                "E_GRID_directload_W": E_GRID_directload_W,
                                "E_appliances_total_W": E_appliances_total_W,
                                "E_data_center_total_W": E_data_center_total_W,
                                "E_industrial_processes_total_W": E_industrial_processes_total_W,
                                "E_auxiliary_units_total_W": E_auxiliary_units_total_W,
                                "E_hotwater_total_W": E_hotwater_total_W,
                                "E_space_heating_total_W": E_space_heating_total_W,
                                "E_space_cooling_total_W": E_space_cooling_total_W,
                                "E_total_to_grid_W_negative": - E_PV_grid_W - E_CHP_grid_W - E_PVT_grid_W,
                                "PEN_from_heat_used_SC_and_PVT_MJoil": PEN_from_heat_used_SC_and_PVT_MJoil,
                                "PEN_saved_from_electricity_sold_CHP_MJoil": PEN_saved_from_electricity_sold_CHP_MJoil,
                                "PEN_saved_from_electricity_sold_Solar_MJoil": PEN_saved_from_electricity_sold_Solar_MJoil,
                                "PEN_HPSolarandHeatRecovery_MJoil": PEN_HPSolarandHeatRecovery_MJoil,
                                "PEN_Lake_MJoil": PEN_Lake_MJoil,
                                "PEN_VCC_MJoil": PEN_VCC_MJoil,
                                "PEN_VCC_backup_MJoil": PEN_VCC_backup_MJoil,
                                "PEN_ACH_MJoil": PEN_ACH_MJoil,
                                "PEN_CT_MJoil": PEN_CT_MJoil,
                                "GHG_from_heat_used_SC_and_PVT_tonCO2": GHG_from_heat_used_SC_and_PVT_tonCO2,
                                "GHG_saved_from_electricity_sold_CHP_tonCO2": GHG_saved_from_electricity_sold_CHP_tonCO2,
                                "GHG_saved_from_electricity_sold_Solar_tonCO2": GHG_saved_from_electricity_sold_Solar_tonCO2,
                                "GHG_HPSolarandHeatRecovery_tonCO2": GHG_HPSolarandHeatRecovery_tonCO2,
                                "GHG_Lake_MJoil": GHG_Lake_MJoil,
                                "GHG_VCC_backup_MJoil": GHG_VCC_backup_MJoil,
                                "GHG_ACH_MJoil": GHG_ACH_MJoil,
                                "GHG_CT_MJoil": GHG_CT_MJoil
                                }) #let's keep this negative so it is something exported, we can use it in the graphs of likelihood

        results.to_csv(
            locator.get_optimization_slave_electricity_activation_pattern_cooling(master_to_slave_vars.individual_number, master_to_slave_vars.generation_number), index=False)


        GHG_electricity_tonCO2 += np.sum(GHG_from_heat_used_SC_and_PVT_tonCO2) + np.sum(
            GHG_saved_from_electricity_sold_CHP_tonCO2) + np.sum(GHG_saved_from_electricity_sold_Solar_tonCO2) + np.sum(
            GHG_HPSolarandHeatRecovery_tonCO2) + np.sum(GHG_Lake_MJoil) + np.sum(GHG_VCC_MJoil) + np.sum(
            GHG_VCC_backup_MJoil) + np.sum(GHG_ACH_MJoil) + np.sum(GHG_CT_MJoil)

        PEN_electricity_MJoil += np.sum(PEN_from_heat_used_SC_and_PVT_MJoil) + np.sum(
            PEN_saved_from_electricity_sold_CHP_MJoil) + np.sum(PEN_saved_from_electricity_sold_Solar_MJoil) + np.sum(
            PEN_HPSolarandHeatRecovery_MJoil) + np.sum(PEN_Lake_MJoil) + np.sum(PEN_VCC_MJoil) + np.sum(
            PEN_VCC_backup_MJoil) + np.sum(PEN_ACH_MJoil) + np.sum(PEN_CT_MJoil)

        for hour in range(len(total_electricity_demand_W)):
            costs_electricity_USD += total_electricity_demand_W[hour] * lca.ELEC_PRICE[hour] - (
                    E_from_CHP_W[hour] + E_from_PV_W[hour] + E_from_PVT_W[hour]) * lca.ELEC_PRICE[hour]

    # if there is district heating and at least one building is in the network
    if config.district_heating_network and master_to_slave_vars.DHN_barcode.count("1") > 0:

        data_heating = pd.read_csv(locator.get_optimization_slave_heating_activation_pattern(master_to_slave_vars.individual_number,
                                                              master_to_slave_vars.generation_number))

        E_used_BackupBoiler_W = np.array(data_heating['E_BackupBoiler_req_W'])
        E_used_BaseBoiler_W = np.array(data_heating['E_BaseBoiler_req_W'])
        E_used_GHP_W = np.array(data_heating['E_GHP_req_W'])
        E_used_HPLake_W = np.array(data_heating['E_HPLake_req_W'])
        E_used_HPSew_W = np.array(data_heating['E_HPSew_req_W'])
        E_used_PeakBoiler_W = np.array(data_heating['E_PeakBoiler_req_W'])
        total_electricity_demand_W = total_electricity_demand_W.add(E_used_BackupBoiler_W)
        total_electricity_demand_W = total_electricity_demand_W.add(E_used_BaseBoiler_W)
        total_electricity_demand_W = total_electricity_demand_W.add(E_used_GHP_W)
        total_electricity_demand_W = total_electricity_demand_W.add(E_used_HPLake_W)
        total_electricity_demand_W = total_electricity_demand_W.add(E_used_HPSew_W)
        total_electricity_demand_W = total_electricity_demand_W.add(E_used_PeakBoiler_W)

        E_from_PV_W = E_PV_gen_W
        E_from_PVT_W = E_PVT_gen_W
        E_from_CHP_W = np.array(data_heating['E_CHP_gen_W'])
        E_from_Furnace_W = np.array(data_heating['E_Furnace_gen_W'])

        E_CHP_directload_W = np.zeros(8760)
        E_CHP_grid_W = np.zeros(8760)
        E_PV_directload_W = np.zeros(8760)
        E_PV_grid_W = np.zeros(8760)
        E_PVT_directload_W = np.zeros(8760)
        E_PVT_grid_W = np.zeros(8760)
        E_Furnace_directload_W = np.zeros(8760)
        E_Furnace_grid_W = np.zeros(8760)
        E_GRID_directload_W = np.zeros(8760)

        for hour in range(8760):
            E_hour_W = total_electricity_demand_W[hour]
            if E_hour_W > 0:
                if E_from_PV_W[hour] > E_hour_W:
                    E_PV_directload_W[hour] = E_hour_W
                    E_PV_grid_W[hour] = E_from_PV_W[hour] - total_electricity_demand_W[hour]
                    E_hour_W = 0
                else:
                    E_hour_W = E_hour_W - E_from_PV_W[hour]
                    E_PV_directload_W[hour] = E_from_PV_W[hour]

                if E_from_PVT_W[hour] > E_hour_W:
                    E_PVT_directload_W[hour] = E_hour_W
                    E_PVT_grid_W[hour] = E_from_PVT_W[hour] - total_electricity_demand_W[hour]
                    E_hour_W = 0
                else:
                    E_hour_W = E_hour_W - E_from_PVT_W[hour]
                    E_PVT_directload_W[hour] = E_from_PVT_W[hour]

                if E_from_CHP_W[hour] > E_hour_W:
                    E_CHP_directload_W[hour] = E_hour_W
                    E_CHP_grid_W[hour] = E_from_CHP_W[hour] - E_hour_W
                    E_hour_W = 0
                else:
                    E_hour_W = E_hour_W - E_from_CHP_W[hour]
                    E_CHP_directload_W[hour] = E_from_CHP_W[hour]

                if E_from_Furnace_W[hour] > E_hour_W:
                    E_Furnace_directload_W[hour] = E_hour_W
                    E_Furnace_grid_W[hour] = E_from_Furnace_W[hour] - E_hour_W
                    E_hour_W = 0
                else:
                    E_hour_W = E_hour_W - E_from_Furnace_W[hour]
                    E_Furnace_directload_W[hour] = E_from_Furnace_W[hour]

                E_GRID_directload_W[hour] = E_hour_W

        PEN_from_heat_used_SC_and_PVT_MJoil = Q_SC_and_PVT_Wh * lca.SOLARCOLLECTORS_TO_OIL * WH_TO_J / 1.0E6
        PEN_saved_from_electricity_sold_CHP_MJoil = E_from_CHP_W * (- lca.EL_TO_OIL_EQ) * WH_TO_J / 1.0E6
        PEN_saved_from_electricity_sold_Solar_MJoil = (np.add(E_PV_gen_W, E_PVT_gen_W)) * (lca.EL_PV_TO_OIL_EQ - lca.EL_TO_OIL_EQ) * WH_TO_J / 1.0E6
        PEN_HPSolarandHeatRecovery_MJoil = E_aux_solar_and_heat_recovery_W * lca.EL_TO_OIL_EQ * WH_TO_J / 1.0E6
        PEN_saved_from_electricity_sold_Furnace_MJoil = E_from_Furnace_W * (- lca.EL_TO_OIL_EQ) * WH_TO_J / 1.0E6
        PEN_AddBoiler_MJoil = E_used_BackupBoiler_W * (lca.EL_TO_OIL_EQ) * WH_TO_J / 1.0E6
        PEN_BaseBoiler_MJoil = E_used_BaseBoiler_W * (lca.EL_TO_OIL_EQ) * WH_TO_J / 1.0E6
        PEN_PeakBoiler_MJoil = E_used_PeakBoiler_W * (lca.EL_TO_OIL_EQ) * WH_TO_J / 1.0E6
        PEN_GHP_MJoil = E_used_GHP_W * (lca.EL_TO_OIL_EQ) * WH_TO_J / 1.0E6
        PEN_HPLake_MJoil = E_used_HPLake_W * (lca.EL_TO_OIL_EQ) * WH_TO_J / 1.0E6
        PEN_HPSew_MJoil = E_used_HPSew_W * (lca.EL_TO_OIL_EQ) * WH_TO_J / 1.0E6

        GHG_from_heat_used_SC_and_PVT_tonCO2 = Q_SC_and_PVT_Wh * lca.SOLARCOLLECTORS_TO_CO2 * WH_TO_J / 1.0E6
        GHG_saved_from_electricity_sold_CHP_tonCO2 = E_from_CHP_W * (- lca.EL_TO_CO2) * WH_TO_J / 1.0E6
        GHG_saved_from_electricity_sold_Solar_tonCO2 = (np.add(E_PV_gen_W, E_PVT_gen_W)) * (lca.EL_PV_TO_CO2 - lca.EL_TO_CO2) * WH_TO_J / 1.0E6
        GHG_HPSolarandHeatRecovery_tonCO2 = E_aux_solar_and_heat_recovery_W * lca.EL_TO_CO2 * WH_TO_J / 1E6
        GHG_saved_from_electricity_sold_Furnace_tonCO2 = np.sum(E_from_Furnace_W) * (- lca.EL_TO_CO2) * WH_TO_J / 1.0E6
        GHG_AddBoiler_tonCO2 = E_used_BackupBoiler_W * (lca.EL_TO_CO2) * WH_TO_J / 1.0E6
        GHG_BaseBoiler_tonCO2 = E_used_BaseBoiler_W * (lca.EL_TO_CO2) * WH_TO_J / 1.0E6
        GHG_PeakBoiler_tonCO2 = E_used_PeakBoiler_W * (lca.EL_TO_CO2) * WH_TO_J / 1.0E6
        GHG_GHP_tonCO2 = E_used_GHP_W * (lca.EL_TO_CO2) * WH_TO_J / 1.0E6
        GHG_HPLake_tonCO2 = E_used_HPLake_W * (lca.EL_TO_CO2) * WH_TO_J / 1.0E6
        GHG_HPSew_tonCO2 = E_used_HPSew_W * (lca.EL_TO_CO2) * WH_TO_J / 1.0E6

        results = pd.DataFrame({"DATE": date,
                                "E_total_req_W": total_electricity_demand_W,
                                "E_used_BackupBoiler_W": E_used_BackupBoiler_W,
                                "E_used_BaseBoiler_W": E_used_BaseBoiler_W,
                                "E_used_GHP_W": E_used_GHP_W,
                                "E_used_HPLake_W": E_used_HPLake_W,
                                "E_used_HPSew_W": E_used_HPSew_W,
                                "E_used_PeakBoiler_W": E_used_PeakBoiler_W,
                                "E_from_PV_W": E_from_PV_W,
                                "E_from_PVT_W": E_from_PVT_W,
                                "E_from_CHP_W": E_from_CHP_W,
                                "E_from_Furnace_W": E_from_Furnace_W,
                                "E_CHP_directload_W": E_CHP_directload_W,
                                "E_CHP_grid_W": E_CHP_grid_W,
                                "E_PV_directload_W": E_PV_directload_W,
                                "E_PV_grid_W": E_PV_grid_W,
                                "E_PVT_directload_W": E_PVT_directload_W,
                                "E_PVT_grid_W": E_PVT_grid_W,
                                "E_Furnace_directload_W": E_Furnace_directload_W,
                                "E_Furnace_grid_W": E_Furnace_grid_W,
                                "E_GRID_directload_W": E_GRID_directload_W,
                                "E_appliances_total_W": E_appliances_total_W,
                                "E_data_center_total_W": E_data_center_total_W,
                                "E_industrial_processes_total_W": E_industrial_processes_total_W,
                                "E_auxiliary_units_total_W": E_auxiliary_units_total_W,
                                "E_hotwater_total_W": E_hotwater_total_W,
                                "E_space_heating_total_W": E_space_heating_total_W,
                                "E_space_cooling_total_W": E_space_cooling_total_W,
                                "E_total_to_grid_W_negative": - E_PV_grid_W - E_CHP_grid_W - E_PVT_grid_W - E_Furnace_grid_W,
                                "PEN_from_heat_used_SC_and_PVT_MJoil": PEN_from_heat_used_SC_and_PVT_MJoil,
                                "PEN_saved_from_electricity_sold_CHP_MJoil": PEN_saved_from_electricity_sold_CHP_MJoil,
                                "PEN_saved_from_electricity_sold_Solar_MJoil": PEN_saved_from_electricity_sold_Solar_MJoil,
                                "PEN_HPSolarandHeatRecovery_MJoil": PEN_HPSolarandHeatRecovery_MJoil,
                                "PEN_saved_from_electricity_sold_Furnace_MJoil": PEN_saved_from_electricity_sold_Furnace_MJoil,
                                "PEN_AddBoiler_MJoil": PEN_AddBoiler_MJoil,
                                "PEN_BaseBoiler_MJoil": PEN_BaseBoiler_MJoil,
                                "PEN_PeakBoiler_MJoil": PEN_PeakBoiler_MJoil,
                                "PEN_GHP_MJoil": PEN_GHP_MJoil,
                                "PEN_HPLake_MJoil": PEN_HPLake_MJoil,
                                "PEN_HPSew_MJoil": PEN_HPSew_MJoil,
                                "GHG_from_heat_used_SC_and_PVT_tonCO2": GHG_from_heat_used_SC_and_PVT_tonCO2,
                                "GHG_saved_from_electricity_sold_CHP_tonCO2": GHG_saved_from_electricity_sold_CHP_tonCO2,
                                "GHG_saved_from_electricity_sold_Solar_tonCO2": GHG_saved_from_electricity_sold_Solar_tonCO2,
                                "GHG_HPSolarandHeatRecovery_tonCO2": GHG_HPSolarandHeatRecovery_tonCO2,
                                "GHG_saved_from_electricity_sold_Furnace_tonCO2": GHG_saved_from_electricity_sold_Furnace_tonCO2,
                                "GHG_AddBoiler_tonCO2": GHG_AddBoiler_tonCO2,
                                "GHG_BaseBoiler_tonCO2": GHG_BaseBoiler_tonCO2,
                                "GHG_PeakBoiler_tonCO2": GHG_PeakBoiler_tonCO2,
                                "GHG_GHP_tonCO2": GHG_GHP_tonCO2,
                                "GHG_HPLake_tonCO2": GHG_HPLake_tonCO2,
                                "GHG_HPSew_tonCO2": GHG_HPSew_tonCO2
                                }) #let's keep this negative so it is something exported, we can use it in the graphs of likelihood

        results.to_csv(
            locator.get_optimization_slave_electricity_activation_pattern_heating(master_to_slave_vars.individual_number, master_to_slave_vars.generation_number), index=False)

        GHG_electricity_tonCO2 += np.sum(GHG_from_heat_used_SC_and_PVT_tonCO2) + np.sum(
            GHG_saved_from_electricity_sold_CHP_tonCO2) + np.sum(GHG_saved_from_electricity_sold_Solar_tonCO2) + np.sum(
            GHG_HPSolarandHeatRecovery_tonCO2) + np.sum(GHG_saved_from_electricity_sold_Furnace_tonCO2) + np.sum(
            GHG_AddBoiler_tonCO2) + np.sum(GHG_BaseBoiler_tonCO2) + np.sum(GHG_PeakBoiler_tonCO2) + np.sum(
            GHG_GHP_tonCO2) + np.sum(GHG_HPLake_tonCO2) + np.sum(GHG_HPSew_tonCO2)

        PEN_electricity_MJoil += np.sum(PEN_from_heat_used_SC_and_PVT_MJoil) + np.sum(
            PEN_saved_from_electricity_sold_CHP_MJoil) + np.sum(PEN_saved_from_electricity_sold_Solar_MJoil) + np.sum(
            PEN_HPSolarandHeatRecovery_MJoil) + np.sum(PEN_saved_from_electricity_sold_Furnace_MJoil) + np.sum(
            PEN_AddBoiler_MJoil) + np.sum(PEN_BaseBoiler_MJoil) + np.sum(PEN_PeakBoiler_MJoil) + np.sum(
            PEN_GHP_MJoil) + np.sum(PEN_HPLake_MJoil) + np.sum(PEN_HPSew_MJoil)

        for hour in range(len(total_electricity_demand_W)):
            costs_electricity_USD += total_electricity_demand_W[hour] * lca.ELEC_PRICE[hour] - (
                        E_from_CHP_W[hour] + E_from_Furnace_W[hour] + E_from_PV_W[hour] + E_from_PVT_W[hour]) * lca.ELEC_PRICE[hour]

    # if all buildings are decentralized heating case
    if master_to_slave_vars.DHN_barcode.count("1") == 0:

        E_from_PV_W = E_PV_gen_W
        E_from_PVT_W = E_PVT_gen_W

        E_PV_directload_W = np.zeros(8760)
        E_PV_grid_W = np.zeros(8760)
        E_PVT_directload_W = np.zeros(8760)
        E_PVT_grid_W = np.zeros(8760)

        E_GRID_directload_W = np.zeros(8760)

        for hour in range(8760):
            E_hour_W = total_electricity_demand_W[hour]
            if E_hour_W > 0:
                if E_from_PV_W[hour] > E_hour_W:
                    E_PV_directload_W[hour] = E_hour_W
                    E_PV_grid_W[hour] = E_from_PV_W[hour] - total_electricity_demand_W[hour]
                    E_hour_W = 0
                else:
                    E_hour_W = E_hour_W - E_from_PV_W[hour]
                    E_PV_directload_W[hour] = E_from_PV_W[hour]

                if E_from_PVT_W[hour] > E_hour_W:
                    E_PVT_directload_W[hour] = E_hour_W
                    E_PVT_grid_W[hour] = E_from_PVT_W[hour] - total_electricity_demand_W[hour]
                    E_hour_W = 0
                else:
                    E_hour_W = E_hour_W - E_from_PVT_W[hour]
                    E_PVT_directload_W[hour] = E_from_PVT_W[hour]

                E_GRID_directload_W[hour] = E_hour_W

        PEN_from_heat_used_SC_and_PVT_MJoil = Q_SC_and_PVT_Wh * lca.SOLARCOLLECTORS_TO_OIL * WH_TO_J / 1.0E6
        PEN_saved_from_electricity_sold_Solar_MJoil = (np.add(E_PV_gen_W, E_PVT_gen_W)) * (lca.EL_PV_TO_OIL_EQ - lca.EL_TO_OIL_EQ) * WH_TO_J / 1.0E6
        PEN_HPSolarandHeatRecovery_MJoil = E_aux_solar_and_heat_recovery_W * lca.EL_TO_OIL_EQ * WH_TO_J / 1.0E6


        GHG_from_heat_used_SC_and_PVT_tonCO2 = Q_SC_and_PVT_Wh * lca.SOLARCOLLECTORS_TO_CO2 * WH_TO_J / 1.0E6
        GHG_saved_from_electricity_sold_Solar_tonCO2 = (np.add(E_PV_gen_W, E_PVT_gen_W)) * (lca.EL_PV_TO_CO2 - lca.EL_TO_CO2) * WH_TO_J / 1.0E6
        GHG_HPSolarandHeatRecovery_tonCO2 = E_aux_solar_and_heat_recovery_W * lca.EL_TO_CO2 * WH_TO_J / 1E6


        results = pd.DataFrame({"DATE": date,
                                "E_total_req_W": total_electricity_demand_W,
                                "E_from_PV_W": E_from_PV_W,
                                "E_from_PVT_W": E_from_PVT_W,
                                "E_PV_directload_W": E_PV_directload_W,
                                "E_PV_grid_W": E_PV_grid_W,
                                "E_PVT_directload_W": E_PVT_directload_W,
                                "E_PVT_grid_W": E_PVT_grid_W,
                                "E_GRID_directload_W": E_GRID_directload_W,
                                "E_appliances_total_W": E_appliances_total_W,
                                "E_data_center_total_W": E_data_center_total_W,
                                "E_industrial_processes_total_W": E_industrial_processes_total_W,
                                "E_auxiliary_units_total_W": E_auxiliary_units_total_W,
                                "E_hotwater_total_W": E_hotwater_total_W,
                                "E_space_heating_total_W": E_space_heating_total_W,
                                "E_space_cooling_total_W": E_space_cooling_total_W,
                                "E_total_to_grid_W_negative": - E_PV_grid_W - E_PVT_grid_W,
                                "PEN_from_heat_used_SC_and_PVT_MJoil": PEN_from_heat_used_SC_and_PVT_MJoil,
                                "PEN_saved_from_electricity_sold_Solar_MJoil": PEN_saved_from_electricity_sold_Solar_MJoil,
                                "PEN_HPSolarandHeatRecovery_MJoil": PEN_HPSolarandHeatRecovery_MJoil,
                                "GHG_from_heat_used_SC_and_PVT_tonCO2": GHG_from_heat_used_SC_and_PVT_tonCO2,
                                "GHG_saved_from_electricity_sold_Solar_tonCO2": GHG_saved_from_electricity_sold_Solar_tonCO2,
                                "GHG_HPSolarandHeatRecovery_tonCO2": GHG_HPSolarandHeatRecovery_tonCO2
                                }) #let's keep this negative so it is something exported, we can use it in the graphs of likelihood

        results.to_csv(
            locator.get_optimization_slave_electricity_activation_pattern_heating(master_to_slave_vars.individual_number, master_to_slave_vars.generation_number), index=False)

        GHG_electricity_tonCO2 += np.sum(GHG_from_heat_used_SC_and_PVT_tonCO2) + np.sum(GHG_saved_from_electricity_sold_Solar_tonCO2) + np.sum(
            GHG_HPSolarandHeatRecovery_tonCO2)

        PEN_electricity_MJoil += np.sum(PEN_from_heat_used_SC_and_PVT_MJoil) + np.sum(PEN_saved_from_electricity_sold_Solar_MJoil) + np.sum(
            PEN_HPSolarandHeatRecovery_MJoil)

        for hour in range(len(total_electricity_demand_W)):
            costs_electricity_USD += total_electricity_demand_W[hour] * lca.ELEC_PRICE[hour] - (E_from_PV_W[hour] + E_from_PVT_W[hour]) * lca.ELEC_PRICE[hour]

    # if all buildings are decentralized cooling case
    if master_to_slave_vars.DCN_barcode.count("1") == 0:

        E_from_PV_W = E_PV_gen_W
        E_from_PVT_W = E_PVT_gen_W

        E_PV_directload_W = np.zeros(8760)
        E_PV_grid_W = np.zeros(8760)
        E_PVT_directload_W = np.zeros(8760)
        E_PVT_grid_W = np.zeros(8760)

        E_GRID_directload_W = np.zeros(8760)

        for hour in range(8760):
            E_hour_W = total_electricity_demand_W[hour]
            if E_hour_W > 0:
                if E_from_PV_W[hour] > E_hour_W:
                    E_PV_directload_W[hour] = E_hour_W
                    E_PV_grid_W[hour] = E_from_PV_W[hour] - total_electricity_demand_W[hour]
                    E_hour_W = 0
                else:
                    E_hour_W = E_hour_W - E_from_PV_W[hour]
                    E_PV_directload_W[hour] = E_from_PV_W[hour]

                if E_from_PVT_W[hour] > E_hour_W:
                    E_PVT_directload_W[hour] = E_hour_W
                    E_PVT_grid_W[hour] = E_from_PVT_W[hour] - total_electricity_demand_W[hour]
                    E_hour_W = 0
                else:
                    E_hour_W = E_hour_W - E_from_PVT_W[hour]
                    E_PVT_directload_W[hour] = E_from_PVT_W[hour]

                E_GRID_directload_W[hour] = E_hour_W

        PEN_from_heat_used_SC_and_PVT_MJoil = Q_SC_and_PVT_Wh * lca.SOLARCOLLECTORS_TO_OIL * WH_TO_J / 1.0E6
        PEN_saved_from_electricity_sold_Solar_MJoil = (np.add(E_PV_gen_W, E_PVT_gen_W)) * (lca.EL_PV_TO_OIL_EQ - lca.EL_TO_OIL_EQ) * WH_TO_J / 1.0E6
        PEN_HPSolarandHeatRecovery_MJoil = E_aux_solar_and_heat_recovery_W * lca.EL_TO_OIL_EQ * WH_TO_J / 1.0E6


        GHG_from_heat_used_SC_and_PVT_tonCO2 = Q_SC_and_PVT_Wh * lca.SOLARCOLLECTORS_TO_CO2 * WH_TO_J / 1.0E6
        GHG_saved_from_electricity_sold_Solar_tonCO2 = (np.add(E_PV_gen_W, E_PVT_gen_W)) * (lca.EL_PV_TO_CO2 - lca.EL_TO_CO2) * WH_TO_J / 1.0E6
        GHG_HPSolarandHeatRecovery_tonCO2 = E_aux_solar_and_heat_recovery_W * lca.EL_TO_CO2 * WH_TO_J / 1E6


        results = pd.DataFrame({"DATE": date,
                                "E_total_req_W": total_electricity_demand_W,
                                "E_from_PV_W": E_from_PV_W,
                                "E_from_PVT_W": E_from_PVT_W,
                                "E_PV_directload_W": E_PV_directload_W,
                                "E_PV_grid_W": E_PV_grid_W,
                                "E_PVT_directload_W": E_PVT_directload_W,
                                "E_PVT_grid_W": E_PVT_grid_W,
                                "E_GRID_directload_W": E_GRID_directload_W,
                                "E_appliances_total_W": E_appliances_total_W,
                                "E_data_center_total_W": E_data_center_total_W,
                                "E_industrial_processes_total_W": E_industrial_processes_total_W,
                                "E_auxiliary_units_total_W": E_auxiliary_units_total_W,
                                "E_hotwater_total_W": E_hotwater_total_W,
                                "E_space_heating_total_W": E_space_heating_total_W,
                                "E_space_cooling_total_W": E_space_cooling_total_W,
                                "E_total_to_grid_W_negative": - E_PV_grid_W - E_PVT_grid_W,
                                "PEN_from_heat_used_SC_and_PVT_MJoil": PEN_from_heat_used_SC_and_PVT_MJoil,
                                "PEN_saved_from_electricity_sold_Solar_MJoil": PEN_saved_from_electricity_sold_Solar_MJoil,
                                "PEN_HPSolarandHeatRecovery_MJoil": PEN_HPSolarandHeatRecovery_MJoil,
                                "GHG_from_heat_used_SC_and_PVT_tonCO2": GHG_from_heat_used_SC_and_PVT_tonCO2,
                                "GHG_saved_from_electricity_sold_Solar_tonCO2": GHG_saved_from_electricity_sold_Solar_tonCO2,
                                "GHG_HPSolarandHeatRecovery_tonCO2": GHG_HPSolarandHeatRecovery_tonCO2
                                }) #let's keep this negative so it is something exported, we can use it in the graphs of likelihood

        results.to_csv(
            locator.get_optimization_slave_electricity_activation_pattern_cooling(master_to_slave_vars.individual_number, master_to_slave_vars.generation_number), index=False)

        GHG_electricity_tonCO2 += np.sum(GHG_from_heat_used_SC_and_PVT_tonCO2) + np.sum(GHG_saved_from_electricity_sold_Solar_tonCO2) + np.sum(
            GHG_HPSolarandHeatRecovery_tonCO2)

        PEN_electricity_MJoil += np.sum(PEN_from_heat_used_SC_and_PVT_MJoil) + np.sum(PEN_saved_from_electricity_sold_Solar_MJoil) + np.sum(
            PEN_HPSolarandHeatRecovery_MJoil)

        for hour in range(len(total_electricity_demand_W)):
            costs_electricity_USD += total_electricity_demand_W[hour] * lca.ELEC_PRICE[hour] - (E_from_PV_W[hour] + E_from_PVT_W[hour]) * lca.ELEC_PRICE[hour]

    return costs_electricity_USD, GHG_electricity_tonCO2, PEN_electricity_MJoil

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    generation = 25
    individual = 10
    print("Calculating imports and exports of individual" + str(individual) + " of generation " + str(generation))

    electricity_calculations_of_all_buildings(generation, individual, locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())