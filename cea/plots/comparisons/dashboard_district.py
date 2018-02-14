"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function


import cea.config
import cea.inputlocator
from cea.plots.comparisons.energy_demand import energy_demand_district
from cea.plots.comparisons.energy_use_intensity import energy_use_intensity
import time
import os
import pandas as pd

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def plots_main(config):

    # initialize timer
    t0 = time.clock()

    # local variables
    scenarios = config.dashboard.scenarios

    # initialize class
    plots = Plots(scenarios)
    plots.demand_comparison()
    plots.demand_intensity_comparison()
    plots.operation_costs_comparison()

    # print execution time
    time_elapsed = time.clock() - t0
    print('done - time elapsed: %d.2f seconds' % time_elapsed)

class Plots():

    def __init__(self, scenarios):
        self.analysis_fields_demand = ["Ef_MWhyr", "Qhsf_MWhyr", "Qwwf_MWhyr", "Qcsf_MWhyr"]
        self.analysis_fields_costs =
        self.scenarios = scenarios
        self.locator = cea.inputlocator.InputLocator(scenarios[0])
        self.data_processed_demand = self.preprocessing_demand_scenarios()
        self.data_processed_costs = self.preprocessing_costs_scenarios()

    def preprocessing_demand_scenarios(self):
        data_processed = []
        for i, scenario in enumerate(self.scenarios):
            locator = cea.inputlocator.InputLocator(scenario)
            scenario_name = os.path.basename(scenario)
            data_raw = (pd.read_csv(locator.get_total_demand())[self.analysis_fields_demand + ["GFA_m2"]]).sum(axis=0)
            data_raw_df = pd.DataFrame({scenario_name:data_raw}, index=data_raw.index).T
            if i == 0:
                data_processed = data_raw_df
            else:
                data_processed = data_processed.append(data_raw_df)
        return data_processed

    def preprocessing_costs_scenarios(self):
        data_processed = []
        for i, scenario in enumerate(self.scenarios):
            locator = cea.inputlocator.InputLocator(scenario)
            scenario_name = os.path.basename(scenario)
            data_raw = (pd.read_csv(locator.get_total_demand())[self.analysis_fields_costs + ["GFA_m2"]]).sum(axis=0)
            data_raw_df = pd.DataFrame({scenario_name:data_raw}, index=data_raw.index).T
            if i == 0:
                data_processed = data_raw_df
            else:
                data_processed = data_processed.append(data_raw_df)
        return data_processed

    def demand_comparison(self):
        title = "Energy Demand of Scenarios"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_energy_demand")
        data = self.data_processed_demand
        energy_demand_district(data, self.analysis_fields_demand, title, output_path)

    def demand_intensity_comparison(self):
        title = "Energy Use Intensity of Scenarios"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_energy_use_intensity")
        data = self.data_processed_demand
        energy_use_intensity(data, self.analysis_fields_demand, title, output_path)

    def operation_costs_comparison(self):
        title = "Operation Costs of Scenarios"
        output_path = self.locator.get_timeseries_plots_file("Scenarios_operation_costs")
        data = self.data_processed_costs
        energy_use_intensity(data, self.analysis_fields_costs, title, output_path)


def main(config):

    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.scenario)

    plots_main(config)


if __name__ == '__main__':
    main(cea.config.Configuration())
