"""
hydraulic network
"""

from __future__ import division
import cea.technologies.thermal_network.thermal_network_matrix as thermal_network_matrix
from cea.technologies.thermal_network.network_layout.main import network_layout as network_layout
import cea.optimization.distribution.network_opt_main as network_opt
import cea.technologies.pumps as pumps
from cea.optimization.prices import Prices as Prices
import cea.config
import cea.globalvar
import cea.inputlocator
from cea.optimization.constants import PUMP_ETA

import pandas as pd
import numpy as np
import time

__author__ = "Lennart Rogenhofer"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Lennart Rogenhofer"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class Optimize_Network(object):
    """
    Storage of information for the network currently being calcuted.
    """
    def __init__(self, locator, config, network_type, gv):
        self.locator = locator
        self.config = config
        self.network_type = network_type

        self.network_name = ''
        self.cost_storage = None
        self.building_names = None
        self.number_of_buildings = 0
        self.gv = gv
        self.prices = None
        self.network_features = None


def calc_Ctot_pump_netw(optimal_plant_loc):
    """
    Computes the total pump investment and operational cost
    :type dicoSupply : class context
    :type ntwFeat : class ntwFeatures
    :rtype pumpCosts : float
    :returns pumpCosts: pumping cost
    """
    network_type = optimal_plant_loc.config.thermal_network.network_type

    # read in node mass flows
    df = pd.read_csv(optimal_plant_loc.locator.get_node_mass_flow_csv_file(network_type, ''), index_col=0)
    mdotA_kgpers = np.array(df)
    mdotnMax_kgpers = np.amax(mdotA_kgpers)  # find highest mass flow of all nodes at all timesteps (should be at plant)

    # read in total pressure loss in kW
    deltaP_kW = pd.read_csv(optimal_plant_loc.locator.get_ploss('', network_type))
    deltaP_kW = deltaP_kW['pressure_loss_total_kW'].sum()
    pumpCosts = deltaP_kW * optimal_plant_loc.prices.ELEC_PRICE

    if optimal_plant_loc.config.thermal_network.network_type == 'DH':
        deltaPmax = np.max(optimal_plant_loc.network_features.DeltaP_DHN)
    else:
        deltaPmax = np.max(optimal_plant_loc.network_features.DeltaP_DCN)

    Capex_a, Opex_fixed = pumps.calc_Cinv_pump(2 * deltaPmax, mdotnMax_kgpers, PUMP_ETA, optimal_plant_loc.gv,
                                               optimal_plant_loc.locator, 'PU1')  # investment of Machinery
    pumpCosts += Opex_fixed

    return Capex_a, pumpCosts


def plant_location_cost_calculation(building_index, optimal_plant_loc):
    """
    Main function which calculates opex and capex costs of the network. This is the value to be minimized.
    :param building_index: A value between 0 and the total number of buildings, indicating next to which building the plant is placed
    :param optimal_plant_loc: Object containing information of current network
    :return: Total cost, value to be minimized
    """
    building_name = optimal_plant_loc.cost_storage.columns[building_index]
    network_layout(optimal_plant_loc.config, optimal_plant_loc.locator, building_name, optimization_flag=True)
    thermal_network_matrix.main(optimal_plant_loc.config)

    ## Cost calculations
    optimal_plant_loc.prices = Prices(optimal_plant_loc.locator, optimal_plant_loc.config)
    optimal_plant_loc.network_features = network_opt.network_opt_main(optimal_plant_loc.config,
                                                                      optimal_plant_loc.locator)
    # calculate Network costs
    # OPEX neglected, see Documentation Master Thesis Lennart Rogenhofer
    if optimal_plant_loc.network_type == 'DH':
        Capex_a_netw = optimal_plant_loc.network_features.pipesCosts_DHN
    else:
        Capex_a_netw = optimal_plant_loc.network_features.pipesCosts_DCN
    # calculate Pressure loss and Pump costs
    Capex_a_pump, Opex_fixed_pump = calc_Ctot_pump_netw(optimal_plant_loc)
    # calculate Heat loss costs
    if optimal_plant_loc.network_type == 'DH':
        # Assume a COP of 1 e.g. in CHP plant
        Opex_heat = optimal_plant_loc.network_features.thermallosses_DHN * optimal_plant_loc.prices.ELEC_PRICE
    else:
        # Assume a COp of 4 e.g.
        Opex_heat = optimal_plant_loc.network_features.thermallosses_DCN / 4 * optimal_plant_loc.prices.ELEC_PRICE

    optimal_plant_loc.cost_storage[building_name]['Capex_total'] = Capex_a_netw + Capex_a_pump
    optimal_plant_loc.cost_storage[building_name]['Opex_total'] = Opex_fixed_pump + Opex_heat
    optimal_plant_loc.cost_storage[building_name]['Cost_total'] = optimal_plant_loc.cost_storage['Capex_total'][
                                                                      building_name] + \
                                                                  optimal_plant_loc.cost_storage['Opex_total'][
                                                                      building_name]
    return optimal_plant_loc.cost_storage[building_name]['Cost_total']


# ============================
# test
# ============================


def main(config):
    """
    runs an optimization calculation for the plant location in the thermal network.
    """
    print('Running thermal_network plant location optimization for scenario %s' % config.scenario)
    start = time.time()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    gv = cea.globalvar.GlobalVariables()
    network_type = config.thermal_network.network_type

    optimal_plant_loc = Optimize_Network(locator, config, network_type, gv)

    total_demand = pd.read_csv(locator.get_total_demand())
    optimal_plant_loc.building_names = total_demand.Name.values
    optimal_plant_loc.number_of_buildings = total_demand.Name.count()

    cost_storage = pd.DataFrame(np.zeros((3, optimal_plant_loc.number_of_buildings)))
    cost_storage.columns = optimal_plant_loc.building_names
    cost_storage.index = ['Capex_total', 'Opex_total', 'Cost_Total']
    optimal_plant_loc.cost_storage = cost_storage

    for building_index in range(optimal_plant_loc.number_of_buildings):
        total_cost = plant_location_cost_calculation(building_index, optimal_plant_loc)

    # output results file to csv
    # Sort values for easier evaluation
    optimal_plant_loc.cost_storag = optimal_plant_loc.cost_storag.reindex_axis(
        sorted(optimal_plant_loc.cost_storag.columns, key=lambda x: float(x[1:])), axis=1)
    optimal_plant_loc.cost_storag.to_csv(
        optimal_plant_loc.locator.get_optimization_network_plant_location_results_file(optimal_plant_loc.network_type))

    print('thermal_network_optimization_main() succeeded')
    print('total time: ', time.time() - start)


if __name__ == '__main__':
    main(cea.config.Configuration())
