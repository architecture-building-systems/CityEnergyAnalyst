"""
multi-objective optimization of supply systems for the CEA
"""

from __future__ import division
import os
import pandas as pd
import numpy as np
import cea.config
import cea.globalvar
import cea.inputlocator
from cea.optimization.prices import Prices as Prices
import cea.optimization.distribution.network_opt_main as network_opt
from cea.optimization.preprocessing.preprocessing_main import preproccessing
import cea.optimization.master.evaluation as evaluation
import cea.optimization.supportFn as sFn
from cea.optimization.constants import *
import cea.optimization.master.cost_model as eM
import cea.optimization.slave.cooling_main as coolMain
import cea.optimization.slave.slave_main as sM
import cea.optimization.master.check as cCheck

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


# optimization

def individual_evaluation(individual, building_names, locator, extra_costs, extra_CO2, extra_primary_energy,
                          solar_features, network_features, gv, config, prices):
    """
    This function evaluates one supply system configuration of the case study.
    :param individual: a list that indicates the supply system configuration
    :type individual: list
    :param building_names: names of all building in the district
    :type building_names: ndarray
    :param locator:
    :param extra_costs: cost of decentralized supply systems
    :param extra_CO2: CO2 emission of decentralized supply systems
    :param extra_primary_energy: Primary energy of decentralized supply systems
    :param solar_features: Energy production potentials of solar technologies, including area of installed panels and annual production
    :type solar_features: dict
    :param network_features: hourly network operating conditions (thermal/pressure losses) and capital costs
    :type network_features: dict
    :param gv:
    :param config:
    :param prices:
    :return:
    """
    individual = evaluation.check_invalid(individual, len(building_names), config)

    # Initialize objective functions costs, CO2 and primary energy
    costs = extra_costs
    CO2 = extra_CO2
    prim = extra_primary_energy
    QUncoveredDesign = 0
    QUncoveredAnnual = 0

    # Create the string representation of the individual
    DHN_barcode, DCN_barcode, DHN_configuration, DCN_configuration = sFn.individual_to_barcode(individual,
                                                                                               building_names)

    # read the total loads from buildings connected to thermal networks
    if DHN_barcode.count("1") == gv.num_tot_buildings:
        network_file_name_heating = "Network_summary_result_all.csv"
        Q_DHNf_W = pd.read_csv(locator.get_optimization_network_all_results_summary('all'), usecols=["Q_DHNf_W"]).values
        Q_heating_max_W = Q_DHNf_W.max()
    elif DHN_barcode.count("1") == 0:
        network_file_name_heating = "Network_summary_result_none.csv"
        Q_heating_max_W = 0
    else:
        network_file_name_heating = "Network_summary_result_" + hex(int(str(DHN_barcode), 2)) + ".csv"
        Q_DHNf_W = pd.read_csv(locator.get_optimization_network_results_summary(DHN_barcode),
                               usecols=["Q_DHNf_W"]).values
        Q_heating_max_W = Q_DHNf_W.max()

    if DCN_barcode.count("1") == gv.num_tot_buildings:
        network_file_name_cooling = "Network_summary_result_all.csv"
                    N_HEAT * 2] == 1:  # if heat recovery is ON, then only need to satisfy cooling load of space cooling and refrigeration
            Q_DCNf_W = pd.read_csv(locator.get_optimization_network_all_results_summary('all'),
                                   usecols=["Q_DCNf_space_cooling_and_refrigeration_W"]).values
        else:
            Q_DCNf_W = pd.read_csv(locator.get_optimization_network_all_results_summary('all'),
                                   usecols=["Q_DCNf_space_cooling_data_center_and_refrigeration_W"]).values
        Q_cooling_max_W = Q_DCNf_W.max()
    elif DCN_barcode.count("1") == 0:
        network_file_name_cooling = "Network_summary_result_none.csv"
        Q_cooling_max_W = 0
    else:
        network_file_name_cooling = "Network_summary_result_" + hex(int(str(DCN_barcode), 2)) + ".csv"

        if individual[
                    N_HEAT * 2] == 1:  # if heat recovery is ON, then only need to satisfy cooling load of space cooling and refrigeration
            Q_DCNf_W = pd.read_csv(locator.get_optimization_network_results_summary(DCN_barcode),
                                   usecols=["Q_DCNf_space_cooling_and_refrigeration_W"]).values
        else:
            Q_DCNf_W = pd.read_csv(locator.get_optimization_network_results_summary(DCN_barcode),
                                   usecols=["Q_DCNf_space_cooling_data_center_and_refrigeration_W"]).values
        Q_cooling_max_W = Q_DCNf_W.max()

    Q_heating_nom_W = Q_heating_max_W * (1 + Q_MARGIN_FOR_NETWORK)
    Q_cooling_nom_W = Q_cooling_max_W * (1 + Q_MARGIN_FOR_NETWORK)

    # Modify the individual with the extra GHP constraint
    try:
        cCheck.GHPCheck(individual, locator, Q_heating_nom_W, gv)
    except:
        print "No GHP constraint check possible \n"

    # Export to context
    ind_num = 1
    gen = 1
    master_to_slave_vars = evaluation.calc_master_to_slave_variables(individual, Q_heating_max_W, Q_cooling_max_W,
                                                                     building_names, ind_num, gen)
    master_to_slave_vars.network_data_file_heating = network_file_name_heating
    master_to_slave_vars.network_data_file_cooling = network_file_name_cooling
    master_to_slave_vars.total_buildings = len(building_names)

    if master_to_slave_vars.number_of_buildings_connected_heating > 1:
        if DHN_barcode.count("0") == 0:
            master_to_slave_vars.fNameTotalCSV = locator.get_total_demand()
        else:
            master_to_slave_vars.fNameTotalCSV = os.path.join(locator.get_optimization_network_totals_folder(),
                                                              "Total_%(DHN_barcode)s.csv" % locals())
    else:
        master_to_slave_vars.fNameTotalCSV = locator.get_optimization_substations_total_file(DHN_barcode)

    if master_to_slave_vars.number_of_buildings_connected_cooling > 1:
        if DCN_barcode.count("0") == 0:
            master_to_slave_vars.fNameTotalCSV = locator.get_total_demand()
        else:
            master_to_slave_vars.fNameTotalCSV = os.path.join(locator.get_optimization_network_totals_folder(),
                                                              "Total_%(DCN_barcode)s.csv" % locals())
    else:
        master_to_slave_vars.fNameTotalCSV = locator.get_optimization_substations_total_file(DCN_barcode)

    # slave optimization of heating networks
    if config.optimization.isheating:
        if DHN_barcode.count("1") > 0:
            (slavePrim, slaveCO2, slaveCosts, QUncoveredDesign, QUncoveredAnnual) = sM.slave_main(locator,
                                                                                                  master_to_slave_vars,
                                                                                                  solar_features, gv,
                                                                                                  config, prices)
        else:
            slaveCO2 = 0
            slaveCosts = 0
            slavePrim = 0
    else:
        slaveCO2 = 0
        slaveCosts = 0
        slavePrim = 0

    costs += slaveCosts
    CO2 += slaveCO2
    prim += slavePrim

    print "Add extra costs"
    (addCosts, addCO2, addPrim) = eM.addCosts(DHN_barcode, DCN_barcode, building_names, locator, master_to_slave_vars,
                                              QUncoveredDesign, QUncoveredAnnual, solar_features, network_features, gv,
                                              config, prices)

    # FIXME: recalculate the addCosts by substracting the decentralized costs and add back to corresponding supply system

    # slave optimization of cooling networks
    if gv.ZernezFlag == 1:
        coolCosts, coolCO2, coolPrim = 0, 0, 0
    elif config.optimization.iscooling and DCN_barcode.count("1") > 0:
        (coolCosts, coolCO2, coolPrim) = coolMain.coolingMain(locator, master_to_slave_vars, network_features, gv,
                                                              prices, config)
    else:
        coolCosts, coolCO2, coolPrim = 0, 0, 0

    costs += addCosts + coolCosts
    CO2 += addCO2 + coolCO2
    prim += addPrim + coolPrim
    # Converting costs into float64 to avoid longer values
    costs = np.float64(costs)
    CO2 = np.float64(CO2)
    prim = np.float64(prim)

    print ('Additional costs = ' + str(addCosts))
    print ('Additional CO2 = ' + str(addCO2))
    print ('Additional prim = ' + str(addPrim))

    print ('Total costs = ' + str(costs))
    print ('Total CO2 = ' + str(CO2))
    print ('Total prim = ' + str(prim))

    return costs, CO2, prim, master_to_slave_vars, individual


