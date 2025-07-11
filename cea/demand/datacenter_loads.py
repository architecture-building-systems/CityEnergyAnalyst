"""
datacenter loads
"""
from __future__ import annotations
from typing import TYPE_CHECKING

import numpy as np
from cea.technologies import heatpumps
from cea.constants import HOURS_IN_YEAR
from cea.demand.constants import T_C_DATA_SUP_0, T_C_DATA_RE_0

if TYPE_CHECKING:
    from cea.demand.building_properties.building_properties_row import BuildingPropertiesRow
    from cea.demand.time_series_data import TimeSeriesData

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Martin Mosteiro"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def has_data_load(bpr: BuildingPropertiesRow):
    """
    Checks if building has a data center load

    :param bpr: BuildingPropertiesRow
    :type bpr: cea.demand.building_properties.BuildingPropertiesRow
    :return: True or False
    :rtype: bool
        """

    if bpr.internal_loads['Ed_Wm2'] > 0.0:
        return True
    else:
        return False


def calc_Edata(tsd: TimeSeriesData, schedules) -> TimeSeriesData:

    tsd.electrical_loads.Edata = schedules['Ed_W']

    return tsd

def calc_mcpcdata(Qcdata_sys):
    if Qcdata_sys > 0.0:
        Tcdata_sys_re = T_C_DATA_RE_0
        Tcdata_sys_sup = T_C_DATA_SUP_0
        mcpcdata_sys = Qcdata_sys / (Tcdata_sys_re - Tcdata_sys_sup)
    else:
        Tcdata_sys_re = np.nan
        Tcdata_sys_sup = np.nan
        mcpcdata_sys = 0.0
    return mcpcdata_sys, Tcdata_sys_re, Tcdata_sys_sup

def calc_Qcdata_sys(bpr: BuildingPropertiesRow, tsd: TimeSeriesData) -> TimeSeriesData:
    # calculate cooling loads for data center
    tsd.cooling_loads.Qcdata = 0.9 * tsd.electrical_loads.Edata * -1.0  # cooling loads are negative

    # calculate distribution losses for data center cooling analogously to space cooling distribution losses
    Y = bpr.building_systems['Y'][0]
    Lv = bpr.building_systems['Lv']
    Qcdata_d_ls = ((T_C_DATA_SUP_0 + T_C_DATA_RE_0) / 2.0 - tsd.weather.T_ext) * (tsd.cooling_loads.Qcdata / np.nanmin(tsd.cooling_loads.Qcdata)) * (
                Lv * Y)
    # calculate system loads for data center
    #WHATCHOUT! if we change it, then the optimization use of wasteheat breaks. mcpdata has to be positive and Qcdata_sys too!
    tsd.cooling_loads.Qcdata_sys = abs(tsd.cooling_loads.Qcdata + Qcdata_d_ls) # convert to positive so we get the mcp in positive numbers
    tsd.cooling_system_mass_flows.mcpcdata_sys, tsd.cooling_system_temperatures.Tcdata_sys_re, tsd.cooling_system_temperatures.Tcdata_sys_sup = np.vectorize(calc_mcpcdata)(abs(tsd.cooling_loads.Qcdata_sys))

    return tsd


def calc_Qcdataf(locator, bpr: BuildingPropertiesRow, tsd: TimeSeriesData) -> TimeSeriesData:
    """
    it calculates final loads
    """
    # GET SYSTEMS EFFICIENCIES
    energy_source = bpr.supply["source_cs"]
    scale_technology = bpr.supply["scale_cs"]
    efficiency_average_year = bpr.supply["eff_cs"]
    if scale_technology == "BUILDING":
        if energy_source == "GRID":
            t_source = (tsd.weather.T_ext + 273)

            # heat pump energy
            tsd.electrical_loads.E_cdata = np.vectorize(heatpumps.HP_air_air)(tsd.cooling_system_mass_flows.mcpcdata_sys, (tsd.cooling_system_temperatures.Tcdata_sys_sup + 273),
                                                                (tsd.cooling_system_temperatures.Tcdata_sys_re + 273), t_source)
            # final to district is zero
            tsd.cooling_loads.DC_cdata = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "NONE":
            tsd.cooling_loads.DC_cdata = np.zeros(HOURS_IN_YEAR)
            tsd.electrical_loads.E_cdata = np.zeros(HOURS_IN_YEAR)
        else:
            raise Exception('check potential error in input database of ALL IN ONE SYSTEMS / COOLING')

    elif scale_technology == "DISTRICT":
        tsd.cooling_loads.DC_cdata = tsd.cooling_loads.Qcdata_sys / efficiency_average_year
        tsd.electrical_loads.E_cdata = np.zeros(HOURS_IN_YEAR)
    elif scale_technology == "NONE":
        tsd.cooling_loads.DC_cdata = np.zeros(HOURS_IN_YEAR)
        tsd.electrical_loads.E_cdata = np.zeros(HOURS_IN_YEAR)
    else:
        raise Exception('check potential error in input database of ALL IN ONE SYSTEMS / COOLING')
    return tsd

