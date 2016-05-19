"""
====================
Sensitivity analysis
====================

"""
from __future__ import division
import os
import globalVar as glob
import supportFn as sFn
import evaluateInd as eI
from deap import base
import evolAlgo.Selection as sel
import numpy as np

reload(glob)
reload(sFn)
reload(eI)
reload(sel)


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
        
        
def sensAnalysis(step, pathX, extraCosts, extraCO2, extraPrim, solarFeat, ntwFeat, gen, bandwidth):

    os.chdir(pathX.pathMasterRes)
    pop, eps, testedPop = sFn.readCheckPoint(pathX, gen, 0)
    toolbox = base.Toolbox()
    
    os.chdir(pathX.pathRaw)
    buildList = sFn.extractList("Total.csv")
    
    gV = glob.globalVariables()
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
                    (costs, CO2, prim) = eI.evalInd(newInd, buildList, pathX, extraCosts, extraCO2, extraPrim, solarFeat, ntwFeat, obj)
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
        
    return ParetoResults, FactorResults, mostSensitive
    