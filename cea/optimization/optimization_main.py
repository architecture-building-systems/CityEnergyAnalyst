"""
============================
multi-objective optimization
============================

"""

from __future__ import division

import cea.optimization.master.master_main as mM
import pandas as pd

import cea.globalvar
import cea.optimization.ntwOpt.NtwMain as ntwM
from cea.optimization.preprocessing.preprocessing import preproccessing

"""
============================
optimization
============================

"""


def moo_optimization(locator, weather_file, gv):

    # read total demand file and names and number of all buildings
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    gv.num_tot_buildings = total_demand.Name.count()

    print "PREPROCESSING + SINGLE BUILDING OPTIMIZATION"
    extraCosts, extraCO2, extraPrim, solarFeat = preproccessing(locator, total_demand, building_names, weather_file, gv)

    print "NETWORK OPTIMIZATION"
    ntwFeat = ntwM.ntwMain2()     #ntwMain2 -linear, #ntwMain - optimization

    print "CONVERSION AND STORAGE OPTIMIZATION"
    # main optimization routine
    mM.EA_Main(locator, building_names, extraCosts, extraCO2, extraPrim, solarFeat, ntwFeat, gv)


"""
============================
test
============================

"""
def test_optimization_main(scenario_path=None):
    """
    run the whole optimization routine
    """
    import cea.inputlocator
    gv = cea.globalvar.GlobalVariables()

    if scenario_path is None:
        scenario_path = gv.scenario_reference

    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    weather_file = locator.get_default_weather()
    moo_optimization(locator=locator, weather_file= weather_file, gv=gv)

    print 'test_optimization_main() succeeded'


if __name__ == '__main__':
    test_optimization_main()

