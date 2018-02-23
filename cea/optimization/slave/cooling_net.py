"""
================
Lake-cooling network connected to chiller and cooling tower
================

Use free cooling from lake as long as possible (Qmax lake from gv and HP Lake operation from slave)
If lake exhausted, use VCC + CT operation

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

def coolingMain(locator, configKey, ntwFeat, HRdata, gv, prices):
    """
    Computes the parameters for the cooling of the complete DCN

    :param locator: path to res folder
    :param configKey: configuration key for the District Heating Network (DHN)
    :param ntwFeat: network features
    :param HRdata: Heat recovery data, 0 if no heat recovery data, 1 if so
    :param gv: global variables
    :type locator: string
    :type configKey: string
    :type ntwFeat: class
    :type HRdata: int
    :type gv: class
    :return: costs, co2, prim
    :rtype: tuple
    """

    ############# Recover the cooling needs

    # Space cooling previously aggregated in the substation routine
    df = pd.read_csv(locator.get_optimization_network_all_results_summary(key='all'),
                     usecols=["T_DCNf_re_K", "mdot_cool_netw_total_kgpers"])
    coolArray = np.nan_to_num(np.array(df))
    T_sup_Cool_K = TsupCool

    # Data center cooling, (treated separately for each building)
    df = pd.read_csv(locator.get_total_demand(), usecols=["Name", "Qcdataf_MWhyr"])
    arrayData = np.array(df)

    # Ice hockey rings, (treated separately for each building)
    df = pd.read_csv(locator.get_total_demand(), usecols=["Name", "Qcref_MWhyr"])
    arrayQice = np.array(df)

    ############# Recover the heat already taken from the lake by the heat pumps
    try:
        dfSlave = pd.read_csv(locator.get_optimization_slave_pp_activation_pattern(configKey), usecols=["Q_coldsource_HPLake_W"])
        Q_lake_Array_W = np.array(dfSlave)
        Q_lake_W = np.sum(Q_lake_Array_W)

    except:
        Q_lake_W = 0

    Q_avail_W = DeltaU + Q_lake_W

    ############# Output results
    costs = ntwFeat.pipesCosts_DCN
    CO2 = 0
    prim = 0

    nBuild = int(np.shape(arrayData)[0])
    nHour = int(np.shape(coolArray)[0])
    CT_Load_W = np.zeros(nHour)
    VCC_nom_W = 0

    calFactor = 0
    TotalCool = 0

    ############ Function for cooling operation


    ########## Cooling operation with Circulating pump and VCC

    opex_total, co2_total, prim_total, calfactor_total, Q_cooling_total, Q_availCopy_W, VCC_nom_Ini_W = coolOperation(coolArray, nHour, Q_avail_W,
                                                                                            TempSup=T_sup_Cool_K)
    costs += opex_total
    CO2 += co2_total
    prim += prim_total
    calFactor += calfactor_total
    TotalCool += Q_cooling_total
    VCC_nom_W = max(VCC_nom_W, VCC_nom_Ini_W)
    Q_avail_W = Q_availCopy_W

    mdot_Max_kgpers = np.amax(coolArray[:, 1])
    Capex_pump, Opex_fixed_pump = PumpModel.calc_Cinv_pump(2 * ntwFeat.DeltaP_DCN, mdot_Max_kgpers, etaPump, gv, locator)
    costs += (Capex_pump + Opex_fixed_pump)
    if HRdata == 0:
        for i in range(nBuild):
            if arrayData[i][1] > 0:
                buildName = arrayData[i][0]
                print buildName
                df = pd.read_csv(locator.get_demand_results_file(buildName),
                                 usecols=["Tcdataf_sup_C", "Tcdataf_re_C", "mcpdataf_kWperC"])
                arrayBuild = np.array(df)

                mdot_max_Data_kWperC = abs(np.amax(arrayBuild[:, -1]) / gv.cp * 1E3)
                Capex_pump, Opex_fixed_pump = PumpModel.calc_Cinv_pump(2 * ntwFeat.DeltaP_DCN, mdot_max_Data_kWperC, etaPump, gv, locator)
                costs += (Capex_pump + Opex_fixed_pump)
                opex_total, co2_total, prim_total, calfactor_total, Q_cooling_total, Q_availCopy_W, VCC_nom_Ini_W = coolOperation(arrayBuild,
                                                                                                        nHour, Q_avail_W)
                costs += opex_total
                CO2 += co2_total
                prim += prim_total
                calFactor += calfactor_total
                TotalCool += Q_cooling_total
                VCC_nom_W = max(VCC_nom_W, VCC_nom_Ini_W)
                Q_avail_W = Q_availCopy_W

    for i in range(nBuild):
        if arrayQice[i][1] > 0:
            buildName = arrayQice[i][0]
            print buildName
            df = pd.read_csv(locator.pathRaw + "/" + buildName + ".csv", usecols=["Tsref_C", "Trref_C", "mcpref_kWperC"])
            arrayBuild = np.array(df)

            mdot_max_ice_kgpers = abs(np.amax(arrayBuild[:, -1]) / gv.cp * 1E3)
            Capex_pump, Opex_fixed_pump = PumpModel.calc_Cinv_pump(2 * ntwFeat.DeltaP_DCN, mdot_max_ice_kgpers, etaPump, gv, locator)
            costs += (Capex_pump + Opex_fixed_pump)
            opex_total, co2_total, prim_total, calfactor_total, Q_cooling_total, Q_availCopy_W, VCC_nom_Ini_W = coolOperation(arrayBuild, nHour,
                                                                                                    Q_avail_W)
            costs += opex_total
            CO2 += co2_total
            prim += prim_total
            calFactor += calfactor_total
            TotalCool += Q_cooling_total
            VCC_nom_W = max(VCC_nom_W, VCC_nom_Ini_W)
            Q_avail_W = Q_availCopy_W


    ########## Operation of the cooling tower
    CT_nom_W = np.amax(CT_Load_W)
    costCopy = costs
    if CT_nom_W > 0:
        for i in range(nHour):
            wdot = CTModel.calc_CT(CT_Load_W[i], CT_nom_W, gv)

            costs += wdot * prices.ELEC_PRICE
            CO2 += wdot * EL_TO_CO2 * 3600E-6
            prim += wdot * EL_TO_OIL_EQ * 3600E-6



    ########## Add investment costs

    Capex_a_VCC, Opex_fixed_VCC = VCCModel.calc_Cinv_VCC(VCC_nom_W, gv, locator)
    costs += (Capex_a_VCC + Opex_fixed_VCC)
    Capex_a_CT, Opex_fixed_CT = CTModel.calc_Cinv_CT(CT_nom_W, gv, locator)
    costs += (Capex_a_CT + Opex_fixed_CT)


    ########### Adjust and add the pumps for filtering and pre-treatment of the water
    calibration = calFactor / 50976000

    extraElec = (127865400 + 85243600) * calibration
    costs += extraElec * prices.ELEC_PRICE
    CO2 += extraElec * EL_TO_CO2 * 3600E-6
    prim += extraElec * EL_TO_OIL_EQ * 3600E-6

    return (costs, CO2, prim)

