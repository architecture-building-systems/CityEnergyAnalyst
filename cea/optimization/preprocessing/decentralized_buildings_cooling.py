"""
====================================
Operation for decentralized buildings
====================================
"""
from __future__ import division


import os
import cea.config
import cea.globalvar
import cea.inputlocator
import time
import numpy as np
import pandas as pd
from cea.optimization.constants import *
import cea.technologies.chiller_vcc as chiller_vcc
import cea.technologies.cooling_tower as cooling_tower
from cea.utilities import dbf
from geopandas import GeoDataFrame as Gdf



def decentralized_cooling_main(locator, building_names, gv, config, prices):
    """
    Computes the parameters for the operation of disconnected buildings
    output results in csv files.
    There is no optimization at this point. The different technologies are calculated and compared 1 to 1 to
    each technology. it is a classical combinatorial problem.
    :param locator: locator class
    :param building_names: list with names of buildings
    :param gv: global variables class
    :type locator: class
    :type building_names: list
    :type gv: class
    :return: results of operation of buildings located in locator.get_optimization_disconnected_folder
    :rtype: Nonetype
    """
    t0 = time.clock()
    prop_geometry = Gdf.from_file(locator.get_zone_geometry())
    restrictions =  Gdf.from_file(locator.get_building_restrictions()) # TODO: delete if not used

    geometry = pd.DataFrame({'Name': prop_geometry.Name, 'Area': prop_geometry.area})
    BestData = {}

    def calc_new_load(mdot_kgpers, T_sup_K, T_re_K, gv, config):
        """
        This function calculates the load distribution side of the district heating distribution.
        :param mdot_kgpers: mass flow
        :param T_sup_K: chilled water supply temperautre
        :param T_re_K: chilled water return temperature
        :param gv: global variables class
        :type mdot_kgpers: float
        :type TsupDH: float
        :type T_re_K: float
        :type gv: class
        :return: Q_cooling_load: load of the distribution
        :rtype: float
        """
        Q_cooling_load_W = mdot_kgpers * gv.cp * (T_re_K - T_sup_K) * (1 + Qloss_Disc)   # for cooling load
        if Q_cooling_load_W < 0:
            Q_cooling_load_W = 0

        return Q_cooling_load_W

    for building_name in building_names:
        print building_name
        loads = pd.read_csv(locator.get_optimization_substations_results_file(building_name),
                            usecols=["T_supply_DC_result_K", "T_return_DC_result_K", "mdot_DC_result_kgpers"])
        Q_cooling_load_W = np.vectorize(calc_new_load)(loads["mdot_DC_result_kgpers"], loads["T_supply_DC_result_K"],
                                            loads["T_return_DC_result_K"], gv, config)
        Q_cooling_annual_W = Q_cooling_load_W.sum()
        Q_cooling_nom_W = Q_cooling_load_W.max()* (1+Qmargin_Disc) # 20% reliability margin on installed capacity

        # Create empty matrices
        result = np.zeros((4,7))
        result[0][0] = 1
        result[1][1] = 1
        result[2][2] = 1
        Q_CT_W = np.zeros(8760)
        InvCosts = np.zeros((4,1))
        resourcesRes = np.zeros((4,4))

        # Calculation to meet cooling demand in disconnected buildings by the following configurations
        # 1: VCC (AHU + ARU + SCU) + CT
        # 2: VCC (AHU + ARU) + VCC (SCU) + CT
        # 3: VCC (AHU + ARU) + ABS (SCU) + CT
        # 4: ABS (AHU + ARU + SCU) + CT
        # TODO: seperate the loads
        T_re_K = loads["T_return_DC_result_K"].values
        T_sup_K = loads["T_supply_DC_result_K"].values
        mdot_kgpers = loads["mdot_DC_result_kgpers"].values

        for hour in range(8760):

            if T_re_K[hour] == 0:
                T_re_K[hour] = T_sup_K[hour]

            # 1: VCC (AHU + ARU + SCU) + CT
            wdot_W, qhotdot_W = chiller_vcc.calc_VCC(mdot_kgpers[hour], T_sup_K[hour], T_re_K[hour], gv) # TODO: add size dependent vcc model
            result[0][4] += prices.ELEC_PRICE * wdot_W # CHF
            result[0][5] += EL_TO_CO2 * wdot_W * 3600E-6 # kgCO2
            result[0][6] += EL_TO_OIL_EQ * wdot_W * 3600E-6 # MJ-oil-eq
            resourcesRes[0][0] += Q_cooling_load_W[hour]
            Q_CT_W[hour] = qhotdot_W

        # sizing of CT
        CT_nom_size_W = np.max(Q_CT_W)*(1+Qmargin_Disc)
        for hour in range(8760):

            # calculate CT operation
            wdot_W = cooling_tower.calc_CT(Q_CT_W[hour], CT_nom_size_W, gv)
            result[0][4] += prices.ELEC_PRICE * wdot_W  # CHF
            result[0][5] += EL_TO_CO2 * wdot_W * 3600E-6  # kgCO2
            result[0][6] += EL_TO_OIL_EQ * wdot_W * 3600E-6  # MJ-oil-eq

        # Calculate Capex/Opex
        Capex_a_VCC, Opex_VCC =chiller_vcc.calc_Cinv_VCC(Q_cooling_nom_W, gv, locator, technology=1)
        Capex_a_CT, Opex_CT = cooling_tower.calc_Cinv_CT(CT_nom_size_W, gv, locator, technology=0)
        InvCosts[0][0] = Capex_a_CT + Opex_CT + Capex_a_VCC + Opex_VCC
        InvCosts[1][0] = Capex_a_CT + Opex_CT + Capex_a_VCC + Opex_VCC



        # Best configuration
        Best = np.zeros((13,1))
        indexBest = 0

        TotalCosts = np.zeros((13,2))
        TotalCO2 = np.zeros((13,2))
        TotalPrim = np.zeros((13,2))

        for i in range(13):
            TotalCosts[i][0] = TotalCO2[i][0] = TotalPrim[i][0] = i

            TotalCosts[i][1] = InvCosts[i][0] + result[i][4]
            TotalCO2[i][1] = result[i][5]
            TotalPrim[i][1] = result[i][6]

        CostsS = TotalCosts[np.argsort(TotalCosts[:,1])]
        CO2S = TotalCO2[np.argsort(TotalCO2[:,1])]
        PrimS = TotalPrim[np.argsort(TotalPrim[:,1])]

        el = len(CostsS)
        rank = 0
        Bestfound = False

        optsearch = np.empty(el)
        optsearch.fill(3)
        indexBest = 0
        geothermal_potential = geothermal_potential_data.set_index('Name')

        # Check the GHP area constraint
        for i in range(10):
            QGHP = (1-i/10) * Q_cooling_nom_W
            areaAvail = geothermal_potential.ix[building_name, 'Area_geo']
            Qallowed = np.ceil(areaAvail/GHP_A) * GHP_HmaxSize #[W_th]
            if Qallowed < QGHP:
                optsearch[i+3] += 1
                Best[i+3][0] = - 1

        while not Bestfound and rank<el:

            optsearch[int(CostsS[rank][0])] -= 1
            optsearch[int(CO2S[rank][0])] -= 1
            optsearch[int(PrimS[rank][0])] -= 1

            if np.count_nonzero(optsearch) != el:
                Bestfound = True
                indexBest = np.where(optsearch == 0)[0][0]

            rank += 1

        # get the best option according to the ranking.
        Best[indexBest][0] = 1
        Qnom_array = np.ones(len(Best[:,0])) * Q_cooling_nom_W

        # Save results in csv file
        dico = {}
        dico[ "BoilerNG Share" ] = result[:,0]
        dico[ "BoilerBG Share" ] = result[:,1]
        dico[ "FC Share" ] = result[:,2]
        dico[ "GHP Share" ] = result[:,3]
        dico[ "Operation Costs [CHF]" ] = result[:,4]
        dico[ "CO2 Emissions [kgCO2-eq]" ] = result[:,5]
        dico[ "Primary Energy Needs [MJoil-eq]" ] = result[:,6]
        dico[ "Annualized Investment Costs [CHF]" ] = InvCosts[:,0]
        dico[ "Total Costs [CHF]" ] = TotalCosts[:,1]
        dico[ "Best configuration" ] = Best[:,0]
        dico[ "Nominal Power" ] = Qnom_array
        dico[ "QfromNG" ] = resourcesRes[:,0]
        dico[ "QfromBG" ] = resourcesRes[:,1]
        dico[ "EforGHP" ] = resourcesRes[:,2]
        dico[ "QfromGHP" ] = resourcesRes[:,3]


        results_to_csv = pd.DataFrame(dico)
        fName_result = locator.get_optimization_disconnected_folder_building_result(building_name)
        results_to_csv.to_csv(fName_result, sep= ',')


        BestComb = {}
        BestComb[ "BoilerNG Share" ] = result[indexBest,0]
        BestComb[ "BoilerBG Share" ] = result[indexBest,1]
        BestComb[ "FC Share" ] = result[indexBest,2]
        BestComb[ "GHP Share" ] = result[indexBest,3]
        BestComb[ "Operation Costs [CHF]" ] = result[indexBest,4]
        BestComb[ "CO2 Emissions [kgCO2-eq]" ] = result[indexBest,5]
        BestComb[ "Primary Energy Needs [MJoil-eq]" ] = result[indexBest,6]
        BestComb[ "Annualized Investment Costs [CHF]" ] = InvCosts[indexBest,0]
        BestComb[ "Total Costs [CHF]" ] = TotalCosts[indexBest,1]
        BestComb[ "Best configuration" ] = Best[indexBest,0]
        BestComb[ "Nominal Power" ] = Q_cooling_nom_W

        BestData[building_name] = BestComb

    if 0:
        fName = locator.get_optimization_disconnected_folder_disc_op_summary()
        results_to_csv = pd.DataFrame(BestData)
        results_to_csv.to_csv(fName, sep= ',')

    print time.clock() - t0, "seconds process time for the Disconnected Building Routine \n"

#============================
#test
#============================


def main(config):
    """
    run the whole preprocessing routine
    """
    from cea.optimization.prices import Prices as Prices
    gv = cea.globalvar.GlobalVariables()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    weather_file = config.weather
    prices = Prices(locator, config)
    decentralized_cooling_main(locator, building_names, gv, config, prices)

    print 'test_decentralized_buildings_cooling() succeeded'

if __name__ == '__main__':
    main(cea.config.Configuration())