"""
================
Lake-cooling network connected to chiller and cooling tower
================

Use free cooling from Lake as long as possible (Qmax Lake from gv and HP Lake operation from slave)
If Lake exhausted, use VCC + CT operation

"""
from __future__ import division

import os

import numpy as np
import pandas as pd
from cea.optimization.constants import *
import cea.technologies.cooling_tower as CTModel
import cea.technologies.chillers as VCCModel
import cea.technologies.pumps as PumpModel
from cea.optimization.slave.cooling_resource_activation import cooling_resource_activator

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# technical model

def coolingMain(locator, configKey, ntwFeat, heat_recovery_data_center, gv, prices):
    """
    Computes the parameters for the cooling of the complete DCN

    :param locator: path to res folder
    :param configKey: configuration key for the District Heating Network (DHN)
    :param ntwFeat: network features
    :param heat_recovery_data_center: Heat recovery data, 0 if no heat recovery data, 1 if so
    :param gv: global variables
    :type locator: string
    :type configKey: string
    :type ntwFeat: class
    :type heat_recovery_data_center: int
    :type gv: class
    :return: costs, co2, prim
    :rtype: tuple
    """

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
    df = pd.read_csv(locator.get_optimization_network_all_results_summary(key='all'),
                     usecols=["T_DCNf_sup_K","T_DCNf_re_K", "mdot_cool_netw_total_kgpers"])
    DCN_cooling = np.nan_to_num(np.array(df))

    Q_cooling_W = np.array(pd.read_csv(locator.get_optimization_network_all_results_summary(key='all'),
                     usecols=["Q_DCNf_W", "Qcdata_netw_total_kWh"])) # importing the cooling demands of DCN (space cooling + refrigeration)
    # Data center cooling, (treated separately for each building)
    df = pd.read_csv(locator.get_total_demand(), usecols=["Name", "Qcdataf_MWhyr"])
    arrayData = np.array(df)

    # cooling requirements based on the Heat Recovery Flag
    Q_cooling_req_W = np.zeros(8760)
    if heat_recovery_data_center == 0:
        for hour in range(8760):
            Q_cooling_req_W[hour] = Q_cooling_W[hour][0] + Q_cooling_W[hour][1]
    else:
        for hour in range(8760):
            Q_cooling_req_W[hour] = Q_cooling_W[hour][0]


    ############# Recover the heat already taken from the Lake by the heat pumps
    try:
        dfSlave = pd.read_csv(locator.get_optimization_slave_heating_activation_pattern(configKey), usecols=["Q_coldsource_HPLake_W"])
        Q_Lake_Array_W = np.array(dfSlave)

    except:
        Q_Lake_Array_W = [0]

    Q_avail_W = DeltaU + np.sum(Q_Lake_Array_W)

    ############# Output results
    costs = ntwFeat.pipesCosts_DCN
    CO2 = 0
    prim = 0

    nBuild = int(np.shape(arrayData)[0])
    nHour = int(np.shape(DCN_cooling)[0])
    VCC_nom_W = 0

    calfactor_buildings = np.zeros(8760)
    TotalCool = 0
    Q_cooling_buildings_from_Lake_W = np.zeros(8760)
    Q_cooling_buildings_from_VCC_W = np.zeros(8760)
    CT_load_buildings_from_VCC_W = np.zeros(8760)
    
    opex_var_buildings_Lake = np.zeros(8760)
    opex_var_buildings_VCC = np.zeros(8760)
    co2_list_buildings_Lake = np.zeros(8760)
    co2_list_buildings_VCC = np.zeros(8760)
    prim_list_buildings_Lake = np.zeros(8760)
    prim_list_buildings_VCC = np.zeros(8760)
    calfactor_total = 0

    opex_var_data_center_Lake = np.zeros(8760)
    opex_var_data_center_VCC = np.zeros(8760)
    co2_list_data_center_Lake = np.zeros(8760)
    co2_list_data_center_VCC = np.zeros(8760)
    prim_list_data_center_Lake = np.zeros(8760)
    prim_list_data_center_VCC = np.zeros(8760)
    calfactor_data_center = np.zeros(8760)
    Q_cooling_data_center_from_Lake_W = np.zeros(8760)
    Q_cooling_data_center_from_VCC_W = np.zeros(8760)

    VCC_nom_Ini_W = 0
    Q_from_Lake_cumulative_W = 0


    for hour in range(8760):
        opex_output, co2_output, prim_output, Q_output, calfactor_output, CT_Load_W = cooling_resource_activator(
            DCN_cooling, hour, Q_avail_W, gv, Q_from_Lake_cumulative_W, prices)

        Q_from_Lake_cumulative_W = Q_from_Lake_cumulative_W + Q_output['Q_from_Lake_W']
        opex_var_buildings_Lake[hour] = opex_output['Opex_var_Lake']
        opex_var_buildings_VCC[hour] = opex_output['Opex_var_VCC']
        co2_list_buildings_Lake[hour] = co2_output['CO2_Lake']
        co2_list_buildings_VCC[hour] = co2_output['CO2_VCC']
        prim_list_buildings_Lake[hour] = prim_output['Primary_Energy_Lake']
        prim_list_buildings_VCC[hour] = prim_output['Primary_Energy_VCC']
        calfactor_buildings[hour] = calfactor_output
        Q_cooling_buildings_from_Lake_W[hour] = Q_output['Q_from_Lake_W']
        Q_cooling_buildings_from_VCC_W[hour] = Q_output['Q_from_VCC_W']
        CT_load_buildings_from_VCC_W[hour] = CT_Load_W

    costs += np.sum(opex_var_buildings_Lake) + np.sum(opex_var_buildings_VCC)
    CO2 += np.sum(co2_list_buildings_Lake) + np.sum(co2_list_buildings_Lake)
    prim += np.sum(prim_list_buildings_Lake) + np.sum(prim_list_buildings_VCC)
    calfactor_total += np.sum(calfactor_buildings)
    TotalCool += np.sum(Q_cooling_buildings_from_Lake_W) + np.sum(Q_cooling_buildings_from_VCC_W)
    VCC_nom_Ini_W = np.amax(Q_cooling_buildings_from_VCC_W) * (1 + Qmargin_Disc)
    VCC_nom_W = max(VCC_nom_W, VCC_nom_Ini_W)

    mdot_Max_kgpers = np.amax(DCN_cooling[:, 1])
    Capex_pump, Opex_fixed_pump = PumpModel.calc_Cinv_pump(2 * ntwFeat.DeltaP_DCN, mdot_Max_kgpers, etaPump, gv, locator)
    costs += (Capex_pump + Opex_fixed_pump)
    CT_load_data_center_from_VCC_W = np.zeros(8760)
    if heat_recovery_data_center == 0:
        for i in range(nBuild):
            if arrayData[i][1] > 0:
                buildName = arrayData[i][0]
                print buildName
                df = pd.read_csv(locator.get_demand_results_file(buildName),
                                 usecols=["Tcdataf_sup_C", "Tcdataf_re_C", "mcpdataf_kWperC"])
                cooling_data_center = np.array(df)

                mdot_max_Data_kWperC = abs(np.amax(cooling_data_center[:, -1]) / gv.cp * 1E3)
                Capex_pump, Opex_fixed_pump = PumpModel.calc_Cinv_pump(2 * ntwFeat.DeltaP_DCN, mdot_max_Data_kWperC, etaPump, gv, locator)
                costs += (Capex_pump + Opex_fixed_pump)
                for hour in range(8760):
                    opex_output, co2_output, prim_output, Q_output, calfactor_output, CT_Load_W = cooling_resource_activator(
                        cooling_data_center, hour, Q_avail_W, gv, Q_from_Lake_cumulative_W, prices)

                    Q_from_Lake_cumulative_W = Q_from_Lake_cumulative_W + Q_output['Q_from_Lake_W']
                    opex_var_data_center_Lake[hour] = opex_output['Opex_var_Lake']
                    opex_var_data_center_VCC[hour] = opex_output['Opex_var_VCC']
                    co2_list_data_center_Lake[hour] = co2_output['CO2_Lake']
                    co2_list_data_center_VCC[hour] = co2_output['CO2_VCC']
                    prim_list_data_center_Lake[hour] = prim_output['Primary_Energy_Lake']
                    prim_list_data_center_VCC[hour] = prim_output['Primary_Energy_VCC']
                    calfactor_data_center[hour] = calfactor_output
                    Q_cooling_data_center_from_Lake_W[hour] = Q_output['Q_from_Lake_W']
                    Q_cooling_data_center_from_VCC_W[hour] = Q_output['Q_from_VCC_W']
                    CT_load_data_center_from_VCC_W[hour] = CT_Load_W

                costs += np.sum(opex_var_data_center_Lake) + np.sum(opex_var_data_center_VCC)
                CO2 += np.sum(co2_list_data_center_Lake) + np.sum(co2_list_data_center_VCC)
                prim += np.sum(prim_list_data_center_Lake) + np.sum(co2_list_data_center_VCC)
                calfactor_total += np.sum(calfactor_data_center)
                TotalCool += np.sum(Q_cooling_data_center_from_Lake_W) + np.sum(Q_cooling_data_center_from_VCC_W)
                VCC_nom_Ini_W = np.amax(Q_cooling_data_center_from_VCC_W) * (1 + Qmargin_Disc)
                VCC_nom_W = max(VCC_nom_W, VCC_nom_Ini_W)

    ########## Operation of the cooling tower
    CT_max_from_VCC = np.amax(CT_load_buildings_from_VCC_W)
    CT_max_from_data_center = np.amax(CT_load_data_center_from_VCC_W)
    CT_nom_W = max(CT_max_from_VCC, CT_max_from_data_center)
    if CT_nom_W > 0:
        for i in range(nHour):
            wdot = CTModel.calc_CT(CT_load_buildings_from_VCC_W[i], CT_nom_W, gv)
            costs += wdot * prices.ELEC_PRICE
            CO2 += wdot * EL_TO_CO2 * 3600E-6
            prim += wdot * EL_TO_OIL_EQ * 3600E-6

    ########## Add investment costs

    Capex_a_VCC, Opex_fixed_VCC = VCCModel.calc_Cinv_VCC(VCC_nom_W, gv, locator)
    costs += (Capex_a_VCC + Opex_fixed_VCC)
    Capex_a_CT, Opex_fixed_CT = CTModel.calc_Cinv_CT(CT_nom_W, gv, locator)
    costs += (Capex_a_CT + Opex_fixed_CT)

    dfSlave1 = pd.read_csv(locator.get_optimization_slave_heating_activation_pattern(configKey))
    date = dfSlave1.DATE.values

    Opex_var_Lake = np.add(opex_var_buildings_Lake, opex_var_data_center_Lake),
    Opex_var_VCC =  np.add(opex_var_buildings_VCC, opex_var_data_center_VCC),
    CO2_from_using_Lake =  np.add(co2_list_buildings_Lake, co2_list_data_center_Lake),
    CO2_from_using_VCC = np.add(co2_list_buildings_VCC, co2_list_data_center_VCC),
    Primary_Energy_from_Lake = np.add(prim_list_buildings_Lake, prim_list_data_center_Lake),
    Primary_Energy_from_VCC = np.add(prim_list_buildings_VCC, prim_list_data_center_VCC),
    Q_from_Lake_W = np.add(Q_cooling_buildings_from_Lake_W, Q_cooling_data_center_from_Lake_W),
    Q_from_VCC_W = np.add(Q_cooling_buildings_from_VCC_W, Q_cooling_data_center_from_VCC_W),
    CT_Load_associated_with_VCC_W =  np.add(CT_load_buildings_from_VCC_W, CT_load_data_center_from_VCC_W)

    results = pd.DataFrame({"DATE": date,
                            "Q_total_cooling_W": Q_cooling_req_W,
                            "Opex_var_Lake": Opex_var_Lake[0],
                            "Opex_var_VCC": Opex_var_VCC[0],
                            "CO2_from_using_Lake": CO2_from_using_Lake[0],
                            "CO2_from_using_VCC": CO2_from_using_VCC[0],
                            "Primary_Energy_from_Lake": Primary_Energy_from_Lake[0],
                            "Primary_Energy_from_VCC": Primary_Energy_from_VCC[0],
                            "Q_from_Lake_W": Q_from_Lake_W[0],
                            "Q_from_VCC_W": Q_from_VCC_W[0],
                            "CT_Load_associated_with_VCC_W": CT_Load_associated_with_VCC_W
                            })


    results.to_csv(locator.get_optimization_slave_cooling_activation_pattern(configKey), index=False)


    ########### Adjust and add the pumps for filtering and pre-treatment of the water
    calibration = calfactor_total / 50976000

    extraElec = (127865400 + 85243600) * calibration
    costs += extraElec * prices.ELEC_PRICE
    CO2 += extraElec * EL_TO_CO2 * 3600E-6
    prim += extraElec * EL_TO_OIL_EQ * 3600E-6

    return (costs, CO2, prim)

