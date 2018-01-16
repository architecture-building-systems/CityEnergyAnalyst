"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import os
import json
import cea.config
import cea.inputlocator
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




def dashboard(locator, config):

    # Local Variables
    final_generation = 500
    generations = [400, 500]

    if generations == []:
        generations = [config.ngen]

    data = []
    for i in generations:
        with open(locator.get_optimization_checkpoint(i), "rb") as fp:
            data.append(json.load(fp))

    # Create Pareto Curve multiple generations
    output_path = locator.get_timeseries_plots_file("District" + '_Pareto_curve_over_generations')
    title = 'Pareto Curve for District'
    pareto_curve_over_generations(data, generations, title, output_path)

    # CREATE PARETO CURVE FINAL GENERATION
    with open(locator.get_optimization_checkpoint(final_generation), "rb") as fp:
        data = json.load(fp)
    output_path = locator.get_timeseries_plots_file("District" + '_Pareto_curve')
    title = 'Pareto Curve for District'
    pareto_curve(data, title, output_path)



def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.scenario)

    dashboard(locator, config)

if __name__ == '__main__':
    main(cea.config.Configuration())
