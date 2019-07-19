"""
Operation for decentralized buildings

"""
from __future__ import division

import time

import numpy as np
import pandas as pd
from geopandas import GeoDataFrame as Gdf

import cea.technologies.boiler as Boiler
import cea.technologies.cogeneration as FC
import cea.technologies.heatpumps as HP
import cea.technologies.substation as substation
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.constants import HOURS_IN_YEAR
from cea.constants import WH_TO_J
from cea.optimization.constants import Q_LOSS_DISCONNECTED, SIZING_MARGIN, GHP_A, GHP_HMAX_SIZE, DISC_BIOGAS_FLAG
from cea.resources.geothermal import calc_ground_temperature
from cea.utilities import dbf
from cea.utilities import epwreader


def disconnected_buildings_heating_main(locator, total_demand, building_names, config, prices, lca):
    """
    Computes the parameters for the operation of disconnected buildings
    output results in csv files.
    There is no optimization at this point. The different technologies are calculated and compared 1 to 1 to
    each technology. it is a classical combinatorial problem.
    :param locator: locator class
    :param building_names: list with names of buildings
    :type locator: class
    :type building_names: list
    :return: results of operation of buildings located in locator.get_optimization_decentralized_folder
    :rtype: Nonetype
    """
    t0 = time.clock()
    prop_geometry = Gdf.from_file(locator.get_zone_geometry())
    restrictions = Gdf.from_file(locator.get_building_restrictions())

    geometry = pd.DataFrame({'Name': prop_geometry.Name, 'Area': prop_geometry.area})
    geothermal_potential_data = dbf.dbf_to_dataframe(locator.get_building_supply())
    geothermal_potential_data = pd.merge(geothermal_potential_data, geometry, on='Name').merge(restrictions, on='Name')
    geothermal_potential_data['Area_geo'] = (1 - geothermal_potential_data['GEOTHERMAL']) * geothermal_potential_data[
        'Area']
    weather_data = epwreader.epw_reader(config.weather)[['year', 'drybulb_C', 'wetbulb_C',
                                                         'relhum_percent', 'windspd_ms', 'skytemp_C']]
    ground_temp = calc_ground_temperature(locator, config, weather_data['drybulb_C'], depth_m=10)

    BestData = {}

    # This will calculate the substantion state if all buildings where connected(this is how we study this)
    substation.substation_main_heating(locator, total_demand, building_names)

    for building_name in building_names:
        print building_name
        # run substation model to derive temperatures of the building
        substation_results = pd.read_csv(locator.get_optimization_substations_results_file(building_name, "DH", ""))
        Qload_Wh = np.vectorize(calc_new_load)(substation_results["mdot_DH_result_kgpers"],
                                               substation_results["T_supply_DH_result_K"],
                                               substation_results["T_return_DH_result_K"])
        Qannual_Wh = Qload_Wh.sum()
        Qnom_W = Qload_Wh.max() * (1 + SIZING_MARGIN)  # 1% reliability margin on installed capacity

        # Create empty matrices
        Opex_a_var_USD = np.zeros((13, 7))
        Capex_total_USD = np.zeros((13, 7))
        Capex_a_USD = np.zeros((13, 7))
        Opex_a_fixed_USD = np.zeros((13, 7))
        Capex_opex_a_fixed_only_USD = np.zeros((13, 7))
        Opex_a_USD = np.zeros((13, 7))
        GHG_tonCO2 = np.zeros((13, 7))
        PEN_MJoil = np.zeros((13, 7))
        Opex_a_var_USD[0][0] = 1
        Opex_a_var_USD[1][1] = 1
        Opex_a_var_USD[2][2] = 1
        resourcesRes = np.zeros((13, 4))
        QannualB_GHP = np.zeros((10, 1))  # For the investment costs of the boiler used with GHP
        Wel_GHP = np.zeros((10, 1))  # For the investment costs of the GHP

        # Supply with the Boiler / FC / GHP
        Tret_K = substation_results["T_return_DH_result_K"].values
        Tsup_K = substation_results["T_supply_DH_result_K"].values
        mdot_kgpers = substation_results["mdot_DH_result_kgpers"].values

        for hour in range(HOURS_IN_YEAR):
            if Tret_K[hour] == 0:
                Tret_K[hour] = Tsup_K[hour]

            # Boiler NG
            BoilerEff = Boiler.calc_Cop_boiler(Qload_Wh[hour], Qnom_W, Tret_K[hour])

            Qgas_Wh = Qload_Wh[hour] / BoilerEff

            Opex_a_var_USD[0][4] += prices.NG_PRICE * Qgas_Wh  # CHF
            GHG_tonCO2[0][5] += Qgas_Wh * WH_TO_J / 1E6 * lca.NG_BACKUPBOILER_TO_CO2_STD / 1E3  # ton CO2
            PEN_MJoil[0][6] += Qgas_Wh * WH_TO_J / 1E6 * lca.NG_BACKUPBOILER_TO_OIL_STD  # MJ-oil-eq
            resourcesRes[0][0] += Qload_Wh[hour]

            if DISC_BIOGAS_FLAG == 1:
                Opex_a_var_USD[0][4] += prices.BG_PRICE * Qgas_Wh  # CHF
                GHG_tonCO2[0][5] += Qgas_Wh * WH_TO_J / 1E6 * lca.BG_BACKUPBOILER_TO_CO2_STD / 1E3  # ton CO2
                PEN_MJoil[0][6] += Qgas_Wh * WH_TO_J / 1E6 * lca.BG_BACKUPBOILER_TO_OIL_STD  # MJ-oil-eq

            # Boiler BG
            # variable costs, emissions and primary energy
            Opex_a_var_USD[1][4] += prices.BG_PRICE * Qgas_Wh  # CHF
            GHG_tonCO2[1][5] += Qgas_Wh * WH_TO_J / 1E6 * lca.BG_BACKUPBOILER_TO_CO2_STD / 1E3  # ton CO2
            PEN_MJoil[1][6] += Qgas_Wh * WH_TO_J / 1E6 * lca.BG_BACKUPBOILER_TO_OIL_STD  # MJ-oil-eq
            resourcesRes[1][1] += Qload_Wh[hour]

            # FC
            (FC_Effel, FC_Effth) = FC.calc_eta_FC(Qload_Wh[hour], Qnom_W, 1, "B")
            Qgas_Wh = Qload_Wh[hour] / (FC_Effth + FC_Effel)
            Qelec_Wh = Qgas_Wh * FC_Effel

            # variable costs, emissions and primary energy
            Opex_a_var_USD[2][4] += prices.NG_PRICE * Qgas_Wh - lca.ELEC_PRICE[
                hour] * Qelec_Wh  # CHF, extra electricity sold to grid
            GHG_tonCO2[2][5] += (0.0874 * Qgas_Wh * 3600E-6 + 773 * 0.45 * Qelec_Wh * 1E-6 -
                                 lca.EL_TO_CO2 * Qelec_Wh * 3600E-6) / 1E3  # tonCO2
            # Bloom box emissions within the FC: 773 lbs / MWh_el (and 1 lbs = 0.45 kg)
            # http://www.carbonlighthouse.com/2011/09/16/bloom-box/
            PEN_MJoil[2][6] += 1.51 * Qgas_Wh * 3600E-6 - lca.EL_TO_OIL_EQ * Qelec_Wh * 3600E-6  # MJ-oil-eq

            resourcesRes[2][0] += Qload_Wh[hour]
            resourcesRes[2][2] += Qelec_Wh

            # GHP
            for i in range(10):

                QnomBoiler_W = i / 10 * Qnom_W
                QnomGHP_W = Qnom_W - QnomBoiler_W

                if Qload_Wh[hour] <= QnomGHP_W:
                    (wdot_el_Wh, qcolddot_Wh, qhotdot_missing_Wh, tsup2_K) = HP.calc_Cop_GHP(ground_temp[hour],
                                                                                             mdot_kgpers[hour],
                                                                                             Tsup_K[hour], Tret_K[hour])

                    if Wel_GHP[i][0] < wdot_el_Wh:
                        Wel_GHP[i][0] = wdot_el_Wh

                    # variable costs, emissions and primary energy
                    Opex_a_var_USD[3 + i][4] += lca.ELEC_PRICE[hour] * wdot_el_Wh  # CHF
                    GHG_tonCO2[3 + i][5] += wdot_el_Wh * WH_TO_J / 1E6 * lca.SMALL_GHP_TO_CO2_STD / 1E3  # ton CO2
                    PEN_MJoil[3 + i][6] += wdot_el_Wh * WH_TO_J / 1E6 * lca.SMALL_GHP_TO_OIL_STD  # MJ-oil-eq

                    resourcesRes[3 + i][2] -= wdot_el_Wh
                    resourcesRes[3 + i][3] += Qload_Wh[hour] - qhotdot_missing_Wh

                    if qhotdot_missing_Wh > 0:
                        print "GHP unable to cover the whole demand, boiler activated!"
                        BoilerEff = Boiler.calc_Cop_boiler(qhotdot_missing_Wh, QnomBoiler_W, tsup2_K)
                        Qgas_Wh = qhotdot_missing_Wh / BoilerEff

                        # variable costs, emissions and primary energy
                        Opex_a_var_USD[3 + i][4] += prices.NG_PRICE * Qgas_Wh  # CHF
                        GHG_tonCO2[3 + i][5] += Qgas_Wh * WH_TO_J / 1E6 * lca.NG_BACKUPBOILER_TO_CO2_STD / 1E3  # ton CO2
                        PEN_MJoil[3 + i][6] += Qgas_Wh * WH_TO_J / 1E6 * lca.NG_BACKUPBOILER_TO_OIL_STD  # MJ-oil-eq

                        QannualB_GHP[i][0] += qhotdot_missing_Wh
                        resourcesRes[3 + i][0] += qhotdot_missing_Wh

                else:
                    # print "Boiler activated to compensate GHP", i
                    # if gv.DiscGHPFlag == 0:
                    #    print QnomGHP
                    #   QnomGHP = 0
                    #   print "GHP not allowed 2, set QnomGHP to zero"

                    TexitGHP_K = QnomGHP_W / (mdot_kgpers[hour] * HEAT_CAPACITY_OF_WATER_JPERKGK) + Tret_K[hour]
                    (wdot_el_Wh, qcolddot_Wh, qhotdot_missing_Wh, tsup2_K) = HP.calc_Cop_GHP(ground_temp[hour],
                                                                                             mdot_kgpers[hour],
                                                                                             TexitGHP_K, Tret_K[hour])

                    if Wel_GHP[i][0] < wdot_el_Wh:
                        Wel_GHP[i][0] = wdot_el_Wh

                    # variable costs, emissions and primary energy
                    Opex_a_var_USD[3 + i][4] += lca.ELEC_PRICE[hour] * wdot_el_Wh  # CHF
                    GHG_tonCO2[3 + i][5] += wdot_el_Wh * WH_TO_J / 1E6 * lca.SMALL_GHP_TO_CO2_STD / 1E3  # ton CO2
                    GHG_tonCO2[3 + i][6] += wdot_el_Wh * WH_TO_J / 1E6 * lca.SMALL_GHP_TO_OIL_STD  # MJ-oil-eq

                    resourcesRes[3 + i][2] -= wdot_el_Wh
                    resourcesRes[3 + i][3] += QnomGHP_W - qhotdot_missing_Wh

                    if qhotdot_missing_Wh > 0:
                        print "GHP unable to cover the whole demand, boiler activated!"
                        BoilerEff = Boiler.calc_Cop_boiler(qhotdot_missing_Wh, QnomBoiler_W, tsup2_K)
                        Qgas_Wh = qhotdot_missing_Wh / BoilerEff

                        Opex_a_var_USD[3 + i][4] += prices.NG_PRICE * Qgas_Wh  # CHF
                        GHG_tonCO2[3 + i][5] += Qgas_Wh * WH_TO_J / 1E6 * lca.NG_BACKUPBOILER_TO_CO2_STD / 1E3  # ton CO2
                        PEN_MJoil[3 + i][6] += Qgas_Wh * WH_TO_J / 1E6 * lca.NG_BACKUPBOILER_TO_OIL_STD  # MJ-oil-eq

                        QannualB_GHP[i][0] += qhotdot_missing_Wh
                        resourcesRes[3 + i][0] += qhotdot_missing_Wh

                    QtoBoiler = Qload_Wh[hour] - QnomGHP_W
                    QannualB_GHP[i][0] += QtoBoiler

                    BoilerEff = Boiler.calc_Cop_boiler(QtoBoiler, QnomBoiler_W, TexitGHP_K)
                    Qgas_Wh = QtoBoiler / BoilerEff

                    # variable costs, emissions and primary energy
                    Opex_a_var_USD[3 + i][4] += prices.NG_PRICE * Qgas_Wh  # CHF
                    GHG_tonCO2[3 + i][5] += Qgas_Wh * WH_TO_J / 1E6 * lca.NG_BACKUPBOILER_TO_CO2_STD / 1E3  # ton CO2
                    PEN_MJoil[3 + i][6] += Qgas_Wh * WH_TO_J / 1E6 * lca.NG_BACKUPBOILER_TO_OIL_STD  # MJ-oil-eq
                    resourcesRes[3 + i][0] += QtoBoiler

        # BOILER
        Capex_a_Boiler_USD, Opex_a_fixed_Boiler_USD, Capex_Boiler_USD = Boiler.calc_Cinv_boiler(Qnom_W, locator, config,
                                                                                                'BO1')
        Capex_total_USD[0][0] = Capex_Boiler_USD
        Capex_total_USD[1][0] = Capex_Boiler_USD
        Capex_a_USD[0][0] = Capex_a_Boiler_USD
        Capex_a_USD[1][0] = Capex_a_Boiler_USD
        Opex_a_fixed_USD[0][0] = Opex_a_fixed_Boiler_USD
        Opex_a_fixed_USD[1][0] = Opex_a_fixed_Boiler_USD
        Capex_opex_a_fixed_only_USD[0][0] = Capex_a_Boiler_USD + Opex_a_fixed_Boiler_USD  # TODO:variable price?
        Capex_opex_a_fixed_only_USD[1][0] = Capex_a_Boiler_USD + Opex_a_fixed_Boiler_USD  # TODO:variable price?

        # FUELC CELL
        Capex_a_FC_USD, Opex_fixed_FC_USD, Capex_FC_USD = FC.calc_Cinv_FC(Qnom_W, locator, config)
        Capex_total_USD[2][0] = Capex_FC_USD
        Capex_a_USD[2][0] = Capex_a_FC_USD
        Opex_a_fixed_USD[2][0] = Opex_fixed_FC_USD
        Capex_opex_a_fixed_only_USD[2][0] = Capex_a_FC_USD + Opex_fixed_FC_USD  # TODO:variable price?

        # BOILER + HEATPUMP
        for i in range(10):
            Opex_a_var_USD[3 + i][0] = i / 10
            Opex_a_var_USD[3 + i][3] = 1 - i / 10

            # Get boiler cossts
            QnomBoiler_W = i / 10 * Qnom_W
            Capex_a_Boiler_USD, Opex_a_fixed_Boiler_USD, Capex_Boiler_USD = Boiler.calc_Cinv_boiler(QnomBoiler_W, locator,
                                                                                                    config, 'BO1')
            Capex_total_USD[3 + i][0] = Capex_Boiler_USD
            Capex_a_USD[3 + i][0] = Capex_a_Boiler_USD
            Opex_a_fixed_USD[3 + i][0] = Opex_a_fixed_Boiler_USD
            Capex_opex_a_fixed_only_USD[3 + i][0] = Capex_a_Boiler_USD + Opex_a_fixed_Boiler_USD  # TODO:variable price?

            # Get heat pump costs
            Capex_a_GHP_USD, Opex_a_fixed_GHP_USD, Capex_GHP_USD = HP.calc_Cinv_GHP(Wel_GHP[i][0], locator, config)
            Capex_total_USD[3 + i][0] += Capex_GHP_USD
            Capex_a_USD[3 + i][0] += Capex_a_GHP_USD
            Opex_a_fixed_USD[3 + i][0] += Opex_a_fixed_GHP_USD
            Capex_opex_a_fixed_only_USD[3 + i][0] += Capex_a_GHP_USD + Opex_a_fixed_GHP_USD  # TODO:variable price?

        # Best configuration
        Best = np.zeros((13, 1))
        indexBest = 0
        TAC_USD = np.zeros((13, 2))
        TotalCO2 = np.zeros((13, 2))
        TotalPrim = np.zeros((13, 2))
        for i in range(13):
            TAC_USD[i][0] = TotalCO2[i][0] = TotalPrim[i][0] = i
            Opex_a_USD[i][1] = Opex_a_fixed_USD[i][0] + + Opex_a_var_USD[i][4]
            TAC_USD[i][1] = Capex_opex_a_fixed_only_USD[i][0] + Opex_a_var_USD[i][4]
            TotalCO2[i][1] = GHG_tonCO2[i][5]
            TotalPrim[i][1] = PEN_MJoil[i][6]

        CostsS = TAC_USD[np.argsort(TAC_USD[:, 1])]
        CO2S = TotalCO2[np.argsort(TotalCO2[:, 1])]
        PrimS = TotalPrim[np.argsort(TotalPrim[:, 1])]

        el = len(CostsS)
        rank = 0
        Bestfound = False

        optsearch = np.empty(el)
        optsearch.fill(3)
        indexBest = 0
        geothermal_potential = geothermal_potential_data.set_index('Name')

        # Check the GHP area constraint
        for i in range(10):
            QGHP = (1 - i / 10) * Qnom_W
            areaAvail = geothermal_potential.ix[building_name, 'Area_geo']
            Qallowed = np.ceil(areaAvail / GHP_A) * GHP_HMAX_SIZE  # [W_th]
            if Qallowed < QGHP:
                optsearch[i + 3] += 1
                Best[i + 3][0] = - 1

        while not Bestfound and rank < el:

            optsearch[int(CostsS[rank][0])] -= 1
            optsearch[int(CO2S[rank][0])] -= 1
            optsearch[int(PrimS[rank][0])] -= 1

            if np.count_nonzero(optsearch) != el:
                Bestfound = True
                indexBest = np.where(optsearch == 0)[0][0]

            rank += 1

        # get the best option according to the ranking.
        Best[indexBest][0] = 1
        Qnom_array = np.ones(len(Best[:, 0])) * Qnom_W

        # Save results in csv file
        dico = {}
        dico["BoilerNG Share"] = Opex_a_var_USD[:, 0]
        dico["BoilerBG Share"] = Opex_a_var_USD[:, 1]
        dico["FC Share"] = Opex_a_var_USD[:, 2]
        dico["GHP Share"] = Opex_a_var_USD[:, 3]
        dico["TAC_USD"] = TAC_USD[:, 1]
        dico["Capex_a_USD"] = Capex_a_USD[:, 0]
        dico["Capex_total_USD"] = Capex_total_USD[:, 0]
        dico["Opex_a_USD"] = Opex_a_USD[:, 1]
        dico["Opex_a_fixed_USD"] = Opex_a_fixed_USD[:, 0]
        dico["Opex_a_var_USD"] = Opex_a_var_USD[:, 4]
        dico["GHG_tonCO2"] = GHG_tonCO2[:, 5]
        dico["PEN_MJoil"] = PEN_MJoil[:, 6]
        dico["Best configuration"] = Best[:, 0]
        dico["Nominal Power"] = Qnom_array
        dico["QfromNG"] = resourcesRes[:, 0]
        dico["QfromBG"] = resourcesRes[:, 1]
        dico["EforGHP"] = resourcesRes[:, 2]
        dico["QfromGHP"] = resourcesRes[:, 3]

        results_to_csv = pd.DataFrame(dico)

        fName_result = locator.get_optimization_decentralized_folder_building_result_heating(building_name)
        results_to_csv.to_csv(fName_result, sep=',')

    print time.clock() - t0, "seconds process time for the Disconnected Building Routine \n"


def calc_new_load(mdot_kgpers, TsupDH, Tret):
    """
    This function calculates the load distribution side of the district heating distribution.
    :param mdot_kgpers: mass flow
    :param TsupDH: supply temeperature
    :param Tret: return temperature
    :type mdot_kgpers: float
    :type TsupDH: float
    :type Tret: float
    :return: Qload_W: load of the distribution
    :rtype: float
    """
    Qload_W = mdot_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK * (TsupDH - Tret) * (1 + Q_LOSS_DISCONNECTED)
    if Qload_W < 0:
        Qload_W = 0
    return Qload_W
