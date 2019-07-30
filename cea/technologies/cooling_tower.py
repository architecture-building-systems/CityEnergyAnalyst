"""
System Modeling: Cooling tower
"""
from __future__ import division
import pandas as pd
from math import ceil, log
from cea.optimization.constants import CT_MAX_SIZE

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# technical model

def calc_CT(q_hot_Wh, Q_unit_size_W):
    """
    For the operation of a water condenser + direct cooling tower based on [B. Stephane, 2012]_
    Maximum cooling power is 10 MW.
    
    :type q_hot_Wh : float
    :param q_hot_Wh: heat rejected from chiller condensers
    :type Q_unit_size_W : float
    :param Q_unit_size_W: installed CT size

    ..[B. Stephane, 2012] B. Stephane (2012), Evidence-Based Model Calibration for Efficient Building Energy Services.
    PhD Thesis, University de Liege, Belgium
    """
    wdot_W = 0
    if q_hot_Wh > Q_unit_size_W:
        # distribute loads to multiple units
        number_of_units = int(ceil(q_hot_Wh / Q_unit_size_W))
        q_hot_per_unit_Wh = q_hot_Wh / number_of_units
        qpartload = q_hot_per_unit_Wh / Q_unit_size_W
    else:
        # operate one unit at the load
        number_of_units = 1
        qpartload = q_hot_Wh / Q_unit_size_W

    # calculate operation of one unit
    wdesign_fan = 0.011 * Q_unit_size_W
    wpartload = 0.8603 * qpartload ** 3 + 0.2045 * qpartload ** 2 - 0.0623 * qpartload + 0.0026

    # calculate outputs of all units
    wdot_W = (wpartload * wdesign_fan) * number_of_units
    
    return wdot_W


def calc_CT_yearly(q_hot_kWh):
    """
    For the operation of a water condenser + direct cooling tower with a fit funciton based on the hourly calculation in calc_CT.

    :type q_hot_kWh : float
    :param q_hot_kWh: heat rejected from chiller condensers
    """
    if q_hot_kWh > 0.0:
        usd_elec = 19450 + 7.562 * 10 ** -9 * q_hot_kWh ** 1.662
    else:
        usd_elec = 0.0

    return usd_elec


# Investment costs

def calc_Cinv_CT(Q_nom_CT_W, locator, config, technology_type):
    """
    Annualized investment costs for the Combined cycle

    :type Q_nom_CT_W : float
    :param Q_nom_CT_W: Nominal size of the cooling tower in [W]

    :rtype InvCa : float
    :returns InvCa: annualized investment costs in Dollars
    """
    Capex_a_CT_USD = 0.0
    Opex_fixed_CT_USD = 0.0
    Capex_CT_USD = 0.0

    if Q_nom_CT_W > 0:
        CT_cost_data = pd.read_excel(locator.get_supply_systems(), sheet_name="CT")
        CT_cost_data = CT_cost_data[CT_cost_data['code'] == technology_type]
        max_chiller_size = max(CT_cost_data['cap_max'].values)

        # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
        # capacity for the corresponding technology from the database
        if Q_nom_CT_W < CT_cost_data.iloc[0]['cap_min']:
            Q_nom_CT_W = CT_cost_data.iloc[0]['cap_min']
        if Q_nom_CT_W <= max_chiller_size:
            CT_cost_data = CT_cost_data[
                (CT_cost_data['cap_min'] <= Q_nom_CT_W) & (CT_cost_data['cap_max'] > Q_nom_CT_W)]

            Inv_a = CT_cost_data.iloc[0]['a']
            Inv_b = CT_cost_data.iloc[0]['b']
            Inv_c = CT_cost_data.iloc[0]['c']
            Inv_d = CT_cost_data.iloc[0]['d']
            Inv_e = CT_cost_data.iloc[0]['e']
            Inv_IR = (CT_cost_data.iloc[0]['IR_%']) / 100
            Inv_LT = CT_cost_data.iloc[0]['LT_yr']
            Inv_OM = CT_cost_data.iloc[0]['O&M_%'] / 100

            InvC = Inv_a + Inv_b * (Q_nom_CT_W) ** Inv_c + (Inv_d + Inv_e * Q_nom_CT_W) * log(Q_nom_CT_W)

            Capex_a_CT_USD =  InvC * (Inv_IR) * (1+ Inv_IR) ** Inv_LT / ((1+Inv_IR) ** Inv_LT - 1)
            Opex_fixed_CT_USD = InvC * Inv_OM
            Capex_CT_USD = InvC

        else:
            number_of_chillers = int(ceil(Q_nom_CT_W / max_chiller_size))
            Q_nom_each_CT = Q_nom_CT_W / number_of_chillers

            for i in range(number_of_chillers):
                CT_cost_data = CT_cost_data[
                    (CT_cost_data['cap_min'] <= Q_nom_each_CT) & (CT_cost_data['cap_max'] > Q_nom_each_CT)]
                Inv_a = CT_cost_data.iloc[0]['a']
                Inv_b = CT_cost_data.iloc[0]['b']
                Inv_c = CT_cost_data.iloc[0]['c']
                Inv_d = CT_cost_data.iloc[0]['d']
                Inv_e = CT_cost_data.iloc[0]['e']
                Inv_IR = (CT_cost_data.iloc[0]['IR_%']) / 100
                Inv_LT = CT_cost_data.iloc[0]['LT_yr']
                Inv_OM = CT_cost_data.iloc[0]['O&M_%'] / 100
                InvC = Inv_a + Inv_b * (Q_nom_each_CT) ** Inv_c + (Inv_d + Inv_e * Q_nom_each_CT) * log(Q_nom_each_CT)
                Capex_a1 = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
                Capex_a_CT_USD = Capex_a_CT_USD + Capex_a1
                Opex_fixed_CT_USD = Opex_fixed_CT_USD + InvC * Inv_OM
                Capex_CT_USD = Capex_CT_USD + InvC

    return Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD














