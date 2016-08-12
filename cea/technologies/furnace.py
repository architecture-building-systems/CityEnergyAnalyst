# -*- coding: utf-8 -*-
"""
==================================================
furnaces
==================================================

"""
from __future__ import division

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


"""
============================
performance model
============================

"""


def calc_eta_furnace(Q_load, Q_design, T_return_to_boiler, MOIST_TYPE, gv):

    """
    Efficiency for Furnace Plant (Wood Chip  CHP Plant, Condensing Boiler)

    Minimum Part load regime: 30% of P_design
    Efficiencies based on LHV !

    Source: POLYCITY HANDBOOK 2012

    Valid for Q_design = 1-10 MW

    Parameters
    ----------
    Q_load : float
        Load of time step

    Q_max : float
        Design Load of Boiler

    up to 6MW_therm_out Capacity proven!
    = 8 MW th (burner)



    Returns
    -------
    eta_therm : float
        thermal Efficiency of Furnace (Lower Heating Value), in abs. numbers

    eta_el : float
        electric efficiency of Furnace (LHV), in abs. numbers

    Q_aux : float
        auxillary power for Plant operation in W

    """

    phi = float(Q_load) / float(Q_design)


    """ Plant Thermal Efficiency """
    if phi > gv.Furn_min_Load:

        #Implement Curves provided by http://www.greenshootscontrols.net/?p=153
        x = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1] # part load regime, phi = Q / Q_max
        y = [0.77, 0.79, 0.82, 0.84, 0.845, 0.85, 0.853, 0.854, 0.855]


        # do the interpolation
        eff_of_phi = interp1d(x, y, kind='linear')


        # get input variables
        #print phi
        eta_therm = eff_of_phi(phi)

    else:
        eta_therm = 0
        #print "Furnace Boiler below minimum Power! 1"
        #raise ModelError

    """ Plant Electric Efficiency """
    if phi < gv.Furn_min_electric:
        eta_el = 0
        #print "Furnace Boiler below minimum Power! 2"

    else:
        x = [2/7.0, 3/7.0, 4/7.0, 5/7.0, 6/7.0, 1] # part load regime, phi = Q / Q_max
        y = [0.025, 0.0625, 0.102, 0.127, 0.146, 0.147]
        eff_el_of_phi = interp1d(x, y, kind='cubic')
        eta_el = eff_el_of_phi(phi)



    # Return Temperature Dependency

    x = [0,15.5, 21, 26.7, 32.2, 37.7, 43.3, 49, 54.4, 60, 65.6, 71.1, 100] # Return Temperature Dependency
    y = [96.8,96.8, 96.2, 95.5, 94.7, 93.2, 91.2, 88.9, 87.3, 86.3, 86.0, 85.9, 85.8] # Return Temperature Dependency
    eff_of_T_return = interp1d(x, y, kind='linear')


    eff_therm_tot = eff_of_T_return(T_return_to_boiler - 273) * eta_therm / eff_of_T_return(60)

    if MOIST_TYPE == "dry":
        eff_therm_tot = eff_of_T_return(T_return_to_boiler - 273) * eta_therm / eff_of_T_return(60) + 0.087 # 8.7 % efficiency gain when using dry fuel
        #print eff_therm_tot
        eta_el += 0.087

    Q_therm_prim = Q_load / eff_therm_tot

    Q_aux = gv.Boiler_P_aux * Q_therm_prim # 0.026 Wh/Wh= 26kWh_el/MWh_th_prim,

    return eff_therm_tot, eta_el, Q_aux


"""
============================
operation costs
============================

"""


def Furnace_op_cost(Q_therm, Q_design, T_return_to_boiler, MOIST_TYPE, gv):
    """
    Calculates the operation cost of a furnace plant (only operation, no annualized cost!)



    Parameters
    ----------
    Q_therm : float
        thermal energy required from furnace plant in Wh

    Q_design : float
        Design Capacity of Furnace Plant (Boiler Thermal power!!)

    T_return_to_boiler : float
        return temperature to the boiler

    MOIST_TYPE : float
        moisture type of the fuel, set in MasterToSlaveVariables ('wet' or 'dry')


    Returns
    -------
    C_furn : float
        Total generation cost for required load (per hour) in CHF, including profits from electricity Sold

    C_furn_per_kWh : float
        cost per kWh in Rp / kWh, Including profits from electricity sold

    Q_primary : float
        required thermal energy per hour (in Wh of wood chips)

    E_furn_el_produced : float
        electricity produced by Furnace Plant


        C_furn, C_furn_per_Wh, Q_prim, Q_th_load
    """

    #if Q_load / Q_design < 0.3:
    #    raise ModelError
    """ Iterating for efficiency as Q_thermal_required is given as input """
    eta_therm_in = 0.6
    eta_therm_real = 1.0
    i = 0

    while 0.999 >= abs(eta_therm_in/eta_therm_real): # Iterating for thermal efficiency and required load
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
        C_furn_therm = Q_prim * gv.Furn_FuelCost_dry #  CHF / Wh - cost of thermal energy
        C_furn_el_sold = (Q_prim * eta_el - Q_aux)* gv.ELEC_PRICE #  CHF / Wh  - directly sold to the grid, as a cost gain
        C_furn = C_furn_therm - C_furn_el_sold
        C_furn_per_Wh = C_furn / Q_th_load


    else:
        C_furn_therm = Q_th_load * 1 / eta_therm_real * gv.Furn_FuelCost_wet
        C_furn_el_sold = (Q_prim * eta_el - Q_aux) * gv.ELEC_PRICE
        C_furn = C_furn_therm - C_furn_el_sold
        C_furn_per_Wh = C_furn / Q_th_load # in CHF / Wh

    E_furn_el_produced = eta_el * Q_prim - Q_aux

    return C_furn, C_furn_per_Wh, Q_prim, Q_th_load, E_furn_el_produced



"""
============================
investment and maintenance costs
============================

"""

def calc_Cinv_furnace(P_design, Q_annual, gv):
    """
    Calculates the cost of a Furnace
    based on Bioenergy 2020 (AFO) and POLYCITY Ostfildern 

    
    Parameters
    ----------
    P_design : float
        Design Power of Furnace Plant (Boiler Thermal power!!) [W]
        
    Q_annual : float
        annual thermal Power output [Wh]
    
    Returns
    -------
    InvC_return : float
        total investment Cost for building the plant
    
    InvCa : float
        annualized investment costs in CHF including labour, operation and maintainance
        
    """
    InvC = 0.670 * gv.EURO_TO_CHF * P_design # 670 € /kW therm(Boiler) = 800 CHF /kW (A+W data)

    Ca_invest =  (InvC * gv.Boiler_i * (1+ gv.Boiler_i) ** gv.Boiler_n / ((1+gv.Boiler_i) ** gv.Boiler_n - 1))
    Ca_maint = Ca_invest * gv.Boiler_C_maintainance
    Ca_labour =  gv.Boiler_C_labour / 1000000.0 * gv.EURO_TO_CHF * Q_annual

    InvCa = Ca_invest + Ca_maint + Ca_labour
    
    return InvCa

