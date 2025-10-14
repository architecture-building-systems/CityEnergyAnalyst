"""
refrigeration loads
"""
from __future__ import annotations
from typing import TYPE_CHECKING

import numpy as np
from cea.technologies import heatpumps
from cea.constants import HOURS_IN_YEAR
from cea.demand.constants import T_C_REF_SUP_0, T_C_REF_RE_0

if TYPE_CHECKING:
    from cea.demand.building_properties.building_properties_row import BuildingPropertiesRow
    from cea.demand.time_series_data import TimeSeriesData

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Martin Mosteiro", "Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def has_refrigeration_load(bpr: BuildingPropertiesRow):
    """
    Checks if building has a hot water system

    :param bpr: BuildingPropertiesRow
    :type bpr: cea.demand.building_properties.BuildingPropertiesRow
    :return: True or False
    :rtype: bool
        """

    if bpr.internal_loads['Qcre_Wm2'] > 0:
        return True
    else:
        return False


def calc_Qcre_sys(bpr: BuildingPropertiesRow, tsd: TimeSeriesData, schedules) -> TimeSeriesData:
    # calculate refrigeration loads
    tsd.cooling_loads.Qcre = schedules['Qcre_W'] * -1.0  # cooling loads are negative
    # calculate distribution losses for refrigeration loads analogously to space cooling distribution losses
    Y = bpr.building_systems['Y'][0]
    Lv = bpr.building_systems['Lv']
    Qcre_d_ls = ((T_C_REF_SUP_0 + T_C_REF_RE_0) / 2.0 - tsd.weather.T_ext) * (tsd.cooling_loads.Qcre / np.nanmin(tsd.cooling_loads.Qcre)) * (Lv * Y)

    # calculate system loads for data center
    tsd.cooling_loads.Qcre_sys = abs(tsd.cooling_loads.Qcre + Qcre_d_ls) #make sure you get the right mcpcre positive
    # writing values to tsd, replacing function and np.vectorize call with simple for loop
    tsd.cooling_system_mass_flows.mcpcre_sys, tsd.cooling_system_temperatures.Tcre_sys_re, tsd.cooling_system_temperatures.Tcre_sys_sup =\
        np.vectorize(calc_refrigeration_temperature_and_massflow)(tsd.cooling_loads.Qcre_sys)

    return tsd


def calc_refrigeration_temperature_and_massflow(Qcre_sys):
    """
    Calculate refrigeration supply and return temperatures and massflows based on the refrigeration load
    This function is intended to be used in np.vectorize form
    :param Qcre_sys: refrigeration load including losses
    :return: refrigeration massflow, refrigeration supply temperature, refrigeration return temperature
    """

    if Qcre_sys > 0.0:
        Tcre_sys_re = T_C_REF_RE_0
        Tcre_sys_sup = T_C_REF_SUP_0
        mcpcre_sys = Qcre_sys / (T_C_REF_RE_0 - T_C_REF_SUP_0)
    else:
        mcpcre_sys = 0.0
        Tcre_sys_re = np.nan
        Tcre_sys_sup = np.nan

    return mcpcre_sys, Tcre_sys_re, Tcre_sys_sup


def calc_Qref(locator, bpr: BuildingPropertiesRow, tsd: TimeSeriesData) -> TimeSeriesData:
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
            tsd.electrical_loads.E_cre = np.vectorize(heatpumps.HP_air_air)(tsd.cooling_system_mass_flows.mcpcre_sys, (tsd.cooling_system_temperatures.Tcre_sys_sup + 273),
                                                                (tsd.cooling_system_temperatures.Tcre_sys_re + 273), t_source)
            # final to district is zero
            tsd.cooling_loads.DC_cre = np.zeros(HOURS_IN_YEAR)
        elif energy_source == "NONE":
            tsd.electrical_loads.E_cre = np.zeros(HOURS_IN_YEAR)
            tsd.cooling_loads.DC_cre = np.zeros(HOURS_IN_YEAR)
        else:
            raise Exception('check potential error in input database of LCA infrastructure / COOLING')

    elif scale_technology == "DISTRICT":
        tsd.cooling_loads.DC_cre = tsd.cooling_loads.Qcs_sys / efficiency_average_year
        tsd.electrical_loads.E_cre = np.zeros(HOURS_IN_YEAR)
    elif scale_technology == "NONE":
        tsd.cooling_loads.DC_cre = np.zeros(HOURS_IN_YEAR)
        tsd.electrical_loads.E_cre = np.zeros(HOURS_IN_YEAR)
    else:
        raise Exception('check potential error in input database of LCA infrastructure / COOLING')
    return tsd

