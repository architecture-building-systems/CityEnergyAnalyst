"""
Vapor-compressor chiller
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

def calc_VCC(mdot_kgpers, T_sup_K, T_re_K, gV):
    """
    For the operation of a Vapor-compressor chiller between a district cooling network and a condenser with fresh water
    to a cooling tower following [D.J. Swider, 2003]_.

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
    qcolddot_W = mdot_kgpers * gV.cp * (T_re_K - T_sup_K)      # required cooling at the chiller evaporator
    tcoolin_K = gV.VCC_tcoolin                     # condenser water inlet temperature in [K]
    
    if qcolddot_W == 0:
        wdot_W = 0
        
    else: 
        #Tim Change:
        #COP = (tret / tcoolin - 0.0201E-3 * qcolddot / tcoolin) \
        #  (0.1980E3 * tret / qcolddot + 168.1846E3 * (tcoolin - tret) / (tcoolin * qcolddot) \
        #  + 0.0201E-3 * qcolddot / tcoolin + 1 - tret / tcoolin)
        
        A = 0.0201E-3 * qcolddot_W / tcoolin_K
        B = T_re_K / tcoolin_K
        C = 0.1980E3 * T_re_K / qcolddot_W + 168.1846E3 * (tcoolin_K - T_re_K) / (tcoolin_K * qcolddot_W)
        
        COP = 1 /( (1+C) / (B-A) -1 )
        
        wdot_W = qcolddot_W / COP
         
    qhotdot_W = wdot_W + qcolddot_W
    
    return wdot_W, qhotdot_W


# Investment costs

def calc_Cinv_VCC(qcold_W, gv, locator, technology=1):
    """
    Annualized investment costs for the vapor compressor chiller

    :type qcold_W : float
    :param qcold_W: peak cooling demand in [W]
    :param gV: globalvar.py

    :returns InvCa: annualized chiller investment cost in CHF/a
    :rtype InvCa: float

    """

    VCC_cost_data = pd.read_excel(locator.get_supply_systems(gv.config.region), sheetname="Chiller")
    technology_code = list(set(VCC_cost_data['code']))
    VCC_cost_data[VCC_cost_data['code'] == technology_code[technology]]
    # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
    # capacity for the corresponding technology from the database
    if qcold_W < VCC_cost_data['cap_min'][0]:
        qcold_W = VCC_cost_data['cap_min'][0]
    VCC_cost_data = VCC_cost_data[
        (VCC_cost_data['cap_min'] <= qcold_W) & (VCC_cost_data['cap_max'] > qcold_W)]

    Inv_a = VCC_cost_data.iloc[0]['a']
    Inv_b = VCC_cost_data.iloc[0]['b']
    Inv_c = VCC_cost_data.iloc[0]['c']
    Inv_d = VCC_cost_data.iloc[0]['d']
    Inv_e = VCC_cost_data.iloc[0]['e']
    Inv_IR = (VCC_cost_data.iloc[0]['IR_%']) / 100
    Inv_LT = VCC_cost_data.iloc[0]['LT_yr']
    Inv_OM = VCC_cost_data.iloc[0]['O&M_%'] / 100

    InvC = Inv_a + Inv_b * (qcold_W) ** Inv_c + (Inv_d + Inv_e * qcold_W) * log(qcold_W)
    Capex_a = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
    Opex_fixed = Capex_a * Inv_OM

    
    return Capex_a, Opex_fixed














