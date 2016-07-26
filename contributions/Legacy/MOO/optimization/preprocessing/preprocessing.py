"""
============================
pre-processing algorithm
============================

"""

from __future__ import division
import contributions.Legacy.MOO.optimization.preprocessing.processheat as hpMain
from contributions.Legacy.MOO.technologies import substation as subsM
from contributions.Legacy.MOO.optimization.preprocessing import decentralized_buildings as dbM
from contributions.Legacy.MOO.optimization.master import summarize_network_main as nM
from contributions.Legacy.MOO.optimization.preprocessing import electricity
import contributions.Legacy.MOO.optimization.supportFn as sFn

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Thuy-An Nguyen", "Tim Vollrath"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def preproccessing(pathX, gV):

    print "Run substation model for each building separately"
    subsM.subsMain(pathX.pathRaw, pathX.pathRaw, pathX.pathSubsRes, "Total.csv", 1, gV) # 1 if disconected buildings are calculated

    print "Heating operation pattern for disconnected buildingsn"
    dbM.discBuildOp(pathX, gV)

    print "Create network file with all buildings connected"
    nM.Network_Summary(pathX.pathRaw, pathX.pathRaw, pathX.pathSubsRes, pathX.pathNtwRes, pathX.pathNtwLayout, "Total.csv", gV)

    print "Solar features extraction"
    solarFeat = sFn.solarRead(pathX, gV)

    print "electricity"
    elecCosts, elecCO2, elecPrim = electricity.calc_pareto_electricity(pathX, gV)
    print elecCosts, elecCO2, elecPrim, "elecCosts, elecCO2, elecPrim \n"

    print "Process Heat "
    hpCosts, hpCO2, hpPrim = hpMain.calc_pareto_Qhp(pathX, gV)

    extraCosts = elecCosts + hpCosts
    extraCO2 = elecCO2 + hpCO2
    extraPrim = elecPrim + hpPrim

    return extraCosts, extraCO2, extraPrim, solarFeat