"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function


import cea.config
import cea.inputlocator
import time
from cea.plots.life_cycle.operation_costs import operation_costs_district
import pandas as pd

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"



def plots_main(locator, config):

    # initialize timer
    t0 = time.clock()

    # local variables
    buildings = config.dashboard.buildings

    # initialize class
    plots = Plots(locator, buildings)

    if len(buildings) == 1: #when only one building is passed.
        plots.operation_costs()
    else:                   # when two or more buildings are passed
        plots.operation_costs()


    # print execution time
    time_elapsed = time.clock() - t0
    print('done - time elapsed: %d.2f seconds' % time_elapsed)

class Plots():

    def __init__(self, locator, buildings):
        self.locator = locator
        self.analysis_fields = ['Qhsf_cost_yr', 'Qwwf_cost_yr', 'QCf_cost_yr', 'Ef_cost_yr']
        self.analysis_fields_m2 = ['Qhsf_cost_m2yr', 'Qwwf_cost_m2yr', 'QCf_cost_m2yr', 'Ef_cost_m2yr']
        self.buildings = self.preprocess_buildings(buildings)
        self.data_processed = self.preprocessing_building_demand()
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

    def preprocessing_building_demand(self):
        data_raw = pd.read_csv(self.locator.get_costs_operation_file()).set_index('Name')
        data_processed = data_raw[self.analysis_fields + self.analysis_fields_m2]
        return data_processed.ix[self.buildings]

    def operation_costs(self):
        title = "Operation costs"+ self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_operation_costs')
        data = self.data_processed
        operation_costs_district(data, self.analysis_fields, self.analysis_fields_m2, title, output_path)

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.scenario)

    plots_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
