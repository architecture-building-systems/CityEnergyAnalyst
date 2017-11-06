"""
multi-objective optimization of supply systems for the CEA
"""

from __future__ import division

import pandas as pd

import cea.optimization.distribution.network_opt_main as network_opt
import cea.optimization.master.master_main as master
from cea.optimization.preprocessing.preprocessing_main import preproccessing

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-an Ngugen", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


# optimization

def moo_optimization(locator, weather_file, gv):
    '''
    This function optimizes the conversion, storage and distribution systems of a heating distribution for the case study.
    It requires that solar technologies be calculated in advance and nodes of a distribution should have been already generated.

    :param locator: path to input locator
    :param weather_file: path to weather file
    :param gv: global variables class
    :type locator: string
    :type weather_file: string
    :type gv: class

    :returns: None
    :rtype: Nonetype
    '''

    # read total demand file and names and number of all buildings
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    gv.num_tot_buildings = total_demand.Name.count()

    # pre-process information regarding resources and technologies (they are treated before the optimization)
    # optimize best systems for every individual building (they will compete against a district distribution solution)
    print "PRE-PROCESSING + SINGLE BUILDING OPTIMIZATION"
    extra_costs, extra_CO2, extra_primary_energy, solarFeat = preproccessing(locator, total_demand, building_names,
                                                                   weather_file, gv)

    # optimize the distribution and linearize the results(at the moment, there is only a linearization of values in Zug)
    print "NETWORK OPTIMIZATION"
    network_features = network_opt.network_opt_main()

    # optimize conversion systems
    print "CONVERSION AND STORAGE OPTIMIZATION"
    master.evolutionary_algo_main(locator, building_names, extra_costs, extra_CO2, extra_primary_energy, solarFeat,
                                  network_features, gv)


#============================
#test
#============================


def run_as_script(scenario_path=None):
    """
    run the whole optimization routine
    """
    import cea.globalvar
    import cea.config
    config = cea.config.Configuration()
    gv = cea.globalvar.GlobalVariables()

    locator = cea.inputlocator.InputLocator(scenario_path=config.scenario)
    weather_file = config.weather
    moo_optimization(locator=locator, weather_file= weather_file, gv= gv)

    print 'test_optimization_main() succeeded'

if __name__ == '__main__':
    run_as_script()

