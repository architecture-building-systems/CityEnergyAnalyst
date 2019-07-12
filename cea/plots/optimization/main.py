"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import os

import pandas as pd

import cea.config
import cea.inputlocator
from cea.analysis.multicriteria.optimization_post_processing.locating_individuals_in_generation_script import \
    locating_individuals_in_generation_script
from cea.plots.optimization.pareto_curve import pareto_curve

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "2.8"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def plots_main(locator, config):
    # local variables
    generation = locator.get_latest_generation()
    multi_criteria_flag = config.plots_optimization.multi_criteria

    if not os.path.exists(locator.get_address_of_individuals_of_a_generation(generation)):
        data_address = locating_individuals_in_generation_script(generation, locator)
    else:
        data_address = pd.read_csv(locator.get_address_of_individuals_of_a_generation(generation))

    # initialize class
    plots = Plots(locator, generation, multi_criteria_flag, data_address)

    # create plots
    plots.pareto_curve_for_one_generation()

    return


class Plots(object):

    def __init__(self, locator, generation, multi_criteria_flag, data_address):
        # local variables
        self.locator = locator
        self.generation = generation
        self.generation = generation
        self.data_address = data_address
        self.multi_criteria_flag = multi_criteria_flag
        # fields of loads in the systems of heating, cooling and electricity
        self.analysis_fields_pareto_objectives = ['TAC_sys_USD', 'GHG_sys_tonCO2', 'PEN_sys_MJoil']
        self.analysis_fields_pareto_multicriteria = ['individual',
                                                     'TAC_sys_USD',
                                                     'GHG_sys_tonCO2',
                                                     'PEN_sys_MJoil',
                                                     'Capex_total_sys_USD',
                                                     'Opex_a_sys_USD']
        self.data_processed = self.data_processing()

    def pareto_curve_for_one_generation(self):
        data = self.data_processed
        title = 'Pareto curve for generation ' + str(self.generation)
        output_path = self.locator.get_timeseries_plots_file('gen' + str(self.generation) + '_pareto_curve',
                                                             "pareto_curve")
        objectives = self.analysis_fields_pareto_objectives
        analysis_fields = self.analysis_fields_pareto_multicriteria
        plot = pareto_curve(data, objectives, analysis_fields, title, output_path)
        return plot

    def data_processing(self, locator, generation):
        # Import multi-criteria data
        if self.multi_criteria_flag:
            try:
                data_processed = pd.read_csv(locator.get_multi_criteria_analysis(generation))
            except IOError:
                raise IOError("Please run the multi-criteria analysis tool first or set multi-criteria = False")
        else:

            data_processed = pd.read_csv(locator.get_optimization_generation_total_performance(generation))
        return data_processed


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    print("Running dashboard with scenario = %s" % config.scenario)
    print("Running dashboard with the next generation = %s" % config.plots_optimization.generation)

    plots_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
