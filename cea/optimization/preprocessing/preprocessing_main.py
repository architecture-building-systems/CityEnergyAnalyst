"""
============================
pre-processing algorithm
============================

"""

from __future__ import division

import cea.optimization.preprocessing.extra_services.processheat as process_heat
from cea.optimization.conversion_storage.master import summarize_network_main
from cea.optimization.preprocessing.baseline import decentralized_buildings
from cea.optimization.preprocessing.extra_services import electricity
from cea.resources import geothermal
from cea.technologies import substation
from cea.utilities import  epwreader

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Thuy-An Nguyen", "Tim Vollrath"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def preproccessing(locator, total_demand, building_names, weather_file, gv):
    '''
    This function aims at preprocessing all data for the optimization.

    :param locator: path to locator function
    :param total_demand: dataframe with total demand and names of all building in the area
    :param building_names: dataframe with names of all buildings in the area
    :param weather_file: path to wather file
    :param gv: path to global variables class
    :return:

    extraCosts: extra pareto optimal costs due to electricity and process heat (
    these are treated separately and not considered inside the optimization)
    extraCO2: extra pareto optimal emissions due to electricity and process heat (
    these are treated separately and not considered inside the optimization)
    extraPrim: extra pareto optimal primary energy due to electricity and process heat (
    these are treated separately and not considered inside the optimization)
    solar_features: extraction of solar features form the results of the solar technologies calculation.
    '''

    # GET ENERGY POTENTIALS
    # geothermal
    T_ambient = epwreader.epw_reader(weather_file)['drybulb_C']
    gv.ground_temperature = geothermal.calc_ground_temperature(T_ambient.values, gv)

    # solar
    print "Solar features extraction"
    solar_features = solarRead(locator, gv)

    # GET LOADS IN SUBSTATIONS
    # prepocess space heating, domestic hot water and space cooling to substation.
    print "Run substation model for each building separately"
    substation.substation_main(locator, total_demand, building_names, gv, Flag = True) # True if disconected buildings are calculated

    # GET COMPETITIVE ALTERNATIVES TO A NETWORK
    # estimate what would be the operation of single buildings only for heating.
    # For cooling all buildings are assumed to be connected to the cooling distribution on site.
    print "Heating operation pattern for single buildings"
    decentralized_buildings.decentralized_main(locator, building_names, gv)

    # GET DH NETWORK
    # at first estimate a distribution with all the buildings connected at it.
    print "Create distribution file with all buildings connected"
    summarize_network_main.network_main(locator, total_demand, building_names, gv, "all") #"_all" key for all buildings

    # GET EXTRAS
    # estimate the extra costs, emissions and primary energy of electricity.
    print "electricity"
    elecCosts, elecCO2, elecPrim = electricity.calc_pareto_electricity(locator, gv)

    # estimate the extra costs, emissions and primary energy for process heat
    print "Process-heat"
    hpCosts, hpCO2, hpPrim = process_heat.calc_pareto_Qhp(locator, total_demand, gv)

    extraCosts = elecCosts + hpCosts
    extraCO2 = elecCO2 + hpCO2
    extraPrim = elecPrim + hpPrim

    return extraCosts, extraCO2, extraPrim, solar_features


class solarFeatures(object):
    def __init__(self):
        self.SolarArea = 35710  # [m2]

        self.PV_Peak = 5680.8  # [kW_el]
        self.PVT_Peak = 849  # [kW_el]
        self.PVT_Qnom = 24512E3  # [W_th]
        self.SC_Qnom = 17359E3  # [W_th]


def solarRead(locator, gV):
    """
    Extract the appropriate solar features

    Parameters
    ----------
    locator : string
        path to raw solar files

    Returns
    -------
    solarFeat : solarFeatures
        includes : the total solar area
        the PV electrical peak production [kW]
        the PVT electrical peak production [kW]
        the PVT heating peak production [Wth]
        the SC heating peak production [Wth]

    """
    solarFeat = solarFeatures()

    PVarray = extractDemand(locator.pathSolarRaw + "/Pv.csv", ["PV_kWh"], gV.DAYS_IN_YEAR)
    solarFeat.PV_Peak = np.amax(PVarray)

    PVarray = extractDemand(locator.pathSolarRaw + "/Pv.csv", ["Area"], gV.DAYS_IN_YEAR)
    solarFeat.SolarAreaPV = PVarray[0][0]

    PVTarray = extractDemand(locator.pathSolarRaw + "/PVT_35.csv", ["PV_kWh"], gV.DAYS_IN_YEAR)
    solarFeat.PVT_Peak = np.amax(PVTarray)

    PVTarray = extractDemand(locator.pathSolarRaw + "/PVT_35.csv", ["Qsc_KWh"], gV.DAYS_IN_YEAR)
    solarFeat.PVT_Qnom = np.amax(PVTarray) * 1000

    PVTarray = extractDemand(locator.pathSolarRaw + "/PVT_35.csv", ["Area"], gV.DAYS_IN_YEAR)
    solarFeat.SolarAreaPVT = PVTarray[0][0]

    SCarray = extractDemand(locator.pathSolarRaw + "/SC_75.csv", ["Qsc_Kw"], gV.DAYS_IN_YEAR)
    solarFeat.SC_Qnom = np.amax(SCarray) * 1000

    SCarray = extractDemand(locator.pathSolarRaw + "/SC_75.csv", ["Area"], gV.DAYS_IN_YEAR)
    solarFeat.SolarAreaSC = SCarray[0][0]

    return solarFeat
