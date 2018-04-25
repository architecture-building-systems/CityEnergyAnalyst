"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import json
import os

import pandas as pd
import numpy as np
import cea.config
import cea.inputlocator
from cea.plots.optimization.individual_activation_curve import individual_activation_curve
from cea.plots.optimization.pareto_capacity_installed import pareto_capacity_installed
from cea.plots.optimization.pareto_curve import pareto_curve
from cea.plots.optimization.pareto_curve_over_generations import pareto_curve_over_generations
from cea.plots.optimization.thermal_storage_curve import thermal_storage_activation_curve

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def plots_main(locator, config):
    # local variables
    generations = config.plots.generations
    individual = config.plots.individual

    # initialize class
    plots = Plots(locator, individual, generations)

    # generate plots
    plots.pareto_multiple_generations()
    plots.pareto_final_generation()
    plots.pareto_final_generation_capacity_installed()
    plots.individual_heating_activation_curve()
    plots.individual_heating_storage_activation_curve()
    plots.individual_electricity_activation_curve()
    plots.individual_cooling_activation_curve()

    return


class Plots():

    def __init__(self, locator, individual, generations):
        # local variables
        self.locator = locator
        self.individual = individual
        self.generations = generations
        self.final_generation = self.preprocess_final_generation(generations)
        # fields of loads in the systems of heating, cooling and electricity
        self.analysis_fields_electricity_loads = ['Electr_netw_total_W', "E_HPSew_req_W", "E_HPLake_req_W",
                                                  "E_GHP_req_W",
                                                  "E_BaseBoiler_req_W",
                                                  "E_PeakBoiler_req_W",
                                                  "E_AddBoiler_req_W",
                                                  "E_aux_storage_solar_and_heat_recovery_req_W",
                                                  "E_total_req_W"]
        self.analysis_fields_heating_loads = ['Q_DHNf_W']
        self.analysis_fields_cooling_loads = ['Q_total_cooling_W']
        self.analysis_fields_heating = ["Q_PVT_to_directload_W",
                                        "Q_SC_ET_to_directload_W",
                                        "Q_SC_FP_to_directload_W",
                                        "Q_server_to_directload_W",
                                        "Q_compair_to_directload_W",
                                        "Q_from_storage_used_W",
                                        "Q_HPLake_W",
                                        "Q_HPSew_W",
                                        "Q_GHP_W",
                                        "Q_CHP_W",
                                        "Q_Furnace_W",
                                        "Q_BaseBoiler_W",
                                        "Q_PeakBoiler_W",
                                        "Q_AddBoiler_W"]
        self.analysis_fields_heating_storage_charging = ["Q_PVT_to_storage_W",
                                                         "Q_SC_ET_to_storage_W",
                                                         "Q_SC_FP_to_storage_W",
                                                         "Q_server_to_storage_W"]
        self.analysis_fields_heating_storage_discharging = ["Q_from_storage_used_W"]
        self.analysis_fields_heating_storage_status = ["Q_storage_content_W"]
        self.analysis_fields_cooling = ['Q_from_Lake_W',
                                        'Q_from_VCC_W',
                                        'Q_from_ACH_W',
                                        'Q_from_VCC_backup_W',
                                        'Q_from_storage_tank_W']
        self.analysis_fields_electricity = ["E_PV_directload_W",
                                            "E_PVT_directload_W",
                                            "E_CHP_directload_W",
                                            "E_Furnace_directload_W",
                                            "E_PV_to_grid_W",
                                            "E_PVT_to_grid_W",
                                            "E_CHP_to_grid_W",
                                            "E_Furnace_to_grid_W",
                                            "E_from_grid_W"]
        self.analysis_fields = ['Base_boiler_BG_capacity_W', 'Base_boiler_NG_capacity_W', 'CHP_BG_capacity_W',
                                'CHP_NG_capacity_W', 'Furnace_dry_capacity_W', 'Furnace_wet_capacity_W',
                                'GHP_capacity_W', 'HP_Lake_capacity_W', 'HP_Sewage_capacity_W',
                                'PVT_capacity_W', 'PV_capacity_W', 'Peak_boiler_BG_capacity_W',
                                'Peak_boiler_NG_capacity_W', 'SC_ET_capacity_W', 'SC_FP_capacity_W',
                                'Disconnected_Boiler_BG_capacity_W',
                                'Disconnected_Boiler_NG_capacity_W',
                                'Disconnected_FC_capacity_W',
                                'Disconnected_GHP_capacity_W']
        self.renewable_sources_fields = ['Base_boiler_BG_capacity_W', 'CHP_BG_capacity_W',
                                         'Furnace_dry_capacity_W', 'Furnace_wet_capacity_W',
                                         'GHP_capacity_W', 'HP_Lake_capacity_W', 'HP_Sewage_capacity_W',
                                         'PVT_capacity_W', 'PV_capacity_W', 'Peak_boiler_BG_capacity_W',
                                         'SC_ET_capacity_W', 'SC_FP_capacity_W',
                                         'Disconnected_Boiler_BG_capacity_W',
                                         'Disconnected_FC_capacity_W',
                                         'Disconnected_GHP_capacity_W']
        self.data_processed = self.preprocessing_generations_data()
        self.data_processed_individual = self.preprocessing_individual_data(self.locator,
                                                                            self.data_processed['final_generation'],
                                                                            self.individual)

    def preprocess_final_generation(self, generations):
        if len(generations) == 1:
            return generations[0]
        else:
            return generations[-1:][0]

    def preprocessing_generations_data(self):

        data_processed = []
        for generation in self.generations:
            with open(self.locator.get_optimization_checkpoint(generation), "rb") as fp:
                data = json.load(fp)
            # get lists of data for performance values of the population
            costs_Mio = [round(objectives[0] / 1000000, 2) for objectives in
                         data['population_fitness']]  # convert to millions
            emissions_ton = [round(objectives[1] / 1000000, 2) for objectives in
                             data['population_fitness']]  # convert to tons x 10^3
            prim_energy_GJ = [round(objectives[2] / 1000000, 2) for objectives in
                              data['population_fitness']]  # convert to gigajoules x 10^3
            individual_names = ['ind' + str(i) for i in range(len(costs_Mio))]

            df_population = pd.DataFrame({'Name': individual_names, 'costs_Mio': costs_Mio,
                                          'emissions_ton': emissions_ton, 'prim_energy_GJ': prim_energy_GJ
                                          }).set_index("Name")

            individual_barcode = [[str(ind) if type(ind) == float else str(ind) for ind in
                                   individual] for individual in data['population']]
            def_individual_barcode = pd.DataFrame({'Name': individual_names,
                                                   'individual_barcode': individual_barcode}).set_index("Name")

            # get lists of data for performance values of the population (hall_of_fame
            costs_Mio_HOF = [round(objectives[0] / 1000000, 2) for objectives in
                             data['halloffame_fitness']]  # convert to millions
            emissions_ton_HOF = [round(objectives[1] / 1000000, 2) for objectives in
                                 data['halloffame_fitness']]  # convert to tons x 10^3
            prim_energy_GJ_HOF = [round(objectives[2] / 1000000, 2) for objectives in
                                  data['halloffame_fitness']]  # convert to gigajoules x 10^3
            individual_names_HOF = ['ind' + str(i) for i in range(len(costs_Mio_HOF))]
            df_halloffame = pd.DataFrame({'Name': individual_names_HOF, 'costs_Mio': costs_Mio_HOF,
                                          'emissions_ton': emissions_ton_HOF,
                                          'prim_energy_GJ': prim_energy_GJ_HOF}).set_index("Name")

            # get dataframe with capacity installed per individual
            for i, individual in enumerate(individual_names):
                dict_capacities = data['capacities'][i]
                dict_network = data['disconnected_capacities'][i]["network"]
                list_dict_disc_capacities = data['disconnected_capacities'][i]["disconnected_capacity"]
                for building, dict_disconnected in enumerate(list_dict_disc_capacities):
                    if building == 0:
                        df_disc_capacities = pd.DataFrame(dict_disconnected, index=[dict_disconnected['building_name']])
                    else:
                        df_disc_capacities = df_disc_capacities.append(
                            pd.DataFrame(dict_disconnected, index=[dict_disconnected['building_name']]))
                df_disc_capacities = df_disc_capacities.set_index('building_name')
                dict_disc_capacities = df_disc_capacities.sum(axis=0).to_dict()  # series with sum of capacities

                if i == 0:
                    df_disc_capacities_final = pd.DataFrame(dict_disc_capacities, index=[individual])
                    df_capacities = pd.DataFrame(dict_capacities, index=[individual])
                    df_network = pd.DataFrame({"network": dict_network}, index=[individual])
                else:
                    df_capacities = df_capacities.append(pd.DataFrame(dict_capacities, index=[individual]))
                    df_network = df_network.append(pd.DataFrame({"network": dict_network}, index=[individual]))
                    df_disc_capacities_final = df_disc_capacities_final.append(
                        pd.DataFrame(dict_disc_capacities, index=[individual]))

            data_processed.append(
                {'population': df_population, 'halloffame': df_halloffame, 'capacities_W': df_capacities,
                 'disconnected_capacities_W': df_disc_capacities_final, 'network': df_network,
                 'spread': data['spread'], 'euclidean_distance': data['euclidean_distance'],
                 'individual_barcode': def_individual_barcode})

        return {'all_generations': data_processed, 'final_generation': data_processed[-1:][0]}

    def preprocessing_individual_data(self, locator, data_raw, individual):

        # get netwoork name
        string_network = data_raw['network'].loc[individual].values[0]
        total_demand = pd.read_csv(locator.get_total_demand())
        building_names = total_demand.Name.values

        # get data about hourly demands in these buildings
        building_demands_df = pd.read_csv(locator.get_optimization_network_results_summary(string_network)).set_index(
            "DATE")

        # get data about the activation patterns of these buildings
        individual_barcode_list = data_raw['individual_barcode'].loc[individual].values[0]
        df_all_generations = pd.read_csv(locator.get_optimization_all_individuals())

        # The current structure of CEA has the following columns saved, in future, this will be slightly changed and
        # correspondingly these columns_of_saved_files needs to be changed
        columns_of_saved_files = ['CHP/Furnace', 'CHP/Furnace Share', 'Base Boiler',
                                  'Base Boiler Share', 'Peak Boiler', 'Peak Boiler Share',
                                  'Heating Lake', 'Heating Lake Share', 'Heating Sewage', 'Heating Sewage Share', 'GHP',
                                  'GHP Share',
                                  'Data Centre', 'Compressed Air', 'PV', 'PV Area Share', 'PVT', 'PVT Area Share', 'SC_ET',
                                  'SC_ET Area Share', 'SC_FP', 'SC_FP Area Share', 'DHN Temperature', 'DHN unit configuration',
                                  'Lake Cooling', 'Lake Cooling Share', 'VCC Cooling', 'VCC Cooling Share',
                                  'Absorption Chiller', 'Absorption Chiller Share', 'Storage', 'Storage Share',
                                  'DCN Temperature', 'DCN unit configuration']
        for i in building_names:  # DHN
            columns_of_saved_files.append(str(i) + ' DHN')

        for i in building_names:  # DCN
            columns_of_saved_files.append(str(i) + ' DCN')


        df_current_individual = pd.DataFrame(np.zeros(shape = (1, len(columns_of_saved_files))), columns=columns_of_saved_files)
        for i, ind in enumerate((columns_of_saved_files)):
            df_current_individual[ind] = individual_barcode_list[i]
        for i in range(len(df_all_generations)):
            matching_number_between_individuals = 0
            for j in columns_of_saved_files:
                if np.isclose(float(df_all_generations[j][i]), float(df_current_individual[j][0])):
                    matching_number_between_individuals = matching_number_between_individuals + 1

            if matching_number_between_individuals >= (len(columns_of_saved_files) - 1):
                # this should ideally be equal to the length of the columns_of_saved_files, but due to a bug, which
                # occasionally changes the type of Boiler from NG to BG or otherwise, this round about is figured for now
                generation_number = df_all_generations['generation'][i]
                individual_number = df_all_generations['individual'][i]

        generation_number = int(generation_number)
        individual_number = int(individual_number)
        # get data about the activation patterns of these buildings (main units)
        data_activation_path = os.path.join(
            locator.get_optimization_slave_heating_activation_pattern(individual_number, generation_number))
        df_heating = pd.read_csv(data_activation_path).set_index("DATE")

        data_activation_path = os.path.join(
            locator.get_optimization_slave_cooling_activation_pattern(individual_number, generation_number))
        df_cooling = pd.read_csv(data_activation_path).set_index("DATE")

        data_activation_path = os.path.join(
            locator.get_optimization_slave_electricity_activation_pattern(individual_number, generation_number))
        df_electricity = pd.read_csv(data_activation_path).set_index("DATE")

        # get data about the activation patterns of these buildings (storage)
        data_storage_path = os.path.join(
            locator.get_optimization_slave_storage_operation_data(individual_number, generation_number))
        df_SO = pd.read_csv(data_storage_path).set_index("DATE")

        # join into one database
        data_processed = df_heating.join(df_cooling).join(df_electricity).join(df_SO).join(building_demands_df)

        return data_processed

    def pareto_multiple_generations(self):
        title = 'Pareto Curve for Multiple Generations'
        output_path = self.locator.get_timeseries_plots_file('District_pareto_multiple_generations')
        data = self.data_processed['all_generations']
        plot = pareto_curve_over_generations(data, self.generations, title, output_path)
        return plot

    def pareto_final_generation(self):
        title = 'Pareto Curve for Final Generation ' + str(self.generations[-1:][0])
        output_path = self.locator.get_timeseries_plots_file('District_pareto_final_generation')
        data = self.data_processed['final_generation']
        plot = pareto_curve(data, title, output_path)
        return plot

    def pareto_final_generation_capacity_installed(self):
        title = 'Capacity Installed in Final Generation' + str(self.generations[-1:][0])
        output_path = self.locator.get_timeseries_plots_file('District_pareto_final_generation_capacity_installed')
        data = self.data_processed['final_generation']
        plot = pareto_capacity_installed(data, self.analysis_fields, self.renewable_sources_fields, title, output_path)
        return plot

    def individual_heating_activation_curve(self):
        title = 'Activation curve  for Individual ' + self.individual + " in generation " + str(self.final_generation)
        output_path = self.locator.get_timeseries_plots_file(
            self.individual + '_gen' + str(self.final_generation) + '_heating_activation_curve')
        anlysis_fields_loads = self.analysis_fields_heating_loads
        data = self.data_processed_individual
        plot = individual_activation_curve(data, anlysis_fields_loads, self.analysis_fields_heating, title, output_path)
        return plot

    def individual_heating_storage_activation_curve(self):
        title = 'Storage Activation curve  for Individual ' + self.individual + " in generation " + str(
            self.final_generation)
        output_path = self.locator.get_timeseries_plots_file(
            self.individual + '_gen' + str(self.final_generation) + '_heating_storage_activation_curve')
        analysis_fields_charging = self.analysis_fields_heating_storage_charging
        analysis_fields_discharging = self.analysis_fields_heating_storage_discharging
        analysis_fields_status = self.analysis_fields_heating_storage_status
        data = self.data_processed_individual
        plot = thermal_storage_activation_curve(data, analysis_fields_charging, analysis_fields_discharging,
                                                analysis_fields_status, title, output_path)
        return plot

    def individual_electricity_activation_curve(self):
        title = 'Activation curve  for Individual ' + self.individual + " in generation " + str(self.final_generation)
        output_path = self.locator.get_timeseries_plots_file(
            self.individual + '_gen' + str(self.final_generation) + '_electricity_activation_curve')
        anlysis_fields_loads = self.analysis_fields_electricity_loads
        data = self.data_processed_individual
        plot = individual_activation_curve(data, anlysis_fields_loads, self.analysis_fields_electricity, title,
                                           output_path)
        return plot

    def individual_cooling_activation_curve(self):
        title = 'Activation curve  for Individual ' + self.individual + " in generation " + str(self.final_generation)
        output_path = self.locator.get_timeseries_plots_file(
            self.individual + '_gen' + str(self.final_generation) + '_cooling_activation_curve')
        anlysis_fields_loads = self.analysis_fields_cooling_loads
        data = self.data_processed_individual
        plot = individual_activation_curve(data, anlysis_fields_loads, self.analysis_fields_cooling, title, output_path)
        return plot


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    print("Running dashboard with scenario = %s" % config.scenario)
    print("Running dashboard with the next generations = %s" % config.plots.generations)
    print("Running dashboard with the next individual = %s" % config.plots.individual)

    plots_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())