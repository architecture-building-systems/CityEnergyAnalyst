# -*- coding: utf-8 -*-
"""
direct expansion units
"""

import numpy as np

from cea.analysis.costs.equations import calc_capex_annualized
from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.constants import DX_COP, PRICE_DX_PER_W

__author__ = "Shanshan Hsieh"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# FIXME: this model is simplified, and required update


def calc_cop_DX(Q_load_W):
    cop = DX_COP

    return cop


def calc_AC_const(Q_load_Wh, COP):
    """
    Calculate the unitary air conditioner's operation for a fixed COP. Return required power supply and thermal energy
    output to the outside air (condenser side) for a given indoor cooling load (evaporator side).

    :param Q_load_Wh: Cooling load in Watt-hours (single value or time series).
    :type Q_load_Wh: int, float, list or pd.Series
    :param COP: Characteristic coefficient of performance of the vapor compression chiller
    :type COP: int, float

    :return p_supply_Wh: Electrical power supply required to provide the given cooling load (single value or time series)
    :rtype p_supply_Wh: int, float, list or pd.Series
    :return q_cw_out_Wh: Thermal energy output to cold water loop, i.e. waste heat (single value or time series)
    :rtype q_cw_out_Wh: int, float, list or pd.Series
    """

    p_supply_Wh = Q_load_Wh / COP
    Q_out_Wh = p_supply_Wh + Q_load_Wh
    return p_supply_Wh, Q_out_Wh


def calc_DX(mdot_kgpers, T_sup_K, T_re_K):
    if np.isclose(mdot_kgpers, 0.0):
        q_chw_W = 0.0
        wdot_W = 0.0
    else:
        q_chw_W = mdot_kgpers * HEAT_CAPACITY_OF_WATER_JPERKGK * (T_re_K - T_sup_K)

        cop_DX = calc_cop_DX(q_chw_W)

        wdot_W = q_chw_W / cop_DX

    return wdot_W, q_chw_W


# investment and maintenance costs

def calc_Cinv_DX(Q_design_W):
    """
    Assume the same cost as gas boilers.
    :type Q_design_W : float
    :param Q_design_W: Design Load of Boiler in [W]
    :rtype InvCa : float
    :returns InvCa: Annualized investment costs in CHF/a including Maintenance Cost
    """
    Capex_a_DX_USD = 0
    Opex_fixed_DX_USD = 0
    Capex_DX_USD = 0

    if Q_design_W > 0:
        InvC = Q_design_W * PRICE_DX_PER_W
        Inv_IR = 5
        Inv_LT = 25
        Inv_OM = 5 / 100

        Capex_a_DX_USD = calc_capex_annualized(InvC, Inv_IR, Inv_LT)
        Opex_fixed_DX_USD = InvC * Inv_OM
        Capex_DX_USD = InvC

    return Capex_a_DX_USD, Opex_fixed_DX_USD, Capex_DX_USD
