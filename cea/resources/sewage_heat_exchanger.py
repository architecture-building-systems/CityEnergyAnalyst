# -*- coding: utf-8 -*-
"""
Sewage source heat exchanger
"""



import pandas as pd
import numpy as np
from cea.constants import HEX_WIDTH_M,VEL_FLOW_MPERS, HEAT_CAPACITY_OF_WATER_JPERKGK, H0_KWPERM2K, MIN_FLOW_LPERS, T_MIN, AT_MIN_K, P_SEWAGEWATER_KGPERM3
import cea.config
import cea.inputlocator
from cea.utilities.date import get_date_range_hours_from_year
from cea.utilities import epwreader

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_sewage_heat_exchanger(locator, config):
    """
    Calaculate the heat extracted from the sewage HEX.

    :param locator: an InputLocator instance set to the scenario to work on
    :param Length_HEX_available: HEX length available
    :type Length_HEX_available: float

    Save the results to `SWP.csv`
    """

    # local variables
    mcpwaste = []
    twaste = []
    mXt = []
    counter = 0
    names = pd.read_csv(locator.get_total_demand()).name
    sewage_water_ratio = config.sewage.sewage_water_ratio
    heat_exchanger_length = config.sewage.heat_exchanger_length
    V_lps_external = config.sewage.sewage_water_district

    # create date range for the calculation year
    weather_file = locator.get_weather_file()
    weather_data = epwreader.epw_reader(weather_file)
    year = weather_data['year'][0]
    date_range = get_date_range_hours_from_year(year)

    for building_name in names:
        building = pd.read_csv(locator.get_demand_results_file(building_name))
        mcp_combi, t_to_sewage = np.vectorize(calc_Sewagetemperature)(building.Qww_sys_kWh, building.Qww_kWh, building.Tww_sys_sup_C,
                                                     building.Tww_sys_re_C, building.mcptw_kWperC, building.mcpww_sys_kWperC, sewage_water_ratio)
        mcpwaste.append(mcp_combi)
        twaste.append(t_to_sewage)
        mXt.append(mcp_combi*t_to_sewage)
        counter = counter +1
    mcpwaste_zone = np.sum(mcpwaste, axis =0)
    mXt_zone = np.sum(mXt, axis =0)
    twaste_zone = [x * (y**-1) * 0.8 if y != 0 else 0 for x,y in zip (mXt_zone, mcpwaste_zone)] # losses in the grid of 20%

    Q_source, t_source, t_out, tin_e, tout_e, mcpwaste_total = np.vectorize(calc_sewageheat)(mcpwaste_zone, twaste_zone, HEX_WIDTH_M,
                                                                              VEL_FLOW_MPERS, H0_KWPERM2K, MIN_FLOW_LPERS,
                                                                              heat_exchanger_length, T_MIN, AT_MIN_K, V_lps_external)

    #save to disk
    locator.ensure_parent_folder_exists(locator.get_sewage_heat_potential())
    pd.DataFrame({"date": pd.to_datetime(date_range), "Qsw_kW" : Q_source, "Ts_C" : t_source, "T_out_sw_C" : t_out, "T_in_sw_C" : twaste_zone,
                  "mww_zone_kWperC":mcpwaste_total,
                    "T_out_HP_C" : tout_e, "T_in_HP_C" : tin_e}).to_csv(locator.get_sewage_heat_potential(),
                                                                      index=False, float_format='%.3f')




# Calc Sewage heat

def calc_Sewagetemperature(Qwwf, Qww, tsww, trww, mcptw, mcpww, SW_ratio):
    """
    Calculate sewage temperature and flow rate released from DHW usages and Fresh Water (FW) in buildings.

    :param Qwwf: final DHW heat requirement
    :type Qwwf: float
    :param Qww: DHW heat requirement
    :type Qww: float
    :param tsww: DHW supply temperature
    :type tsww: float
    :param trww: DHW return temperature
    :type trww: float
    :param totwater: fresh water flow rate
    :type totwater: float
    :param mcpww: DHW heat capacity
    :type mcpww: float
    :param SW_ratio: ratio of decrease/increase in sewage water due to solids and also water intakes.
    :type SW_ratio: float

    :returns mcp_combi: sewage water heat capacity [kW_K]
    :rtype mcp_combi: float
    :returns t_to_sewage: sewage water temperature
    :rtype t_to_sewage: float
    """

    if Qwwf > 0:
        Qloss_to_spur = Qwwf - Qww
        t_spur = tsww - Qloss_to_spur / mcpww
        m_DHW = mcpww * SW_ratio
        m_TW = mcptw * SW_ratio
        mcp_combi = m_DHW + m_TW
        t_combi = ( m_DHW * t_spur + m_TW * trww ) / mcp_combi
        t_to_sewage = 0.90 * t_combi                  # assuming 10% thermal loss through piping
    else:
        t_to_sewage = trww
        mcp_combi = mcptw * SW_ratio  # in [kW_K]
    return mcp_combi, t_to_sewage # in lh or kgh and in C