def calc_decentralized_building_costs(config, locator, master_to_slave_vars, DHN_barcode, DCN_barcode, buildList):
    CostDiscBuild = 0
    CO2DiscBuild = 0
    PrimDiscBuild = 0
    nBuildinNtw = len(buildList)

    if config.optimization.isheating:
        for (index, building_name) in zip(DHN_barcode, buildList):
            if index == "0":
                df = pd.read_csv(locator.get_optimization_disconnected_folder_building_result_heating(building_name))
                dfBest = df[df["Best configuration"] == 1]
                CostDiscBuild += dfBest["Annualized Investment Costs [CHF]"].iloc[0]  # [CHF]
                CO2DiscBuild += dfBest["CO2 Emissions [kgCO2-eq]"].iloc[0]  # [kg CO2]
                PrimDiscBuild += dfBest["Primary Energy Needs [MJoil-eq]"].iloc[0]  # [MJ-oil-eq]
            else:
                nBuildinNtw += 1
    if config.optimization.iscooling:
        PV_barcode = ''
        for (index, building_name) in zip(DCN_barcode, buildList):
            if index == "0":  # choose the best decentralized configuration
                df = pd.read_csv(locator.get_optimization_disconnected_folder_building_result_cooling(building_name,
                                                                                                      configuration='AHU_ARU_SCU'))
                dfBest = df[df["Best configuration"] == 1]
                CostDiscBuild += dfBest["Annualized Investment Costs [CHF]"].iloc[0]  # [CHF]
                CO2DiscBuild += dfBest["CO2 Emissions [kgCO2-eq]"].iloc[0]  # [kg CO2]
                PrimDiscBuild += dfBest["Primary Energy Needs [MJoil-eq]"].iloc[0]  # [MJ-oil-eq]
                to_PV = 1
                if dfBest["single effect ACH to AHU_ARU_SCU Share"].iloc[0] == 1:
                    to_PV = 0
                if dfBest["double effect ACH to AHU_ARU_SCU Share"].iloc[0] == 1:
                    to_PV = 0
                if dfBest["single effect ACH to SCU Share"].iloc[0] == 1:
                    to_PV = 0


            else:  # adding costs for buildings in which the centralized plant provides a part of the load requirements
                DCN_unit_configuration = master_to_slave_vars.DCN_supplyunits
                if DCN_unit_configuration == 1:  # corresponds to AHU in the central plant, so remaining load need to be provided by decentralized plant
                    decentralized_configuration = 'ARU_SCU'
                    df = pd.read_csv(
                        locator.get_optimization_disconnected_folder_building_result_cooling(building_name,
                                                                                             decentralized_configuration))
                    dfBest = df[df["Best configuration"] == 1]
                    CostDiscBuild += dfBest["Annualized Investment Costs [CHF]"].iloc[0]  # [CHF]
                    CO2DiscBuild += dfBest["CO2 Emissions [kgCO2-eq]"].iloc[0]  # [kg CO2]
                    PrimDiscBuild += dfBest["Primary Energy Needs [MJoil-eq]"].iloc[0]  # [MJ-oil-eq]
                    to_PV = 1
                    if dfBest["single effect ACH to ARU_SCU Share"].iloc[0] == 1:
                        to_PV = 0
                    if dfBest["double effect ACH to ARU_SCU Share"].iloc[0] == 1:
                        to_PV = 0

                if DCN_unit_configuration == 2:  # corresponds to ARU in the central plant, so remaining load need to be provided by decentralized plant
                    decentralized_configuration = 'AHU_SCU'
                    df = pd.read_csv(
                        locator.get_optimization_disconnected_folder_building_result_cooling(building_name,
                                                                                             decentralized_configuration))
                    dfBest = df[df["Best configuration"] == 1]
                    CostDiscBuild += dfBest["Annualized Investment Costs [CHF]"].iloc[0]  # [CHF]
                    CO2DiscBuild += dfBest["CO2 Emissions [kgCO2-eq]"].iloc[0]  # [kg CO2]
                    PrimDiscBuild += dfBest["Primary Energy Needs [MJoil-eq]"].iloc[0]  # [MJ-oil-eq]
                    to_PV = 1
                    if dfBest["single effect ACH to AHU_SCU Share"].iloc[0] == 1:
                        to_PV = 0
                    if dfBest["double effect ACH to AHU_SCU Share"].iloc[0] == 1:
                        to_PV = 0

                if DCN_unit_configuration == 3:  # corresponds to SCU in the central plant, so remaining load need to be provided by decentralized plant
                    decentralized_configuration = 'AHU_ARU'
                    df = pd.read_csv(
                        locator.get_optimization_disconnected_folder_building_result_cooling(building_name,
                                                                                             decentralized_configuration))
                    dfBest = df[df["Best configuration"] == 1]
                    CostDiscBuild += dfBest["Annualized Investment Costs [CHF]"].iloc[0]  # [CHF]
                    CO2DiscBuild += dfBest["CO2 Emissions [kgCO2-eq]"].iloc[0]  # [kg CO2]
                    PrimDiscBuild += dfBest["Primary Energy Needs [MJoil-eq]"].iloc[0]  # [MJ-oil-eq]
                    to_PV = 1
                    if dfBest["single effect ACH to AHU_ARU Share"].iloc[0] == 1:
                        to_PV = 0
                    if dfBest["double effect ACH to AHU_ARU Share"].iloc[0] == 1:
                        to_PV = 0

                if DCN_unit_configuration == 4:  # corresponds to AHU + ARU in the central plant, so remaining load need to be provided by decentralized plant
                    decentralized_configuration = 'SCU'
                    df = pd.read_csv(
                        locator.get_optimization_disconnected_folder_building_result_cooling(building_name,
                                                                                             decentralized_configuration))
                    dfBest = df[df["Best configuration"] == 1]
                    CostDiscBuild += dfBest["Annualized Investment Costs [CHF]"].iloc[0]  # [CHF]
                    CO2DiscBuild += dfBest["CO2 Emissions [kgCO2-eq]"].iloc[0]  # [kg CO2]
                    PrimDiscBuild += dfBest["Primary Energy Needs [MJoil-eq]"].iloc[0]  # [MJ-oil-eq]
                    to_PV = 1
                    if dfBest["single effect ACH to SCU Share"].iloc[0] == 1:
                        to_PV = 0
                    if dfBest["double effect ACH to SCU Share"].iloc[0] == 1:
                        to_PV = 0

                if DCN_unit_configuration == 5:  # corresponds to AHU + SCU in the central plant, so remaining load need to be provided by decentralized plant
                    decentralized_configuration = 'ARU'
                    df = pd.read_csv(
                        locator.get_optimization_disconnected_folder_building_result_cooling(building_name,
                                                                                             decentralized_configuration))
                    dfBest = df[df["Best configuration"] == 1]
                    CostDiscBuild += dfBest["Annualized Investment Costs [CHF]"].iloc[0]  # [CHF]
                    CO2DiscBuild += dfBest["CO2 Emissions [kgCO2-eq]"].iloc[0]  # [kg CO2]
                    PrimDiscBuild += dfBest["Primary Energy Needs [MJoil-eq]"].iloc[0]  # [MJ-oil-eq]
                    to_PV = 1
                    if dfBest["single effect ACH to ARU Share"].iloc[0] == 1:
                        to_PV = 0
                    if dfBest["double effect ACH to ARU Share"].iloc[0] == 1:
                        to_PV = 0

                if DCN_unit_configuration == 6:  # corresponds to ARU + SCU in the central plant, so remaining load need to be provided by decentralized plant
                    decentralized_configuration = 'AHU'
                    df = pd.read_csv(
                        locator.get_optimization_disconnected_folder_building_result_cooling(building_name,
                                                                                             decentralized_configuration))
                    dfBest = df[df["Best configuration"] == 1]
                    CostDiscBuild += dfBest["Annualized Investment Costs [CHF]"].iloc[0]  # [CHF]
                    CO2DiscBuild += dfBest["CO2 Emissions [kgCO2-eq]"].iloc[0]  # [kg CO2]
                    PrimDiscBuild += dfBest["Primary Energy Needs [MJoil-eq]"].iloc[0]  # [MJ-oil-eq]
                    to_PV = 1
                    if dfBest["single effect ACH to AHU Share"].iloc[0] == 1:
                        to_PV = 0
                    if dfBest["double effect ACH to AHU Share"].iloc[0] == 1:
                        to_PV = 0

                if DCN_unit_configuration == 7:  # corresponds to AHU + ARU + SCU from central plant
                    to_PV = 1

                nBuildinNtw += 1
            PV_barcode = PV_barcode + str(to_PV)

    costs_discentralized_buildings = {'CostDiscBuild': CostDiscBuild, 'CO2DiscBuild': CO2DiscBuild,
                                      'PrimDiscBuild': PrimDiscBuild}

    return costs_discentralized_buildings


