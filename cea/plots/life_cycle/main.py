"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import pandas as pd

import cea.config
import cea.inputlocator
from cea.plots.life_cycle.emissions import emissions
from cea.plots.life_cycle.emissions_intensity import emissions_intensity
from cea.plots.life_cycle.operation_costs import operation_costs_district
from cea.plots.life_cycle.primary_energy import primary_energy
from cea.plots.life_cycle.primary_energy_intensity import primary_energy_intensity

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
    buildings = config.plots.buildings

    # initialize class
    plots = Plots(locator, buildings)
    category = "basic//life-cycle"

    if len(buildings) == 1:  # when only one building is passed.
        plots.operation_costs(category)
        plots.emissions(category)
        plots.emissions_intensity(category)
        plots.primary_energy(category)
        plots.primary_energy_intensity(category)
    else:  # when two or more buildings are passed
        plots.operation_costs(category)
        plots.emissions(category)
        plots.emissions_intensity(category)
        plots.primary_energy(category)
        plots.primary_energy_intensity(category)


class Plots(object):

    def __init__(self, locator, buildings):
        self.locator = locator
        self.analysis_fields_costs = ['DC_cs_cost_yr',
                                      'DC_cdata_cost_yr',
                                      'DC_cre_cost_yr',
                                      'DH_ww_cost_yr',
                                      'DH_hs_cost_yr',
                                      'SOLAR_ww_cost_yr',
                                      'SOLAR_hs_cost_yr',
                                      'GRID_cost_yr',
                                      'PV_cost_yr',
                                      'NG_hs_cost_yr',
                                      'COAL_hs_cost_yr',
                                      'OIL_hs_cost_yr',
                                      'WOOD_hs_cost_yr',
                                      'NG_ww_cost_yr',
                                      'COAL_ww_cost_yr',
                                      'OIL_ww_cost_yr',
                                      'WOOD_ww_cost_yr'
                                      ]
        self.analysis_fields_emissions = ['E_ghg_ton', 'O_ghg_ton', 'M_ghg_ton']
        self.analysis_fields_emissions_m2 = ['E_ghg_kgm2', 'O_ghg_kgm2', 'M_ghg_kgm2']
        self.analysis_fields_primary_energy = ['E_nre_pen_GJ', 'O_nre_pen_GJ', 'M_nre_pen_GJ']
        self.analysis_fields_primary_energy_m2 = ['E_nre_pen_MJm2', 'O_nre_pen_MJm2', 'M_nre_pen_MJm2']
        self.buildings = self.preprocess_buildings(buildings)
        self.data_processed = self.preprocessing_building_costs()
        self.data_processed_emissions = self.preprocessing_building_emissions()
        self.plot_title_tail = self.preprocess_plot_title(buildings)
        self.plot_output_path_header = self.preprocess_plot_outputpath(buildings)

    def preprocess_plot_outputpath(self, buildings):
        if buildings == []:  # get all buildings of the district if not indicated a single building
            return "District"
        elif len(buildings) == 1:
            return "Building_" + str(buildings[0])
        else:
            return "District"

    def preprocess_plot_title(self, buildings):
        if buildings == []:  # get all buildings of the district if not indicated a single building
            return " for District"
        elif len(buildings) == 1:
            return " for Building " + str(buildings[0])
        else:
            return " for Selected Buildings"

    def preprocess_buildings(self, buildings):
        if buildings == []:  # get all buildings of the district if not indicated a single building
            return self.locator.get_zone_building_names()
        else:
            return buildings

    def preprocessing_building_costs(self):
        data_raw = pd.read_csv(self.locator.get_costs_operation_file()).set_index('Name')
        self.analysis_fields_costs = self.erase_zeros(data_raw, self.analysis_fields_costs)
        data_processed = data_raw[self.analysis_fields_costs]
        return data_processed.ix[self.buildings]

    def erase_zeros(self, data, fields):
        analysis_fields_no_zero = []
        for field in fields:
            sum = data[field].sum()
            if sum > 0:
                analysis_fields_no_zero += [field]
        return analysis_fields_no_zero

    def preprocessing_building_emissions(self):
        data_raw_embodied_emissions = pd.read_csv(self.locator.get_lca_embodied()).set_index('Name')
        data_raw_operation_emissions = pd.read_csv(self.locator.get_lca_operation()).set_index('Name')
        data_raw_mobility_emissions = pd.read_csv(self.locator.get_lca_mobility()).set_index('Name')
        data_processed = data_raw_embodied_emissions.join(data_raw_operation_emissions, lsuffix='y').join(
            data_raw_mobility_emissions, lsuffix='y2')
        return data_processed.ix[self.buildings]

    def operation_costs(self, category):
        title = "Operation Costs" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_operation_costs',
                                                             category)
        data = self.data_processed
        return operation_costs_district(data, self.analysis_fields_costs, title, output_path)

    def emissions(self, category):
        title = "Green House Gas Emissions" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_emissions', category)
        data = self.data_processed_emissions
        return emissions(data, self.analysis_fields_emissions, title, output_path)

    def emissions_intensity(self, category):
        title = "Green House Gas Emissions intensity" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_emissions_intensity',
                                                             category)
        data = self.data_processed_emissions
        return emissions_intensity(data, self.analysis_fields_emissions_m2, title, output_path)

    def primary_energy(self, category):
        title = "Primary energy (non-renewable)" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_primary_energy', category)
        data = self.data_processed_emissions
        return primary_energy(data, self.analysis_fields_primary_energy, title, output_path)

    def primary_energy_intensity(self, category):
        title = "Primary energy intensity (non-renewable)" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_primary_energy_intensity',
                                                             category)
        data = self.data_processed_emissions
        return primary_energy_intensity(data, self.analysis_fields_primary_energy_m2, title, output_path)


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.scenario)

    plots_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