def calc_sewageheat(mcp_kWC_zone, tin_C, w_HEX_m, Vf_ms, h0, min_lps, L_HEX_m, tmin_C, ATmin, V_lps_external):
    """
    Calculates the operation of sewage heat exchanger.

    :param mcp_kWC_total: heat capacity of total sewage in a zone
    :type mcp_kWC_total: float
    :param tin_C: sewage inlet temperature of a zone
    :type tin_C: float
    :param w_HEX_m: width of the sewage HEX
    :type w_HEX_m: float
    :param Vf_ms: sewage flow rate [m/s]
    :type Vf_ms: float
    :param cp: water specific heat capacity
    :type cp: float
    :param h0: sewage heat transfer coefficient
    :type h0: float
    :param min_lps: sewage minimum flow rate in [lps]
    :type min_lps: float
    :param L_HEX_m: HEX length available
    :type L_HEX_m: float
    :param tmin_C: minimum temperature of extraction
    :type tmin_C: float
    :param ATmin: minimum area of heat exchange
    :type ATmin: float

    :returns Q_source: heat supplied by sewage
    :rtype: float
    :returns t_source: sewage heat supply temperature
    :rtype t_source: float
    :returns tb2: sewage return temperature
    :rtype tbs: float
    :returns ta1: temperature inlet of the cold stream (from the HP)
    :rtype ta1: float
    :returns ta2: temperature outlet of the cold stream (to the HP)
    :rtype ta2: float

    ..[J.A. Fonseca et al., 2016] J.A. Fonseca, Thuy-An Nguyen, Arno Schlueter, Francois Marechal (2016). City Enegy
    Analyst (CEA): Integrated framework for analysis and optimization of building energy systems in neighborhoods and
    city districts. Energy and Buildings.
    """
    V_lps_zone = mcp_kWC_zone/ (HEAT_CAPACITY_OF_WATER_JPERKGK / 1E3)
    V_lps_total = V_lps_zone + V_lps_external
    mcp_kWC_total = mcp_kWC_zone + ((V_lps_external /1000) * P_SEWAGEWATER_KGPERM3 * (HEAT_CAPACITY_OF_WATER_JPERKGK/1E3)) #kW_C
    mcp_max = (Vf_ms * w_HEX_m * 0.20) * P_SEWAGEWATER_KGPERM3 * (HEAT_CAPACITY_OF_WATER_JPERKGK /1E3)  # 20 cm is the depth of the active water in contact with the HEX
    A_HEX = w_HEX_m * L_HEX_m   # area of heat exchange

    if min_lps < V_lps_total:
        if mcp_kWC_total >= mcp_max:
            mcp_kWC_total = mcp_max

        # B is the sewage, A is the heat pump
        mcpa = mcp_kWC_total * 1.1 # the flow in the heat pumps slightly above the flow on the sewage side
        tb1 = tin_C
        ta1 = tin_C - ((tin_C - tmin_C) + ATmin / 2)
        alpha = h0 * A_HEX * (1 / mcpa - 1 / mcp_kWC_total)
        n = ( 1 - np.exp( -alpha ) ) / (1 - mcpa / mcp_kWC_total * np.exp(-alpha))
        tb2 = tb1 + mcpa / mcp_kWC_total * n * (ta1 - tb1)
        Q_source = mcp_kWC_total * (tb1 - tb2)
        ta2 = ta1 + Q_source / mcpa
        t_source = ( tb2 + tb1 ) / 2
    else:
        tb1 = tin_C
        tb2 = tin_C
        ta1 = tin_C
        ta2 = tin_C
        Q_source = 0
        t_source = tin_C

    return Q_source, t_source, tb2, ta1, ta2, mcp_kWC_total


def main(config):

    locator = cea.inputlocator.InputLocator(config.scenario)

    calc_sewage_heat_exchanger(locator=locator, config=config)


if __name__ == '__main__':
    main(cea.config.Configuration())
