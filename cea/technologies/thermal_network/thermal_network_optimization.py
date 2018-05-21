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


def calc_Ctot_pump_netw(ntwFeat, gv, locator, prices, config):
    """
    Computes the total pump investment cost
    :type dicoSupply : class context
    :type ntwFeat : class ntwFeatures
    :rtype pumpCosts : float
    :returns pumpCosts: pumping cost
    """
    pumpCosts = 0
    network_type = config.thermal_network.network_type

    # read in node mass flows
    df = pd.read_csv(locator.get_node_mass_flow_csv_file(network_type, ''), index_col=0)
    mdotA_kgpers = np.array(df)
    mdotnMax_kgpers = np.amax(mdotA_kgpers) #find highest mass flow of all nodes at all timesteps (should be at plant)

    # read in total pressure loss in kW
    deltaP_kW = pd.read_csv(locator.get_ploss('', network_type))
    deltaP_kW = deltaP_kW['pressure_loss_total_kW'].sum()
    pumpCosts = deltaP_kW * prices.ELEC_PRICE

    if config.thermal_network.network_type == 'DH':
        deltaPmax = np.max(ntwFeat.DeltaP_DHN)
    else:
        deltaPmax = np.max(ntwFeat.DeltaP_DCN)

    Capex_a, Opex_fixed = pumps.calc_Cinv_pump(2*deltaPmax, mdotnMax_kgpers, PUMP_ETA, gv, locator, 'PU1')  # investment of Machinery
    pumpCosts += Opex_fixed

    return Capex_a, pumpCosts


def plant_location_cost_calculation(config, locator, building_index, Cost_storage, network_type):
    building_name = Cost_storage.columns(building_index)
    network_layout(config, locator, building_name, optimization_flag=True)
    thermal_network_matrix.main(config)

    ## Cost calculations
    prices = Prices(locator, config)
    network_features = network_opt.network_opt_main(config, locator)
    # calculate Network costs
    # OPEX neglected, see Documentation Master Thesis Lennart Rogenhofer
    if network_type == 'DH':
        Capex_a_netw = network_features.pipesCosts_DHN
    else:
        Capex_a_netw = network_features.pipesCosts_DCN
    # calculate Pressure loss and Pump costs
    Capex_a_pump, Opex_fixed_pump = calc_Ctot_pump_netw(network_features, gv, locator, prices, config)
    # calculate Heat loss costs
    if network_type == 'DH':
        # Assume a COP of 1 e.g. in CHP plant
        Opex_heat = network_features.thermallosses_DHN * prices.ELEC_PRICE
    else:
        # Assume a COp of 4 e.g.
        Opex_heat = network_features.thermallosses_DCN / 4 * prices.ELEC_PRICE

    Cost_storage[building_name]['Capex_total'] = Capex_a_netw + Capex_a_pump
    Cost_storage[building_name]['Opex_total'] = Opex_fixed_pump + Opex_heat
    Cost_storage[building_name]['Cost_total'] = Cost_storage['Capex_total'][building_name] + \
                                                Cost_storage['Opex_total'][building_name]

    return Cost_storage

# ============================
# test
# ============================


def main(config):
    """
    run the whole network summary routine
    """
    print('Running thermal_network plant location optimization for scenario %s' % config.scenario)
    start = time.time()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    gv = cea.globalvar.GlobalVariables()
    network_type = config.thermal_network.network_type

    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    num_tot_buildings = total_demand.Name.count()

    Cost_storage = pd.DataFrame(np.zeros((3, num_tot_buildings)))
    Cost_storage.columns = building_names
    Cost_storage.index = ['Capex_total', 'Opex_total', 'Cost_Total']


    for building_index in range(len(building_names)):
        Cost_storage = plant_location_cost_calculation(config, locator, building_index, Cost_storage, network_type)

    # output results file to csv
    # Sort values for easier evaluation
    Cost_storage = Cost_storage.reindex_axis(sorted(Cost_storage.columns, key=lambda x: float(x[1:])), axis=1)
    Cost_storage.to_csv(locator.get_optimization_network_plant_location_results_file(network_type))

    print('thermal_network_optimization_main() succeeded')
    print('total time: ', time.time() - start)

if __name__ == '__main__':
    main(cea.config.Configuration())