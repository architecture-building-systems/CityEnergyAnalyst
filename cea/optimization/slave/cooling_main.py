"""
================
Lake-cooling network connected to chiller and cooling tower
================

Use free cooling from Lake as long as possible (Qmax Lake from gv and HP Lake operation from slave)
If Lake exhausted, use VCC + CT operation

"""
from __future__ import division
import numpy as np
import pandas as pd
import cea.config
import cea.technologies.cooling_tower as CTModel
import cea.technologies.chiller_vapor_compression as VCCModel
import cea.technologies.pumps as PumpModel
import cea.technologies.chiller_absorption as chiller_absorption
import cea.technologies.cogeneration as cogeneration
from cea.optimization.slave.cooling_resource_activation import cooling_resource_activator
from cea.technologies.thermal_network.thermal_network_matrix import calculate_ground_temperature
from cea.optimization.constants import EL_TO_CO2, EL_TO_OIL_EQ, Q_MARGIN_DISCONNECTED, PUMP_ETA, DELTA_U, \
    ACH_T_IN_FROM_CHP, ACH_TYPE_DOUBLE

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# technical model

def coolingMain(locator, master_to_slave_vars, ntwFeat, gv, prices):
    """
    Computes the parameters for the cooling of the complete DCN

    :param locator: path to res folder
    :param ntwFeat: network features
    :param gv: global variables
    :param prices: Prices imported from the database
    :type locator: string
    :type ntwFeat: class
    :type gv: class
    :type prices: class
    :return: costs, co2, prim
    :rtype: tuple
    """

    config = cea.config.Configuration() # FIXME: move out

    ############# Recover the cooling needs
    # Cooling demands in a neighborhood are divided into three categories currently. They are
    # 1. Space Cooling in buildings
    # 2. Data center Cooling
    # 3. Refrigeration Needs
    # Data center cooling can also be done by recovering the heat and heating other demands during the same time
    # whereas Space cooling and refrigeration needs are to be provided by District Cooling Network or decentralized cooling
    # Currently, all the buildings are assumed to be connected to DCN
    # In the following code, the cooling demands of Space cooling and refrigeration are first satisfied by using Lake and VCC
    # This is then followed by checking of the Heat recovery from Data Centre, if it is allowed, then the corresponding
    # cooling demand is ignored. If not, the corresponding coolind demand is also satisfied by DCN.

    # Space cooling previously aggregated in the substation routine
    df = pd.read_csv(locator.get_optimization_network_data_folder(master_to_slave_vars.network_data_file_cooling),
                     usecols=["T_DCNf_sup_K", "T_DCNf_re_K", "mdot_DC_netw_total_kgpers"])
    DCN_operation_parameters = np.nan_to_num(np.array(df))

    Qc_DCN_W = np.array(pd.read_csv(locator.get_optimization_network_data_folder(master_to_slave_vars.network_data_file_cooling),
                                    usecols=["Q_DCNf_W",
                                             "Qcdata_netw_total_kWh"]))  # importing the cooling demands of DCN (space cooling + refrigeration)
    # Data center cooling, (treated separately for each building)
    df = pd.read_csv(locator.get_total_demand(), usecols=["Name", "Qcdataf_MWhyr"])
    arrayData = np.array(df)

    # cooling requirements based on the Heat Recovery Flag
    Q_cooling_req_W = np.zeros(8760)
    if master_to_slave_vars.WasteServersHeatRecovery == 0:
        for hour in range(8760):
            Q_cooling_req_W[hour] = Qc_DCN_W[hour][0] + Qc_DCN_W[hour][1]
    else:
        for hour in range(8760):
            Q_cooling_req_W[hour] = Qc_DCN_W[hour][0]
    # FIXME[Q to BK]: how is this connected to the DCN_operation_parameters?

    ############# Recover the heat already taken from the Lake by the heat pumps
    try:
        dfSlave = pd.read_csv(
            locator.get_optimization_slave_heating_activation_pattern(master_to_slave_vars.individual_number,
                                                                      master_to_slave_vars.generation_number),
            usecols=["Q_coldsource_HPLake_W"])
        Q_Lake_Array_W = np.array(dfSlave)

    except:
        Q_Lake_Array_W = [0]

    Qc_available_from_lake_W = DELTA_U + np.sum(Q_Lake_Array_W)
    Qc_available_from_lake_W = 0

    ############# Output results
    costs = ntwFeat.pipesCosts_DCN
    CO2 = 0
    prim = 0

    nBuild = int(np.shape(arrayData)[0])
    nHour = int(np.shape(DCN_operation_parameters)[0])
    VCC_nom_W = 0

    calfactor_buildings = np.zeros(8760)
    TotalCool = 0
    Q_cooling_buildings_from_Lake_W = np.zeros(8760)
    Q_cooling_buildings_from_VCC_W = np.zeros(8760)
    Q_cooling_buildings_from_ACH_W = np.zeros(8760)
    CT_load_buildings_from_VCC_W = np.zeros(8760)

    opex_var_buildings_Lake = np.zeros(8760)
    opex_var_buildings_VCC = np.zeros(8760)
    opex_var_buildings_ACH = np.zeros(8760)
    co2_list_buildings_Lake = np.zeros(8760)
    co2_list_buildings_VCC = np.zeros(8760)
    co2_list_buildings_ACH = np.zeros(8760)
    prim_list_buildings_Lake = np.zeros(8760)
    prim_list_buildings_VCC = np.zeros(8760)
    prim_list_buildings_ACH = np.zeros(8760)
    calfactor_total = 0

    opex_var_data_center_Lake = np.zeros(8760)
    opex_var_data_center_VCC = np.zeros(8760)
    opex_var_data_center_ACH = np.zeros(8760)
    co2_list_data_center_Lake = np.zeros(8760)
    co2_list_data_center_VCC = np.zeros(8760)
    co2_list_data_center_ACH = np.zeros(8760)
    prim_list_data_center_Lake = np.zeros(8760)
    prim_list_data_center_VCC = np.zeros(8760)
    prim_list_data_center_ACH = np.zeros(8760)
    calfactor_data_center = np.zeros(8760)
    Q_cooling_data_center_from_Lake_W = np.zeros(8760)
    Q_cooling_data_center_from_VCC_W = np.zeros(8760)
    Q_cooling_data_center_from_ACH_W = np.zeros(8760)

    VCC_nom_Ini_W = 0
    Qc_from_lake_cumulative_W = 0

    # temporal variables
    Qc_peak_load_W = 0.7 * Q_cooling_req_W.max()  # FIXME: assumption
    Qc_tank_max_W = master_to_slave_vars.Storage_cooling_size * Q_cooling_req_W.max()
    Qc_tank_avail_W = Qc_tank_max_W
    Qc_tank_discharged_W = 0.1 * Qc_tank_max_W  # FIXME: assumption
    Qc_tank_charged_W = 0.1 * Qc_tank_max_W  # FIXME: assumption
    Qc_VCC_max_W = master_to_slave_vars.VCC_cooling_size * Q_cooling_req_W.max()
    Qc_ACH_max_W = master_to_slave_vars.Absorption_chiller_size * Q_cooling_req_W.max()
    limits = {'Qc_peak_load_W': Qc_peak_load_W,
              'Qc_tank_discharged_W': Qc_tank_discharged_W, 'Qc_tank_charged_W': Qc_tank_charged_W,
              'Qc_VCC_max_W': Qc_VCC_max_W, 'Qc_ACH_max_W': Qc_ACH_max_W, 'Qc_tank_max_W': Qc_tank_max_W}
    cooling_resource_potentials = {'Qc_tank_avail_W': Qc_tank_avail_W, 'Qc_avail_from_lake_W': Qc_available_from_lake_W,
                                   'Qc_from_lake_cumulative_W': Qc_from_lake_cumulative_W}

    T_ground_K = calculate_ground_temperature(locator)

    for hour in range(nHour):
        opex, co2, primary_energy, \
        Qc_supply_to_DCN, calfactor_output, \
        Qc_CT_W, Qh_CHP_ACH_W, \
        cooling_resource_potentials = cooling_resource_activator(DCN_operation_parameters[hour],
                                                                 limits, cooling_resource_potentials,
                                                                 T_ground_K[hour], prices, master_to_slave_vars)

        Qc_from_lake_cumulative_W = Qc_from_lake_cumulative_W + Qc_supply_to_DCN[
            'Qc_from_Lake_W']  # update lake cooling potential
        # save results for each time-step
        opex_var_buildings_Lake[hour] = opex['Opex_var_Lake']
        opex_var_buildings_VCC[hour] = opex['Opex_var_VCC']
        opex_var_buildings_ACH[hour] = opex['Opex_var_ACH']
        co2_list_buildings_Lake[hour] = co2['CO2_Lake']
        co2_list_buildings_VCC[hour] = co2['CO2_VCC']
        co2_list_buildings_ACH[hour] = co2['CO2_ACH']
        prim_list_buildings_Lake[hour] = primary_energy['Primary_Energy_Lake']
        prim_list_buildings_VCC[hour] = primary_energy['Primary_Energy_VCC']
        prim_list_buildings_ACH[hour] = primary_energy['Primary_Energy_ACH']
        calfactor_buildings[hour] = calfactor_output
        Q_cooling_buildings_from_Lake_W[hour] = Qc_supply_to_DCN['Qc_from_Lake_W']
        Q_cooling_buildings_from_VCC_W[hour] = Qc_supply_to_DCN['Qc_from_VCC_W']
        Q_cooling_buildings_from_ACH_W[hour] = Qc_supply_to_DCN['Qc_from_ACH_W']
        CT_load_buildings_from_VCC_W[hour] = Qc_CT_W

    costs += np.sum(opex_var_buildings_Lake) + np.sum(opex_var_buildings_VCC)
    CO2 += np.sum(co2_list_buildings_Lake) + np.sum(co2_list_buildings_Lake)
    prim += np.sum(prim_list_buildings_Lake) + np.sum(prim_list_buildings_VCC)
    calfactor_total += np.sum(calfactor_buildings)
    TotalCool += np.sum(Q_cooling_buildings_from_Lake_W) + np.sum(Q_cooling_buildings_from_VCC_W)
    VCC_nom_Ini_W = np.amax(Q_cooling_buildings_from_VCC_W) * (1 + Q_MARGIN_DISCONNECTED)
    VCC_nom_W = max(VCC_nom_W, VCC_nom_Ini_W)

    mdot_Max_kgpers = np.amax(DCN_operation_parameters[:, 1])
    Capex_pump, Opex_fixed_pump = PumpModel.calc_Cinv_pump(2 * ntwFeat.DeltaP_DCN, mdot_Max_kgpers, PUMP_ETA, gv,
                                                           locator)
    costs += (Capex_pump + Opex_fixed_pump)
    CT_load_data_center_from_VCC_W = np.zeros(8760)
    if master_to_slave_vars.WasteServersHeatRecovery == 0:
        for i in range(nBuild):
            if arrayData[i][1] > 0:
                buildName = arrayData[i][0]
                print buildName
                df = pd.read_csv(locator.get_demand_results_file(buildName),
                                 usecols=["Tcdataf_sup_C", "Tcdataf_re_C", "mcpdataf_kWperC"])
                cooling_data_center = np.array(df)

                mdot_max_Data_kWperC = abs(np.amax(cooling_data_center[:, -1]) / gv.cp * 1E3)
                Capex_pump, Opex_fixed_pump = PumpModel.calc_Cinv_pump(2 * ntwFeat.DeltaP_DCN, mdot_max_Data_kWperC,
                                                                       PUMP_ETA, gv, locator)
                costs += (Capex_pump + Opex_fixed_pump)
                for hour in range(8760):
                    opex, co2, primary_energy, Qc_supply_to_DCN, calfactor_output, Qc_CT_W = cooling_resource_activator(
                        cooling_data_center, Qc_available_from_lake_W, Qc_from_lake_cumulative_W, prices)

                    Qc_from_lake_cumulative_W = Qc_from_lake_cumulative_W + Qc_supply_to_DCN['Q_from_Lake_W']
                    opex_var_data_center_Lake[hour] = opex['Opex_var_Lake']
                    opex_var_data_center_VCC[hour] = opex['Opex_var_VCC']
                    opex_var_data_center_ACH[hour] = opex['Opex_var_ACH']
                    co2_list_data_center_Lake[hour] = co2['CO2_Lake']
                    co2_list_data_center_VCC[hour] = co2['CO2_VCC']
                    co2_list_data_center_ACH[hour] = co2['CO2_ACH']
                    prim_list_data_center_Lake[hour] = primary_energy['Primary_Energy_Lake']
                    prim_list_data_center_VCC[hour] = primary_energy['Primary_Energy_VCC']
                    prim_list_data_center_ACH[hour] = primary_energy['Primary_Energy_ACH']
                    calfactor_data_center[hour] = calfactor_output
                    Q_cooling_data_center_from_Lake_W[hour] = Qc_supply_to_DCN['Q_from_Lake_W']
                    Q_cooling_data_center_from_VCC_W[hour] = Qc_supply_to_DCN['Q_from_VCC_W']
                    Q_cooling_data_center_from_ACH_W[hour] = Qc_supply_to_DCN['Q_from_ACH_W']

                    CT_load_data_center_from_VCC_W[hour] = Qc_CT_W

                costs += np.sum(opex_var_data_center_Lake) + np.sum(opex_var_data_center_VCC)
                CO2 += np.sum(co2_list_data_center_Lake) + np.sum(co2_list_data_center_VCC)
                prim += np.sum(prim_list_data_center_Lake) + np.sum(co2_list_data_center_VCC)
                calfactor_total += np.sum(calfactor_data_center)
                TotalCool += np.sum(Q_cooling_data_center_from_Lake_W) + np.sum(Q_cooling_data_center_from_VCC_W)
                VCC_nom_Ini_W = np.amax(Q_cooling_data_center_from_VCC_W) * (1 + Q_MARGIN_DISCONNECTED)
                VCC_nom_W = max(VCC_nom_W, VCC_nom_Ini_W)

    ########## Operation of the cooling tower
    CT_max_from_VCC = np.amax(CT_load_buildings_from_VCC_W)
    CT_max_from_data_center = np.amax(CT_load_data_center_from_VCC_W)
    CT_nom_W = max(CT_max_from_VCC, CT_max_from_data_center)
    if CT_nom_W > 0:
        for i in range(nHour):
            wdot = CTModel.calc_CT(CT_load_buildings_from_VCC_W[i], CT_nom_W)
            costs += wdot * prices.ELEC_PRICE
            CO2 += wdot * EL_TO_CO2 * 3600E-6
            prim += wdot * EL_TO_OIL_EQ * 3600E-6

    ########## Operation of the CCGT #FIXME: could be combined with CT?
    CCGT_SIZE = 10000  # W # FIXME: CCGT size is based on ACH size, and we need to do some conversion from heating power to el power
    GT_fuel_type = 'NG'  # FIXME: also has to come from optimization, but realisticallly, should be NG in Singapore
    if Qh_CHP_ACH_W > 0:
        # get CCGT performance limits and functions
        CCGT_performances = cogeneration.calc_cop_CCGT(CCGT_SIZE, ACH_T_IN_FROM_CHP, GT_fuel_type, prices)
        # unpack
        Q_used_prim_W_CCGT_fn = CCGT_performances['q_input_fn_q_output_W']
        cost_per_Wh_th_CCGT_fn = CCGT_performances[
            'fuel_cost_per_Wh_th_fn_q_output_W']  # gets interpolated cost function
        Qh_output_CCGT_min_W = CCGT_performances['q_output_min_W']
        Qh_output_CCGT_max_W = CCGT_performances['q_output_max_W']
        eta_elec_interpol = CCGT_performances['eta_el_fn_q_input']

        for i in range(nHour):
            if Qh_CHP_ACH_W > Qh_output_CCGT_min_W:  # operation Possible if above minimal load
                if Qh_CHP_ACH_W < Qh_output_CCGT_max_W:  # Normal operation Possible within partload regime
                    cost_per_Wh_th = cost_per_Wh_th_CCGT_fn(Qh_CHP_ACH_W)
                    Q_used_prim_CCGT_W = Q_used_prim_W_CCGT_fn(Qh_CHP_ACH_W)
                    Qh_from_CCGT_W = Qh_CHP_ACH_W.copy()
                    Qh_CHP_ACH_W = 0
                    E_CHP_gen_W = np.float(eta_elec_interpol(Q_used_prim_CCGT_W)) * Q_used_prim_CCGT_W

                else:  # Only part of the demand can be delivered as 100% load achieved
                    cost_per_Wh_th = cost_per_Wh_th_CCGT_fn(Qh_output_CCGT_max_W)
                    Q_used_prim_CCGT_W = Q_used_prim_W_CCGT_fn(Qh_output_CCGT_max_W)
                    Qh_from_CCGT_W = Qh_output_CCGT_max_W
                    Qh_CHP_ACH_W -= Qh_output_CCGT_max_W  # FIXME: activate more than one CHP again?
                    E_CHP_gen_W = np.float(eta_elec_interpol(Qh_output_CCGT_max_W)) * Q_used_prim_CCGT_W

            opex_CCGT = cost_per_Wh_th * Qh_from_CCGT_W
            # FIXME: not sure how the following part are connected to the rest here...
            source_CHP = 1
            cost_CHP = opex_CCGT
            Q_CHP_gen_W = Qh_from_CCGT_W
            E_gas_CHP_W = Q_used_prim_CCGT_W

    ########## Add investment costs # FIXME: still need to add ACH / CCGT / Tank
    Capex_a_VCC, Opex_fixed_VCC = VCCModel.calc_Cinv_VCC(VCC_nom_W, gv, locator)
    costs += (Capex_a_VCC + Opex_fixed_VCC)

    Capex_a_ACH, Opex_ACH = chiller_absorption.calc_Cinv(limits['Qc_ACH_max_W'], locator, ACH_TYPE_DOUBLE, config)
    costs += (Capex_a_ACH + Opex_ACH)

    Capex_a_CT, Opex_fixed_CT = CTModel.calc_Cinv_CT(CT_nom_W, gv, locator)
    costs += (Capex_a_CT + Opex_fixed_CT)



    dfSlave1 = pd.read_csv(
        locator.get_optimization_slave_heating_activation_pattern(master_to_slave_vars.individual_number,
                                                                  master_to_slave_vars.generation_number))
    date = dfSlave1.DATE.values

    Opex_var_Lake = np.add(opex_var_buildings_Lake, opex_var_data_center_Lake)
    Opex_var_VCC = np.add(opex_var_buildings_VCC, opex_var_data_center_VCC)
    Opex_var_ACH = np.add(opex_var_buildings_ACH, opex_var_data_center_ACH)
    CO2_from_using_Lake = np.add(co2_list_buildings_Lake, co2_list_data_center_Lake)
    CO2_from_using_VCC = np.add(co2_list_buildings_VCC, co2_list_data_center_VCC)
    CO2_from_using_ACH = np.add(co2_list_buildings_ACH, co2_list_data_center_ACH)
    Primary_Energy_from_Lake = np.add(prim_list_buildings_Lake, prim_list_data_center_Lake)
    Primary_Energy_from_VCC = np.add(prim_list_buildings_VCC, prim_list_data_center_VCC)
    Primary_Energy_from_ACH = np.add(prim_list_buildings_ACH, prim_list_data_center_ACH)
    Q_from_Lake_W = np.add(Q_cooling_buildings_from_Lake_W, Q_cooling_data_center_from_Lake_W)
    Q_from_VCC_W = np.add(Q_cooling_buildings_from_VCC_W, Q_cooling_data_center_from_VCC_W)
    Q_from_ACH_W = np.add(Q_cooling_buildings_from_ACH_W, Q_cooling_data_center_from_ACH_W)
    CT_Load_associated_with_VCC_W = np.add(CT_load_buildings_from_VCC_W, CT_load_data_center_from_VCC_W)

    results = pd.DataFrame({"DATE": date,
                            "Q_total_cooling_W": Q_cooling_req_W,
                            "Opex_var_Lake": Opex_var_Lake[0],
                            "Opex_var_VCC": Opex_var_VCC[0],
                            "Opex_var_ACH": Opex_var_ACH,
                            "CO2_from_using_Lake": CO2_from_using_Lake[0],
                            "CO2_from_using_VCC": CO2_from_using_VCC[0],
                            "CO2_from_using_ACH": CO2_from_using_ACH[0],
                            "Primary_Energy_from_Lake": Primary_Energy_from_Lake[0],
                            "Primary_Energy_from_VCC": Primary_Energy_from_VCC[0],
                            "Primary_Energy_from_ACH": Primary_Energy_from_ACH[0],
                            "Q_from_Lake_W": Q_from_Lake_W[0],
                            "Q_from_VCC_W": Q_from_VCC_W[0],
                            "Q_from_ACH_W": Q_from_ACH_W[0],
                            "CT_Load_associated_with_VCC_W": CT_Load_associated_with_VCC_W
                            })

    results.to_csv(locator.get_optimization_slave_cooling_activation_pattern(master_to_slave_vars.individual_number,
                                                                             master_to_slave_vars.generation_number),
                   index=False)

    ########### Adjust and add the pumps for filtering and pre-treatment of the water
    calibration = calfactor_total / 50976000

    extraElec = (127865400 + 85243600) * calibration
    costs += extraElec * prices.ELEC_PRICE
    CO2 += extraElec * EL_TO_CO2 * 3600E-6
    prim += extraElec * EL_TO_OIL_EQ * 3600E-6

    return (costs, CO2, prim)
