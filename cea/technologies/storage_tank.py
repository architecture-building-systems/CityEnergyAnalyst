"""
Sensible Heat Storage - Fully Mixed tank
"""

from __future__ import division
import numpy as np
from scipy.integrate import odeint
import math
from cea.technologies.thermal_network.substation_matrix import calc_area_HEX, calc_dTm_HEX
from cea.demand.constants import TWW_SETPOINT, B_F
from cea.constants import ASPECT_RATIO, HEAT_CAPACITY_OF_WATER_JPERKGK, P_WATER_KGPERM3, WH_TO_J
from cea.technologies.constants import U_COOL, U_HEAT, TANK_HEX_EFFECTIVENESS
from cea.optimization.constants import T_TANK_FULLY_DISCHARGED_K, T_TANK_FULLY_CHARGED_K, DT_COOL, TANK_SIZE_MULTIPLIER

__author__ = "Shanshan Hsieh"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["ShanShan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# CONSTANTS REFACTORED FROM GV
U_DHWTANK = 0.225  # tank insulation heat transfer coefficient in W/m2-K, value taken from SIA 385


def calc_fully_mixed_tank(T_start_C, T_ambient_C, q_discharged_W, q_charged_W, V_tank_m3, tank_type):
    """
    Temporary inputs:
    T_start_C = 6 degree C
    T_ambient_C = external temperature of each time step
    q_discharged_W = cooling loads fulfilled by tank
    q_charged_W = excess cooling from VCC or ACH
    V_tank_m3 = volume of tank

    the output should be saved and used as T_start_C in the next time step

    :param T_start_C: Tank temperature at the beginning of the time step
    :param T_ambient_C: Ambient temperature at the location of tank
    :param q_discharged_W: thermal energy discharged from tank
    :param q_charged_W: thermal energy charged to tank
    :param V_tank_m3: tank volume
    :return:
    """
    Area_tank_surface_m2 = calc_tank_surface_area(V_tank_m3)
    q_loss_W = calc_cold_tank_heat_loss(Area_tank_surface_m2, T_start_C, T_ambient_C)
    T_tank_C = calc_tank_temperature(T_start_C, q_loss_W, q_discharged_W, q_charged_W, V_tank_m3, tank_type)
    return T_tank_C


def calc_dhw_tank_heat_balance(T_int_C, T_ext_C, T_tank_C, V_tank_m3, q_tank_discharged_W, area_tank_surface_m2):
    """
    This algorithm calculates the heat flows within a fully mixed water storage tank.
    Heat flows include sensible heat loss to the environment (q_loss_W), heat charged into the tank (q_charged_W),
    and heat discharged from the tank (q_discharged_W).

    :param T_tank_C: tank temperature in [C]
    :param Tww_setpoint: DHW temperature set point in [C]
    :param T_int_C: room temperature in [C]
    :param T_ext_C: ambient temperature in [C]
    :param V_tank_m3: DHW tank size in [m3]

    :type T_tank_C: float
    :type Tww_setpoint: float
    :type T_int_C: float
    :type T_ext_C: float
    :type V_tank_m3: float
    :return q_loss_W: storage sensible heat loss in [Wh].
    :return q_discharged_W: heat discharged from the tank in [Wh], including dhw heating demand and distribution heat loss.
    :return q_charged_W: heat charged into the tank in [Wh].
    :rtype q_loss_W: float
    :rtype q_discharged_W: float
    :rtype q_charged_W: float
    """

    T_basement_C = T_int_C - B_F * (T_int_C - T_ext_C)  # Calculate T_basement_C in basement according to EN
    q_loss_W = calc_hot_tank_heat_loss(area_tank_surface_m2, T_tank_C, T_basement_C)
    if q_tank_discharged_W <= 0:
        q_charged_W = 0
    else:
        q_charged_W = q_tank_discharged_W + q_loss_W + P_WATER_KGPERM3 * V_tank_m3 * (
            HEAT_CAPACITY_OF_WATER_JPERKGK / 1000) * (
                                                           TWW_SETPOINT - T_tank_C) / 3.6

    return q_loss_W, q_tank_discharged_W, q_charged_W


def calc_hot_tank_heat_loss(Area_tank_surface_m2, T_tank_C, tamb):
    q_loss_W = U_DHWTANK * Area_tank_surface_m2 * (T_tank_C - tamb)  # tank heat loss to the room in [Wh]
    return q_loss_W

def calc_cold_tank_heat_loss(Area_tank_surface_m2, T_tank_C, T_ambient_C):
    q_loss_W = U_DHWTANK * Area_tank_surface_m2 * (T_ambient_C - T_tank_C)  # tank heat gain from the room in [Wh]
    return q_loss_W


def calc_tank_surface_area(V_tank_m3):
    h = (4 * V_tank_m3 * ASPECT_RATIO ** 2 / math.pi) ** (
    1.0 / 3.0)  # tank height in [m], derived from tank Aspect Ratio(AR)
    if h == 0:
        r = 0
    else:
        r = (V_tank_m3 / (math.pi * h)) ** (1.0 / 2.0)  # tank radius in [m], assuming tank shape is cylinder
    A_tank_m2 = 2 * math.pi * r ** 2 + 2 * math.pi * r * h  # tank surface area in [m2].
    return A_tank_m2


def ode_hot_water_tank(y, t, q_loss_W, q_discharged_W, q_charged_W, V_tank_m3):
    """
    This algorithm describe the energy balance of the dhw tank with a differential equation.

    :param y: storage temperature in C.
    :param t: time steps.
    :param q_loss_W: storage tank sensible heat loss in W.
    :param q_discharged_W: heat discharged from the tank in W.
    :param q_charged_W: heat charged into the tank in W.
    :param V_tank_m3: DHW tank size in [m3]
    :type y: float
    :type t: float
    :type q_loss_W: float
    :type q_discharged_W: float
    :type q_charged_W: float
    :type V_tank_m3: float

    :return dydt: change in temperature at each time step.
    :type dydt: float
    """
    if V_tank_m3 == 0:
        dydt = 0
    else:
        mcp_tank_JperK = (P_WATER_KGPERM3 * V_tank_m3 * HEAT_CAPACITY_OF_WATER_JPERKGK)
        net_energy_flow_J = (q_charged_W - q_loss_W - q_discharged_W) * WH_TO_J
        dydt = net_energy_flow_J / mcp_tank_JperK
    return dydt


def ode_cold_water_tank(y, t, q_gain_W, q_discharged_W, q_charged_W, V_tank_m3):
    """
    This algorithm describe the energy balance of the dhw tank with a differential equation.

    :param y: storage temperature in C.
    :param t: time steps.
    :param q_gain_W: storage tank sensible heat loss in W.
    :param q_discharged_W: heat discharged from the tank in W.
    :param q_charged_W: heat charged into the tank in W.
    :param V_tank_m3: DHW tank size in [m3]
    :type y: float
    :type t: float
    :type q_gain_W: float
    :type q_discharged_W: float
    :type q_charged_W: float
    :type V_tank_m3: float

    :return dydt: change in temperature at each time step.
    :type dydt: float
    """
    if V_tank_m3 == 0:
        dydt = 0
    else:
        mcp_tank_JperK = (P_WATER_KGPERM3 * V_tank_m3 * HEAT_CAPACITY_OF_WATER_JPERKGK)
        net_energy_flow_J = (q_gain_W + q_discharged_W - q_charged_W) * WH_TO_J
        dydt = net_energy_flow_J / mcp_tank_JperK
    return dydt


def calc_tank_temperature(T_start_C, q_loss_W, q_discharged_W, q_charged_W, V_tank_m3, tank_type):
    """
    This algorithm solves the differential equation, ode.

    :param T_start_C: initial tank temperature in [C]
    :param q_loss_W: storage tank sensible heat loss in Wh.
    :param q_discharged_W: heat discharged from the tank in Wh.
    :param q_charged_W: heat charged into the tank in Wh.
    :param V_tank_m3: DHW tank size in [m3]

    :type T_start_C: float
    :type q_loss_W: float
    :type q_discharged_W: float
    :type q_charged_W: float
    :type V_tank_m3: float

    :returns T_tank_C: tank temperature after the energy balance
    :rtype T_tank_C: float
    """
    t = np.linspace(0, 1, 2)
    if tank_type == 'hot_water':
        y = odeint(ode_hot_water_tank, T_start_C, t, args=(
            q_loss_W, q_discharged_W, q_charged_W, V_tank_m3))
    elif tank_type == 'cold_water':
        y = odeint(ode_cold_water_tank, T_start_C, t, args=(
            q_loss_W, q_discharged_W, q_charged_W, V_tank_m3))
    else:
        raise ValueError('Please specified the tank type, it should be either cold_water or hot_water.')
    T_tank_C = y[1]
    return T_tank_C[0]


# use the optimized (numba_cc) versions of the ode function in this module if available
try:
    # import Numba AOT versions of the functions above, overwriting them
    from storagetank_cc import (ode)
except ImportError:
    # fall back to using the python version
    # print('failed to import from storagetank_cc.pyd, falling back to pure python functions')
    pass


# ================================
# cold water storage tank design
# ================================


def calc_storage_tank_properties(DCN_operation_parameters, Qc_tank_charge_max_W, Qc_tank_discharge_peak_W, peak_hour,
                                 master_to_slave_vars):
    # discharging
    if master_to_slave_vars.WasteServersHeatRecovery == 1:
        mdot_DCN_peak_kgpers = DCN_operation_parameters.loc[
            peak_hour, 'mdot_cool_space_cooling_and_refrigeration_netw_all_kgpers']  # TODO: ideally, it should come from Qc_DCN_W
        T_sup_DCN_peak_K = DCN_operation_parameters.loc[peak_hour, 'T_DCNf_space_cooling_and_refrigeration_sup_K']
        T_re_DCN_peak_K = DCN_operation_parameters.loc[peak_hour, 'T_DCNf_space_cooling_and_refrigeration_re_K']
    else:
        mdot_DCN_peak_kgpers = DCN_operation_parameters.loc[
            peak_hour, 'mdot_cool_space_cooling_data_center_and_refrigeration_netw_all_kgpers']  # TODO: ideally, it should come from Qc_DCN_W
        T_sup_DCN_peak_K = DCN_operation_parameters.loc[
            peak_hour, 'T_DCNf_space_cooling_data_center_and_refrigeration_sup_K']
        T_re_DCN_peak_K = DCN_operation_parameters.loc[
            peak_hour, 'T_DCNf_space_cooling_data_center_and_refrigeration_re_K']

    area_HEX_tank_discharege_m2, UA_HEX_tank_discharge_WperK = calc_cold_storage_discharge_HEX(
        mdot_DCN_peak_kgpers, Qc_tank_discharge_peak_W, T_TANK_FULLY_CHARGED_K, T_re_DCN_peak_K, T_sup_DCN_peak_K)

    # charging
    T_sup_VCC_K = T_TANK_FULLY_CHARGED_K - DT_COOL
    T_re_VCC_K = T_TANK_FULLY_DISCHARGED_K - DT_COOL
    mcp_charge_kgpers = Qc_tank_charge_max_W / (T_re_VCC_K - T_sup_VCC_K)
    area_HEX_tank_charge_m2, UA_HEX_tank_charge_WperK = calc_cold_storage_charge_HEX(mcp_charge_kgpers,
                                                                                     Qc_tank_charge_max_W,
                                                                                     T_TANK_FULLY_DISCHARGED_K,
                                                                                     T_sup_VCC_K,
                                                                                     T_re_VCC_K)

    # calculate tank volume
    Q_tank_capacity_J = TANK_SIZE_MULTIPLIER * Qc_tank_discharge_peak_W * WH_TO_J
    m_tank_kg = Q_tank_capacity_J / (
    HEAT_CAPACITY_OF_WATER_JPERKGK * (T_TANK_FULLY_DISCHARGED_K - T_TANK_FULLY_CHARGED_K))
    V_tank_m3 = m_tank_kg / P_WATER_KGPERM3

    return area_HEX_tank_discharege_m2, UA_HEX_tank_discharge_WperK, area_HEX_tank_charge_m2, UA_HEX_tank_charge_WperK, V_tank_m3


# ====================
# HEX sizing
# ====================

def calc_cold_storage_discharge_HEX(m_hot_0, Q_hot_0, T_cold_in, T_hot_in, T_hot_out):
    """

    :param mcp_hot: secondary side
    :param Q_hot: required heat from the primary side
    :param T_cold_in:
    :param T_hot_in:
    :param T_hot_out:
    :return:
    """
    # nominal conditions on the tank side
    mcp_hot_0 = m_hot_0*HEAT_CAPACITY_OF_WATER_JPERKGK
    mcp_cold_0 = mcp_hot_0 * (T_hot_in - T_hot_out) / ((T_hot_in - T_cold_in) * TANK_HEX_EFFECTIVENESS)
    T_cold_out = Q_hot_0 / mcp_cold_0 + T_cold_in #todo: check if the number is realistic
    dTm_0 = calc_dTm_HEX(T_hot_in, T_hot_out, T_cold_in, T_cold_out)
    # Area heat exchange and UA_heating
    Area_HEX_m2, UA_WperK = calc_area_HEX(Q_hot_0, dTm_0, U_COOL)

    return Area_HEX_m2, UA_WperK


def calc_cold_storage_charge_HEX(mcp_cold_0, Q_cold_0, T_hot_in, T_cold_in, T_cold_out):
    '''

    :param mcp_cold_0: nominal capacity mass flow rate primary side
    :param Q_cold_0: nominal cooling load
    :param T_hot_in: nominal in temperature of secondary side
    :param T_cold_in: nominal in temperature of primary side
    :param T_cold_out: nominal out temperature of primary side

    :return Area_HEX_m2: Heat exchanger area in [m2]
    :return UA_WperK: UA_WperK [W/K]
    '''

    # nominal conditions on the tank side
    mcp_hot_0 = mcp_cold_0 * (T_cold_out - T_cold_in) / ((T_hot_in - T_cold_in) * TANK_HEX_EFFECTIVENESS)
    T_hot_out = T_hot_in - Q_cold_0 / mcp_hot_0  #todo: check if the number is realistic
    dTm_0 = calc_dTm_HEX(T_hot_in, T_hot_out, T_cold_in, T_cold_out)
    # Area heat exchange and UA_WperK
    Area_HEX_m2, UA_WperK = calc_area_HEX(Q_cold_0, dTm_0, U_HEAT)

    return Area_HEX_m2, UA_WperK
