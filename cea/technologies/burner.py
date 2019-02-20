# -*- coding: utf-8 -*-
"""
gas burners
"""

from __future__ import division
from scipy.interpolate import interp1d
from math import log, ceil
import pandas as pd
from cea.optimization.constants import BOILER_P_AUX

__author__ = "Shanshan Hsieh"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# FIXME: this model is modified from the boiler model, the difference is that whether the flue gas is directed used (burner), or extracted by water via heat exchangers (boilers).

# operation costs

def calc_cop_burner(Q_load_W, Q_design_W):
    """
    This function calculates efficiency of gas burners supplying heat directly to the high temperature generators
    in double effect absorption chillers.
    :param Q_load_W: Load of time step
    :type Q_load_W: float
    :type Q_design_W: float
    :param Q_design_W: Design Load of Boiler
    :retype burner_eff: float
    :returns burner_eff: efficiency of Boiler (Lower Heating Value), in abs. numbers
    """

    burner_eff = 0.85  # assumption taken from the lowest efficiency of gas boilers

    return burner_eff


def burner_op_cost(Q_load_W, Q_design_W, FuelType, ElectricityType, lca, prices):
    """
    This function calculates the operation cost of gas burners supplying heat directly to the high temperature generators
    in double effect absorption chillers.
    Assume similar operating cost as boilers.
    :type Q_load_W : float
    :param Q_load_W: Load of time step
    :type Q_design_W: float
    :param Q_design_W: Design Load of Boiler
    :type T_return_to_boiler_K : float
    :param T_return_to_boiler_K: return temperature to Boiler (from DH network)
    :param gV: globalvar.py
    :rtype C_boil_therm : float
    :returns C_boil_therm: Total generation cost for required load (per hour) in CHF
    :rtype C_boil_per_Wh : float
    :returns C_boil_per_Wh: cost per Wh in CHF / kWh
    :rtype Q_primary : float
    :returns Q_primary: required thermal energy per hour (in Wh Natural Gas)
    :rtype E_aux_Boiler: float
    :returns E_aux_Boiler: auxiliary electricity of boiler operation
    """

    # gas burner efficiency
    eta_burner = calc_cop_burner(Q_load_W, Q_design_W)

    if FuelType == 'BG':
        GAS_PRICE = prices.BG_PRICE
    else:
        GAS_PRICE = prices.NG_PRICE

    if ElectricityType == 'green':
        ELEC_PRICE = lca.ELEC_PRICE_GREEN
    else:
        ELEC_PRICE = lca.ELEC_PRICE

    C_boil_therm = Q_load_W / eta_burner * GAS_PRICE + (
                                                       BOILER_P_AUX * ELEC_PRICE) * Q_load_W  # CHF / Wh - cost of thermal energy
    C_boil_per_Wh = 1 / eta_burner * GAS_PRICE + BOILER_P_AUX * ELEC_PRICE
    E_aux_W = BOILER_P_AUX * Q_load_W

    Q_primary_W = Q_load_W / eta_burner

    return C_boil_therm, C_boil_per_Wh, Q_primary_W, E_aux_W


# investment and maintenance costs

def calc_Cinv_burner(Q_design_W, locator, config, technology_type):
    """
    Assume the same cost as gas boilers.
    :type Q_design_W : float
    :param Q_design_W: Design Load of Boiler in [W]
    :param gV: globalvar.py
    :rtype InvCa : float
    :returns InvCa: Annualized investment costs in CHF/a including Maintenance Cost
    """
    Capex_a_burner_USD = 0
    Opex_fixed_burner_USD = 0
    Capex_burner_USD = 0

    if Q_design_W > 0:

        boiler_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="Boiler")
        boiler_cost_data = boiler_cost_data[boiler_cost_data['code'] == technology_type]
        # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
        # capacity for the corresponding technology from the database
        if Q_design_W < boiler_cost_data.iloc[0]['cap_min']:
            Q_design_W = boiler_cost_data.iloc[0]['cap_min']
        max_boiler_size = boiler_cost_data.iloc[0]['cap_max']

        if Q_design_W <= max_boiler_size:

            boiler_cost_data = boiler_cost_data[
                (boiler_cost_data['cap_min'] <= Q_design_W) & (boiler_cost_data['cap_max'] > Q_design_W)]

            Inv_a = boiler_cost_data.iloc[0]['a']
            Inv_b = boiler_cost_data.iloc[0]['b']
            Inv_c = boiler_cost_data.iloc[0]['c']
            Inv_d = boiler_cost_data.iloc[0]['d']
            Inv_e = boiler_cost_data.iloc[0]['e']
            Inv_IR = (boiler_cost_data.iloc[0]['IR_%']) / 100
            Inv_LT = boiler_cost_data.iloc[0]['LT_yr']
            Inv_OM = boiler_cost_data.iloc[0]['O&M_%'] / 100

            InvC = Inv_a + Inv_b * (Q_design_W) ** Inv_c + (Inv_d + Inv_e * Q_design_W) * log(Q_design_W)

            Capex_a_burner_USD = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
            Opex_fixed_burner_USD = Capex_a_burner_USD * Inv_OM
            Capex_burner_USD = InvC

        else:
            number_of_boilers = int(ceil(Q_design_W / max_boiler_size))
            Q_nom_W = Q_design_W / number_of_boilers

            boiler_cost_data = boiler_cost_data[
                (boiler_cost_data['cap_min'] <= Q_nom_W) & (boiler_cost_data['cap_max'] > Q_nom_W)]

            Inv_a = boiler_cost_data.iloc[0]['a']
            Inv_b = boiler_cost_data.iloc[0]['b']
            Inv_c = boiler_cost_data.iloc[0]['c']
            Inv_d = boiler_cost_data.iloc[0]['d']
            Inv_e = boiler_cost_data.iloc[0]['e']
            Inv_IR = (boiler_cost_data.iloc[0]['IR_%']) / 100
            Inv_LT = boiler_cost_data.iloc[0]['LT_yr']
            Inv_OM = boiler_cost_data.iloc[0]['O&M_%'] / 100

            InvC = (Inv_a + Inv_b * (Q_nom_W) ** Inv_c + (Inv_d + Inv_e * Q_nom_W) * log(Q_nom_W)) * number_of_boilers

            Capex_a_burner_USD = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
            Opex_fixed_burner_USD = Capex_a_burner_USD * Inv_OM
            Capex_burner_USD = InvC


    return Capex_a_burner_USD, Opex_fixed_burner_USD, Capex_burner_USD