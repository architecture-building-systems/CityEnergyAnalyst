# -*- coding: utf-8 -*-
"""
furnaces
"""
from __future__ import division

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
    Efficiency for Furnace Plant (Wood Chip  CHP Plant, Condensing Boiler) based on LHV.

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
        #print "Furnace Boiler below minimum Power! 1"
        #raise ModelError

    # calculate plant electrical efficiency
    if phi < gv.Furn_min_electric:
        eta_el = 0
        #print "Furnace Boiler below minimum Power! 2"

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
        #print eff_therm_tot
        eta_el += 0.087

    Q_therm_prim = Q_load / eff_therm_tot  # primary energy requirement

    Q_aux = gv.Boiler_P_aux * Q_therm_prim # 0.026 Wh/Wh= 26kWh_el/MWh_th_prim,

    return eff_therm_tot, eta_el, Q_aux


# operation costs

def furnace_op_cost(Q_therm, Q_design, T_return_to_boiler, MOIST_TYPE, gv):
    """
    Calculates the operation cost of a furnace plant (only operation, no annualized cost!)

    :type Q_therm : float
    :param Q_therm: thermal energy required from furnace plant in [Wh]

    :type Q_design : float
    :param Q_design: Design Load of Boiler [W]

    :type T_return_to_boiler : float
    :param T_return_to_boiler: return temperature to the boiler

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
        Q_th_load = Q_therm / eta_therm_real # primary energy needed
        if Q_design < Q_th_load:
            Q_th_load = Q_design -1

        Furnace_eff = Furnace_eff(Q_th_load, Q_design, T_return_to_boiler, MOIST_TYPE, gv)

        eta_therm_real, eta_el, Q_aux = Furnace_eff

        if eta_therm_real == 0:
            print "error found in Cost Mapping Furnace"
            eta_el = 0
            Q_aux = 0

            break

    Q_prim = Q_th_load
    Q_th_load = Q_therm

    if MOIST_TYPE == "dry":
        C_furn_therm = Q_prim * gv.Furn_FuelCost_dry #  [CHF / Wh] fuel cost of thermal energy
        C_furn_el_sold = (Q_prim * eta_el - Q_aux)* gv.ELEC_PRICE #  [CHF / Wh] cost gain by selling el. to the grid.
        C_furn = C_furn_therm - C_furn_el_sold
        C_furn_per_Wh = C_furn / Q_th_load

    else:
        C_furn_therm = Q_th_load * 1 / eta_therm_real * gv.Furn_FuelCost_wet
        C_furn_el_sold = (Q_prim * eta_el - Q_aux) * gv.ELEC_PRICE
        C_furn = C_furn_therm - C_furn_el_sold
        C_furn_per_Wh = C_furn / Q_th_load # in CHF / Wh

    E_furn_el_produced = eta_el * Q_prim - Q_aux

    return C_furn, C_furn_per_Wh, Q_prim, Q_th_load, E_furn_el_produced



# investment and maintenance costs

def calc_Cinv_furnace(Q_design, Q_annual, gv):
    """
    Calculates the annualized investment cost of a Furnace
    based on Bioenergy 2020 (AFO) and POLYCITY Ostfildern 

    :type Q_design : float
    :param Q_design: Design Load of Boiler
        
    :type Q_annual : float
    :param Q_annual: annual thermal Power output [Wh]

    :param gV: globalvar.py

    :rtype InvC_return : float
    :returns InvC_return: total investment Cost for building the plant
    
    :rtype InvCa : float
    :returns InvCa: annualized investment costs in [CHF] including O&M
        
    """
    InvC = 0.670 * gv.EURO_TO_CHF * Q_design # 670 € /kW therm(Boiler) = 800 CHF /kW (A+W data)

    Ca_invest =  (InvC * gv.Boiler_i * (1+ gv.Boiler_i) ** gv.Boiler_n / ((1+gv.Boiler_i) ** gv.Boiler_n - 1))
    Ca_maint = Ca_invest * gv.Boiler_C_maintainance
    Ca_labour =  gv.Boiler_C_labour / 1000000.0 * gv.EURO_TO_CHF * Q_annual

    InvCa = Ca_invest + Ca_maint + Ca_labour
    
    return InvCa

