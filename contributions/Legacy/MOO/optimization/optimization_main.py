"""
============================
multi-objective optimization
============================

"""
#WINDOWS
Header = "C:\ArcGIS\ESMdata\DataFinal\MOO\HEB/"   # path to the input / output folders
CodePath = "C:\urben\MOO/"    # path to this UESM_MainZug.py file
matlabDir = "C:/Program Files/MATLAB/R2014a/bin"    # path to the Matlab core files

import sys
sys.path.append(CodePath)


########################### Import modules

from __future__ import division


import contributions.Legacy.MOO.optimization.master.evolAlgo.masterMain as mM
from contributions.Legacy.MOO.optimization.preprocessing import preproccessing
import contributions.Legacy.MOO.analysis.sensitivity as sens
import contributions.Legacy.MOO.ntwOpt.Python.NtwMain as ntwM
import contributions.Legacy.MOO.globalVar as glob


gV = glob.globalVariables()
pathX = gV.pathX

"""
============================
optimization
============================

"""


def moo_optimization(pathX, gV):

    # call pre-processing
    extraCosts, extraCO2, extraPrim, solarFeat = preproccessing(pathX, gV)

    # network optimization
    finalDir = CodePath + "ntwOpt/"
    ntwFeat = ntwM.ntwMain2(matlabDir, finalDir, Header)     #ntwMain2 -linear, #ntwMain - optimization

    # main optimization routine
    mM.EA_Main(pathX, extraCosts, extraCO2, extraPrim, solarFeat, ntwFeat, gV)


"""
============================
Analysis
============================

"""

def sensitivity_analysis(finances, extraCO2, extraPrim, solarFeat, ntwFeat, Generation, sensibilityStep):

    # sensitivity analysis
    bandwidth = sens.sensBandwidth()

    paretoResults, FactorResults, mostSensitive = sens.sensAnalysis(sensibilityStep, pathX, finances, extraCO2,
                                                                    extraPrim, solarFeat, ntwFeat, Generation, bandwidth)
    return paretoResults, FactorResults, mostSensitive


"""
============================
test
============================

"""

Generation = 24
sensibilityStep = gV.sensibilityStep
