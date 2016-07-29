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


def moo_optimization(pathX, gv):

    # call pre-processing
    extraCosts, extraCO2, extraPrim, solarFeat = preproccessing(pathX, gv)

    # network optimization
    ntwFeat = ntwM.ntwMain2()     #ntwMain2 -linear, #ntwMain - optimization

    # main optimization routine
    mM.EA_Main(pathX, extraCosts, extraCO2, extraPrim, solarFeat, ntwFeat, gv)


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

    if scenario_path is None:
        scenario_path = r'c:\reference-case\baseline'

    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    gv = cea.globalvar.GlobalVariables()

    moo_optimization(pathX=locator, gv=gv)

    print 'test_optimization_main() succeeded'


if __name__ == '__main__':
    test_optimization_main()

