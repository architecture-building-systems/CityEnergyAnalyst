# -*- coding: utf-8 -*-
"""
refrigeration loads
"""
from __future__ import division
import numpy as np
import pandas as pd
from cea.technologies import heatpumps
from cea.constants import HOURS_IN_YEAR

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

    tsd['Qcre_sys'] = schedules['Qcre'] * bpr.internal_loads['Qcre_Wm2']

    def function(Qcre_sys):
        if Qcre_sys > 0:
            Tcref_re_0 = 5
            Tcref_sup_0 = 1
            mcpref = Qcre_sys/(Tcref_re_0-Tcref_sup_0)
        else:
            mcpref = 0.0
            Tcref_re_0 = 0.0
            Tcref_sup_0 = 0.0
        return mcpref, Tcref_re_0, Tcref_sup_0

    tsd['mcpcre_sys'], tsd['Tcre_sys_re'], tsd['Tcre_sys_sup'] = np.vectorize(function)(tsd['Qcre_sys'])

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

