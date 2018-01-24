"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import json
import os
import cea.config
import cea.inputlocator
from cea.plots.optimization.pareto_capacity_installed import pareto_capacity_installed
import pandas as pd

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def data_processing(locator, analysis_fields, data_raw, individual):
    data_processed = []

    # get building names conneted to the network
    string_network = data_raw['disconnected_capacities'][individual]['network']
    list_building_names = [x['building_name'] for x in data_raw['disconnected_capacities'][individual]['disconnected_capacity']]
    buildings_connected = []
    for building, network in zip(list_building_names, string_network):
        if network == '1': # the building is connected
            buildings_connected.append(building)

    # get data about hourly demands in these buildings
    building_demands_df = pd.read_csv(locator.get_optimization_network_results_summary(string_network), usecols=analysis_fields)

    # get data about the activation patterns of these buildings
    individual_barcode_list = data_raw['population'][individual]
    individual_barcode_list_string = [str(round(ind,2)) if type(ind) == float else str(ind) for ind in individual_barcode_list]
    # Read individual and transform into a barcode of hegadecimal characters
    length_network = len(string_network)
    length_unit_activation = len(individual_barcode_list_string) - length_network
    unit_activation_barcode = "".join(individual_barcode_list_string[0:length_unit_activation])
    pop_individual_to_Hcode = hex(int(str(string_network), 2))
    pop_name_hex = unit_activation_barcode + pop_individual_to_Hcode

    # get data about the activation patterns of these buildings (main units)
    data_activation_path = os.path.join(locator.get_optimization_slave_results_folder(),
                                        pop_name_hex + '_PPActivationPattern.csv')
    df_PPA = pd.read_csv(data_activation_path)
    df_PPA['index'] = xrange(8760)

    # get data about the activation patterns of these buildings (storage)
    data_storage_path = os.path.join(locator.get_optimization_slave_results_folder(),
                                     pop_name_hex + '_StorageOperationData.csv')
    df_SO = pd.read_csv(data_storage_path)
    df_SO['index'] = xrange(8760)
    index = df_PPA['index']


    data_processed.append({'buildings_connected': buildings_connected, 'buildings_demand_W': building_demands_df,
                           'activation_units':data_activation_path})

    return data_processed


def dashboard(locator, config):
    # Local Variables
    generation = int(config.dashboard.generations[-1:][0]) # choose always the last one in the list
    individual = config.dashboard.individual

    # CREATE CAPACITY INSTALLED FOR INDIVIDUALS
    output_path = locator.get_timeseries_plots_file(
        "ind" + str(individual) + '_gen' + str(generation) + '_pareto_curve_capacity_installed')
    analysis_fields_units = ['Base_boiler_BG_capacity_W', 'Base_boiler_NG_capacity_W', 'CHP_BG_capacity_W',
                       'CHP_NG_capacity_W', 'Furnace_dry_capacity_W', 'Furnace_wet_capacity_W',
                       'GHP_capacity_W', 'HP_Lake_capacity_W', 'HP_Sewage_capacity_W',
                       'PVT_capacity_W', 'PV_capacity_W', 'Peak_boiler_BG_capacity_W',
                       'Peak_boiler_NG_capacity_W', 'SC_capacity_W',
                       'Disconnected_Boiler_BG_capacity_W',
                       'Disconnected_Boiler_NG_capacity_W',
                       'Disconnected_FC_capacity_W',
                       'Disconnected_GHP_capacity_W']
    anlysis_fields_loads = ['Electr_netw_total_W', 'Q_DCNf_W', 'Q_DHNf_W']
    title = 'Activation curve for Individual ' + str(individual) + " in generation " + str(generation)
    with open(locator.get_optimization_checkpoint(generation), "rb") as fp:
        data_raw = json.load(fp)
    data_processed = data_processing(locator, anlysis_fields_loads, data_raw, individual)
    pareto_capacity_installed(data_processed[-1:][0], analysis_fields_units, renewable_sources_fields, title, output_path)


def main(config):
    locator = cea.inputlocator.InputLocator(config.dashboard.scenario)

    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.dashboard.scenario)

    dashboard(locator, config)

if __name__ == '__main__':
    main(cea.config.Configuration())
