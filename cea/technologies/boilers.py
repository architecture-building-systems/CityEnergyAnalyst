# -*- coding: utf-8 -*-
"""
condensing boilers
"""


from __future__ import division
from scipy.interpolate import interp1d


__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

#operation costs

def cond_boiler_operation(Q_load, Q_design, T_return_to_boiler):

    """
    This function calculates efficiency for operation of condensing Boilers at DH plant based on LHV.
    This efficiency accounts for boiler efficiency only (not plant efficiency!)

    operational efficiency after:
        http://www.greenshootscontrols.net/?p=153

    :param Q_load: Load of time step
    :type Q_load: float

    :type Q_design: float
    :param Q_design: Design Load of Boiler

    :type T_return_to_boiler : float
    :param T_return_to_boiler: Return Temperature of the network to the boiler [K]

    :retype boiler_eff: float
    :returns boiler_eff: efficiency of Boiler (Lower Heating Value), in abs. numbers

    """
    #TODO[SH]: Operation efficiency Reference link doesn't work

    #Implement Curves provided by http://www.greenshootscontrols.net/?p=153
    x = [0, 15.5, 21, 26.7, 32.2, 37.7, 43.3, 49, 54.4, 60, 65.6, 71.1, 100] # Return Temperature Dependency
    y = [96.8, 96.8, 96.2, 95.5, 94.7, 93.2, 91.2, 88.9, 87.3, 86.3, 86.0, 85.9, 85.8] # Return Temperature Dependency
    x1 = [0, 0.05, 0.25, 0.5, 0.75, 1] # Load Point dependency
    y1 = [99.5, 99.3, 98.3, 97.6, 97.1, 96.8] # Load Point Dependency

    # do the interpolation
    eff_of_T_return = interp1d(x, y, kind='linear')
    eff_of_phi = interp1d(x1, y1, kind='cubic')

    # get input variables
    if Q_design > 0:
        phi = float(Q_load) / float(Q_design)
    else:
        phi = 0

    #if phi < gV.Boiler_min:
    #    print "Boiler at too low part load, see Model_Boiler_condensing, line 100"

        #raise model error!!

    if T_return_to_boiler == 0: # accounting with times with no flow
        T_return = 0
    else:
        T_return = T_return_to_boiler - 273

    eff_score = eff_of_phi(phi) / eff_of_phi(1)

    boiler_eff = (eff_score * eff_of_T_return(T_return) )/ 100.0


    return boiler_eff


