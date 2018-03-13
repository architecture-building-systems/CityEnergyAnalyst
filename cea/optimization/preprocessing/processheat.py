"""
========================================
Boiler Pre-treatment for Heat Processing
At The moment, process heet is excluded form the optimization process.
It is considered that whenever the case, the most competitive alterantive is to have a dedicated natural gas boiler

========================================

"""
from __future__ import division
import pandas as pd
from cea.technologies import boilers
from cea.optimization.constants import *


def calc_pareto_Qhp(locator, total_demand, gv, config, prices):
    """
    This function calculates the contribution to the pareto optimal results of process heating,

    :param locator: locator class
    :param total_demand: dataframe with building demand
    :param gv: global variables
    :type locator: class
    :type total_demand: class
    :type gv: class
    :return: hpCosts, hpCO2, hpPrim
    :rtype: tuple
    """
    hpCosts = 0
    hpCO2 = 0
    hpPrim = 0



    if total_demand["Qhprof_MWhyr"].sum()>0:
        df = total_demand[total_demand.Qhprof_MWhyr != 0]

        for name in df.Name :
            # Extract process heat needs
            Qhprof = pd.read_csv(locator.get_demand_results_file(name), usecols=["Qhprof_kWh"]).Qhprof_kWh.values

            Qnom = 0
            Qannual = 0
            # Operation costs / CO2 / Prim
            for i in range(8760):
                Qgas = Qhprof[i] * 1E3 / Boiler_eta_hp # [Wh] Assumed 0.9 efficiency

                if Qgas < Qnom:
                    Qnom = Qgas * (1+Qmargin_Disc)

                Qannual += Qgas
                hpCosts += Qgas * prices.NG_PRICE # [CHF]
                hpCO2 += Qgas * 3600E-6 * NG_BACKUPBOILER_TO_CO2_STD # [kg CO2]
                hpPrim += Qgas * 3600E-6 * NG_BACKUPBOILER_TO_OIL_STD # [MJ-oil-eq]

            # Investment costs
            Capex_a_hp, Opex_fixed_hp = boilers.calc_Cinv_boiler(Qnom, Qannual, gv, locator)
            hpCosts += (Capex_a_hp + Opex_fixed_hp)
    else:
        hpCosts = hpCO2 = hpPrim = 0
    return hpCosts, hpCO2, hpPrim











