"""
Operation for decentralized buildings

"""
from __future__ import division
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
import time
import numpy as np
import pandas as pd
from cea.optimization.constants import Q_LOSS_DISCONNECTED, SIZING_MARGIN, GHP_A, GHP_HMAX_SIZE, DISC_BIOGAS_FLAG
import cea.technologies.boiler as Boiler
import cea.technologies.cogeneration as FC
import cea.technologies.heatpumps as HP
from cea.resources.geothermal import calc_ground_temperature
from cea.utilities import dbf
from geopandas import GeoDataFrame as Gdf
from cea.utilities import epwreader
from cea.constants import HOURS_IN_YEAR


def disconnected_buildings_heating_main(locator, building_names, config, prices, lca):
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
    def calc_new_load(mdot, TsupDH, Tret):
        """
        This function calculates the load distribution side of the district heating distribution.
        :param mdot: mass flow
        :param TsupDH: supply temeperature
        :param Tret: return temperature
        :type mdot: float
        :type TsupDH: float
        :type Tret: float
        :return: Qload: load of the distribution
        :rtype: float
        """
        Qload = mdot * HEAT_CAPACITY_OF_WATER_JPERKGK * (TsupDH - Tret) * (1 + Q_LOSS_DISCONNECTED)
        if Qload < 0:
            Qload = 0

        return Qload

    for building_name in building_names:
        print building_name
        loads = pd.read_csv(locator.get_optimization_substations_results_file(building_name, "DH"),
                            usecols=["T_supply_DH_result_K", "T_return_DH_result_K", "mdot_DH_result_kgpers"])
        Qload = np.vectorize(calc_new_load)(loads["mdot_DH_result_kgpers"], loads["T_supply_DH_result_K"],
                                            loads["T_return_DH_result_K"])
        Qannual = Qload.sum()
        Qnom = Qload.max() * (1 + SIZING_MARGIN)  # 1% reliability margin on installed capacity


        # Create empty matrices
        Opex_a_var_USD = np.zeros((13, 7))
        Capex_total_USD = np.zeros((13, 7))
        Capex_a_USD = np.zeros((13, 7))
        Opex_a_fixed_USD = np.zeros((13, 7))
        Capex_opex_a_fixed_only_USD = np.zeros((13, 7))
        Opex_a_USD = np.zeros((13, 7))
        GHG_kgCO2 = np.zeros((13, 7))
        PEN_MJoil = np.zeros((13, 7))
        Opex_a_var_USD[0][0] = 1
        Opex_a_var_USD[1][1] = 1
        Opex_a_var_USD[2][2] = 1
        resourcesRes = np.zeros((13, 4))
        QannualB_GHP = np.zeros((10, 1))  # For the investment costs of the boiler used with GHP
        Wel_GHP = np.zeros((10, 1))  # For the investment costs of the GHP

        # Supply with the Boiler / FC / GHP
        Tret = loads["T_return_DH_result_K"].values
        TsupDH = loads["T_supply_DH_result_K"].values
        mdot = loads["mdot_DH_result_kgpers"].values

        for hour in range(HOURS_IN_YEAR):
            if Tret[hour] == 0:
                Tret[hour] = TsupDH[hour]

            # Boiler NG
            BoilerEff = Boiler.calc_Cop_boiler(Qload[hour], Qnom, Tret[hour])

            Qgas = Qload[hour] / BoilerEff

            Opex_a_var_USD[0][4] += prices.NG_PRICE * Qgas  # CHF
            GHG_kgCO2[0][5] += lca.NG_BACKUPBOILER_TO_CO2_STD * Qgas * 3600E-6  # kgCO2
            PEN_MJoil[0][6] += lca.NG_BACKUPBOILER_TO_OIL_STD * Qgas * 3600E-6  # MJ-oil-eq
            resourcesRes[0][0] += Qload[hour]

            if DISC_BIOGAS_FLAG == 1:
                Opex_a_var_USD[0][4] += prices.BG_PRICE * Qgas  # CHF
                GHG_kgCO2[0][5] += lca.BG_BACKUPBOILER_TO_CO2_STD * Qgas * 3600E-6  # kgCO2
                PEN_MJoil[0][6] += lca.BG_BACKUPBOILER_TO_OIL_STD * Qgas * 3600E-6  # MJ-oil-eq

            # Boiler BG
            # variable costs, emissions and primary energy
            Opex_a_var_USD[1][4] += prices.BG_PRICE * Qgas  # CHF
            GHG_kgCO2[1][5] += lca.BG_BACKUPBOILER_TO_CO2_STD * Qgas * 3600E-6  # kgCO2
            PEN_MJoil[1][6] += lca.BG_BACKUPBOILER_TO_OIL_STD * Qgas * 3600E-6  # MJ-oil-eq
            resourcesRes[1][1] += Qload[hour]

            # FC
            (FC_Effel, FC_Effth) = FC.calc_eta_FC(Qload[hour], Qnom, 1, "B")
            Qgas = Qload[hour] / (FC_Effth + FC_Effel)
            Qelec = Qgas * FC_Effel

            # variable costs, emissions and primary energy
            Opex_a_var_USD[2][4] += prices.NG_PRICE * Qgas - lca.ELEC_PRICE[hour] * Qelec  # CHF, extra electricity sold to grid
            GHG_kgCO2[2][5] += 0.0874 * Qgas * 3600E-6 + 773 * 0.45 * Qelec * 1E-6 - lca.EL_TO_CO2 * Qelec * 3600E-6  # kgCO2
            # Bloom box emissions within the FC: 773 lbs / MWh_el (and 1 lbs = 0.45 kg)
            # http://www.carbonlighthouse.com/2011/09/16/bloom-box/
            PEN_MJoil[2][6] += 1.51 * Qgas * 3600E-6 - lca.EL_TO_OIL_EQ * Qelec * 3600E-6  # MJ-oil-eq

            resourcesRes[2][0] += Qload[hour]
            resourcesRes[2][2] += Qelec

            # GHP
            for i in range(10):

                QnomBoiler = i / 10 * Qnom
                QnomGHP = Qnom - QnomBoiler

                if Qload[hour] <= QnomGHP:
                    (wdot_el, qcolddot, qhotdot_missing, tsup2) = HP.calc_Cop_GHP(ground_temp[hour], mdot[hour], TsupDH[hour], Tret[hour])

                    if Wel_GHP[i][0] < wdot_el:
                        Wel_GHP[i][0] = wdot_el

                    # variable costs, emissions and primary energy
                    Opex_a_var_USD[3 + i][4] += lca.ELEC_PRICE[hour] * wdot_el  # CHF
                    GHG_kgCO2[3 + i][5] += lca.SMALL_GHP_TO_CO2_STD * wdot_el * 3600E-6  # kgCO2
                    PEN_MJoil[3 + i][6] += lca.SMALL_GHP_TO_OIL_STD * wdot_el * 3600E-6  # MJ-oil-eq

                    resourcesRes[3 + i][2] -= wdot_el
                    resourcesRes[3 + i][3] += Qload[hour] - qhotdot_missing

                    if qhotdot_missing > 0:
                        print "GHP unable to cover the whole demand, boiler activated!"
                        BoilerEff = Boiler.calc_Cop_boiler(qhotdot_missing, QnomBoiler, tsup2)
                        Qgas = qhotdot_missing / BoilerEff

                        # variable costs, emissions and primary energy
                        Opex_a_var_USD[3 + i][4] += prices.NG_PRICE * Qgas  # CHF
                        GHG_kgCO2[3 + i][5] += lca.NG_BACKUPBOILER_TO_CO2_STD * Qgas * 3600E-6  # kgCO2
                        PEN_MJoil[3 + i][6] += lca.NG_BACKUPBOILER_TO_OIL_STD * Qgas * 3600E-6  # MJ-oil-eq

                        QannualB_GHP[i][0] += qhotdot_missing
                        resourcesRes[3 + i][0] += qhotdot_missing

                else:
                    # print "Boiler activated to compensate GHP", i
                    # if gv.DiscGHPFlag == 0:
                    #    print QnomGHP
                    #   QnomGHP = 0
                    #   print "GHP not allowed 2, set QnomGHP to zero"

                    TexitGHP = QnomGHP / (mdot[hour] * HEAT_CAPACITY_OF_WATER_JPERKGK) + Tret[hour]
                    (wdot_el, qcolddot, qhotdot_missing, tsup2) = HP.calc_Cop_GHP(ground_temp[hour], mdot[hour], TexitGHP, Tret[hour])

                    if Wel_GHP[i][0] < wdot_el:
                        Wel_GHP[i][0] = wdot_el

                    #variable costs, emissions and primary energy
                    Opex_a_var_USD[3 + i][4] += lca.ELEC_PRICE[hour] * wdot_el  # CHF
                    GHG_kgCO2[3 + i][5] += lca.SMALL_GHP_TO_CO2_STD * wdot_el * 3600E-6  # kgCO2
                    GHG_kgCO2[3 + i][6] += lca.SMALL_GHP_TO_OIL_STD * wdot_el * 3600E-6  # MJ-oil-eq

                    resourcesRes[3 + i][2] -= wdot_el
                    resourcesRes[3 + i][3] += QnomGHP - qhotdot_missing

                    if qhotdot_missing > 0:
                        print "GHP unable to cover the whole demand, boiler activated!"
                        BoilerEff = Boiler.calc_Cop_boiler(qhotdot_missing, QnomBoiler, tsup2)
                        Qgas = qhotdot_missing / BoilerEff

                        Opex_a_var_USD[3 + i][4] += prices.NG_PRICE * Qgas  # CHF
                        GHG_kgCO2[3 + i][5] += lca.NG_BACKUPBOILER_TO_CO2_STD * Qgas * 3600E-6  # kgCO2
                        PEN_MJoil[3 + i][6] += lca.NG_BACKUPBOILER_TO_OIL_STD * Qgas * 3600E-6  # MJ-oil-eq

                        QannualB_GHP[i][0] += qhotdot_missing
                        resourcesRes[3 + i][0] += qhotdot_missing

                    QtoBoiler = Qload[hour] - QnomGHP
                    QannualB_GHP[i][0] += QtoBoiler

                    BoilerEff = Boiler.calc_Cop_boiler(QtoBoiler, QnomBoiler, TexitGHP)
                    Qgas = QtoBoiler / BoilerEff

                    #variable costs, emissions and primary energy
                    Opex_a_var_USD[3 + i][4] += prices.NG_PRICE * Qgas  # CHF
                    GHG_kgCO2[3 + i][5] += lca.NG_BACKUPBOILER_TO_CO2_STD * Qgas * 3600E-6  # kgCO2
                    PEN_MJoil[3 + i][6] += lca.NG_BACKUPBOILER_TO_OIL_STD * Qgas * 3600E-6  # MJ-oil-eq
                    resourcesRes[3 + i][0] += QtoBoiler

        #BOILER
        Capex_a_Boiler_USD, Opex_a_fixed_Boiler_USD, Capex_Boiler_USD = Boiler.calc_Cinv_boiler(Qnom, locator, config, 'BO1')
        Capex_total_USD[0][0] = Capex_Boiler_USD
        Capex_total_USD[1][0] = Capex_Boiler_USD
        Capex_a_USD[0][0] = Capex_a_Boiler_USD
        Capex_a_USD[1][0] = Capex_a_Boiler_USD
        Opex_a_fixed_USD[0][0] = Opex_a_fixed_Boiler_USD
        Opex_a_fixed_USD[1][0] = Opex_a_fixed_Boiler_USD
        Capex_opex_a_fixed_only_USD[0][0] = Capex_a_Boiler_USD + Opex_a_fixed_Boiler_USD #TODO:variable price?
        Capex_opex_a_fixed_only_USD[1][0] = Capex_a_Boiler_USD + Opex_a_fixed_Boiler_USD #TODO:variable price?

        #FUELC CELL
        Capex_a_FC_USD, Opex_fixed_FC_USD, Capex_FC_USD = FC.calc_Cinv_FC(Qnom, locator, config)
        Capex_total_USD[2][0] = Capex_FC_USD
        Capex_a_USD[2][0] = Capex_a_FC_USD
        Opex_a_fixed_USD[2][0] = Opex_fixed_FC_USD
        Capex_opex_a_fixed_only_USD[2][0] = Capex_a_FC_USD + Opex_fixed_FC_USD #TODO:variable price?

        # BOILER + HEATPUMP
        for i in range(10):
            Opex_a_var_USD[3 + i][0] = i / 10
            Opex_a_var_USD[3 + i][3] = 1 - i / 10

            #Get boiler cossts
            QnomBoiler = i / 10 * Qnom
            Capex_a_Boiler_USD, Opex_a_fixed_Boiler_USD, Capex_Boiler_USD = Boiler.calc_Cinv_boiler(QnomBoiler, locator, config, 'BO1')
            Capex_total_USD[3 + i][0] = Capex_Boiler_USD
            Capex_a_USD[3 + i][0] = Capex_a_Boiler_USD
            Opex_a_fixed_USD[3 + i][0] = Opex_a_fixed_Boiler_USD
            Capex_opex_a_fixed_only_USD[3 + i][0] = Capex_a_Boiler_USD + Opex_a_fixed_Boiler_USD  # TODO:variable price?

            #Get heat pump costs
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
            TotalCO2[i][1] = GHG_kgCO2[i][5]
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
            QGHP = (1 - i / 10) * Qnom
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
        Qnom_array = np.ones(len(Best[:, 0])) * Qnom

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
        dico["GHG_kgCO2"] = GHG_kgCO2[:, 5]
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

        BestComb = {}
        BestComb["BoilerNG Share"] = Opex_a_var_USD[indexBest, 0]
        BestComb["BoilerBG Share"] = Opex_a_var_USD[indexBest, 1]
        BestComb["FC Share"] = Opex_a_var_USD[indexBest, 2]
        BestComb["GHP Share"] = Opex_a_var_USD[indexBest, 3]
        BestComb["TAC_USD"] = TAC_USD[indexBest, 1]
        BestComb["Capex_a_USD"] = Capex_a_USD[indexBest, 0]
        BestComb["Capex_total_USD"] = Capex_total_USD[indexBest, 0]
        BestComb["Opex_a_USD"] = Opex_a_USD[indexBest, 1]
        BestComb["Opex_a_fixed_USD"] = Opex_a_fixed_USD[indexBest, 0]
        BestComb["Opex_a_var_USD"] = Opex_a_var_USD[indexBest, 4]
        BestComb["GHG_kgCO2"] = GHG_kgCO2[indexBest, 5]
        BestComb["PEN_MJoil"] = PEN_MJoil[indexBest, 6]
        BestComb["Best configuration"] = Best[indexBest, 0]
        BestComb["Nominal Power"] = Qnom

        BestData[building_name] = BestComb

    if 0:
        fName = locator.get_optimization_decentralized_folder_disc_op_summary_heating()
        results_to_csv = pd.DataFrame(BestData)
        results_to_csv.to_csv(fName, sep=',')

    print time.clock() - t0, "seconds process time for the Disconnected Building Routine \n"
