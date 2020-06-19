"""
Boiler Pre-treatment for Heat Processing

At the moment, process heat is excluded form the optimization process.
It is considered that whenever the case, the most competitive alternative is to have a dedicated natural gas boiler


"""



import pandas as pd
from cea.technologies import boiler
from cea.technologies.constants import BOILER_ETA_HP
from cea.constants import HOURS_IN_YEAR, WH_TO_J


def calc_pareto_Qhp(locator, total_demand, prices, lca):
    """
    This function calculates the contribution to the pareto optimal results of process heating,

    :param locator: locator class
    :param total_demand: dataframe with building demand
    :type locator: class
    :type total_demand: class
    :return: hpCosts, hpCO2, hpPrim
    :rtype: tuple
    """
    hpCosts = 0
    hpCO2 = 0
    hpPrim = 0

    boiler_cost_data = pd.read_excel(locator.get_database_conversion_systems(), sheet_name="Boiler")

    if total_demand["Qhpro_sys_MWhyr"].sum()>0:
        df = total_demand[total_demand.Qhpro_sys_MWhyr != 0]

        for name in df.Name :
            # Extract process heat needs
            Qhpro_sys_kWh = pd.read_csv(locator.get_demand_results_file(name), usecols=["Qhpro_sys_kWh"]).Qhpro_sys_kWh.values

            Qnom_Wh = 0
            Qannual_Wh = 0
            # Operation costs / CO2 / Prim
            for i in range(HOURS_IN_YEAR):
                Qgas_Wh = Qhpro_sys_kWh[i] * 1E3 / BOILER_ETA_HP # [Wh] Assumed 0.9 efficiency

                if Qgas_Wh < Qnom_Wh:
                    Qnom_Wh = Qgas_Wh

                Qannual_Wh += Qgas_Wh
                hpCosts += Qgas_Wh * prices.NG_PRICE # [CHF]
                hpCO2 += Qgas_Wh * WH_TO_J / 1.0E6 * lca.NG_BACKUPBOILER_TO_CO2_STD / 1E3 # [ton CO2]
                hpPrim += Qgas_Wh * WH_TO_J / 1.0E6 * lca.NG_BACKUPBOILER_TO_OIL_STD # [MJ-oil-eq]

            # Investment costs

            Capex_a_hp_USD, Opex_fixed_hp_USD, Capex_hp_USD = boiler.calc_Cinv_boiler(Qnom_Wh, 'BO1', boiler_cost_data)
            hpCosts += (Capex_a_hp_USD + Opex_fixed_hp_USD)
    else:
        hpCosts = hpCO2 = hpPrim = 0
    return hpCosts, hpCO2, hpPrim











