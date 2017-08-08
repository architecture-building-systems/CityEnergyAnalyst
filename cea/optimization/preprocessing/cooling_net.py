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

import cea.technologies.cooling_tower as CTModel
import cea.technologies.chillers as VCCModel
import cea.technologies.pumps as PumpModel

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# technical model

def coolingMain(locator, configKey, ntwFeat, HRdata, gv):
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
    df = pd.read_csv(os.path.join(locator.get_optimization_network_results_folder(), "Network_summary_result_all.csv"),
                     usecols=["T_DCNf_re_K", "mdot_cool_netw_total_kgpers"])
    coolArray = np.nan_to_num(np.array(df))
    T_sup_Cool_K = gv.TsupCool

    # Data center cooling, (treated separately for each building)
    df = pd.read_csv(locator.get_total_demand(), usecols=["Name", "Qcdataf_MWhyr"])
    arrayData = np.array(df)

    # Ice hockey rings, (treated separately for each building)
    df = pd.read_csv(locator.get_total_demand(), usecols=["Name", "Qcref_MWhyr"])
    arrayQice = np.array(df)

    ############# Recover the heat already taken from the lake by the heat pumps
    try:
        os.chdir(locator.get_optimization_slave_results_folder())
        fNameSlaveRes = configKey + "PPActivationPattern.csv"

        dfSlave = pd.read_csv(fNameSlaveRes, usecols=["Qcold_HPLake_W"])

        Q_lake_Array_W = np.array(dfSlave)
        Q_lake_W = np.sum(Q_lake_Array_W)

    except:
        Q_lake_W = 0

    Q_avail_W = gv.DeltaU + Q_lake_W
    print Q_avail_W, "Qavail"

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
    def coolOperation(dataArray, el, Q_availIni_W, TempSup=0):
        """
        :param dataArray:
        :param el:
        :param Q_availIni_W:
        :param TempSup:
        :type dataArray: list
        :type el:
        :type Q_availIni_W: float?
        :type TempSup:
        :return: toCosts, toCO2, toPrim, toCalfactor, toTotalCool, QavailCopy, VCCnomIni
        :rtype: float, float, float, float, float, float, float
        """
        toTotalCool = 0
        toCalfactor = 0
        toCosts = 0
        toCO2 = 0
        toPrim = 0

        Q_availCopy_W = Q_availIni_W
        VCC_nom_Ini_W = 0

        for i in range(el):

            if TempSup > 0:
                T_sup_K = TempSup
                T_re_K = dataArray[i][-2]
                mdot_kgpers = abs(dataArray[i][-1])
            else:
                T_sup_K = dataArray[i][-3] + 273
                T_re_K = dataArray[i][-2] + 273
                mdot_kgpers = abs(dataArray[i][-1] * 1E3 / gv.cp)

            Q_need_W = abs(mdot_kgpers * gv.cp * (T_re_K - T_sup_K))
            toTotalCool += Q_need_W

            if Q_availCopy_W - Q_need_W >= 0:  # Free cooling possible from the lake
                Q_availCopy_W -= Q_need_W

                # Delta P from linearization after distribution optimization
                deltaP = 2 * (gv.DeltaP_Coeff * mdot_kgpers + gv.DeltaP_Origin)

                toCalfactor += deltaP * mdot_kgpers / 1000 / gv.etaPump
                toCosts += deltaP * mdot_kgpers / 1000 * gv.ELEC_PRICE / gv.etaPump
                toCO2 += deltaP * mdot_kgpers / 1000 * gv.EL_TO_CO2 / gv.etaPump * 0.0036
                toPrim += deltaP * mdot_kgpers / 1000 * gv.EL_TO_OIL_EQ / gv.etaPump * 0.0036

            else:
                print "Lake exhausted !"
                wdot_W, qhotdot_W = VCCModel.calc_VCC(mdot_kgpers, T_sup_K, T_re_K, gv)
                if Q_need_W > VCC_nom_Ini_W:
                    VCC_nom_Ini_W = Q_need_W * (1 + gv.Qmargin_Disc)

                toCosts += wdot_W * gv.ELEC_PRICE
                toCO2 += wdot_W * gv.EL_TO_CO2 * 3600E-6
                toPrim += wdot_W * gv.EL_TO_OIL_EQ * 3600E-6

                CT_Load_W[i] += qhotdot_W

        return toCosts, toCO2, toPrim, toCalfactor, toTotalCool, Q_availCopy_W, VCC_nom_Ini_W

    ########## Cooling operation with Circulating pump and VCC

    print "Space cooling operation"
    toCosts, toCO2, toPrim, toCalfactor, toTotalCool, Q_availCopy_W, VCC_nom_Ini_W = coolOperation(coolArray, nHour, Q_avail_W,
                                                                                            TempSup=T_sup_Cool_K)
    costs += toCosts
    CO2 += toCO2
    prim += toPrim
    calFactor += toCalfactor
    TotalCool += toTotalCool
    VCC_nom_W = max(VCC_nom_W, VCC_nom_Ini_W)
    Q_avail_W = Q_availCopy_W
    print Q_avail_W, "Qavail after space cooling"

    mdot_Max_kgpers = np.amax(coolArray[:, 1])
    costs += PumpModel.Pump_Cost(2 * ntwFeat.DeltaP_DCN, mdot_Max_kgpers, gv.etaPump, gv)

    if HRdata == 0:
        print "Data centers cooling operation"
        for i in range(nBuild):
            if arrayData[i][1] > 0:
                buildName = arrayData[i][0]
                print buildName
                df = pd.read_csv(locator.get_demand_results_file(buildName),
                                 usecols=["Tcdataf_sup_C", "Tcdataf_re_C", "mcpdataf_kWperC"])
                arrayBuild = np.array(df)

                mdot_max_Data_kWperC = abs(np.amax(arrayBuild[:, -1]) / gv.cp * 1E3)
                costs += PumpModel.Pump_Cost(2 * ntwFeat.DeltaP_DCN, mdot_max_Data_kWperC, gv.etaPump, gv)

                toCosts, toCO2, toPrim, toCalfactor, toTotalCool, Q_availCopy_W, VCC_nom_Ini_W = coolOperation(arrayBuild,
                                                                                                        nHour, Q_avail_W)
                costs += toCosts
                CO2 += toCO2
                prim += toPrim
                calFactor += toCalfactor
                TotalCool += toTotalCool
                VCC_nom_W = max(VCC_nom_W, VCC_nom_Ini_W)
                Q_avail_W = Q_availCopy_W
                print Q_avail_W, "Qavail after data center"

    print "refrigeration cooling operation"
    for i in range(nBuild):
        if arrayQice[i][1] > 0:
            buildName = arrayQice[i][0]
            print buildName
            df = pd.read_csv(locator.pathRaw + "/" + buildName + ".csv", usecols=["Tsref_C", "Trref_C", "mcpref_kWperC"])
            arrayBuild = np.array(df)

            mdot_max_ice_kgpers = abs(np.amax(arrayBuild[:, -1]) / gv.cp * 1E3)
            costs += PumpModel.Pump_Cost(2 * ntwFeat.DeltaP_DCN, mdot_max_ice_kgpers, gv.etaPump, gv)

            toCosts, toCO2, toPrim, toCalfactor, toTotalCool, Q_availCopy_W, VCC_nom_Ini_W = coolOperation(arrayBuild, nHour,
                                                                                                    Q_avail_W)
            costs += toCosts
            CO2 += toCO2
            prim += toPrim
            calFactor += toCalfactor
            TotalCool += toTotalCool
            VCC_nom_W = max(VCC_nom_W, VCC_nom_Ini_W)
            Q_avail_W = Q_availCopy_W
            print Q_avail_W, "Qavail after ice"

    print costs, CO2, prim, "operation for cooling"
    print TotalCool, "TotalCool"

    ########## Operation of the cooling tower
    CT_nom_W = np.amax(CT_Load_W)
    costCopy = costs
    if CT_nom_W > 0:
        for i in range(nHour):
            wdot_W = CTModel.calc_CT(CT_Load_W[i], CT_nom_W, gv)

            costs += wdot_W * gv.ELEC_PRICE
            CO2 += wdot_W * gv.EL_TO_CO2 * 3600E-6
            prim += wdot_W * gv.EL_TO_OIL_EQ * 3600E-6

        print costs - costCopy, "costs after operation of CT"

    ########## Add investment costs

    costs += VCCModel.calc_Cinv_VCC(VCC_nom_W, gv)
    print VCCModel.calc_Cinv_VCC(VCC_nom_W, gv), "InvC VCC"
    costs += CTModel.calc_Cinv_CT(CT_nom_W, gv)
    print CTModel.calc_Cinv_CT(CT_nom_W, gv), "InvC CT"

    ########### Adjust and add the pumps for filtering and pre-treatment of the water
    calibration = calFactor / 50976000
    print calibration, "adjusting factor"

    extraElec = (127865400 + 85243600) * calibration
    costs += extraElec * gv.ELEC_PRICE
    CO2 += extraElec * gv.EL_TO_CO2 * 3600E-6
    prim += extraElec * gv.EL_TO_OIL_EQ * 3600E-6

    save_file = 1
    if save_file == 1:
        results = pd.DataFrame({
            "costs": [costs],
            "CO2": [CO2],
            "prim":[prim]
        })

        results.to_csv(locator.get_optimization_slave_pp_activation_cooling_pattern(configKey), sep=',')

        print "Cooling Results saved in : ", locator.get_optimization_slave_results_folder()
        print " as : ", configKey + "_coolingresults.csv"

    return (costs, CO2, prim)

