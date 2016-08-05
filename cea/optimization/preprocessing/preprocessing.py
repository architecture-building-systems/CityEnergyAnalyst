"""
============================
pre-processing algorithm
============================

"""

from __future__ import division
import cea.optimization.preprocessing.processheat as hpMain
import pandas as pd
from cea.technologies import substation as subsM
from cea.optimization.preprocessing import decentralized_buildings as dbM
from cea.optimization.master import summarize_network_main as nM
from cea.optimization.preprocessing import electricity
from cea.utilities import  epwreader
from cea.resources import geothermal
import cea.optimization.supportFn as sFn

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Thuy-An Nguyen", "Tim Vollrath"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def preproccessing(locator, weather_file, gv):

    # read total demand file and names and number of all buildings
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    gv.num_tot_buildings = total_demand.Name.count()

    # read weather and calculate ground temperature
    T_ambient = epwreader.epw_reader(weather_file)['drybulb_C']
    gv.ground_temperature = geothermal.calc_ground_temperature(T_ambient.values, gv)

    print "Run substation model for each building separately"
    #subsM.subsMain(locator, total_demand, building_names, gv, Flag = True) # 1 if disconected buildings are calculated

    print "Heating operation pattern for disconnected buildings"
    #dbM.discBuildOp(locator, building_names, gv)

    print "Create network file with all buildings connected"
    #nM.Network_Summary(locator, total_demand, building_names, gv Flag = True)

    print "Solar features extraction"
    solarFeat = sFn.solarRead(locator, gv)

    print "electricity"
    elecCosts, elecCO2, elecPrim = electricity.calc_pareto_electricity(locator, gv)

    extraCosts = elecCosts
    extraCO2 = elecCO2
    extraPrim = elecPrim

    return extraCosts, extraCO2, extraPrim, solarFeat