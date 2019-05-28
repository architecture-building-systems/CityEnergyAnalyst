# -*- coding: utf-8 -*-
"""
refrigeration loads
"""
from __future__ import division
import numpy as np
import pandas as pd
from cea.technologies import heatpumps
from cea.constants import HOURS_IN_YEAR
from cea.demand.constants import T_C_REF_SUP_0, T_C_REF_RE_0

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def has_refrigeration_load(bpr):
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


def calc_Qcre_sys(bpr, tsd, schedules):
    # calculate refrigeration loads
    tsd['Qcre'] = schedules['Qcre'] * bpr.internal_loads['Qcre_Wm2'] * -1.0  # cooling loads are negative
    # calculate distribution losses for refrigeration loads analogously to space cooling distribution losses
    Y = bpr.building_systems['Y'][0]
    Lv = bpr.building_systems['Lv']
    Qcre_d_ls = ((T_C_REF_SUP_0 + T_C_REF_RE_0) / 2 - tsd['T_ext']) * (tsd['Qcre'] / np.nanmin(tsd['Qcre'])) * (Lv * Y)
    # calculate system loads for data center
    tsd['Qcre_sys'] = tsd['Qcre'] + Qcre_d_ls

    # writing values to tsd, replacing function and np.vectorize call with simple for loop
    for h in range(HOURS_IN_YEAR):
        if tsd['Qcre_sys'][h] > 0:
            tsd['mcpcre_sys'][h] = tsd['Qcre_sys'][h] / (T_C_REF_RE_0 - T_C_REF_SUP_0)
            tsd['Tcre_sys_re'][h] = T_C_REF_RE_0
            tsd['Tcre_sys_sup'][h] = T_C_REF_SUP_0

    return tsd


def calc_Qref(locator, bpr, tsd):
    """
    it calculates final loads
    """
    # GET SYSTEMS EFFICIENCIES
    data_systems = pd.read_excel(locator.get_life_cycle_inventory_supply_systems(), "COOLING").set_index('code')
    type_system = bpr.supply['type_cs']
    energy_source = data_systems.loc[type_system, 'source_cs']

    if energy_source == "GRID":
        if bpr.supply['type_cs'] in {'T2', 'T3'}:
            if bpr.supply['type_cs'] == 'T2':
                t_source = (tsd['T_ext'] + 273)
            if bpr.supply['type_cs'] == 'T3':
                t_source = (tsd['T_ext_wetbulb'] + 273)

            # heat pump energy
            tsd['E_cre'] = np.vectorize(heatpumps.HP_air_air)(tsd['mcpcre_sys'], (tsd['Tcre_sys_sup'] + 273),
                                                                (tsd['Tcre_sys_re'] + 273), t_source)
            # final to district is zero
            tsd['DC_cre'] = np.zeros(HOURS_IN_YEAR)
    elif energy_source == "DC":
        tsd['DC_cre'] = tsd['Qcre_sys']
        tsd['E_cre'] = np.zeros(HOURS_IN_YEAR)
    else:
        tsd['E_cre'] = np.zeros(HOURS_IN_YEAR)

    return tsd

