"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import json

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

    #get data about hourly demands in these buildings
    # for i, building in enumerate(buildings_connected):
    #     if i == 0:
    #         building_demands_df = pd.read_csv(locator.get_demand_results_file(building))
    #     else:
    #         df2 = pd.read_csv(locator.get_demand_results_file(building))
    #         for field in analysis_fields:
    #             building_demands_df[field] = building_demands_df[field].values + df2[field].values

    # get data abotu the activation patterns of these buildings
    individual_barcode_list = data_raw['population'][individual]
    ntwList = data['networkList']
    pop_individual = [str(pop[individual][i])]


    for i in xrange(len(pop[individual])):
        if type(pop[individual][i]) is float:
            pop_individual.append((str(pop[individual][i])[0:4]))
        else:
            pop_individual.append(str(pop[individual][i]))

    # Read individual and transform into a barcode of hegadecimal characters
    individual_barcode = sFn.individual_to_barcode(pop_individual)
    length_network = len(individual_barcode)
    length_unit_activation = len(pop_individual) - length_network
    unit_activation_barcode = "".join(pop_individual[0:length_unit_activation])
    pop_individual_to_Hcode = hex(int(str(individual_barcode), 2))
    pop_name_hex = unit_activation_barcode + pop_individual_to_Hcode

    data_activation_path = os.path.join(locator.get_optimization_slave_results_folder(),
                                        pop_name_hex + '_PPActivationPattern.csv')
    df_PPA = pd.read_csv(data_activation_path)
    df_PPA['index'] = xrange(8760)

    data_storage_path = os.path.join(locator.get_optimization_slave_results_folder(),
                                     pop_name_hex + '_StorageOperationData.csv')
    df_SO = pd.read_csv(data_storage_path)
    df_SO['index'] = xrange(8760)
    index = df_PPA['index']

    if i == 0:
        df_network = pd.DataFrame({"network": dict_network}, index=[individual])
    else:
        df_network = df_network.append(pd.DataFrame({"network": dict_network}, index=[individual]))

    data_processed.append({'buildings_connected': buildings_connected, 'buildings_demand': building_demands_df,
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
    anlysis_fields_loads = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh"]
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
