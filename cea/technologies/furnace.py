# -*- coding: utf-8 -*-
"""
furnaces
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


# performance model

def calc_eta_furnace(Q_load, Q_design, T_return_to_boiler, MOIST_TYPE, gv):

    """
    Efficiency for co-generation plant with wood chip furnace, based on LHV.
    Electricity is produced through organic rankine cycle.

    Capacity : 1-10 [MW], Minimum Part Load: 30% of P_design
    Source: POLYCITY HANDBOOK 2012

    :type Q_load : float
    :param Q_load: Load of time step

    :type Q_design : float
    :param Q_design: Design Load of Boiler

    :type T_return_to_boiler : float
    :param T_return_to_boiler: return temperature to the boiler

    :type MOIST_TYPE : float
    :param MOIST_TYPE: moisture type of the fuel, set in MasterToSlaveVariables ('wet' or 'dry')

    :param gV: globalvar.py

    up to 6MW_therm_out Capacity proven!
    = 8 MW th (burner)

    :rtype eta_therm : float
    :returns eta_therm: thermal Efficiency of Furnace (LHV), in abs. numbers

    :rtype eta_el : float
    :returns eat_el: electric efficiency of Furnace (LHV), in abs. numbers

    :rtyp;e Q_aux : float
    :returns Q_aux: auxiliary power for Plant operation [W]

    """

    phi = float(Q_load) / float(Q_design)
    
    # calculate plant thermal efficiency
    if phi > gv.Furn_min_Load:

        #Implement Curves provided by http://www.greenshootscontrols.net/?p=153
        x = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1] # part load regime, phi = Q / Q_max
        y = [0.77, 0.79, 0.82, 0.84, 0.845, 0.85, 0.853, 0.854, 0.855]

        # do the interpolation
        eff_of_phi = interpolate.interp1d(x, y, kind='linear')

        # get input variables
        eta_therm = eff_of_phi(phi)

    else:
        eta_therm = 0


    # calculate plant electrical efficiency
    if phi < gv.Furn_min_electric:
        eta_el = 0


    else:
        x = [2/7.0, 3/7.0, 4/7.0, 5/7.0, 6/7.0, 1] # part load regime, phi = Q / Q_max
        y = [0.025, 0.0625, 0.102, 0.127, 0.146, 0.147]
        eff_el_of_phi = interpolate.interp1d(x, y, kind='cubic')
        eta_el = eff_el_of_phi(phi)



    # Return Temperature Dependency
    x = [0,15.5, 21, 26.7, 32.2, 37.7, 43.3, 49, 54.4, 60, 65.6, 71.1, 100] # Return Temperature Dependency
    y = [96.8,96.8, 96.2, 95.5, 94.7, 93.2, 91.2, 88.9, 87.3, 86.3, 86.0, 85.9, 85.8] # Return Temperature Dependency
    eff_of_T_return = interpolate.interp1d(x, y, kind='linear')

    eff_therm_tot = eff_of_T_return(T_return_to_boiler - 273) * eta_therm / eff_of_T_return(60)

    if MOIST_TYPE == "dry":
        eff_therm_tot = eff_of_T_return(T_return_to_boiler - 273) * eta_therm / eff_of_T_return(60) + 0.087 # 8.7 % efficiency gain when using dry fuel
        eta_el += 0.087

    Q_therm_prim = Q_load / eff_therm_tot  # primary energy requirement

    Q_aux = gv.Boiler_P_aux * Q_therm_prim # 0.026 Wh/Wh= 26kWh_el/MWh_th_prim,

    return eff_therm_tot, eta_el, Q_aux


# operation costs

def furnace_op_cost(Q_therm_W, Q_design_W, T_return_to_boiler_K, MOIST_TYPE, gv):
    """
    Calculates the operation cost of a furnace plant (only operation, no annualized cost!)

    :type Q_therm_W : float
    :param Q_therm_W: thermal energy required from furnace plant in [Wh]

    :type Q_design_W : float
    :param Q_design_W: Design Load of Boiler [W]

    :type T_return_to_boiler_K : float
    :param T_return_to_boiler_K: return temperature to the boiler

    :type MOIST_TYPE : float
    :param MOIST_TYPE: moisture type of the fuel, set in MasterToSlaveVariables ('wet' or 'dry')

    :param gV: globalvar.py

    :rtype C_furn : float
    :returns C_furn: Total generation cost for required load (per hour) in [CHF], including profits from electricity sold

    :rtype C_furn_per_kWh : float
    :returns C_furn_per_kWh: cost generation per kWh thermal energy  produced in [Rp / kWh], including profits from
    electricity sold

    :rtype Q_primary : float
    :returns Q_primary: required thermal energy per hour [Wh] of wood chips

    :rtype E_furn_el_produced : float
    :returns E_furn_el_produced: electricity produced by furnace plant in [Wh]
    """

    #if Q_load / Q_design < 0.3:
    #    raise ModelError

    ## Iterating for efficiency as Q_therm is given as input
    eta_therm_in = 0.6
    eta_therm_real = 1.0
    i = 0

    # Iterating for thermal efficiency and required load
    while 0.999 >= abs(eta_therm_in/eta_therm_real):
        if i != 0:
            eta_therm_in = eta_therm_real
        i += 1
        Q_th_load_W = Q_therm_W / eta_therm_real # primary energy needed
        if Q_design_W < Q_th_load_W:
            Q_th_load_W = Q_design_W - 1

        Furnace_eff = Furnace_eff(Q_th_load_W, Q_design_W, T_return_to_boiler_K, MOIST_TYPE, gv)

        eta_therm_real, eta_el, Q_aux_W = Furnace_eff

        if eta_therm_real == 0:
            eta_el = 0
            Q_aux_W = 0

            break

    Q_prim_W = Q_th_load_W
    Q_th_load_W = Q_therm_W

    if MOIST_TYPE == "dry":
        C_furn_therm = Q_prim_W * gv.Furn_FuelCost_dry #  [CHF / Wh] fuel cost of thermal energy
        C_furn_el_sold = (Q_prim_W * eta_el - Q_aux_W)* gv.ELEC_PRICE #  [CHF / Wh] cost gain by selling el. to the grid.
        C_furn = C_furn_therm - C_furn_el_sold
        C_furn_per_Wh = C_furn / Q_th_load_W

    else:
        C_furn_therm = Q_th_load_W * 1 / eta_therm_real * gv.Furn_FuelCost_wet
        C_furn_el_sold = (Q_prim_W * eta_el - Q_aux_W) * gv.ELEC_PRICE
        C_furn = C_furn_therm - C_furn_el_sold
        C_furn_per_Wh = C_furn / Q_th_load_W # in CHF / Wh

    E_furn_el_produced = eta_el * Q_prim_W - Q_aux_W

    return C_furn, C_furn_per_Wh, Q_prim_W, Q_th_load_W, E_furn_el_produced



# investment and maintenance costs

def calc_Cinv_furnace(Q_design_W, Q_annual_W, gv, locator, technology=0):
    """
    Calculates the annualized investment cost of a Furnace
    based on Bioenergy 2020 (AFO) and POLYCITY Ostfildern 

    :type Q_design_W : float
    :param Q_design_W: Design Load of Boiler
        
    :type Q_annual_W : float
    :param Q_annual_W: annual thermal Power output [Wh]

    :param gv: globalvar.py

    :rtype InvC_return : float
    :returns InvC_return: total investment Cost for building the plant
    
    :rtype InvCa : float
    :returns InvCa: annualized investment costs in [CHF] including O&M
        
    """
    furnace_cost_data = pd.read_excel(locator.get_supply_systems(gv.config.region), sheetname="Furnace")
    technology_code = list(set(furnace_cost_data['code']))
    furnace_cost_data[furnace_cost_data['code'] == technology_code[technology]]
    # if the Q_design is below the lowest capacity available for the technology, then it is replaced by the least
    # capacity for the corresponding technology from the database
    if Q_design_W < furnace_cost_data['cap_min'][0]:
        Q_design_W = furnace_cost_data['cap_min'][0]
    furnace_cost_data = furnace_cost_data[
        (furnace_cost_data['cap_min'] <= Q_design_W) & (furnace_cost_data['cap_max'] > Q_design_W)]

    Inv_a = furnace_cost_data.iloc[0]['a']
    Inv_b = furnace_cost_data.iloc[0]['b']
    Inv_c = furnace_cost_data.iloc[0]['c']
    Inv_d = furnace_cost_data.iloc[0]['d']
    Inv_e = furnace_cost_data.iloc[0]['e']
    Inv_IR = (furnace_cost_data.iloc[0]['IR_%']) / 100
    Inv_LT = furnace_cost_data.iloc[0]['LT_yr']
    Inv_OM = furnace_cost_data.iloc[0]['O&M_%'] / 100

    InvC = Inv_a + Inv_b * (Q_design_W) ** Inv_c + (Inv_d + Inv_e * Q_design_W) * log(Q_design_W)

    Capex_a = InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)
    Opex_fixed = Capex_a * Inv_OM

    
    return Capex_a, Opex_fixed

