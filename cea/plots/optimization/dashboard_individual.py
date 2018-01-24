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
    individual_barcode_list_string = [str(ind)[0:4] if type(ind) == float else str(ind) for ind in individual_barcode_list]
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

    # get data about the activation patterns of these buildings (storage)
    data_storage_path = os.path.join(locator.get_optimization_slave_results_folder(),
                                     pop_name_hex + '_StorageOperationData.csv')
    df_SO = pd.read_csv(data_storage_path)

    data_processed.append({'buildings_connected': buildings_connected, 'buildings_demand_W': building_demands_df,
                           'activation_units_data':df_PPA, 'storage_data':df_SO})

    return data_processed


def dashboard(locator, config):
    # Local Variables
    generation = int(config.dashboard.generations[-1:][0]) # choose always the last one in the list
    individual = config.dashboard.individual

    # CREATE CAPACITY INSTALLED FOR INDIVIDUALS
    output_path = locator.get_timeseries_plots_file(
        "ind" + str(individual) + '_gen' + str(generation) + '_pareto_curve_capacity_installed')
    analysis_fields_units = ['E_CC_gen_W',
                             'E_GHP_req_W',
                             'E_PP_and_storage_W',
                             'E_aux_HP_uncontrollable_W',
                             'E_consumed_without_buildingdemand_W',
                             'E_produced_total_W',
                             'E_solar_gen_W',
                             'Q_AddBoiler_W',
                             'Q_BoilerBase_W',
                             'Q_BoilerPeak_W',
                             'Q_CC_W',
                             'Q_Furnace_W',
                             'Q_GHP_W',
                             'Q_HPLake_W',
                             'Q_HPSew_W',
                             'Q_Network_Demand_after_Storage_W',
                             'Q_excess_W',
                             'Q_primaryAddBackupSum_W',
                             'Q_uncontrollable_W',
                             'Q_uncovered_W',
                             'Qcold_HPLake_W',


                             'E_PVT_Wh',
                             'E_PV_Wh',
                             'E_aux_HP_uncontrollable_Wh',
                             'E_aux_ch_W',
                             'E_aux_dech_W',
                             'E_consumed_total_without_buildingdemand_W',
                             'E_produced_total_W',
                             'HPCompAirDesignArray_kWh',
                             'HPScDesignArray_Wh',
                             'HPServerHeatDesignArray_kWh',
                             'HPpvt_designArray_Wh',
                             'P_HPCharge_max_W',
                             'Q_DH_networkload_W',
                             'Q_SCandPVT_gen_Wh',
                             'Q_from_storage_used_W',
                             'Q_missing_W',
                             'Q_rejected_fin_W'
                             ]
    anlysis_fields_loads = ['Electr_netw_total_W', 'Q_DCNf_W', 'Q_DHNf_W']
    title = 'Activation curve for Individual ' + str(individual) + " in generation " + str(generation)
    with open(locator.get_optimization_checkpoint(generation), "rb") as fp:
        data_raw = json.load(fp)
    data_processed = data_processing(locator, anlysis_fields_loads, data_raw, individual)
    individual_activation_curve(data_processed, analysis_fields_units, renewable_sources_fields, title, output_path)


def main(config):
    locator = cea.inputlocator.InputLocator(config.dashboard.scenario)

    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.dashboard.scenario)

    dashboard(locator, config)

if __name__ == '__main__':
    main(cea.config.Configuration())
