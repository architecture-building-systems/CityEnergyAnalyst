"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import time

import cea.config
import cea.inputlocator

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# def check_prerequisites_solar_potential(locator):
#
#     names_building = locator.get_zone_building_names()
#     load_check_file = os.path.isfile(locator.get_radiation_building(names_building[0]))
#     if load_check_file:
#         check_flag = "OK"
#     else:
#         check_flag = "Solar potential plots were NOT created. Check the output of the solar radiation tool is consistent"
#     return check_flag

def plots_main(config):
    # initialize timer
    t0 = time.clock()

    # local variables
    categories_to_plot = config.dashboard.categories

    if "solar_potentials" in categories_to_plot:
        from cea.plots.solar_potential.dashboard_district import dashboard as dashboard_solar
        locator = cea.inputlocator.InputLocator(config.scenario)
        dashboard_solar(locator, config)
        print("solar potential plots successfully saved in plots folder of scenario: ", config.scenario)

    if "technology_potentials" in categories_to_plot:
        from cea.plots.solar_technology_potentials.dashboard_district import plot_main as dashboard_technology
        locator = cea.inputlocator.InputLocator(config.scenario)
        dashboard_technology(locator, config)
        print("technology potential plots successfully saved in plots folder of scenario: ", config.scenario)

    if "energy_demand" in categories_to_plot:
        from cea.plots.demand.dashboard_district import dashboard as dashboard_demand
        locator = cea.inputlocator.InputLocator(config.scenario)
        dashboard_demand(locator, config)
        print("energy demand plots successfully saved in plots folder of scenario: ", config.scenario)

    if "life_cycle" in categories_to_plot:
        from cea.plots.life_cycle.dashboard_district import plots_main as dashboard_lca
        locator = cea.inputlocator.InputLocator(config.scenario)
        dashboard_lca(locator, config)
        print("life cycle plots successfully saved in plots folder of scenario: ", config.scenario)

    if "optimization" in categories_to_plot:
        from cea.plots.life_cycle.dashboard_district import plots_main as dashboard_lca
        locator = cea.inputlocator.InputLocator(config.scenario)
        dashboard_lca(locator, config)
        print("optimization plots successfully saved in plots folder of scenario: ", config.scenario)

    if "scenarios_comparisons" in categories_to_plot:
        from cea.plots.comparisons.dashboard_district import plots_main as dashboard_comparisons
        dashboard_comparisons(config)
        print("scenario comparison plots successfully saved in plots folder of scenario: ", config.scenario)

    # print execution time
    time_elapsed = time.clock() - t0
    print('done - time elapsed: %d.2f seconds' % time_elapsed)

def main(config):
    # print out all configuration variables used by this script
    print("Running plots for the next categories = %s" % config.dashboard.categories)
    plots_main(config)


if __name__ == '__main__':
    main(cea.config.Configuration())
