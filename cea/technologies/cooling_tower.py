"""
System Modeling: Cooling tower
"""
from __future__ import division
import pandas as pd
from math import log

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# technical model

def calc_CT(qhotdot_W, Qdesign_W, gV):
    """
    For the operation of a water condenser + direct cooling tower based on [B. Stephane, 2012]_
    Maximum cooling power is 10 MW.
    
    :type qhotdot_W : float
    :param qhotdot_W: heating power to condenser, From Model_VCC
    :type Qdesign_W : float
    :param Qdesign_W: Nominal cooling power
    

    :type wdot : float
    :param wdot: electric power needed for the variable speed drive fan

    ..[B. Stephane, 2012] B. Stephane (2012), Evidence-Based Model Calibration for Efficient Building Energy Services.
    PhD Thesis, University de Liege, Belgium
    """
    if qhotdot_W < gV.CT_maxSize:
        print "Error in CT model, over the max capacity"
    qpartload = qhotdot_W / Qdesign_W

    wdesign_fan = 0.011 * Qdesign_W
    wpartload = 0.8603 * qpartload ** 3 + 0.2045 * qpartload ** 2 - 0.0623 * \
                qpartload + 0.0026
    
    wdot_W = wpartload * wdesign_fan
    
    return wdot_W
    

# Investment costs

def calc_Cinv_CT(CT_size_W, gv, locator, technology=0):
    """
    Annualized investment costs for the Combined cycle

    :type CT_size_W : float
    :param CT_size_W: Size of the Cooling tower in [W]

    :rtype InvCa : float
    :returns InvCa: annualized investment costs in Dollars
    """
    if CT_size_W > 0:
        CT_cost_data = pd.read_excel(locator.get_supply_systems(gv.config.region), sheetname="CT")
        technology_code = list(set(CT_cost_data['code']))
        CT_cost_data[CT_cost_data['code'] == technology_code[technology]]
        # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
        # capacity for the corresponding technology from the database
        if CT_size_W < CT_cost_data['cap_min'][0]:
            CT_size_W = CT_cost_data['cap_min'][0]
        CT_cost_data = CT_cost_data[
            (CT_cost_data['cap_min'] <= CT_size_W) & (CT_cost_data['cap_max'] > CT_size_W)]

        Inv_a = CT_cost_data.iloc[0]['a']
        Inv_b = CT_cost_data.iloc[0]['b']
        Inv_c = CT_cost_data.iloc[0]['c']
        Inv_d = CT_cost_data.iloc[0]['d']
        Inv_e = CT_cost_data.iloc[0]['e']
        Inv_IR = (CT_cost_data.iloc[0]['IR_%']) / 100
        Inv_LT = CT_cost_data.iloc[0]['LT_yr']
        Inv_OM = CT_cost_data.iloc[0]['O&M_%'] / 100

        InvC = Inv_a + Inv_b * (CT_size_W) ** Inv_c + (Inv_d + Inv_e * CT_size_W) * log(CT_size_W)

        Capex_a =  InvC * (Inv_IR) * (1+ Inv_IR) ** Inv_LT / ((1+Inv_IR) ** Inv_LT - 1)
        Opex_fixed = Capex_a * Inv_OM

    else:
        Capex_a = 0
        Opex_fixed = 0

    return Capex_a, Opex_fixed














