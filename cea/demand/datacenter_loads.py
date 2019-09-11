# -*- coding: utf-8 -*-
"""
datacenter loads
"""
from __future__ import division
import numpy as np
import pandas as pd
from cea.technologies import heatpumps
from cea.constants import HOURS_IN_YEAR
from cea.demand.constants import T_C_DATA_SUP_0, T_C_DATA_RE_0

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Martin Mosteiro"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def has_data_load(bpr):
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


def calc_Edata(bpr, tsd, schedules):

    tsd['Edata'] = schedules['Ed'] * bpr.internal_loads['Ed_Wm2']

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

def calc_Qcdata_sys(bpr, tsd):
    # calculate cooling loads for data center
    tsd['Qcdata'] = 0.9 * tsd['Edata'] * -1.0  # cooling loads are negative

    # calculate distribution losses for data center cooling analogously to space cooling distribution losses
    Y = bpr.building_systems['Y'][0]
    Lv = bpr.building_systems['Lv']
    Qcdata_d_ls = ((T_C_DATA_SUP_0 + T_C_DATA_RE_0) / 2.0 - tsd['T_ext']) * (tsd['Qcdata'] / np.nanmin(tsd['Qcdata'])) * (
                Lv * Y)
    # calculate system loads for data center
    #WHATCHOUT! if we change it, then the optimization use of wasteheat breaks. mcpdata has to be positive and Qcdata_sys too!
    tsd['Qcdata_sys'] = abs(tsd['Qcdata'] + Qcdata_d_ls) # convert to positive so we get the mcp in positive numbers
    tsd['mcpcdata_sys'], tsd['Tcdata_sys_re'], tsd['Tcdata_sys_sup'] = np.vectorize(calc_mcpcdata)(abs(tsd['Qcdata_sys']))

    return tsd


def calc_Qcdataf(locator, bpr, tsd):
    """
    it calculates final loads
    """
    # GET SYSTEMS EFFICIENCIES
    data_systems = pd.read_excel(locator.get_life_cycle_inventory_supply_systems(), "COOLING").set_index('code')
    type_system = bpr.supply['type_cs']
    energy_source = data_systems.loc[type_system, "source_cs"]

    if energy_source == "GRID":
        if bpr.supply['type_cs'] in {'T2', 'T3'}:
            if bpr.supply['type_cs'] == 'T2':
                t_source = (tsd['T_ext'] + 273)
            if bpr.supply['type_cs'] == 'T3':
                t_source = (tsd['T_ext_wetbulb'] + 273)

            # heat pump energy
            tsd['E_cdata'] = np.vectorize(heatpumps.HP_air_air)(tsd['mcpcdata_sys'], (tsd['Tcdata_sys_sup'] + 273),
                                                                (tsd['Tcdata_sys_re'] + 273), t_source)
            # final to district is zero
            tsd['DC_cdata'] = np.zeros(HOURS_IN_YEAR)
    elif energy_source == "DC":
        tsd['DC_cdata'] = tsd['Qcdata_sys']
        tsd['E_cdata'] = np.zeros(HOURS_IN_YEAR)
    else:
        tsd['E_cdata'] = np.zeros(HOURS_IN_YEAR)
        tsd['DC_cdata'] = np.zeros(HOURS_IN_YEAR)
    return tsd

