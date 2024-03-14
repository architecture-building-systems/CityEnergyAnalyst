"""
System Modeling: Cooling tower
"""



import pandas as pd
from math import ceil, log
from cea.technologies.constants import CT_MIN_PARTLOAD_RATIO
from cea.analysis.costs.equations import calc_capex_annualized
__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# technical model
def calc_CT_const(q_hot_Wh, eff_rating):
    """
    Calculate the cooling tower's operational behaviour assuming a constant efficiency rating. i.e. return electrical
    power demand for fans, pumping and water treatment given a certain heat rejection load.

    :param q_hot_Wh: heat rejection load on the cooling tower
    :type q_hot_Wh: int, float, list or pd.Series
    :param eff_rating: average efficiency rating of the cooling tower
    :type eff_rating: float

    :return p_el_vent: power demand of the cooling tower (ventilation, pumping, water treatment) in Watt-hours
    :rtype p_el_vent: float, list or pd.Series
    :return q_anth_Wh: anthropogenic heat emissions from cooling tower in Watt-hours
    :rtype p_el_vent: float, list or pd.Series
    """
    p_el_vent = q_hot_Wh * eff_rating
    q_anth_Wh = q_hot_Wh + p_el_vent
    return p_el_vent, q_anth_Wh


def calc_CT(q_hot_Wh, Q_nom_W):
    """
    For the operation of a water condenser + direct cooling tower based on [B. Stephane, 2012]_
    Maximum cooling power is 10 MW.
    
    :type q_hot_Wh : float
    :param q_hot_Wh: heat rejected from chiller condensers
    :type Q_nom_W : float
    :param Q_nom_W: installed CT size

    ..[B. Stephane, 2012] B. Stephane (2012), Evidence-Based Model Calibration for Efficient Building Energy Services.
    PhD Thesis, University de Liege, Belgium
    """
    if (Q_nom_W > 0.0 and q_hot_Wh > 0.0):
        # calculate CT operation at part load
        q_partload_ratio = q_hot_Wh / Q_nom_W
        w_partload_factor = calc_CT_partload_factor(q_partload_ratio)

        # calculate nominal fan power
        w_nom_fan = 0.011 * Q_nom_W # _[B. Stephane, 2012]

        # calculate total electricity consumption
        el_W = w_partload_factor * w_nom_fan

    else:
        el_W = 0.0

    return el_W


def calc_CT_partload_factor(q_part_load_ratio):
    """
    Calculate the partload factor according to partload ratio.
    The equation is only valid when the part load ratio is higher than 15%.
    :param q_part_load_ratio:
    :return:
    ..[Nguyen,T., 2015] Thuy-An,Nguyen (2015), Optimization of a District Energy System in the context of Urban Transformation.
    Master Thesis, ETHZ.
    ..[Grahovac,M., 2012] Grahovac, M. et al. (2012). VC CHILLERS AND PV PANELS: A GENERIC PLANNING TOOL PROVIDING THE
    OPTIMAL DIMENSIONS TO MINIMIZE COSTS OR EMISSIONS. Presented at the Forth German-Austrian IBPSA Conference BauSIM,
    Berlin University of the Arts.
    """
    if q_part_load_ratio < CT_MIN_PARTLOAD_RATIO:
        q_part_load_ratio = CT_MIN_PARTLOAD_RATIO
    w_partload_factor = 0.8603 * q_part_load_ratio ** 3 + 0.2045 * q_part_load_ratio ** 2 - 0.0623 * q_part_load_ratio + 0.0026
    return w_partload_factor


def calc_CT_yearly(q_hot_kWh):
    """
    For the operation of a water condenser + direct cooling tower with a fit function based on the hourly calculation in calc_CT.

    :type q_hot_kWh : float
    :param q_hot_kWh: heat rejected from chiller condensers
    """
    if q_hot_kWh > 0.0:
        usd_elec = 19450 + 7.562 * 10 ** -9 * q_hot_kWh ** 1.662
    else:
        usd_elec = 0.0

    return usd_elec


# Investment costs

def calc_Cinv_CT(Q_nom_CT_W, locator, technology_type):
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
        CT_cost_data = pd.read_excel(locator.get_database_conversion_systems(), sheet_name="CT")
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
            Inv_IR = CT_cost_data.iloc[0]['IR_%']
            Inv_LT = CT_cost_data.iloc[0]['LT_yr']
            Inv_OM = CT_cost_data.iloc[0]['O&M_%'] / 100

            InvC = Inv_a + Inv_b * (Q_nom_CT_W) ** Inv_c + (Inv_d + Inv_e * Q_nom_CT_W) * log(Q_nom_CT_W)

            Capex_a_CT_USD = calc_capex_annualized(InvC, Inv_IR, Inv_LT)
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
                Inv_IR = CT_cost_data.iloc[0]['IR_%']
                Inv_LT = CT_cost_data.iloc[0]['LT_yr']
                Inv_OM = CT_cost_data.iloc[0]['O&M_%'] / 100
                InvC = Inv_a + Inv_b * (Q_nom_each_CT) ** Inv_c + (Inv_d + Inv_e * Q_nom_each_CT) * log(Q_nom_each_CT)
                Capex_a1 = calc_capex_annualized(InvC, Inv_IR, Inv_LT)
                Capex_a_CT_USD = Capex_a_CT_USD + Capex_a1
                Opex_fixed_CT_USD = Opex_fixed_CT_USD + InvC * Inv_OM
                Capex_CT_USD = Capex_CT_USD + InvC

    return Capex_a_CT_USD, Opex_fixed_CT_USD, Capex_CT_USD


def main():
    import numpy as np
    q_hot_Wh = np.arange(0.0, 1E3, 100)
    Q_nom_W = 1E3
    wdot_W = np.vectorize(calc_CT)(q_hot_Wh, Q_nom_W)
    print(wdot_W)




if __name__ == '__main__':
    main()








