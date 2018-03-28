"""
Sensible Heat Storage - Fully Mixed tank
"""

from __future__ import division
import numpy as np
from scipy.integrate import odeint
import math
from cea.demand.constants import TWW_SETPOINT, B_F
from cea.constants import ASPECT_RATIO, HEAT_CAPACITY_OF_WATER_JPERKGK, P_WATER_KGPERM3

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


def calc_fully_mixed_tank(T_start_C, T_ambient_C, q_discharged_W, q_charged_W, V_tank_m3):
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
    q_loss_W = calc_tank_heat_loss(Area_tank_surface_m2, T_start_C, T_ambient_C)
    T_tank_C = calc_tank_temperature(T_start_C, q_loss_W, q_discharged_W, q_charged_W, V_tank_m3)
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
    q_loss_W = calc_tank_heat_loss(area_tank_surface_m2, T_tank_C, T_basement_C)
    if q_tank_discharged_W <= 0:
        q_charged_W = 0
    else:
        q_charged_W = q_tank_discharged_W + q_loss_W + P_WATER_KGPERM3 * V_tank_m3 * (HEAT_CAPACITY_OF_WATER_JPERKGK / 1000) * (
        TWW_SETPOINT - T_tank_C) / 3.6

    return q_loss_W, q_tank_discharged_W, q_charged_W


def calc_tank_heat_loss(Area_tank_surface_m2, T_tank_C, tamb):
    q_loss_W = U_DHWTANK * Area_tank_surface_m2 * (T_tank_C - tamb)  # tank heat loss to the room in [Wh]
    return q_loss_W


def calc_tank_surface_area(V_tank_m3):
    h = (4 * V_tank_m3 * ASPECT_RATIO ** 2 / math.pi) ** (
    1.0 / 3.0)  # tank height in [m], derived from tank Aspect Ratio(AR)
    r = (V_tank_m3 / (math.pi * h)) ** (1.0 / 2.0)  # tank radius in [m], assuming tank shape is cylinder
    A_tank_m2 = 2 * math.pi * r ** 2 + 2 * math.pi * r * h  # tank surface area in [m2].
    return A_tank_m2


def ode(y, t, q_loss_W, q_discharged_W, q_charged_W, Pwater, Cpw, V_tank_m3):
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
    dydt = (q_charged_W - q_loss_W - q_discharged_W) / (Pwater * V_tank_m3 * Cpw)
    return dydt


def calc_tank_temperature(T_start_C, q_loss_W, q_discharged_W, q_charged_W, V_tank_m3):
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
    y = odeint(ode, T_start_C, t, args=(
    q_loss_W, q_discharged_W, q_charged_W, P_WATER_KGPERM3, HEAT_CAPACITY_OF_WATER_JPERKGK / 1000, V_tank_m3))
    T_tank_C = y[1]
    return T_tank_C



# use the optimized (numba_cc) versions of the ode function in this module if available
try:
    # import Numba AOT versions of the functions above, overwriting them
    from storagetank_cc import (ode)
except ImportError:
    # fall back to using the python version
    # print('failed to import from storagetank_cc.pyd, falling back to pure python functions')
    pass
