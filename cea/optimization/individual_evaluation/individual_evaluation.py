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

def individual_evaluation(individual, building_names, locator, extra_costs, extra_CO2, extra_primary_energy, solar_features,
                          network_features, gv, config, prices):
    '''
    This function optimizes the conversion, storage and distribution systems of a heating distribution for the case study.
    It requires that solar technologies be calculated in advance and nodes of a distribution should have been already generated.

    :param locator: path to input locator
    :param weather_file: path to weather file
    :param gv: global variables class
    :type locator: string
    :type weather_file: string
    :type gv: class

    :returns: None
    :rtype: Nonetype
    '''
    individual = evaluation.check_invalid(individual, len(building_names), config)


    # Initialize objective functions costs, CO2 and primary energy
    costs = extra_costs
    CO2 = extra_CO2
    prim = extra_primary_energy
    QUncoveredDesign = 0
    QUncoveredAnnual = 0

    # Create the string representation of the individual
    DHN_barcode, DCN_barcode, DHN_configuration, DCN_configuration = sFn.individual_to_barcode(individual, building_names)

    if DHN_barcode.count("1") == gv.num_tot_buildings:
        network_file_name_heating = "Network_summary_result_all.csv"
        Q_DHNf_W = pd.read_csv(locator.get_optimization_network_all_results_summary('all'), usecols=["Q_DHNf_W"]).values
        Q_heating_max_W = Q_DHNf_W.max()
    elif DHN_barcode.count("1") == 0:
        network_file_name_heating = "Network_summary_result_none.csv"
        Q_heating_max_W = 0
    else:
        network_file_name_heating = "Network_summary_result_" + hex(int(str(DHN_barcode), 2)) + ".csv"
        Q_DHNf_W = pd.read_csv(locator.get_optimization_network_results_summary(DHN_barcode), usecols=["Q_DHNf_W"]).values
        Q_heating_max_W = Q_DHNf_W.max()

    if DCN_barcode.count("1") == gv.num_tot_buildings:
        network_file_name_cooling = "Network_summary_result_all.csv"
        if individual[N_HEAT * 2] == 1: # if heat recovery is ON, then only need to satisfy cooling load of space cooling and refrigeration
            Q_DCNf_W = pd.read_csv(locator.get_optimization_network_all_results_summary('all'), usecols=["Q_DCNf_space_cooling_and_refrigeration_W"]).values
        else:
            Q_DCNf_W = pd.read_csv(locator.get_optimization_network_all_results_summary('all'), usecols=["Q_DCNf_space_cooling_data_center_and_refrigeration_W"]).values
        Q_cooling_max_W = Q_DCNf_W.max()
    elif DCN_barcode.count("1") == 0:
        network_file_name_cooling = "Network_summary_result_none.csv"
        Q_cooling_max_W = 0
    else:
        network_file_name_cooling = "Network_summary_result_" + hex(int(str(DCN_barcode), 2)) + ".csv"

        if individual[N_HEAT * 2] == 1: # if heat recovery is ON, then only need to satisfy cooling load of space cooling and refrigeration
            Q_DCNf_W = pd.read_csv(locator.get_optimization_network_results_summary(DCN_barcode), usecols=["Q_DCNf_space_cooling_and_refrigeration_W"]).values
        else:
            Q_DCNf_W = pd.read_csv(locator.get_optimization_network_results_summary(DCN_barcode), usecols=["Q_DCNf_space_cooling_data_center_and_refrigeration_W"]).values
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
    master_to_slave_vars = evaluation.calc_master_to_slave_variables(individual, Q_heating_max_W, Q_cooling_max_W, building_names, ind_num, gen)
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

    if config.optimization.isheating:

        if DHN_barcode.count("1") > 0:

            (slavePrim, slaveCO2, slaveCosts, QUncoveredDesign, QUncoveredAnnual) = sM.slave_main(locator,
                                                                                                  master_to_slave_vars,
                                                                                                  solar_features, gv, config, prices)
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
    (addCosts, addCO2, addPrim) = eM.addCosts(DHN_barcode, DCN_barcode, building_names, locator, master_to_slave_vars, QUncoveredDesign,
                                              QUncoveredAnnual, solar_features, network_features, gv, config, prices)

    if gv.ZernezFlag == 1:
        coolCosts, coolCO2, coolPrim = 0, 0, 0
    elif config.optimization.iscooling and DCN_barcode.count("1") > 0:
        (coolCosts, coolCO2, coolPrim) = coolMain.coolingMain(locator, master_to_slave_vars, network_features, gv, prices, config)
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

        if not os.path.exists(locator.PVT_totals()):
            raise ValueError("Missing PVT potential of the scenario. Consider running photovoltaic-thermal script first")
        if not os.path.exists(locator.SC_totals(panel_type = 'FP')):
            raise ValueError(
                "Missing SC potential of panel type 'FP' of the scenario. Consider running solar-collector script first with panel_type as SC1 and t-in-SC as 75")

        if not os.path.exists(locator.SC_totals(panel_type = 'ET')):
            raise ValueError(
                "Missing SC potential of panel type 'ET' of the scenario. Consider running solar-collector script first with panel_type as SC2 and t-in-SC as 150")

        if not os.path.exists(locator.get_sewage_heat_potential()):
            raise ValueError("Missing sewage potential of the scenario. Consider running sewage heat exchanger script first")

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
                                                                             weather_file, gv, config,
                                                                             prices)

    # optimize the distribution and linearize the results(at the moment, there is only a linearization of values in Zug)
    network_features = network_opt.network_opt_main(config, locator)
    # TODO: connect to interface (config)
    heating_block = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 90.0, 6]
    cooling_block = [0, 0, 0, 0, 0, 0, 0, 0, 6, 1]
    heating_network = []
    cooling_network = []
    for i in range(gv.num_tot_buildings):
        heating_network.append(0)
        cooling_network.append(1)

    individual = heating_block + cooling_block + heating_network + cooling_network


    individual_evaluation(individual, building_names, locator, extra_costs,
                                                      extra_CO2,
                                                      extra_primary_energy,
                                                      solarFeat,
                                                      network_features, gv, config,
                                                      prices)



    print 'test_optimization_main() succeeded'

def demand_files_exist(config, locator):
    # verify that the necessary demand files exist
    return all(os.path.exists(locator.get_demand_results_file(building_name)) for building_name in locator.get_zone_building_names())

if __name__ == '__main__':
    main(cea.config.Configuration())
