"""
Boiler Pre-treatment for Heat Processing

At the moment, process heat is excluded form the optimization process.
It is considered that whenever the case, the most competitive alternative is to have a dedicated natural gas boiler


"""
from __future__ import division
import pandas as pd
from cea.technologies import boiler
from cea.optimization.constants import BOILER_ETA_HP, SIZING_MARGIN


def calc_pareto_Qhp(locator, total_demand, prices, lca, config):
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



    if total_demand["Qhpro_sys_MWhyr"].sum()>0:
        df = total_demand[total_demand.Qhpro_sys_MWhyr != 0]

        for name in df.Name :
            # Extract process heat needs
            Qhpro_sys = pd.read_csv(locator.get_demand_results_file(name), usecols=["Qhpro_sys_kWh"]).Qhpro_sys_kWh.values

            Qnom = 0
            Qannual = 0
            # Operation costs / CO2 / Prim
            for i in range(8760):
                Qgas = Qhpro_sys[i] * 1E3 / BOILER_ETA_HP # [Wh] Assumed 0.9 efficiency

                if Qgas < Qnom:
                    Qnom = Qgas * (1 + SIZING_MARGIN)

                Qannual += Qgas
                hpCosts += Qgas * prices.NG_PRICE # [CHF]
                hpCO2 += Qgas * 3600E-6 * lca.NG_BACKUPBOILER_TO_CO2_STD # [kg CO2]
                hpPrim += Qgas * 3600E-6 * lca.NG_BACKUPBOILER_TO_OIL_STD # [MJ-oil-eq]

            # Investment costs

            Capex_a_hp_USD, Opex_fixed_hp_USD, Capex_hp_USD = boiler.calc_Cinv_boiler(Qnom, locator, config, 'BO1')
            hpCosts += (Capex_a_hp_USD + Opex_fixed_hp_USD)
    else:
        hpCosts = hpCO2 = hpPrim = 0
    return hpCosts, hpCO2, hpPrim