# ============================
# test
# ============================


def main(config):
    """
    run the whole optimization routine
    """
    gv = cea.globalvar.GlobalVariables()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    weather_file = config.weather

    try:
        if not demand_files_exist(config, locator):
            raise ValueError("Missing demand data of the scenario. Consider running demand script first")

        if not os.path.exists(locator.get_total_demand()):
            raise ValueError("Missing total demand of the scenario. Consider running demand script first")

        if not os.path.exists(locator.PV_totals()):
            raise ValueError("Missing PV potential of the scenario. Consider running photovoltaic script first")

        if config.optimization.isheating:
            if not os.path.exists(locator.PVT_totals()):
                raise ValueError(
                    "Missing PVT potential of the scenario. Consider running photovoltaic-thermal script first")

        if not os.path.exists(locator.SC_totals(panel_type='FP')):
            raise ValueError(
                "Missing SC potential of panel type 'FP' of the scenario. Consider running solar-collector script first with panel_type as SC1 and t-in-SC as 75")

        if not os.path.exists(locator.SC_totals(panel_type='ET')):
            raise ValueError(
                "Missing SC potential of panel type 'ET' of the scenario. Consider running solar-collector script first with panel_type as SC2 and t-in-SC as 150")

        if not os.path.exists(locator.get_sewage_heat_potential()):
            raise ValueError(
                "Missing sewage potential of the scenario. Consider running sewage heat exchanger script first")

        if not os.path.exists(locator.get_optimization_network_edge_list_file(config.thermal_network.network_type, '')):
            raise ValueError("Missing network edge list. Consider running thermal network script first")
    except ValueError as err:
        import sys
        print(err.message)
        sys.exit(1)

    # read total demand file and names and number of all buildings
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    gv.num_tot_buildings = total_demand.Name.count()
    prices = Prices(locator, config)

    # pre-process information regarding resources and technologies (they are treated before the optimization)
    # optimize best systems for every individual building (they will compete against a district distribution solution)
    extra_costs, extra_CO2, extra_primary_energy, solarFeat = preproccessing(locator, total_demand, building_names,
                                                                             weather_file, gv, config, prices)

    # optimize the distribution and linearize the results(at the moment, there is only a linearization of values in Zug)
    network_features = network_opt.network_opt_main(config, locator)

    # heating technologies at the centralized plant
    heating_block = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 90.0, 6]
    # FIXME: connect PV to config
    # cooling technologies at the centralized plant
    centralized_vcc_size = config.supply_system_simulation.centralized_vcc
    centralized_ach_size = config.supply_system_simulation.centralized_ach
    centralized_storage_size = config.supply_system_simulation.centralized_storage
    cooling_block = [0, 0, 0, 0, 0, 0, 0, 0, 6, 1]
    cooling_block[2:4] = [1, centralized_vcc_size] if (centralized_vcc_size != 0) else [0, 0]
    cooling_block[4:6] = [1, centralized_ach_size] if (centralized_ach_size != 0) else [0, 0]
    cooling_block[6:8] = [1, centralized_storage_size] if (centralized_storage_size != 0) else [0, 0]

    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    dc_connected_buildings = config.supply_system_simulation.dc_connected_buildings

    # buildings connected to networks
    heating_network = [0] * building_names.size
    cooling_network = [0] * building_names.size
    for building in dc_connected_buildings:
        index = np.where(building_names == building)[0][0]
        cooling_network[index] = 1

    individual = heating_block + cooling_block + heating_network + cooling_network
    individual_evaluation(individual, building_names, locator, extra_costs, extra_CO2, extra_primary_energy,
                          solarFeat, network_features, gv, config, prices)

    print 'individual evaluation succeeded'


def demand_files_exist(config, locator):
    # verify that the necessary demand files exist
    return all(os.path.exists(locator.get_demand_results_file(building_name)) for building_name in
               locator.get_zone_building_names())


if __name__ == '__main__':
    main(cea.config.Configuration())
