



import numpy_financial as npf


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# Calculates the EQUIVALENT ANNUAL COSTS (1. Step PRESENT VALUE OF COSTS (PVC), 2. Step EQUIVALENT ANNUAL COSTS)
def calc_opex_annualized(OpC_USDyr, Inv_IR_perc, Inv_LT_yr):
    """
    Calculate Annuitized Operating Expenditure (OPEX) -
    Calculations based on http://fahmi.ba.free.fr/docs/Courses/2012%20HEC/FBA_FE_Chap1_time_value_derivation.pdf

    :param OpC_USDyr: Operating Expenditure in USD per year
    :param Inv_IR_perc: Interest Rate in percentage
    :param Inv_LT_yr: Lifetime in years
    :return: Annuitized Operating Expenditure in USD per year
    """
    if Inv_IR_perc == 0:
        return OpC_USDyr

    Inv_IR = Inv_IR_perc / 100
    opex_list = [0.0]
    opex_list.extend(Inv_LT_yr * [OpC_USDyr])
    opexnpv = npf.npv(Inv_IR, opex_list)
    EAC = ((opexnpv * Inv_IR) / (1 - (1 + Inv_IR) ** (-Inv_LT_yr)))  # calculate positive EAC
    return EAC


def calc_capex_annualized(InvC_USD, Inv_IR_perc, Inv_LT_yr):
    """
    Calculate Annuitized Capital Expenditure (CAPEX) -
    Calculations based on http://fahmi.ba.free.fr/docs/Courses/2012%20HEC/FBA_FE_Chap1_time_value_derivation.pdf

    :param InvC_USD: Capital Expenditure in USD
    :param Inv_IR_perc: Interest Rate in percentage
    :param Inv_LT_yr: Lifetime in years
    :return: Annuitized Capital Expenditure in USD
    """
    if Inv_IR_perc == 0:
        return InvC_USD / Inv_LT_yr

    Inv_IR = Inv_IR_perc / 100
    return -((-InvC_USD * Inv_IR) / (1 - (1 + Inv_IR) ** (-Inv_LT_yr)))
