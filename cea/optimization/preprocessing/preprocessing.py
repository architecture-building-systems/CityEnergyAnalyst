"""
============================
pre-processing algorithm
============================

"""

from __future__ import division
import cea.optimization.preprocessing.processheat as hpMain
from cea.technologies import substation as subsM
from cea.optimization.preprocessing import decentralized_buildings as dbM
from cea.optimization.master import summarize_network_main as nM
from cea.optimization.preprocessing import electricity
import cea.optimization.supportFn as sFn

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Thuy-An Nguyen", "Tim Vollrath"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def preproccessing(locator, gv):

    print "Run substation model for each building separately"
    subsM.subsMain(locator.pathRaw, locator.pathSubsRes, locator.get_total_demand(), 1, gv) # 1 if disconected buildings are calculated

    print "Heating operation pattern for disconnected buildings"
    dbM.discBuildOp(locator, gv)

    print "Create network file with all buildings connected"
    nM.Network_Summary(locator.pathRaw, locator.pathRaw, locator.pathSubsRes, locator.pathNtwRes, locator.pathNtwLayout, "Total.csv", gv)

    print "Solar features extraction"
    solarFeat = sFn.solarRead(locator, gv)

    print "electricity"
    elecCosts, elecCO2, elecPrim = electricity.calc_pareto_electricity(locator, gv)
    print elecCosts, elecCO2, elecPrim, "elecCosts, elecCO2, elecPrim \n"

    print "Process Heat "
    hpCosts, hpCO2, hpPrim = hpMain.calc_pareto_Qhp(locator, gv)

    extraCosts = elecCosts + hpCosts
    extraCO2 = elecCO2 + hpCO2
    extraPrim = elecPrim + hpPrim

    return extraCosts, extraCO2, extraPrim, solarFeat