def cond_boiler_op_cost(Q_therm, Q_design, T_return_to_boiler, BoilerFuelType, ElectricityType, gV):
    """
    Calculates the operation cost of a Condensing Boiler (only operation, not annualized cost)

    :type Q_therm : float
    :param Q_therm: Load of time step

    :type Q_design: float
    :param Q_design: Design Load of Boiler

    :type T_return_to_boiler : float
    :param T_return_to_boiler: return temperature to Boiler (from DH network)

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

    # Iterating for efficiency as Q_thermal_required is given as input

    #if float(Q_therm) / float(Q_design) < gV.Boiler_min:
    #    print "error expected in Boiler operation, below min part load!"

    #print float(Q_therm) / float(Q_design)

    # boiler efficiency
    eta_boiler = cond_boiler_operation(Q_therm, Q_design, T_return_to_boiler)


    if BoilerFuelType == 'BG':
        GAS_PRICE = gV.BG_PRICE
        #MaintananceCost = gV.Boiler_C_maintainance_fazBG
    else:
        GAS_PRICE = gV.NG_PRICE
        #MaintananceCost = gV.Boiler_C_maintainance_fazNG


    if ElectricityType == 'green':
        ELEC_PRICE = gV.ELEC_PRICE_GREEN
    else:
        ELEC_PRICE = gV.ELEC_PRICE

    C_boil_therm = Q_therm / eta_boiler * GAS_PRICE + (gV.Boiler_P_aux* ELEC_PRICE ) * Q_therm #  CHF / Wh - cost of thermal energy
    C_boil_per_Wh = 1/ eta_boiler * GAS_PRICE + gV.Boiler_P_aux* ELEC_PRICE
    E_aux_Boiler = gV.Boiler_P_aux * Q_therm

    Q_primary = Q_therm / eta_boiler

    return C_boil_therm, C_boil_per_Wh, Q_primary, E_aux_Boiler


def calc_Cop_boiler(Q_load, Q_design, T_return_to_boiler):

    """
    This function calculates efficiency for operation of condensing Boilers based on LHV.
    This efficiency accounts for boiler efficiency only (not plant efficiency!)

    operational efficiency after:
        http://www.greenshootscontrols.net/?p=153


    :param Q_load: Load of time step
    :type Q_load: float

    :type Q_design: float
    :param Q_design: Design Load of Boiler

    :type T_return_to_boiler : float
    :param T_return_to_boiler: Return Temperature of the network to the boiler [K]


    :retype boiler_eff: float
    :returns boiler_eff: efficiency of Boiler (Lower Heating Value), in abs. numbers
    """

    #Implement Curves provided by http://www.greenshootscontrols.net/?p=153
    x = [0, 15.5, 21, 26.7, 32.2, 37.7, 43.3, 49, 54.4, 60, 65.6, 71.1, 100] # Return Temperature Dependency
    y = [96.8, 96.8, 96.2, 95.5, 94.7, 93.2, 91.2, 88.9, 87.3, 86.3, 86.0, 85.9, 85.8] # Return Temperature Dependency
    x1 = [0.0, 0.05, 0.25, 0.5, 0.75, 1.0] # Load Point dependency
    y1 = [100.0, 99.3, 98.3, 97.6, 97.1, 96.8] # Load Point Dependency

     # do the interpolation
    eff_of_T_return = interp1d(x, y, kind='linear')
    eff_of_phi = interp1d(x1, y1, kind='cubic')

    # get input variables
    if Q_design > 0:
        phi = float(Q_load) / float(Q_design)

    else:
        phi = 0
    #if phi < gV.Boiler_min:
    #    print "Boiler at too low part load, see Model_Boiler_condensing, line 100"

        #raise model error!!


    T_return = T_return_to_boiler - 273
    eff_score = eff_of_phi(phi) / eff_of_phi(1)
    boiler_eff = (eff_score * eff_of_T_return(T_return) )/ 100.0

    return boiler_eff



# investment and maintenance costs

def calc_Cinv_boiler(Q_design, Q_annual, gV):
    """
    Calculates the annual cost of a boiler (based on A+W cost of oil boilers) [CHF / a]
    and Faz. 2012 data

    :type Q_design : float
    :param Q_design: Design Load of Boiler in [W]

    :type Q_annual : float
    :param Q_annual: Annual thermal load required from Boiler in [Wh]

    :param gV: globalvar.py

    :rtype InvCa : float
    :returns InvCa: Annualized investment costs in CHF/a including Maintenance Cost
    """
    # TODO[SH]: check source
    if Q_design >0:
        InvC = 28000 # after A+W

        if Q_design <= 90000 and Q_design >= 28000:
            InvC_exkl_MWST = 28000 + 0.275 * (Q_design - 28000) # linear interpolation of A+W data
            InvC = (gV.MWST + 1) * InvC_exkl_MWST

        elif Q_design > 90000 and Q_design  <= 320000: # 320kW = maximum Power of conventional Gas Boiler,
            InvC = 45000 + 0.11 * (Q_design - 90000)

        InvCa =  InvC * gV.Boiler_i * (1+ gV.Boiler_i) ** gV.Boiler_n / ((1+gV.Boiler_i) ** gV.Boiler_n - 1)

        if Q_design > 320000: # 320kW = maximum Power of conventional Gas Boiler
            InvCa = gV.EURO_TO_CHF * (84000 + 14 * Q_design / 1000) # after Faz.2012

        Maint_C_annual = gV.Boiler_C_maintainance_faz * Q_annual / 1E6 * gV.EURO_TO_CHF # 3.5 euro per MWh_th FAZ 2013
        Labour_C = gV.Boiler_C_labour * Q_annual / 1E6 * gV.EURO_TO_CHF # approx 4 euro per MWh_th

        InvCa += Maint_C_annual + Labour_C

    else:
        InvCa = 0

    return InvCa

