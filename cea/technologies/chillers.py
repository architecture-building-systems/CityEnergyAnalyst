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

def calc_VCC(mdot, tsup, tret, gV):
    """
    For the operation of a Vapor-compressor chiller between a district cooling network and a condenser with fresh water
    to a cooling tower following [D.J. Swider, 2003]_.

    :type mdot : float
    :param mdot: plant supply mass flow rate to the district cooling network
    :type tsup : float
    :param tsup: plant supply temperature to DCN
    :type tret : float
    :param tret: plant return temperature from DCN
    :param gV: globalvar.py

    :rtype wdot : float
    :returns wdot: chiller electric power requirement
    :rtype qhotdot : float
    :returns qhotdot: condenser heat rejection

    ..[D.J. Swider, 2003] D.J. Swider (2003). A comparison of empirically based steady-state models for
    vapor-compression liquid chillers. Applied Thermal Engineering.

    """
    qcolddot = mdot * gV.cp * (tret - tsup)      # required cooling at the chiller evaporator
    tcoolin = gV.VCC_tcoolin                     # condenser water inlet temperature in [K]
    
    if qcolddot == 0:
        wdot = 0
        
    else: 
        #Tim Change:
        #COP = (tret / tcoolin - 0.0201E-3 * qcolddot / tcoolin) \
        #  (0.1980E3 * tret / qcolddot + 168.1846E3 * (tcoolin - tret) / (tcoolin * qcolddot) \
        #  + 0.0201E-3 * qcolddot / tcoolin + 1 - tret / tcoolin)
        
        A = 0.0201E-3 * qcolddot / tcoolin 
        B = tret / tcoolin
        C = 0.1980E3 * tret / qcolddot + 168.1846E3 * (tcoolin - tret) / (tcoolin * qcolddot)
        
        COP = 1 /( (1+C) / (B-A) -1 )
        
        wdot = qcolddot / COP
         
    qhotdot = wdot + qcolddot
    
    return wdot, qhotdot


# Investment costs

def calc_Cinv_VCC(qcold, gV, locator, technology=1):
    """
    Annualized investment costs for the vapor compressor chiller

    :type qcold : float
    :param qcold: peak cooling demand in [W]
    :param gV: globalvar.py

    :returns InvCa: annualized chiller investment cost in CHF/a
    :rtype InvCa: float

    """

    VCC_cost_data = pd.read_excel(locator.get_supply_systems_cost(), sheetname="Chiller")
    technology_code = list(set(VCC_cost_data['code']))
    VCC_cost_data[VCC_cost_data['code'] == technology_code[technology]]
    # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
    # capacity for the corresponding technology from the database
    if qcold < VCC_cost_data['cap_min'][0]:
        qcold = VCC_cost_data['cap_min'][0]
    VCC_cost_data = VCC_cost_data[
        (VCC_cost_data['cap_min'] <= qcold) & (VCC_cost_data['cap_max'] > qcold)]

    Inv_a = VCC_cost_data.iloc[0]['a']
    Inv_b = VCC_cost_data.iloc[0]['b']
    Inv_c = VCC_cost_data.iloc[0]['c']
    Inv_d = VCC_cost_data.iloc[0]['d']
    Inv_e = VCC_cost_data.iloc[0]['e']
    Inv_IR = (VCC_cost_data.iloc[0]['IR_%']) / 100
    Inv_LT = VCC_cost_data.iloc[0]['LT_yr']
    Inv_OM = VCC_cost_data.iloc[0]['O&M_%'] / 100

    InvC = Inv_a + Inv_b * (qcold) ** Inv_c + (Inv_d + Inv_e * qcold) * log(qcold)
    Capex_a = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
    Opex_fixed = Capex_a * Inv_OM

    
    return Capex_a, Opex_fixed














