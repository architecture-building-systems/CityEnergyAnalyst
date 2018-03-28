"""
Sensible Heat Storage - Fully Mixed tank
"""

from __future__ import division
import numpy as np
from scipy.integrate import odeint
import math
from cea.demand import constants
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

    :param T_start_C:
    :param T_ambient_C:
    :param q_discharged_W:
    :param q_charged_W:
    :param V_tank_m3:
    :return:
    """
    Area_tank_surface_m2 = calc_tank_surface_area(V_tank_m3)
    q_loss_W = calc_tank_heat_loss(Area_tank_surface_m2, T_start_C, T_ambient_C)
    T_tank_C = calc_tank_temperature(T_start_C, q_loss_W, q_discharged_W, q_charged_W, V_tank_m3)
    return T_tank_C



def calc_dhw_tank_heat_flows(ta, te, T_tank_C, V, q_tank_discharged_W, Area_tank_surface_m2):
    """
    This algorithm calculates the heat flows within a fully mixed water storage tank.
    Heat flows include sensible heat loss to the environment (q_loss_W), heat charged into the tank (q_charged_W),
    and heat discharged from the tank (q_discharged_W).

    :param T_tank_C: tank temperature in [C]
    :param Tww_setpoint: DHW temperature set point in [C]
    :param ta: room temperature in [C]
    :param te: ambient temperature in [C]
    :param V: DHW tank size in [m3]
    :param gv: globalvar.py

    :type T_tank_C: float
    :type Tww_setpoint: float
    :type ta: float
    :type te: float
    :type V: float
    :return q_loss_W: storage sensible heat loss in [Wh].
    :return q_discharged_W: heat discharged from the tank in [Wh], including dhw heating demand and distribution heat loss.
    :return q_charged_W: heat charged into the tank in [Wh].
    :rtype q_loss_W: float
    :rtype q_discharged_W: float
    :rtype q_charged_W: float
    """

    tamb = ta - constants.B_F * (ta - te)  # Calculate tamb in basement according to EN
    q_loss_W = calc_tank_heat_loss(Area_tank_surface_m2, T_tank_C, tamb)
    if q_tank_discharged_W <= 0:
        q_charged_W = 0
    else:
        q_charged_W = q_tank_discharged_W + q_loss_W + P_WATER_KGPERM3 * V * (HEAT_CAPACITY_OF_WATER_JPERKGK / 1000) * (
        constants.TWW_SETPOINT - T_tank_C) / 3.6

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


def ode(y, t, ql, qd, qc, Pwater, Cpw, Vtank):
    """
    This algorithm describe the energy balance of the dhw tank with a differential equation.

    :param y: storage sensible temperature in K.
    :param t: time steps.
    :param ql: storage tank sensible heat loss in Wh.
    :param qd: heat discharged from the tank in Wh.
    :param qc: heat charged into the tank in Wh.
    :param Vtank: DHW tank size in [m3]
    :type y: float
    :type t: float
    :type ql: float
    :type qd: float
    :type qc: float
    :type Vtank: float

    :return dydt: change in temperature at each time step.
    :type dydt: float
    """
    dydt = (qc - ql - qd) / (Pwater * Vtank * Cpw)
    return dydt


def calc_tank_temperature(T_start_C, q_loss_W, q_discharged_W, q_charged_W, V_tank_m3):
    """
    This algorithm solves the differential equation, ode.

    :param T_start_C: initial tank temperature in [C]
    :param q_loss_W: storage tank sensible heat loss in Wh.
    :param q_discharged_W: heat discharged from the tank in Wh.
    :param q_charged_W: heat charged into the tank in Wh.
    :param V_tank_m3: DHW tank size in [m3]
    :param gv: globalvar.py

    :type T_start_C: float
    :type q_loss_W: float
    :type q_discharged_W: float
    :type q_charged_W: float
    :type V_tank_m3: float

    :returns y[1]: solution of the ode
    :rtype y[1]: float
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
