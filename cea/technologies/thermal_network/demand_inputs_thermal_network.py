from __future__ import print_function

"""
Hydraulic - thermal network
"""

from __future__ import division
import numpy as np

__author__ = "Lennart Rogenhofer"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Martin Mosteiro Romero", "Shanshan Hsieh", "Lennart Rogenhofer", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def calc_demand_aggregation(building_demand):
    '''
    This function computes the average  temperature between two vectors of heating demand.
    In this case, domestic hotwater and space heating.

    :param Q_ahu: air heating load
    :param Q_aru: air recirculating load
    :param Q_scu: sensible cooling load
    :param t_ahu: demand temperature of air heating unit
    :param mcpcsf_ahu_kWperC: mass flow rate of air heating unit
    :param t_aru: demand temperature of air recirculating unit
    :param mcpcsf_aru_kWperC: mass flow rate of air recirculating unit
    :param t_scu: demand temperature of sensible cooling load
    :param mcpcsf_scu_kWperC: mass flow rate of sensible cooling unit
    :return: Qcsf_total_Wh: total cooling load
    :return: t_avg_sup_K: average demand temperature
    :return: m_total_WperK: total mass flow of demand
    '''
    Qcsf_total_Wh = (abs(building_demand.Qcsf_ahu_kWh.values) + abs(building_demand.Qcsf_aru_kWh.values) + abs(building_demand.Qcsf_scu_kWh.values)) * 1000
    m_total_WperK = (building_demand.mcpcsf_ahu_kWperC.values + building_demand.mcpcsf_aru_kWperC.values + building_demand.mcpcsf_scu_kWperC.values)*1000

    if Qcsf_total_Wh > 0:
        T_avg_sup_K = ((building_demand.T_ahu_sup.values +273.15) * building_demand.mcpcsf_ahu_kWperC.values + (building_demand.T_aru_sup.values+273.15)
                     * building_demand.mcpcsf_aru_kWperC.values + (building_demand.T_scu_sup.values+273.15) * building_demand.mcpcsf_scu_kWperC.values) \
                     / m_total_WperK # average supply temperature

        T_avg_ret_K = ((building_demand.T_ahu_ret.values+273.15) * building_demand.mcpcsf_ahu_kWperC_ret.values + (building_demand.T_aru_ret.values+273.15)
                     * building_demand.mcpcsf_aru_kWperC.values + (building_demand.T_scu_ret.values+273.15) * building_demand.mcpcsf_scu_kWperC.values) \
                     / m_total_WperK #average return temperature
    else: # if there is no flow rate, t_avg_sup_K = t_ahu = t_aru = t_scu
        T_avg_sup_K = (building_demand.T_ahu_sup.values + building_demand.T_aru_sup.values + building_demand.T_scu_sup.values) / 3 +273.15
        T_avg_ret_K = (building_demand.T_ahu_ret.values + building_demand.T_aru_ret.values + building_demand.T_scu_ret.values) / 3 +273.15
    return np.float(Qcsf_total_Wh), np.float(T_avg_sup_K), np.float(T_avg_ret_K), np.float(m_total_WperK)
