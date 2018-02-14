"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import json
import os

import pandas as pd

import cea.config
import cea.inputlocator
from cea.plots.optimization.pareto_capacity_installed import pareto_capacity_installed
from cea.plots.optimization.pareto_curve import pareto_curve
from cea.plots.optimization.pareto_curve_over_generations import pareto_curve_over_generations

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def data_processing(data_raw):
    data_processed = []
    for data in data_raw:
        # get lists of data for performance values of the population
        costs_Mio = [round(objectives[0] / 1000000, 2) for objectives in
                     data['population_fitness']]  # convert to millions
        emissions_ton = [round(objectives[1] / 1000000, 2) for objectives in
                         data['population_fitness']]  # convert to tons x 10^3
        prim_energy_GJ = [round(objectives[2] / 1000000, 2) for objectives in
                          data['population_fitness']]  # convert to gigajoules x 10^3
        individual_names = ['ind' + str(i) for i in range(len(costs_Mio))]

        df_population = pd.DataFrame({'Name': individual_names, 'costs_Mio': costs_Mio,
                                        'emissions_ton': emissions_ton, 'prim_energy_GJ': prim_energy_GJ}).set_index("Name")

        # get lists of data for performance values of the population (hall_of_fame
        costs_Mio_HOF = [round(objectives[0] / 1000000, 2) for objectives in
                         data['halloffame_fitness']]  # convert to millions
        emissions_ton_HOF = [round(objectives[1] / 1000000, 2) for objectives in
                             data['halloffame_fitness']]  # convert to tons x 10^3
        prim_energy_GJ_HOF = [round(objectives[2] / 1000000, 2) for objectives in
                              data['halloffame_fitness']]  # convert to gigajoules x 10^3
        individual_names_HOF = ['ind' + str(i) for i in range(len(costs_Mio_HOF))]
        df_halloffame = pd.DataFrame({'Name': individual_names_HOF, 'costs_Mio': costs_Mio_HOF,
                                        'emissions_ton': emissions_ton_HOF, 'prim_energy_GJ': prim_energy_GJ_HOF}).set_index("Name")


        # get dataframe with capacity installed per individual
        for i, individual in enumerate(individual_names):
            dict_capacities = data['capacities'][i]
            dict_network = data['disconnected_capacities'][i]["network"]
            list_dict_disc_capacities = data['disconnected_capacities'][i]["disconnected_capacity"]
            for building, dict_disconnected in enumerate(list_dict_disc_capacities):
                if building ==0:
                    df_disc_capacities = pd.DataFrame(dict_disconnected, index=[dict_disconnected['building_name']])
                else:
                    df_disc_capacities = df_disc_capacities.append(pd.DataFrame(dict_disconnected, index=[dict_disconnected['building_name']]))
            df_disc_capacities = df_disc_capacities.set_index('building_name')
            dict_disc_capacities = df_disc_capacities.sum(axis=0).to_dict() # series with sum of capacities

            if i == 0:
                df_disc_capacities_final = pd.DataFrame(dict_disc_capacities, index=[individual])
                df_capacities = pd.DataFrame(dict_capacities, index=[individual])
                df_network = pd.DataFrame({"network":dict_network}, index=[individual])
            else:
                df_capacities = df_capacities.append(pd.DataFrame(dict_capacities, index=[individual]))
                df_network = df_network.append(pd.DataFrame({"network":dict_network}, index=[individual]))
                df_disc_capacities_final = df_disc_capacities_final.append(pd.DataFrame(dict_disc_capacities, index=[individual]))

        data_processed.append({'population':df_population, 'halloffame':df_halloffame, 'capacities_W':df_capacities,
                               'disconnected_capacities_W':df_disc_capacities_final, 'network':df_network,
                               'spread': data['spread'], 'euclidean_distance': data['euclidean_distance'] })
    return data_processed


def dashboard(locator, config):
    # Local Variables
    generations = config.dashboard.generations

    data_raw = []
    for i in generations:
        with open(locator.get_optimization_checkpoint(i), "rb") as fp:
            data_raw.append(json.load(fp))
    data_processed = data_processing(data_raw)

    # CREATE PARETO CURVE MULTIPLE GENERATIONS
    output_path = locator.get_timeseries_plots_file("District" + '_pareto_curve_over_generations')
    title = 'Pareto Curve for District'
    pareto_curve_over_generations(data_processed, generations, title, output_path)
    #
    # CREATE PARETO CURVE FINAL GENERATION
    output_path = locator.get_timeseries_plots_file("District" + '_pareto_curve_performance')
    title = 'Pareto Curve for District'
    pareto_curve(data_processed[-1:][0], title, output_path)

    # CREATE CAPACITY INSTALLED FOR INDIVIDUALS
    output_path = locator.get_timeseries_plots_file("District" + '_pareto_curve_capacity_installed')
    analysis_fields = ['Base_boiler_BG_capacity_W', 'Base_boiler_NG_capacity_W', 'CHP_BG_capacity_W',
                       'CHP_NG_capacity_W', 'Furnace_dry_capacity_W', 'Furnace_wet_capacity_W',
                       'GHP_capacity_W', 'HP_Lake_capacity_W', 'HP_Sewage_capacity_W',
                       'PVT_capacity_W', 'PV_capacity_W', 'Peak_boiler_BG_capacity_W',
                       'Peak_boiler_NG_capacity_W', 'SC_capacity_W',
                       'Disconnected_Boiler_BG_capacity_W',
                       'Disconnected_Boiler_NG_capacity_W',
                       'Disconnected_FC_capacity_W',
                       'Disconnected_GHP_capacity_W']
    renewable_sources_fields =['Base_boiler_BG_capacity_W', 'CHP_BG_capacity_W',
                       'Furnace_dry_capacity_W', 'Furnace_wet_capacity_W',
                       'GHP_capacity_W', 'HP_Lake_capacity_W', 'HP_Sewage_capacity_W',
                       'PVT_capacity_W', 'PV_capacity_W', 'Peak_boiler_BG_capacity_W', 'SC_capacity_W',
                       'Disconnected_Boiler_BG_capacity_W',
                       'Disconnected_FC_capacity_W',
                       'Disconnected_GHP_capacity_W']
    title = 'Capacity Installed of the Pareto Curve for District'
    pareto_capacity_installed(data_processed[-1:][0], analysis_fields, renewable_sources_fields, title, output_path)


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.scenario)

    dashboard(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
