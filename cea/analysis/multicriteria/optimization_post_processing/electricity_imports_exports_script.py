"""
Electricity imports and exports script

This file takes in the values of the electricity activation pattern (which is only considering buildings present in
network and corresponding district energy systems) and adds in the electricity requirement of decentralized buildings
and recalculates the imports from grid and exports to the grid
"""
from __future__ import division
from __future__ import print_function

import os
import pandas as pd
import numpy as np
import cea.config
import cea.inputlocator
from cea.optimization.lca_calculations import lca_calculations

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def electricity_import_and_exports(generation, individual, locator, config):
    category = "optimization-detailed"

    data_network_electricity = pd.read_csv(os.path.join(
        locator.get_optimization_slave_electricity_activation_pattern_cooling(individual, generation)))

    data_cooling = pd.read_csv(
        os.path.join(locator.get_optimization_slave_cooling_activation_pattern(individual, generation)))

    all_individuals_of_generation = pd.read_csv(locator.get_optimization_individuals_in_generation(generation))

    data_current_individual = all_individuals_of_generation[np.isclose(all_individuals_of_generation['individual'], individual)]
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values

    total_electricity_demand_W= data_network_electricity['E_total_req_W']
    E_decentralized_appliances_W = np.zeros(8760)

    DCN_barcode = ""
    for name in building_names: # identifying the DCN code
        DCN_barcode += str(int(data_current_individual[name + ' DCN'].values[0]))

    for i, name in zip(DCN_barcode, building_names): # adding the electricity demand from the decentralized buildings
        if i is '0':
            building_demand = pd.read_csv(locator.get_demand_results_folder() + '//' + name + ".csv",
                                          usecols=['E_sys_kWh'])

            E_decentralized_appliances_W += building_demand['E_sys_kWh']*1000

    total_electricity_demand_W = total_electricity_demand_W.add(E_decentralized_appliances_W)

    E_for_hot_water_demand_W = np.zeros(8760)

    for i, name in zip(DCN_barcode, building_names): # adding the electricity demand for hot water from all buildings
        building_demand = pd.read_csv(locator.get_demand_results_folder() + '//' + name + ".csv",
                                      usecols=['E_ww_kWh'])

        E_for_hot_water_demand_W += building_demand['E_ww_kWh']*1000

    total_electricity_demand_W = total_electricity_demand_W.add(E_for_hot_water_demand_W)
    # Electricity of Energy Systems
    lca = lca_calculations(locator, config)

    E_VCC_W = data_cooling['Opex_var_VCC'] / lca.ELEC_PRICE
    E_VCC_backup_W = data_cooling['Opex_var_VCC_backup'] / lca.ELEC_PRICE
    E_ACH_W = data_cooling['Opex_var_ACH'] / lca.ELEC_PRICE
    E_CT_W = abs(data_cooling['Opex_var_CT']) / lca.ELEC_PRICE
    total_electricity_demand_W = total_electricity_demand_W.add(E_VCC_W)
    total_electricity_demand_W = total_electricity_demand_W.add(E_VCC_backup_W)
    total_electricity_demand_W = total_electricity_demand_W.add(E_ACH_W)
    total_electricity_demand_W = total_electricity_demand_W.add(E_CT_W)

    E_from_CHP_W = data_network_electricity['E_CHP_to_directload_W'] + data_network_electricity['E_CHP_to_grid_W']
    E_from_PV_W = data_network_electricity['E_PV_to_directload_W'] + data_network_electricity['E_PV_to_grid_W']

    E_CHP_to_directload_W = np.zeros(8760)
    E_CHP_to_grid_W = np.zeros(8760)
    E_PV_to_directload_W = np.zeros(8760)
    E_PV_to_grid_W = np.zeros(8760)
    E_from_grid_W = np.zeros(8760)

    for hour in range(8760):
        E_hour_W = total_electricity_demand_W[hour]
        if E_hour_W > 0:
            if E_from_PV_W[hour] > E_hour_W:
                E_PV_to_directload_W[hour] = E_hour_W
                E_PV_to_grid_W[hour] = E_from_PV_W[hour] - total_electricity_demand_W[hour]
                E_hour_W = 0
            else:
                E_hour_W = E_hour_W - E_from_PV_W[hour]
                E_PV_to_directload_W[hour] = E_from_PV_W[hour]

            if E_from_CHP_W[hour] > E_hour_W:
                E_CHP_to_directload_W[hour] = E_hour_W
                E_CHP_to_grid_W[hour] = E_from_CHP_W[hour] - E_hour_W
                E_hour_W = 0
            else:
                E_hour_W = E_hour_W - E_from_CHP_W[hour]
                E_CHP_to_directload_W[hour] = E_from_CHP_W[hour]

            E_from_grid_W[hour] = E_hour_W

    date = data_network_electricity.DATE.values

    results = pd.DataFrame({"DATE": date,
                            "E_total_req_W": total_electricity_demand_W,
                            "E_from_grid_W": E_from_grid_W,
                            "E_VCC_W": E_VCC_W,
                            "E_VCC_backup_W": E_VCC_backup_W,
                            "E_ACH_W": E_ACH_W,
                            "E_CT_W": E_CT_W,
                            "E_PV_to_directload_W": E_PV_to_directload_W,
                            "E_CHP_to_directload_W": E_CHP_to_directload_W,
                            "E_CHP_to_grid_W": E_CHP_to_grid_W,
                            "E_PV_to_grid_W": E_PV_to_grid_W,
                            "E_for_hot_water_demand_W": E_for_hot_water_demand_W,
                            "E_decentralized_appliances_W": E_decentralized_appliances_W,
                            "E_total_to_grid_W_negative": - E_PV_to_grid_W - E_CHP_to_grid_W}) #let's keep this negative so it is something exported, we can use it in the graphs of likelihood

    results.to_csv(
        locator.get_optimization_slave_electricity_activation_pattern_processed(individual, generation, category), index=False)

    return  results

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    generation = 25
    individual = 10
    print("Calculating imports and exports of individual" + str(individual) + " of generation " + str(generation))

    electricity_import_and_exports(generation, individual, locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())