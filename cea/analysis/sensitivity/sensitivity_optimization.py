"""
Sensitivity analysis
"""
from __future__ import division

import os

from cea import globalvar as glob
# import cea.globalVar as glob
import cea.optimization.conversion_storage.master.evaluation as eI
import numpy as np
from deap import base
from deap import creator
from deap import tools

import cea.optimization.conversion_storage.master.selection as sel
import cea.optimization.supportFn as sFn

__author__ = "Tim Vollrath"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Tim Vollrath"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class sensBandwidth(object):
    def __init__(self):
        
        # Number of factors to test
        self.nFactors = 3
        
        # Electricity price
        self.minElec = -0.1
        self.maxElec = 0.1
        
        # Natural gas
        self.minNG = -0.1
        self.maxNG = 0.1

        # Biogas
        self.minBG = -0.1
        self.maxBG = 0.1

def sensAnalysis(locator, extraCosts, extraCO2, extraPrim, solarFeat, ntwFeat, gen):

    gV = glob.GlobalVariables()
    step = gV.sensibilityStep

    bandwidth = sensBandwidth()

    os.chdir(locator.get_optimization_master_results_folder())
    pop, eps, testedPop = sFn.readCheckPoint(locator, gen, 0)
    toolbox = base.Toolbox()


    os.chdir(locator.pathRaw)
    buildList = sFn.extractList("Total.csv")

    ParetoResults = np.zeros( len(pop) )
    FactorResults = np.zeros((step + 1, bandwidth.nFactors * 2))

    def sensOneFactor(obj, factor_name, mini, maxi, colNumber):
        iniValue = getattr(obj, factor_name)
        index = 0
                
        for delta in np.arange(mini, maxi + 1E-5, (maxi-mini)/step):
            FactorResults[index][colNumber + 0] = delta
            if abs(delta) > 1E-10:
                setattr(obj, factor_name, iniValue * (1+delta))
    
                newpop = []
                for ind in pop:
                    newInd = toolbox.clone(ind)
                    newpop.append(newInd)
                    (costs, CO2, prim) = eI.evaluation_main(newInd, buildList, locator, extraCosts, extraCO2, extraPrim, solarFeat, ntwFeat, obj)
                    newInd.fitness.values = (costs, CO2, prim)
                
                selection = sel.selectPareto(newpop)
                for i in range(len(newpop)):
                    if newpop[i] in selection:
                        ParetoResults[i] += 1
                
                FactorResults[index][colNumber + 1] = len(newpop) - len(selection)

            index += 1

        setattr(obj, factor_name, iniValue)

    
    sensOneFactor(gV, 'ELEC_PRICE', bandwidth.minElec, bandwidth.maxElec, 0)
    sensOneFactor(gV, 'NG_PRICE', bandwidth.minNG, bandwidth.maxNG, 2)
    sensOneFactor(gV, 'BG_PRICE', bandwidth.minBG, bandwidth.maxBG, 4)
    
    indexSensible = FactorResults.argmax()%(2*bandwidth.nFactors)
    if indexSensible == 1:
        mostSensitive = 'Electricity price'
    elif indexSensible == 3:
        mostSensitive = 'NG price'
    else:
        mostSensitive = 'BG price'

    print ParetoResults
    print FactorResults
    print mostSensitive
    return ParetoResults, FactorResults, mostSensitive

gen = 24
def run_as_script(scenario_path=None):
    """
    run the whole optimization routine
    """
    import cea.globalvar
    import pandas as pd
    import cea.optimization.distribution.network_opt_main as network_opt
    from cea.optimization.preprocessing.preprocessing_main import preproccessing
    gv = cea.globalvar.GlobalVariables()

    if scenario_path is None:
        scenario_path = gv.scenario_reference

    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)


    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    gv.num_tot_buildings = total_demand.Name.count()


    weather_file = locator.get_default_weather()

    extraCosts, extraCO2, extraPrim, solarFeat = preproccessing(locator, total_demand, building_names,
                                                                   weather_file, gv)
    ntwFeat = network_opt.network_opt_main()
    sensAnalysis(locator, extraCosts, extraCO2, extraPrim, solarFeat, ntwFeat, gen)

    print 'test_optimization_main() succeeded'

if __name__ == '__main__':
    run_as_script(r'C:\reference-case-zug\baseline')