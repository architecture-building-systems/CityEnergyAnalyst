"""
==================================================
cogeneration (combined heat and power)
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
operation costs
============================

"""


def calc_Cop_FC(Q_load, Q_design, phi_threshold, approach_call):

    """
    VALID FOR Q in range of 1-10kW_el !
    Compared to LHV of NG

    Efficiency for operation of a SOFC (based on LHV of nat. gas)

    Includes all auxillary losses

    Fuel = Natural Gas

    Modeled after:
        Approach A:
            http://energy.gov/eere/fuelcells/distributedstationary-fuel-cell-systems
            and
            NREL : p.5  of http://www.nrel.gov/vehiclesandfuels/energystorage/pdfs/36169.pdf

        Approach B:
            http://etheses.bham.ac.uk/641/1/Staffell10PhD.pdf

    Parameters
    ----------
    Q_load : float
        Load of time step

    Q_design : float
        Design Load of FC

    phi_threshold : float
        where Maximum Efficiency is reached, used for Approach A

    approach_call : string
        choose "A" or "B": A = NREL-Approach, B = Empiric Approach

    Returns
    -------
    eta_el : float
        electric efficiency of FC (Lower Heating Value), in abs. numbers

    Q_fuel : float
        Heat demand from fuel (in Watt)



    """
    phi = 0.0


    """ APPROACH A - AFTER NREL """
    if approach_call == "A":

        phi = float (Q_load) / float(Q_design)
        eta_max = 0.425 # from energy.gov

        if phi >= phi_threshold: # from NREL-Shape
            eta_el = eta_max - ((1/6.0 * eta_max)/ (1.0-phi_threshold) )* abs(phi-phi_threshold)


        if phi < phi_threshold:
            if phi <= 118/520.0 * phi_threshold:
                eta_el = eta_max * 2/3 * (phi / (phi_threshold*118/520.0))


            if phi < 0.5 * phi_threshold and phi >= 118/520.0 * phi_threshold:
                eta_el = eta_max * 2/3.0 + eta_max * 0.25 * (phi-phi_threshold*118/520.0) / (phi_threshold * (0.5 - 118/520.0))

            if phi > 0.5 * phi_threshold and phi < phi_threshold:
                eta_el = eta_max * (2/3.0 + 0.25)  +  1/12.0 * eta_max * (phi - phi_threshold * 0.5) / (phi_threshold * (1-0.5))

        eta_therm_max = 0.45 # constant, after energy.gov

        if phi < phi_threshold:
            eta_therm = 0.5 * eta_therm_max * (phi / phi_threshold)

        else:
            eta_therm = 0.5 * eta_therm_max * (1 + eta_therm_max * ((phi - phi_threshold) / (1 - phi_threshold)))


    """ SECOND APPROACH  after http://etheses.bham.ac.uk/641/"""
    if approach_call == "B":

        if Q_design > 0:
            phi = float(Q_load) / float(Q_design)

        else:
            phi = 0

        eta_el_max = 0.39  # after http://etheses.bham.ac.uk/641/
        eta_therm_max = 0.58   # http://etheses.bham.ac.uk/641/     * 1.11 as this source gives eff. of HHV
        eta_el_score = -0.220 + 5.277 * phi - 9.127 * phi**2 + 7.172* phi ** 3 - 2.103* phi**4
        eta_therm_score = 0.9 - 0.07 * phi + 0.17 * phi**2

        eta_el = eta_el_max * eta_el_score
        eta_therm = eta_therm_max * eta_therm_score

        if phi < 0.2:
            eta_el = 0


    return eta_el, eta_therm


"""
============================
investment and maintenance costs
============================

"""

def calc_Cinv_CCT(CC_size, gV):
    """
    Annualized investment costs for the Combined cycle

    Parameters
    ----------
    CC_size : float
        Electrical size of the CC

    Returns
    -------
    InvCa : float
        annualized investment costs in CHF

    """
    InvC = 32978 * (CC_size * 1E-3) ** 0.5946
    InvCa = InvC * gV.CC_i * (1+ gV.CC_i) ** gV.CC_n / \
            ((1+gV.CC_i) ** gV.CC_n - 1)

    return InvCa


def calc_Cinv_FC(P_design, gV):
    """
    Calculates the cost of a Fuel Cell in CHF

    http://hexis.com/sites/default/files/media/publikationen/140623_hexis_galileo_ibb_profitpaket.pdf?utm_source=HEXIS+Mitarbeitende&utm_campaign=06d2c528a5-1_Newsletter_2014_Mitarbeitende_DE&utm_medium=email&utm_term=0_e97bc1703e-06d2c528a5-

    Parameters
    ----------
    P_design : float
        Design THERMAL Load of Fuel Cell [W_th]

    Returns
    -------
    InvC_return : float
        total investment Cost

    InvCa : float
        annualized investment costs in CHF

    """

    InvC = (1+gV.FC_overhead) * gV.FC_stack_cost * P_design / 1000 # FC_stack_cost = 55'000 CHF  / kW_therm, 10 % extra (overhead) cost

    InvCa =  InvC * gV.FC_i * (1+ gV.FC_i) ** gV.FC_n / ((1+gV.FC_i) ** gV.FC_n - 1)


    return InvCa
