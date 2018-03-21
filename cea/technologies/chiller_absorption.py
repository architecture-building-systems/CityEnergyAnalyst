"""
Absorption chillers
"""
from __future__ import division
import pandas as pd
import numpy as np
from math import log
from cea.optimization.constants import *
from sympy import *
from cea.optimization.constants import *

__author__ = "Shanshan Hsieh"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# technical model

def calc_absorption_chillers_main(mdot_kgpers, T_sup_K, T_re_K, locator, gv):
    """
    Assumptions: constant flow rate at the secondary sides (chilled water, cooling water, hot water)

    :type mdot_kgpers : float
    :param mdot_kgpers: plant supply mass flow rate to the district cooling network
    :type T_sup_K : float
    :param T_sup_K: plant supply temperature to DCN
    :type T_re_K : float
    :param T_re_K: plant return temperature from DCN
    :param gV: globalvar.py

    :rtype wdot : float
    :returns wdot: chiller electric power requirement
    :rtype qhotdot : float
    :returns qhotdot: condenser heat rejection

    ..[D.J. Swider, 2003] D.J. Swider (2003). A comparison of empirically based steady-state models for
    vapor-compression liquid chillers. Applied Thermal Engineering.

    """

    mcp_e_kWperK = mdot_kgpers * gv.Cpw  # TODO: replace gv.Cpw
    q_e_kW = mcp_e_kWperK * (T_sup_K - T_re_K)

    chiller_properties = read_chiller_properties_db(locator.get_supply_systems(gv.config.region)) # FIXME: read somewhere else

    # solve operating conditions at given demand
    operating_conditions = calc_operating_conditions(T_re_K, T_sup_K, q_e_kW, chiller_properties, gv)

    if q_e_kW == 0:
        wdot_W = 0
        q_ac_W = 0
    else:
        operating_conditions = calc_operating_conditions(T_re_K, T_sup_K, q_e_kW, gv)
        COP = 0.87
        wdot_W = operating_conditions['q_e_kW'] / COP
        q_ac_W = operating_conditions['q_ac_kW']*1000 #to W

    return wdot_W, q_ac_W

def calc_operating_conditions(T_re_K, T_sup_K, q_e_kW, gv):

    # external water circuits (e: chilled water, ac: cooling water, d: hot water)
    T_ac_in_C = VCC_tcoolin - 273.0  # condenser water inlet temperature # TODO: okay for now, but ideally, it should be connected to groud water temperature
    T_e_in_C = T_re_K - 273.0
    T_e_out_C = T_sup_K -273.0
    T_e_mean_C = (T_e_in_C - T_e_out_C)/2
    T_d_in_C = T_GENERATOR_IN_C # local constant
    m_ac_kgpers = 3.023 # TODO: read from system database
    m_d_kgpers = 1.395 # TODO: read from system database
    mcp_ac_kWperK = m_ac_kgpers * gv.Cpw
    mcp_d_kWperK = m_d_kgpers* gv.Cpw


    # technology specs # FIXME: read from system database
    t = [np.nan, 0.42, 0.9, 0.53, -2.5, 0.94, -0.4]
    u = [np.nan, -2.5, 1.8, -2.1, 1.5, -2.3, 1.6]

    # variables to solve
    T_d_mean_C, T_ac_mean_C, q_d_kW, q_ac_kW = symbols('T_d_mean_C T_ac_mean_C q_d_kW q_ac_kW')

    # characteristic temperature differences
    ddt_e = T_d_mean_C + u[1] * T_ac_mean_C + u[2] * T_e_mean_C
    ddt_d = T_d_mean_C + u[3] * T_ac_mean_C + u[4] * T_e_mean_C
    ddt_ac = T_d_mean_C + u[5] * T_ac_mean_C + u[6] * T_e_mean_C

    # systems of equations
    eq_e = t[1] * ddt_e + t[2] - q_e_kW
    eq_d = t[3] * ddt_d + t[4] - q_d_kW
    eq_ac = t[5] * ddt_ac + t[6] - q_ac_kW
    eq_bal_ac = T_ac_mean_C * 2 - q_ac_kW / mcp_d_kWperK

    # solve with sympy
    eq_sys = [eq_e, eq_d, eq_ac, eq_bal_ac]
    unknown_variables = (T_d_mean_C, T_ac_mean_C, q_d_kW, q_ac_kW)
    (T_d_mean_C, T_ac_mean_C, q_d_kW, q_ac_kW) = tuple(*linsolve(eq_sys, unknown_variables))

    # calculate results
    T_d_out_C = T_d_in_C - q_d_kW / mcp_d_kWperK
    T_ac_out_C = T_ac_in_C + q_ac_kW / mcp_ac_kWperK

    return {'T_d_out_C':T_d_out_C, 'T_ac_out_C':T_ac_out_C, 'q_e_kW': q_e_kW, 'q_d_kW': q_d_kW, 'q_ac_kw':q_ac_kW}

def read_chiller_properties_db(database_path):
    data = pd.read_excel(database_path, sheetname="Abs_chiller")
    type_abs_chiller = 'ACH1' #FIXME: choose according to size
    chiller_properties = data[data['code']== type_abs_chiller].reset_index().t.to_dict()[0]
    return chiller_properties
# Investment costs



