"""
============================
multi-objective optimization
============================

"""

########################### Import modules

from __future__ import division

import cea.optimization.master.master_main as mM
from cea.optimization.preprocessing.preprocessing import preproccessing
import cea.optimization.ntwOpt.Python.NtwMain as ntwM

"""
============================
optimization
============================

"""


def moo_optimization(locator, weather_file, gv):

    print "PREPROCESSING + SINGLE BUILDING OPTIMIZATION"
    extraCosts, extraCO2, extraPrim, solarFeat = preproccessing(locator, weather_file, gv)

    print "NETWORK OPTIMIZATION"
    ntwFeat = ntwM.ntwMain2()     #ntwMain2 -linear, #ntwMain - optimization

    print "CONVERSION AND STORAGE OPTIMIZATION"
    # main optimization routine
    mM.EA_Main(locator, extraCosts, extraCO2, extraPrim, solarFeat, ntwFeat, gv)


"""
============================
test
============================

"""
def test_optimization_main(scenario_path=None):
    """
    run the whole optimization routine
    """
    import cea.globalvar
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

