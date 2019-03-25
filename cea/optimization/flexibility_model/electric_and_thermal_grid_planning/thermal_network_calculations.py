from __future__ import division
import time
from cea.optimization.flexibility_model.electric_and_thermal_grid_planning import process_results
from cea.optimization.flexibility_model.electric_and_thermal_grid_planning.electrical_grid_calculations import electrical_grid_calculations
import cea.globalvar
import cea.inputlocator
import cea.config
import pandas as pd
from distutils.dir_util import copy_tree
# from cea.technologies.thermal_network.network_layout.main import network_layout
from cea.optimization.flexibility_model.electric_and_thermal_grid_planning.network_layout_main import network_layout
from cea.technologies.thermal_network import thermal_network
from cea.technologies.thermal_network import thermal_network_costs

__author__ =  "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = [ "Sreepathi Bhargava Krishna", "Thanh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def thermal_network_calculations(individual, config, network_number, building_names, generation):
    # ============================
    # Solve the electrical grid problem, and decide on the best electrical line types and lengths. It is an optimization
    # problem for a fixed demand
    # ============================
    dict_connected = {}
    for i in range(len(building_names)):
        dict_connected[i] = individual[i]
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    copy_tree(locator.get_networks_folder(), locator.get_electric_networks_folder()) # resetting the streets layout to the scenario default

    m = electrical_grid_calculations(dict_connected, config, locator, network_number, generation)

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
    thermal_network.main(config)
    # total_annual_cost, total_annual_capex, total_annual_opex = 0.0, 0.0, 0.0
    network_type = config.thermal_network.network_type
    gv = cea.globalvar.GlobalVariables()
    network_info = thermal_network_costs.Thermal_Network(locator, config, network_type, gv)
    disconnected_buildings_index = []
    for i in range(len(individual)):
        if individual[i] == 0:
            disconnected_buildings_index.append(i)

    network_info.building_names = building_names
    network_info.number_of_buildings_in_district = len(building_names)
    network_info.disconnected_buildings_index = disconnected_buildings_index

    total_annual_cost, total_annual_capex, total_annual_opex, cost_storage_df = thermal_network_costs.calc_Ctot_cs_district(network_info)
    total_demand = pd.read_csv(locator.get_total_demand())
    length_m, average_diameter_m = thermal_network_costs.calc_network_size(network_info)

    if network_type == 'DC':
        annual_demand_district_MWh = total_demand['Qcs_sys_MWhyr'].sum()
        annual_demand_disconnected_MWh = 0
        for building_index in disconnected_buildings_index:
            annual_demand_disconnected_MWh += total_demand.ix[building_index, 'Qcs_sys_MWhyr']
        annual_demand_network_MWh = annual_demand_district_MWh - annual_demand_disconnected_MWh
    else:
        raise ValueError('This optimization procedure is not ready for district heating yet!')

    cost_output = {}
    cost_output['total_annual_cost'] = round(cost_storage_df.ix['total'][0], 2)
    cost_output['annual_opex'] = round(cost_storage_df.ix['opex'][0], 2)
    cost_output['annual_capex'] = round(cost_storage_df.ix['capex'][0], 2)
    cost_output['total_cost_per_MWh'] = round(cost_output['total_annual_cost'] / annual_demand_district_MWh, 2)
    cost_output['opex_per_MWh'] = round(cost_output['annual_opex'] / annual_demand_district_MWh, 2)
    cost_output['capex_per_MWh'] = round(cost_output['annual_capex'] / annual_demand_district_MWh, 2)
    cost_output['annual_demand_district_MWh'] = round(annual_demand_district_MWh, 2)
    cost_output['annual_demand_disconnected_MWh'] = round(annual_demand_disconnected_MWh, 2)
    cost_output['annual_demand_network_MWh'] = round(annual_demand_network_MWh, 2)
    cost_output['opex_plant'] = round(cost_storage_df.ix['opex_plant'][0], 2)
    cost_output['opex_pump'] = round(cost_storage_df.ix['opex_pump'][0], 2)
    cost_output['opex_hex'] = round(cost_storage_df.ix['opex_hex'][0], 2)
    cost_output['el_network_MWh'] = round(cost_storage_df.ix['el_network_MWh'][0], 2)
    cost_output['el_price'] = network_info.prices.ELEC_PRICE
    cost_output['capex_network'] = round(cost_storage_df.ix['capex_network'][0], 2)
    cost_output['capex_pumps'] = round(cost_storage_df.ix['capex_pump'][0], 2)
    cost_output['capex_hex'] = round(cost_storage_df.ix['capex_hex'][0], 2)
    cost_output['capex_chiller'] = round(cost_storage_df.ix['capex_chiller'][0], 2)
    cost_output['capex_CT'] = round(cost_storage_df.ix['capex_CT'][0], 2)
    cost_output['avg_diam_m'] = average_diameter_m
    cost_output['network_length_m'] = length_m
    cost_output = pd.DataFrame.from_dict(cost_output, orient='index').T
    cost_output.to_csv(locator.get_optimization_network_layout_costs_file_concept(config.thermal_network.network_type, network_number, generation))

    print (locator.get_optimization_network_layout_costs_file_concept(config.thermal_network.network_type, network_number, generation))
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
