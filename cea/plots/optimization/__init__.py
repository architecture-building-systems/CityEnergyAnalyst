from __future__ import division
from __future__ import print_function

import numpy as np
import pandas as pd
import os
import json
import cea.config
import cea.plots
from cea.analysis.multicriteria.optimization_post_processing.individual_configuration import supply_system_configuration
from cea.optimization.lca_calculations import LcaCalculations
from cea.analysis.multicriteria.optimization_post_processing.locating_individuals_in_generation_script import \
    locating_individuals_in_generation_script


"""
Implements py:class:`cea.plots.OptimizationOverviewPlotBase` as a base class for all plots in the category "optimization-overview" and also
set's the label for that category.
"""

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# identifies this package as a plots category and sets the label name for the category
label = 'Optimization overview'


class OptimizationOverviewPlotBase(cea.plots.PlotBase):
    """Implements properties / methods used by all plots in this category"""
    category_name = "optimization"

    # default parameters for plots in this category - override if your plot differs
    expected_parameters = {
        'generation': 'plots-optimization:generation',
        'network-type': 'plots-optimization:network-type',
        'multicriteria': 'plots-optimization:multicriteria',
        'scenario-name': 'general:scenario-name',
        'detailed-electricity-pricing': 'general:detailed-electricity-pricing'
    }

    def __init__(self, project, parameters, cache):
        """

        :param project: The project to base plots on (some plots span scenarios)
        :param parameters: The plot parameters as, e.g., per the dashboard.yml file
        :param cea.plots.PlotCache cache: a PlotCache instance for speeding up plotting
        """
        super(OptimizationOverviewPlotBase, self).__init__(project, parameters, cache)
        self.category_path = os.path.join('testing', 'optimization-overview')
        self.generation = self.parameters['generation']
        self.network_type = self.parameters['network-type']
        self.detailed_electricity_pricing = self.parameters['detailed-electricity-pricing']

        address_of_individuals_path = self.locator.get_address_of_individuals_of_a_generation(self.generation)
        if not os.path.exists(address_of_individuals_path):
            self.data_address = locating_individuals_in_generation_script(self.generation, self.locator)
        else:
            self.data_address = pd.read_csv(address_of_individuals_path)

    def preprocessing_generations_data(self):
        with open(self.locator.get_optimization_checkpoint(self.generation), "rb") as fp:
            data = json.load(fp)
        # get lists of data for performance values of the population
        costs_Mio = [round(objectives[0] / 1000000, 2) for objectives in
                     data['tested_population_fitness']]  # convert to millions
        individual_names = ['ind' + str(i) for i in range(len(costs_Mio))]
        individual_barcode = [[str(ind) if type(ind) == float else str(ind) for ind in
                               individual] for individual in data['tested_population']]
        def_individual_barcode = pd.DataFrame({'Name': individual_names,
                                               'individual_barcode': individual_barcode}).set_index("Name")
        data_processed = {'individual_barcode': def_individual_barcode}
        return data_processed

    def preprocessing_final_generation_data_cost_centralized(self):
        return self.cache.lookup(data_path=os.path.join(self.category_name, 'preprocessing_final_generation_data_cost_centralized'),
                                 plot=self, producer=self._preprocessing_final_generation_data_cost_centralized)

    def _preprocessing_final_generation_data_cost_centralized(self):
        data_raw = self.preprocessing_generations_data()
        total_demand = pd.read_csv(self.locator.get_total_demand())
        building_names = total_demand.Name.values

        preprocessing_costs = pd.read_csv(self.locator.get_preprocessing_costs())

        # The current structure of CEA has the following columns saved, in future, this will be slightly changed and
        # correspondingly these columns_of_saved_files needs to be changed
        columns_of_saved_files = ['CHP/Furnace', 'CHP/Furnace Share', 'Base Boiler',
                                  'Base Boiler Share', 'Peak Boiler', 'Peak Boiler Share',
                                  'Heating Lake', 'Heating Lake Share', 'Heating Sewage', 'Heating Sewage Share', 'GHP',
                                  'GHP Share',
                                  'Data Centre', 'Compressed Air', 'PV', 'PV Area Share', 'PVT', 'PVT Area Share',
                                  'SC_ET',
                                  'SC_ET Area Share', 'SC_FP', 'SC_FP Area Share', 'DHN Temperature',
                                  'DHN unit configuration',
                                  'Lake Cooling', 'Lake Cooling Share', 'VCC Cooling', 'VCC Cooling Share',
                                  'Absorption Chiller', 'Absorption Chiller Share', 'Storage', 'Storage Share',
                                  'DCN Temperature', 'DCN unit configuration']
        for i in building_names:  # DHN
            columns_of_saved_files.append(str(i) + ' DHN')

        for i in building_names:  # DCN
            columns_of_saved_files.append(str(i) + ' DCN')

        individual_index = data_raw['individual_barcode'].index.values
        if self.network_type == 'DH':
            data_activation_path = os.path.join(
                self.locator.get_optimization_slave_investment_cost_detailed(1, 1))
            df_heating_costs = pd.read_csv(data_activation_path)
            column_names = df_heating_costs.columns.values
            column_names = np.append(column_names, ['Opex_HP_Sewage', 'Opex_HP_Lake', 'Opex_GHP', 'Opex_CHP_BG',
                                                    'Opex_CHP_NG', 'Opex_Furnace_wet', 'Opex_Furnace_dry',
                                                    'Opex_BaseBoiler_BG', 'Opex_BaseBoiler_NG', 'Opex_PeakBoiler_BG',
                                                    'Opex_PeakBoiler_NG', 'Opex_BackupBoiler_BG',
                                                    'Opex_BackupBoiler_NG',
                                                    'Capex_SC', 'Capex_PVT', 'Capex_Boiler_backup', 'Capex_storage_HEX',
                                                    'Capex_furnace', 'Capex_Boiler', 'Capex_Boiler_peak', 'Capex_Lake',
                                                    'Capex_CHP',
                                                    'Capex_Sewage', 'Capex_pump', 'Opex_Total', 'Capex_Total',
                                                    'Capex_Boiler_Total',
                                                    'Opex_Boiler_Total', 'Opex_CHP_Total', 'Opex_Furnace_Total',
                                                    'Disconnected_costs',
                                                    'Capex_Decentralized', 'Opex_Decentralized', 'Capex_Centralized',
                                                    'Opex_Centralized', 'Electricity_Costs', 'Process_Heat_Costs'])

            data_processed = pd.DataFrame(np.zeros([len(data_raw['individual_barcode']), len(column_names)]),
                                          columns=column_names)

        else:
            assert self.network_type == 'DC', "don't know how to handle network_type {}".format(self.network_type)

            data_activation_path = os.path.join(
                self.locator.get_optimization_slave_investment_cost_detailed_cooling(1, 1))
            df_cooling_costs = pd.read_csv(data_activation_path)
            column_names = df_cooling_costs.columns.values
            column_names = np.append(column_names,
                                     ['Opex_var_ACH_USD', 'Opex_var_CCGT_USD', 'Opex_var_CT_USD', 'Opex_var_Lake_USD', 'Opex_var_VCC_USD',
                                      'Opex_var_PV_USD',
                                      'Opex_var_VCC_backup_USD', 'Capex_ACH_USD', 'Capex_CCGT_USD', 'Capex_CT_USD', 'Capex_Tank_USD',
                                      'Capex_VCC_USD', 'Capex_a_PV_USD',
                                      'Capex_VCC_backup_USD', 'Opex_Total_USD', 'Capex_Total_USD', 'Opex_var_pumps_USD',
                                      'Disconnected_costs_USD',
                                      'Capex_Decentralized_USD', 'Opex_Decentralized_USD', 'Capex_Centralized_USD',
                                      'Opex_Centralized_USD', 'Electricitycosts_for_hotwater_USD',
                                      'Electricitycosts_for_appliances_USD', 'Process_Heat_Costs_USD', 'Network_costs_USD',
                                      'Substation_costs_USD'])

            data_processed = pd.DataFrame(np.zeros([len(data_raw['individual_barcode']), len(column_names)]),
                                          columns=column_names)
        try:
            data_mcda = pd.read_csv(self.locator.get_multi_criteria_analysis(self.generation))
        except IOError:
            raise IOError("Please run the multi-criteria analysis tool first for the generation you would like to visualize")

        lca = LcaCalculations(self.locator,  self.detailed_electricity_pricing)

        for individual_code in range(len(data_raw['individual_barcode'])):

            individual_barcode_list = data_raw['individual_barcode'].loc[individual_index[individual_code]].values[0]
            df_current_individual = pd.DataFrame(np.zeros(shape=(1, len(columns_of_saved_files))),
                                                 columns=columns_of_saved_files)
            for i, ind in enumerate((columns_of_saved_files)):
                df_current_individual[ind] = individual_barcode_list[i]
            data_address_individual = self.data_address[self.data_address['individual_list'] == individual_index[individual_code]]

            generation_pointer = data_address_individual['generation_number_address'].values[
                0]  # points to the correct file to be referenced from optimization folders
            individual_pointer = data_address_individual['individual_number_address'].values[0]

            if self.network_type == 'DH':
                data_activation_path = os.path.join(
                    self.locator.get_optimization_slave_investment_cost_detailed(individual_pointer, generation_pointer))
                df_heating_costs = pd.read_csv(data_activation_path)

                data_activation_path = os.path.join(
                    self.locator.get_optimization_slave_heating_activation_pattern(individual_pointer, generation_pointer))
                df_heating = pd.read_csv(data_activation_path).set_index("DATE")

                for column_name in df_heating_costs.columns.values:
                    data_processed.loc[individual_code][column_name] = df_heating_costs[column_name].values

                data_processed.loc[individual_code]['Opex_HP_Sewage'] = np.sum(df_heating['Opex_var_HP_Sewage'])
                data_processed.loc[individual_code]['Opex_HP_Lake'] = np.sum(df_heating['Opex_var_HP_Lake'])
                data_processed.loc[individual_code]['Opex_GHP'] = np.sum(df_heating['Opex_var_GHP'])
                data_processed.loc[individual_code]['Opex_CHP_BG'] = np.sum(df_heating['Opex_var_CHP_BG'])
                data_processed.loc[individual_code]['Opex_CHP_NG'] = np.sum(df_heating['Opex_var_CHP_NG'])
                data_processed.loc[individual_code]['Opex_Furnace_wet'] = np.sum(df_heating['Opex_var_Furnace_wet'])
                data_processed.loc[individual_code]['Opex_Furnace_dry'] = np.sum(df_heating['Opex_var_Furnace_dry'])
                data_processed.loc[individual_code]['Opex_BaseBoiler_BG'] = np.sum(df_heating['Opex_var_BaseBoiler_BG'])
                data_processed.loc[individual_code]['Opex_BaseBoiler_NG'] = np.sum(df_heating['Opex_var_BaseBoiler_NG'])
                data_processed.loc[individual_code]['Opex_PeakBoiler_BG'] = np.sum(df_heating['Opex_var_PeakBoiler_BG'])
                data_processed.loc[individual_code]['Opex_PeakBoiler_NG'] = np.sum(df_heating['Opex_var_PeakBoiler_NG'])
                data_processed.loc[individual_code]['Opex_BackupBoiler_BG'] = np.sum(
                    df_heating['Opex_var_BackupBoiler_BG'])
                data_processed.loc[individual_code]['Opex_BackupBoiler_NG'] = np.sum(
                    df_heating['Opex_var_BackupBoiler_NG'])

                data_processed.loc[individual_code]['Capex_SC'] = data_processed.loc[individual_code]['Capex_a_SC'] + \
                                                                  data_processed.loc[individual_code]['Opex_fixed_SC']
                data_processed.loc[individual_code]['Capex_PVT'] = data_processed.loc[individual_code]['Capex_a_PVT'] + \
                                                                   data_processed.loc[individual_code]['Opex_fixed_PVT']
                data_processed.loc[individual_code]['Capex_Boiler_backup'] = data_processed.loc[individual_code][
                                                                                 'Capex_a_Boiler_backup'] + \
                                                                             data_processed.loc[individual_code][
                                                                                 'Opex_fixed_Boiler_backup']
                data_processed.loc[individual_code]['Capex_storage_HEX'] = data_processed.loc[individual_code][
                                                                               'Capex_a_storage_HEX'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_fixed_storage_HEX']
                data_processed.loc[individual_code]['Capex_furnace'] = data_processed.loc[individual_code][
                                                                           'Capex_a_furnace'] + \
                                                                       data_processed.loc[individual_code][
                                                                           'Opex_fixed_furnace']
                data_processed.loc[individual_code]['Capex_Boiler'] = data_processed.loc[individual_code][
                                                                          'Capex_a_Boiler'] + \
                                                                      data_processed.loc[individual_code][
                                                                          'Opex_fixed_Boiler']
                data_processed.loc[individual_code]['Capex_Boiler_peak'] = data_processed.loc[individual_code][
                                                                               'Capex_a_Boiler_peak'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_fixed_Boiler_peak']
                data_processed.loc[individual_code]['Capex_Lake'] = data_processed.loc[individual_code][
                                                                        'Capex_a_Lake'] + \
                                                                    data_processed.loc[individual_code][
                                                                        'Opex_fixed_Lake']
                data_processed.loc[individual_code]['Capex_Sewage'] = data_processed.loc[individual_code][
                                                                          'Capex_a_Sewage'] + \
                                                                      data_processed.loc[individual_code][
                                                                          'Opex_fixed_Boiler']
                data_processed.loc[individual_code]['Capex_pump'] = data_processed.loc[individual_code][
                                                                        'Capex_a_pump'] + \
                                                                    data_processed.loc[individual_code][
                                                                        'Opex_fixed_pump']
                data_processed.loc[individual_code]['Capex_CHP'] = data_processed.loc[individual_code]['Capex_a_CHP'] + \
                                                                   data_processed.loc[individual_code]['Opex_fixed_CHP']
                data_processed.loc[individual_code]['Disconnected_costs'] = df_heating_costs['CostDiscBuild']

                data_processed.loc[individual_code]['Capex_Boiler_Total'] = data_processed.loc[individual_code][
                                                                                'Capex_Boiler'] + \
                                                                            data_processed.loc[individual_code][
                                                                                'Capex_Boiler_peak'] + \
                                                                            data_processed.loc[individual_code][
                                                                                'Capex_Boiler_backup']
                data_processed.loc[individual_code]['Opex_Boiler_Total'] = data_processed.loc[individual_code][
                                                                               'Opex_BackupBoiler_NG'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_BackupBoiler_BG'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_PeakBoiler_NG'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_PeakBoiler_BG'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_BaseBoiler_NG'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_BaseBoiler_BG']
                data_processed.loc[individual_code]['Opex_CHP_Total'] = data_processed.loc[individual_code][
                                                                            'Opex_CHP_NG'] + \
                                                                        data_processed.loc[individual_code][
                                                                            'Opex_CHP_BG']

                data_processed.loc[individual_code]['Opex_Furnace_Total'] = data_processed.loc[individual_code][
                                                                                'Opex_Furnace_wet'] + \
                                                                            data_processed.loc[individual_code][
                                                                                'Opex_Furnace_dry']

                data_processed.loc[individual_code]['Electricity_Costs'] = preprocessing_costs['elecCosts'].values[0]
                data_processed.loc[individual_code]['Process_Heat_Costs'] = preprocessing_costs['hpCosts'].values[0]

                data_processed.loc[individual_code]['Opex_Centralized'] \
                    = data_processed.loc[individual_code]['Opex_HP_Sewage'] + data_processed.loc[individual_code][
                    'Opex_HP_Lake'] + \
                      data_processed.loc[individual_code]['Opex_GHP'] + data_processed.loc[individual_code][
                          'Opex_CHP_BG'] + \
                      data_processed.loc[individual_code]['Opex_CHP_NG'] + data_processed.loc[individual_code][
                          'Opex_Furnace_wet'] + \
                      data_processed.loc[individual_code]['Opex_Furnace_dry'] + data_processed.loc[individual_code][
                          'Opex_BaseBoiler_BG'] + \
                      data_processed.loc[individual_code]['Opex_BaseBoiler_NG'] + data_processed.loc[individual_code][
                          'Opex_PeakBoiler_BG'] + \
                      data_processed.loc[individual_code]['Opex_PeakBoiler_NG'] + data_processed.loc[individual_code][
                          'Opex_BackupBoiler_BG'] + \
                      data_processed.loc[individual_code]['Opex_BackupBoiler_NG'] + \
                      data_processed.loc[individual_code]['Electricity_Costs'] + data_processed.loc[individual_code][
                          'Process_Heat_Costs']

                data_processed.loc[individual_code]['Capex_Centralized'] = data_processed.loc[individual_code][
                                                                               'Capex_SC'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Capex_PVT'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Capex_Boiler_backup'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Capex_storage_HEX'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Capex_furnace'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Capex_Boiler'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Capex_Boiler_peak'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Capex_Lake'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Capex_Sewage'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Capex_pump']

                data_processed.loc[individual_code]['Capex_Decentralized'] = df_heating_costs['Capex_Disconnected']
                data_processed.loc[individual_code]['Opex_Decentralized'] = df_heating_costs['Opex_Disconnected']
                data_processed.loc[individual_code]['Capex_Total'] = data_processed.loc[individual_code][
                                                                         'Capex_Centralized'] + \
                                                                     data_processed.loc[individual_code][
                                                                         'Capex_Decentralized']
                data_processed.loc[individual_code]['Opex_Total'] = data_processed.loc[individual_code][
                                                                        'Opex_Centralized'] + \
                                                                    data_processed.loc[individual_code][
                                                                        'Opex_Decentralized']

            elif self.network_type == 'DC':
                data_mcda_ind = data_mcda[data_mcda['individual'] == individual_index[individual_code]]

                for column_name in df_cooling_costs.columns.values:
                    data_processed.loc[individual_code][column_name] = df_cooling_costs[column_name].values[0]

                data_processed.loc[individual_code]['Opex_var_ACH_USD'] = data_mcda_ind['Opex_total_ACH_USD'].values[0] - \
                                                                      data_mcda_ind['Opex_fixed_ACH_USD'].values[0]
                data_processed.loc[individual_code]['Opex_var_CCGT_USD'] = data_mcda_ind['Opex_total_CCGT_USD'].values[0] - \
                                                                       data_mcda_ind['Opex_fixed_CCGT_USD'].values[0]
                data_processed.loc[individual_code]['Opex_var_CT_USD'] = data_mcda_ind['Opex_total_CT_USD'].values[0] - \
                                                                     data_mcda_ind['Opex_fixed_CT_USD'].values[0]
                data_processed.loc[individual_code]['Opex_var_Lake_USD'] = data_mcda_ind['Opex_total_Lake_USD'].values[0] - \
                                                                       data_mcda_ind['Opex_fixed_Lake_USD'].values[0]
                data_processed.loc[individual_code]['Opex_var_VCC_USD'] = data_mcda_ind['Opex_total_VCC_USD'].values[0] - \
                                                                      data_mcda_ind['Opex_fixed_VCC_USD'].values[0]
                data_processed.loc[individual_code]['Opex_var_VCC_backup_USD'] = \
                data_mcda_ind['Opex_total_VCC_backup_USD'].values[0] - data_mcda_ind['Opex_fixed_VCC_backup_USD'].values[0]
                data_processed.loc[individual_code]['Opex_var_pumps_USD'] = data_mcda_ind['Opex_var_pump_USD'].values[0]
                data_processed.loc[individual_code]['Opex_var_PV_USD'] = data_mcda_ind['Opex_total_PV_USD'].values[0] - \
                                                                     data_mcda_ind['Opex_fixed_PV_USD'].values[0]

                data_processed.loc[individual_code]['Capex_a_ACH_USD'] = (
                        data_mcda_ind['Capex_a_ACH_USD'].values[0] + data_mcda_ind['Opex_fixed_ACH_USD'].values[0])
                data_processed.loc[individual_code]['Capex_a_CCGT_USD'] = data_mcda_ind['Capex_a_CCGT_USD'].values[0] + \
                                                                      data_mcda_ind['Opex_fixed_CCGT_USD'].values[0]
                data_processed.loc[individual_code]['Capex_a_CT_USD'] = data_mcda_ind['Capex_a_CT_USD'].values[0] + \
                                                                    data_mcda_ind['Opex_fixed_CT_USD'].values[0]
                data_processed.loc[individual_code]['Capex_a_Tank_USD'] = data_mcda_ind['Capex_a_Tank_USD'].values[0] + \
                                                                      data_mcda_ind['Opex_fixed_Tank_USD'].values[0]
                data_processed.loc[individual_code]['Capex_a_VCC_USD'] = (
                        data_mcda_ind['Capex_a_VCC_USD'].values[0] + data_mcda_ind['Opex_fixed_VCC_USD'].values[0])
                data_processed.loc[individual_code]['Capex_a_VCC_backup_USD'] = (data_mcda_ind['Capex_a_VCC_backup_USD'].values[
                                                                                0] + data_mcda_ind[
                                                                                'Opex_fixed_VCC_backup_USD'].values[0])
                data_processed.loc[individual_code]['Capex_a_pump_USD'] = (data_mcda_ind['Capex_pump_USD'].values[0] + \
                                                                      data_mcda_ind['Opex_fixed_pump_USD'].values[0])
                data_processed.loc[individual_code]['Capex_a_PV_USD'] = data_mcda_ind['Capex_a_PV_USD'].values[0]
                data_processed.loc[individual_code]['Substation_costs_USD'] = data_mcda_ind['Substation_costs_USD'].values[0]
                data_processed.loc[individual_code]['Network_costs_USD'] = data_mcda_ind['Network_costs_USD'].values[0]

                data_processed.loc[individual_code]['Capex_Decentralized_USD'] = data_mcda_ind['Capex_a_disconnected_USD']
                data_processed.loc[individual_code]['Opex_Decentralized_USD'] = data_mcda_ind['Opex_total_disconnected_USD']

                data_processed.loc[individual_code]['Electricitycosts_for_hotwater_USD'] = (
                        data_mcda_ind['Electricity_for_hotwater_GW'].values[0] * 1000000000 * lca.ELEC_PRICE.mean())
                data_processed.loc[individual_code]['Electricitycosts_for_appliances_USD'] = (
                        data_mcda_ind['Electricity_for_appliances_GW'].values[0] * 1000000000 * lca.ELEC_PRICE.mean())
                data_processed.loc[individual_code]['Process_Heat_Costs'] = preprocessing_costs['hpCosts'].values[0]

                data_processed.loc[individual_code]['Opex_Centralized_USD'] = data_processed.loc[individual_code][
                                                                              'Opex_var_ACH_USD'] + \
                                                                          data_processed.loc[individual_code][
                                                                              'Opex_var_CCGT_USD'] + \
                                                                          data_processed.loc[individual_code][
                                                                              'Opex_var_CT_USD'] + \
                                                                          data_processed.loc[individual_code][
                                                                              'Opex_var_Lake_USD'] + \
                                                                          data_processed.loc[individual_code][
                                                                              'Opex_var_VCC_USD'] + \
                                                                          data_processed.loc[individual_code][
                                                                              'Opex_var_VCC_backup_USD'] + \
                                                                          data_processed.loc[individual_code][
                                                                              'Opex_var_pumps_USD'] + \
                                                                          data_processed.loc[individual_code][
                                                                              'Electricitycosts_for_hotwater_USD'] + \
                                                                          data_processed.loc[individual_code][
                                                                              'Process_Heat_Costs_USD'] + \
                                                                          data_processed.loc[individual_code][
                                                                              'Opex_var_PV_USD'] + \
                                                                          data_processed.loc[individual_code][
                                                                              'Electricitycosts_for_appliances_USD']

                data_processed.loc[individual_code]['Capex_Centralized_USD'] = data_processed.loc[individual_code][
                                                                               'Capex_a_ACH_USD'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Capex_a_CCGT_USD'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Capex_a_CT_USD'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Capex_a_Tank_USD'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Capex_a_VCC_USD'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Capex_a_VCC_backup_USD'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Capex_pump_USD'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_fixed_ACH_USD'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_fixed_CCGT_USD'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_fixed_CT_USD'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_fixed_Tank_USD'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_fixed_VCC_USD'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_fixed_VCC_backup_USD'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Opex_fixed_pump_USD'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Capex_a_PV_USD'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Substation_costs_USD'] + \
                                                                           data_processed.loc[individual_code][
                                                                               'Network_costs_USD']

                data_processed.loc[individual_code]['Capex_Total_USD'] = data_processed.loc[individual_code][
                                                                         'Capex_Centralized_USD'] + \
                                                                     data_processed.loc[individual_code][
                                                                         'Capex_Decentralized_USD']
                data_processed.loc[individual_code]['Opex_Total_USD'] = data_processed.loc[individual_code][
                                                                        'Opex_Centralized_USD'] + \
                                                                    data_processed.loc[individual_code][
                                                                        'Opex_Decentralized_USD']

        individual_names = ['ind' + str(i) for i in data_processed.index.values]
        data_processed['indiv'] = individual_names
        data_processed.set_index('indiv', inplace=True)
        return data_processed

    def preprocessing_multi_criteria_data(self):
        return self.cache.lookup(data_path=os.path.join(self.category_name, 'preprocessing_multi_criteria_data'),
                                 plot=self, producer=self._preprocessing_multi_criteria_data)

    def _preprocessing_multi_criteria_data(self):
        try:
            data_multi_criteria = pd.read_csv(self.locator.get_multi_criteria_analysis(self.generation))
        except IOError:
            raise IOError("Please run the multi-criteria analysis tool first for the generation {}".format(
                self.generation))
        return data_multi_criteria

    def preprocessing_capacities_data(self):
        return self.cache.lookup(data_path=os.path.join(self.category_name, 'preprocessing_capacities_data'),
                                 plot=self, producer=self._preprocessing_capacities_data)

    def _preprocessing_capacities_data(self):
        data_generation = self.preprocessing_generations_data()
        column_names = ['Lake_kW', 'VCC_LT_kW', 'VCC_HT_kW', 'single_effect_ACH_LT_kW',
                        'single_effect_ACH_HT_kW', 'DX_kW', 'CHP_CCGT_thermal_kW',
                        'Storage_thermal_kW', 'CT_kW', 'Buildings Connected Share']
        individual_index = data_generation['individual_barcode'].index.values
        capacities_of_generation = pd.DataFrame(np.zeros([len(individual_index), len(column_names)]),
                                                columns=column_names)

        for i, ind in enumerate(individual_index):

            data_address_individual = self.data_address[self.data_address['individual_list'] == ind]

            # points to the correct file to be referenced from optimization folders
            generation_pointer = data_address_individual['generation_number_address'].values[0]
            individual_pointer = data_address_individual['individual_number_address'].values[0]
            district_supply_sys, building_connectivity = supply_system_configuration(generation_pointer,
                                                                                     individual_pointer, self.locator,
                                                                                     self.network_type)

            for name in column_names:
                if name is 'Buildings Connected Share':
                    connected_buildings = len(building_connectivity.loc[building_connectivity.Type == "CENTRALIZED"])
                    total_buildings = connected_buildings + len(
                        building_connectivity.loc[building_connectivity.Type == "DECENTRALIZED"])
                    capacities_of_generation.iloc[i][name] = np.float(connected_buildings * 100 / total_buildings)
                else:
                    capacities_of_generation.iloc[i][name] = district_supply_sys[name].sum()

        capacities_of_generation['indiv'] = individual_index
        capacities_of_generation.set_index('indiv', inplace=True)
        return capacities_of_generation


if __name__ == '__main__':
    # run all the plots in this category
    config = cea.config.Configuration()
    from cea.plots.categories import list_categories
    from cea.plots.cache import NullPlotCache, PlotCache
    import time

    def plot_category(cache):
        for category in list_categories():
            if category.label != label:
                continue
            print('category:', category.name, ':', category.label)
            for plot_class in category.plots:
                print('plot_class:', plot_class)
                parameters = {
                    k: config.get(v) for k, v in plot_class.expected_parameters.items()
                }
                plot = plot_class(config.project, parameters=parameters, cache=cache)
                assert plot.name, 'plot missing name: %s' % plot
                assert plot.category_name == category.name
                print('plot:', plot.name, '/', plot.id(), '/', plot.title)

                # plot the plot!
                plot.plot()


    null_plot_cache = NullPlotCache()
    plot_cache = PlotCache(config.project)

    # test plots with cache
    t0 = time.time()
    for i in range(3):
        plot_category(plot_cache)
    time_with_cache = (time.time() - t0) / 3

    # test plots without cache
    t0 = time.time()
    for i in range(3):
        plot_category(null_plot_cache)
    time_without_cache = (time.time() - t0) / 3

    print('Average without cache: %.2f seconds' % time_without_cache)
    print('Average with cache: %.2f seconds' % time_with_cache)
