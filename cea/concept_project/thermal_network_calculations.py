from __future__ import division
import time
from cea.concept_project import process_results
from cea.concept_project.electrical_grid_calculations import electrical_grid_calculations
import cea.globalvar
import cea.inputlocator
import cea.config
import pandas as pd
from distutils.dir_util import copy_tree
# from cea.technologies.thermal_network.network_layout.main import network_layout
from cea.concept_project.network_layout_main import network_layout
from cea.technologies.thermal_network import thermal_network_matrix
from cea.technologies.thermal_network import thermal_network_costs

def thermal_network_calculations(individual, config, network_number, building_names):
    # ============================
    # Solve the electrical grid problem, and decide on the best electrical line types and lengths. It is an optimization
    # problem for a fixed demand
    # ============================
    dict_connected = {}
    for i in range(len(building_names)):
        dict_connected[i] = individual[i]
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    copy_tree(locator.get_networks_folder(), locator.get_electric_networks_folder()) # resetting the streets layout to the scenario default

    m = electrical_grid_calculations(dict_connected, config, locator)

    electrical_grid_file_name = 'electrical_grid'
    thermal_network_file_name = 'electrical_grid_as_streets'
    default_streets_file_name = 'streets'

    input_path_name = electrical_grid_file_name

    # ============================
    # Create shape file of the thermal network based on the buildings connected, which is further processed
    # ============================
    process_results.creating_thermal_network_shape_file_main(m, electrical_grid_file_name, thermal_network_file_name, config, locator, dict_connected)

    connected_building_names = []  # Placeholder, this is only used in Network optimization
    network_layout(config, locator, connected_building_names, input_path_name)
    # thermal_network_matrix.main(config)
    total_annual_cost, total_annual_capex, total_annual_opex = 0.0, 0.0, 0.0
    # total_annual_cost, total_annual_capex, total_annual_opex = thermal_network_costs.main(dict_connected, config, network_number)
    print total_annual_cost, total_annual_capex, total_annual_opex

    return total_annual_cost, total_annual_capex, total_annual_opex

def main(config):

    dict_connected = [{0: 1, 1: 1, 2: 0, 3: 1, 4: 0, 5: 1, 6: 0, 7: 1, 8: 1, 9: 1}
                      # {0: 0, 1: 1, 2: 0, 3: 1, 4: 0, 5: 1, 6: 0, 7: 1, 8: 1, 9: 0},
                      # # {0: 0, 1: 1, 2: 0, 3: 1, 4: 0, 5: 1, 6: 0, 7: 1, 8: 1, 9: 1},
                      # # {0: 0, 1: 1, 2: 0, 3: 1, 4: 0, 5: 1, 6: 1, 7: 1, 8: 1, 9: 0},
                      # # {0: 0, 1: 1, 2: 0, 3: 1, 4: 1, 5: 1, 6: 0, 7: 1, 8: 1, 9: 0},
                      # # {0: 0, 1: 1, 2: 1, 3: 1, 4: 0, 5: 1, 6: 0, 7: 1, 8: 1, 9: 0},
                      # {0: 1, 1: 0, 2: 0, 3: 1, 4: 0, 5: 1, 6: 0, 7: 0, 8: 0, 9: 0}
                      ]

    t0 = time.clock()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    for i in range(len(dict_connected)):
        network_number = i
        thermal_network_calculations(dict_connected[i], config, network_number, building_names)
    print 'main() succeeded'
    print 'total time: ', time.clock() - t0


if __name__ == '__main__':
    main(cea.config.Configuration())
