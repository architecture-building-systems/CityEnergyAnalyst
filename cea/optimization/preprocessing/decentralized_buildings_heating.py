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
from cea.constants import WH_TO_J
from cea.optimization.constants import Q_LOSS_DISCONNECTED, SIZING_MARGIN, GHP_A, GHP_HMAX_SIZE
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
    weather_path = locator.get_weather_file()
    weather_data = epwreader.epw_reader(weather_path)[['year', 'drybulb_C', 'wetbulb_C',
                                                         'relhum_percent', 'windspd_ms', 'skytemp_C']]

    T_ground_K = calc_ground_temperature(locator, weather_data['drybulb_C'], depth_m=10)


    # This will calculate the substation state if all buildings where connected(this is how we study this)
    substation.substation_main_heating(locator, total_demand, building_names)

    for building_name in building_names:
        # run substation model to derive temperatures of the building
        substation_results = pd.read_csv(locator.get_optimization_substations_results_file(building_name, "DH", ""))
        q_load_Wh = np.vectorize(calc_new_load)(substation_results["mdot_DH_result_kgpers"],
                                                substation_results["T_supply_DH_result_K"],
                                                substation_results["T_return_DH_result_K"])
        Qannual_Wh = q_load_Wh.sum()
        Qnom_W = q_load_Wh.max() * (1 + SIZING_MARGIN)

        # Create empty matrices
        Opex_a_var_USD = np.zeros((13, 7))
        Capex_total_USD = np.zeros((13, 7))
        Capex_a_USD = np.zeros((13, 7))
        Opex_a_fixed_USD = np.zeros((13, 7))
        Capex_opex_a_fixed_only_USD = np.zeros((13, 7))
        Opex_a_USD = np.zeros((13, 7))
        GHG_tonCO2 = np.zeros((13, 7))
        PEN_MJoil = np.zeros((13, 7))
        # indicate supply technologies for each configuration
        Opex_a_var_USD[0][0] = 1  # Boiler NG
        Opex_a_var_USD[1][1] = 1  # Boiler BG
        Opex_a_var_USD[2][2] = 1  # Fuel Cell

        resourcesRes = np.zeros((13, 4))
        Q_Boiler_for_GHP_W = np.zeros((10, 1))  # Save peak capacity of GHP Backup Boilers
        GHP_el_size_W = np.zeros((10, 1))  # Save peak capacity of GHP

        # save supply system activation of all supply configurations
        heating_dispatch = {}

        # Supply with the Boiler / FC / GHP
        Tret_K = substation_results["T_return_DH_result_K"].values
        Tsup_K = substation_results["T_supply_DH_result_K"].values
        mdot_kgpers = substation_results["mdot_DH_result_kgpers"].values

        ## Start Hourly calculation
        print building_name, ' decentralized heating supply systems simulations...'
        Tret_K = np.where(Tret_K > 0.0, Tret_K, Tsup_K)

        ## 0: Boiler NG
        BoilerEff = np.vectorize(Boiler.calc_Cop_boiler)(q_load_Wh, Qnom_W, Tret_K)
        Qgas_to_Boiler_Wh = np.divide(q_load_Wh, BoilerEff, out=np.zeros_like(q_load_Wh), where=BoilerEff != 0.0)
        Boiler_Status = np.where(Qgas_to_Boiler_Wh > 0.0, 1, 0)
        # add costs
        Opex_a_var_USD[0][4] += sum(prices.NG_PRICE * Qgas_to_Boiler_Wh)  # CHF
        GHG_tonCO2[0][5] += sum(Qgas_to_Boiler_Wh * WH_TO_J / 1E6 * lca.NG_BACKUPBOILER_TO_CO2_STD / 1E3)  # ton CO2
        PEN_MJoil[0][6] += sum(Qgas_to_Boiler_Wh * WH_TO_J / 1E6 * lca.NG_BACKUPBOILER_TO_OIL_STD)  # MJ-oil-eq
        # add activation
        resourcesRes[0][0] += sum(q_load_Wh)  # q from NG
        heating_dispatch[0] = {'Q_Boiler_gen_directload_W': q_load_Wh,
                                         'Boiler_Status': Boiler_Status,
                                         'NG_Boiler_req_W': Qgas_to_Boiler_Wh,
                                         'E_hs_ww_req_W': np.zeros(8760)}

        ## 1: Boiler BG
        # add costs
        Opex_a_var_USD[1][4] += sum(prices.BG_PRICE * Qgas_to_Boiler_Wh)  # CHF
        GHG_tonCO2[1][5] += sum(Qgas_to_Boiler_Wh * WH_TO_J / 1E6 * lca.BG_BACKUPBOILER_TO_CO2_STD / 1E3)  # ton CO2
        PEN_MJoil[1][6] += sum(Qgas_to_Boiler_Wh * WH_TO_J / 1E6 * lca.BG_BACKUPBOILER_TO_OIL_STD)  # MJ-oil-eq
        # add activation
        resourcesRes[1][1] += sum(q_load_Wh)  # q from BG
        heating_dispatch[1] = {'Q_Boiler_gen_directload_W': q_load_Wh,
                               'Boiler_Status': Boiler_Status,
                               'BG_Boiler_req_W': Qgas_to_Boiler_Wh,
                               'E_hs_ww_req_W': np.zeros(8760)}

        ## 2: Fuel Cell
        (FC_Effel, FC_Effth) = np.vectorize(FC.calc_eta_FC)(q_load_Wh, Qnom_W, 1, "B")
        Qgas_to_FC_Wh = q_load_Wh / (FC_Effth + FC_Effel)  # FIXME: should be q_load_Wh/FC_Effth?
        el_from_FC_Wh = Qgas_to_FC_Wh * FC_Effel
        FC_Status = np.where(Qgas_to_FC_Wh > 0.0, 1, 0)
        # add variable costs, emissions and primary energy
        Opex_a_var_USD[2][4] += sum(
            prices.NG_PRICE * Qgas_to_FC_Wh - lca.ELEC_PRICE * el_from_FC_Wh)  # CHF, extra electricity sold to grid
        GHG_tonCO2_from_FC = (0.0874 * Qgas_to_FC_Wh * 3600E-6 + 773 * 0.45 * el_from_FC_Wh * 1E-6 -
                              lca.EL_TO_CO2 * el_from_FC_Wh * 3600E-6) / 1E3
        GHG_tonCO2[2][5] += sum(GHG_tonCO2_from_FC)  # tonCO2
        # Bloom box emissions within the FC: 773 lbs / MWh_el (and 1 lbs = 0.45 kg)
        # http://www.carbonlighthouse.com/2011/09/16/bloom-box/
        PEN_MJoil_from_FC = 1.51 * Qgas_to_FC_Wh * 3600E-6 - lca.EL_TO_OIL_EQ * el_from_FC_Wh * 3600E-6
        PEN_MJoil[2][6] += sum(PEN_MJoil_from_FC)  # MJ-oil-eq
        # add activation
        resourcesRes[2][0] = sum(q_load_Wh)  # q from NG
        resourcesRes[2][2] = sum(el_from_FC_Wh)  # el for GHP # FIXME: el from FC
        heating_dispatch[2] = {'Q_Fuelcell_gen_directload_W': q_load_Wh,
                               'Fuelcell_Status': FC_Status,
                               'NG_FuelCell_req_W': Qgas_to_FC_Wh,
                               'E_Fuelcell_gen_export_W': el_from_FC_Wh,
                               'E_hs_ww_req_W': np.zeros(8760)}

        # 3-13: Boiler NG + GHP
        for i in range(10):
            # set nominal size for Boiler and GHP
            QnomBoiler_W = i / 10 * Qnom_W
            QnomGHP_W = Qnom_W - QnomBoiler_W

            # GHP operation
            Texit_GHP_nom_K = QnomGHP_W / (mdot_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK) + Tret_K
            el_GHP_Wh, q_load_NG_Boiler_Wh, \
            qhot_missing_Wh, \
            tsup2_K, q_from_GHP_Wh = np.vectorize(calc_GHP_operation)(QnomGHP_W, T_ground_K, Texit_GHP_nom_K,
                                                                      Tret_K, Tsup_K, mdot_kgpers, q_load_Wh)
            GHP_el_size_W[i][0] = max(el_GHP_Wh)
            GHP_Status = np.where(q_from_GHP_Wh > 0.0, 1, 0)
            # GHP Backup Boiler operation
            if max(qhot_missing_Wh) > 0.0:
                print "GHP unable to cover the whole demand, boiler activated!"
                Qnom_GHP_Backup_Boiler_W = max(qhot_missing_Wh)
                BoilerEff = np.vectorize(Boiler.calc_Cop_boiler)(qhot_missing_Wh, Qnom_GHP_Backup_Boiler_W, tsup2_K)
                Qgas_to_GHPBoiler_Wh = np.divide(qhot_missing_Wh, BoilerEff,
                                                 out=np.zeros_like(qhot_missing_Wh), where=BoilerEff != 0.0)
            else:
                Qgas_to_GHPBoiler_Wh = np.zeros(q_load_Wh.shape[0])
                Qnom_GHP_Backup_Boiler_W = 0.0
            Q_Boiler_for_GHP_W[i][0] = Qnom_GHP_Backup_Boiler_W
            GHPbackupBoiler_Status = np.where(qhot_missing_Wh > 0.0, 1, 0)

            # NG Boiler operation
            BoilerEff = np.vectorize(Boiler.calc_Cop_boiler)(q_load_NG_Boiler_Wh, QnomBoiler_W, Texit_GHP_nom_K)
            Qgas_to_Boiler_Wh = np.divide(q_load_NG_Boiler_Wh, BoilerEff,
                                          out=np.zeros_like(q_load_NG_Boiler_Wh), where=BoilerEff != 0.0)
            Boiler_Status = np.where(q_load_NG_Boiler_Wh > 0.0, 1, 0)

            # add costs
            # electricity
            el_total_Wh = el_GHP_Wh
            Opex_a_var_USD[3 + i][4] += sum(lca.ELEC_PRICE * el_total_Wh)  # CHF
            GHG_tonCO2[3 + i][5] += sum(el_total_Wh * WH_TO_J / 1E6 * lca.SMALL_GHP_TO_CO2_STD / 1E3)  # ton CO2
            PEN_MJoil[3 + i][6] += sum(el_total_Wh * WH_TO_J / 1E6 * lca.SMALL_GHP_TO_OIL_STD)  # MJ-oil-eq
            # gas
            Q_gas_total_Wh = Qgas_to_GHPBoiler_Wh + Qgas_to_Boiler_Wh
            Opex_a_var_USD[3 + i][4] += sum(prices.NG_PRICE * Q_gas_total_Wh)  # CHF
            GHG_tonCO2[3 + i][5] += sum(
                Q_gas_total_Wh * WH_TO_J / 1E6 * lca.NG_BACKUPBOILER_TO_CO2_STD / 1E3)  # ton CO2
            PEN_MJoil[3 + i][6] += sum(Q_gas_total_Wh * WH_TO_J / 1E6 * lca.NG_BACKUPBOILER_TO_OIL_STD)  # MJ-oil-eq
            # add activation
            resourcesRes[3 + i][0] = sum(qhot_missing_Wh + q_load_NG_Boiler_Wh)
            resourcesRes[3 + i][2] = sum(el_GHP_Wh)
            resourcesRes[3 + i][3] = sum(q_from_GHP_Wh)

            heating_dispatch[3 + i] = {'Q_GHP_gen_directload_W': q_from_GHP_Wh,
                                       'Q_BackupBoiler_gen_directload_W': qhot_missing_Wh,
                                       'Q_Boiler_gen_directload_W': q_load_NG_Boiler_Wh,
                                       'GHP_Status': GHP_Status,
                                       'BackupBoiler_Status': GHPbackupBoiler_Status,
                                       'Boiler_Status': Boiler_Status,
                                       'NG_BackupBoiler_req_Wh': Qgas_to_GHPBoiler_Wh,
                                       'NG_Boiler_req_Wh': Qgas_to_Boiler_Wh,
                                       'E_hs_ww_req_W': el_GHP_Wh}

        # Add all costs
        # 0: Boiler NG
        Capex_a_Boiler_USD, Opex_a_fixed_Boiler_USD, Capex_Boiler_USD = Boiler.calc_Cinv_boiler(Qnom_W, locator, config,
                                                                                                'BO1')
        Capex_total_USD[0][0] = Capex_Boiler_USD
        Capex_a_USD[0][0] = Capex_a_Boiler_USD
        Opex_a_fixed_USD[0][0] = Opex_a_fixed_Boiler_USD
        Capex_opex_a_fixed_only_USD[0][0] = Capex_a_Boiler_USD + Opex_a_fixed_Boiler_USD  # TODO:variable price?

        # 1: Boiler BG
        Capex_total_USD[1][0] = Capex_Boiler_USD
        Capex_a_USD[1][0] = Capex_a_Boiler_USD
        Opex_a_fixed_USD[1][0] = Opex_a_fixed_Boiler_USD
        Capex_opex_a_fixed_only_USD[1][0] = Capex_a_Boiler_USD + Opex_a_fixed_Boiler_USD  # TODO:variable price?

        # 2: Fuel Cell
        Capex_a_FC_USD, Opex_fixed_FC_USD, Capex_FC_USD = FC.calc_Cinv_FC(Qnom_W, locator, config)
        Capex_total_USD[2][0] = Capex_FC_USD
        Capex_a_USD[2][0] = Capex_a_FC_USD
        Opex_a_fixed_USD[2][0] = Opex_fixed_FC_USD
        Capex_opex_a_fixed_only_USD[2][0] = Capex_a_FC_USD + Opex_fixed_FC_USD  # TODO:variable price?

        # 3-13: BOILER + GHP
        for i in range(10):
            Opex_a_var_USD[3 + i][0] = i / 10  # Boiler share
            Opex_a_var_USD[3 + i][3] = 1 - i / 10  # GHP share

            # Get boiler costs
            QnomBoiler_W = i / 10 * Qnom_W
            Capex_a_Boiler_USD, Opex_a_fixed_Boiler_USD, Capex_Boiler_USD = Boiler.calc_Cinv_boiler(QnomBoiler_W,
                                                                                                    locator,
                                                                                                    config, 'BO1')

            Capex_total_USD[3 + i][0] += Capex_Boiler_USD
            Capex_a_USD[3 + i][0] += Capex_a_Boiler_USD
            Opex_a_fixed_USD[3 + i][0] += Opex_a_fixed_Boiler_USD
            Capex_opex_a_fixed_only_USD[3 + i][
                0] += Capex_a_Boiler_USD + Opex_a_fixed_Boiler_USD  # TODO:variable price?

            # Get back up boiler costs
            Qnom_Backup_Boiler_W = Q_Boiler_for_GHP_W[i][0]
            Capex_a_GHPBoiler_USD, Opex_a_fixed_GHPBoiler_USD, Capex_GHPBoiler_USD = Boiler.calc_Cinv_boiler(
                Qnom_Backup_Boiler_W, locator,
                config, 'BO1')

            Capex_total_USD[3 + i][0] += Capex_GHPBoiler_USD
            Capex_a_USD[3 + i][0] += Capex_a_GHPBoiler_USD
            Opex_a_fixed_USD[3 + i][0] += Opex_a_fixed_GHPBoiler_USD
            Capex_opex_a_fixed_only_USD[3 + i][
                0] += Capex_a_GHPBoiler_USD + Opex_a_fixed_GHPBoiler_USD  # TODO:variable price?

            # Get ground source heat pump costs
            Capex_a_GHP_USD, Opex_a_fixed_GHP_USD, Capex_GHP_USD = HP.calc_Cinv_GHP(GHP_el_size_W[i][0], locator,
                                                                                    config)
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
        performance_results = {
            "BoilerNG Share": Opex_a_var_USD[:, 0],
            "BoilerBG Share": Opex_a_var_USD[:, 1],
            "FC Share": Opex_a_var_USD[:, 2],
            "GHP Share": Opex_a_var_USD[:, 3],
            "TAC_USD": TAC_USD[:, 1],
            "Capex_a_USD": Capex_a_USD[:, 0],
            "Capex_total_USD": Capex_total_USD[:, 0],
            "Opex_a_USD": Opex_a_USD[:, 1],
            "Opex_a_fixed_USD": Opex_a_fixed_USD[:, 0],
            "Opex_a_var_USD": Opex_a_var_USD[:, 4],
            "GHG_tonCO2": GHG_tonCO2[:, 5],
            "PEN_MJoil": PEN_MJoil[:, 6],
            "Best configuration": Best[:, 0]}

        results_to_csv = pd.DataFrame(performance_results)

        fName_result = locator.get_optimization_decentralized_folder_building_result_heating(building_name)
        results_to_csv.to_csv(fName_result, sep=',')

        # save activation for the best supply system configuration
        best_activation_df = pd.DataFrame.from_dict(heating_dispatch[indexBest])  #
        best_activation_df.to_csv(
            locator.get_optimization_decentralized_folder_building_result_heating_activation(building_name))

    print time.clock() - t0, "seconds process time for the Disconnected Building Routine \n"


def calc_GHP_operation(QnomGHP_W, T_ground_K, Texit_GHP_nom_K, Tret_K, Tsup_K, mdot_kgpers, q_load_Wh):
    if q_load_Wh <= QnomGHP_W:
        q_load_NG_Boiler_Wh = 0.0
        (el_GHP_Wh, qcolddot_Wh, qhot_missing_Wh, tsup2_K) = HP.calc_Cop_GHP(T_ground_K,
                                                                             mdot_kgpers,
                                                                             Tsup_K, Tret_K)
        q_from_GHP_Wh = q_load_Wh - qhot_missing_Wh

    else:
        (el_GHP_Wh, qcolddot_Wh, qhot_missing_Wh, tsup2_K) = HP.calc_Cop_GHP(T_ground_K,
                                                                             mdot_kgpers,
                                                                             Texit_GHP_nom_K, Tret_K)
        q_from_GHP_Wh = QnomGHP_W - qhot_missing_Wh
        q_load_NG_Boiler_Wh = q_load_Wh - QnomGHP_W

    return el_GHP_Wh, q_load_NG_Boiler_Wh, qhot_missing_Wh, tsup2_K, q_from_GHP_Wh


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
