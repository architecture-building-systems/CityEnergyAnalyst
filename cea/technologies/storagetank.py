"""
Sensible Heat Storage - Fully Mixed tank
"""

from __future__ import division
import numpy as np
from scipy.integrate import odeint
import math

__author__ = "Shanshan Hsieh"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["ShanShan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def calc_Qww_ls_st(ta, te, Tww_st, V, Qww, Qww_ls_r, Qww_ls_nr, gv):
    """
    This algorithm calculates the heat flows within a fully mixed water storage tank.
    Heat flows include sensible heat loss to the environment (ql), heat charged into the tank (qc),
    and heat discharged from the tank (qd).

    :param Tww_st: tank temperature in [C]
    :param Tww_setpoint: DHW temperature set point in [C]
    :param ta: room temperature in [C]
    :param te: ambient temperature in [C]
    :param V: DHW tank size in [m3]
    :param Qww: DHW demand in [Wh]
    :param Qww_ls_r: recoverable loss in distribution in [Wh]
    :param Qww_ls_nr: non-recoverable loss in distribution in [Wh]
    :param gv: globalvar.py

    :type Tww_st: float
    :type Tww_setpoint: float
    :type ta: float
    :type te: float
    :type V: float
    :type Qww: float
    :type Qww_ls_nr: float


    :return ql: storage sensible heat loss in [Wh].
    :return qd: heat discharged from the tank in [Wh], including dhw heating demand and distribution heat loss.
    :return qc: heat charged into the tank in [Wh].
    :rtype ql: float
    :rtype qd: float
    :rtype qc: float
    """

    tamb = ta - gv.Bf * (ta - te)         # Calculate tamb in basement according to EN
    if V > 0:
        h = ( 4 * V * gv.AR ** 2 / math.pi ) ** ( 1.0 / 3.0 )     # tank height in [m], derived from tank Aspect Ratio(AR)
        r = ( V / ( math.pi * h ) ) ** ( 1.0 / 2.0 )         # tank radius in [m], assuming tank shape is cylinder
        Atank = 2 * math.pi * r ** 2 + 2 * math.pi * r * h      # tank surface area in [m2].
    else:
        Atank = 0
    ql = gv.U_dhwtank * Atank * ( Tww_st - tamb )       # tank heat loss to the room in [Wh]
    qd = Qww + Qww_ls_r + Qww_ls_nr
    if Qww <= 0:
        qc = 0
    else:
        qc = qd + ql + gv.Pwater * V * gv.Cpw * ( gv.Tww_setpoint - Tww_st ) / 3.6

    return ql, qd, qc


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

def solve_ode_storage(Tww_st_0, ql, qd, qc, Vtank, gv):
    """
    This algorithm solves the differential equation, ode.

    :param Tww_st_0: initial tank temperature in [C]
    :param ql: storage tank sensible heat loss in Wh.
    :param qd: heat discharged from the tank in Wh.
    :param qc: heat charged into the tank in Wh.
    :param Vtank: DHW tank size in [m3]
    :param gv: globalvar.py

    :type Tww_st_0: float
    :type ql: float
    :type qd: float
    :type qc: float
    :type Vtank: float

    :returns y[1]: solution of the ode
    :rtype y[1]: float
    """
    t = np.linspace(0,1,2)
    y = odeint(ode, Tww_st_0, t, args = (ql, qd, qc, gv.Pwater, gv.Cpw, Vtank))

    return y[1]


# use the optimized (numba_cc) versions of the ode function in this module if available
try:
    # import Numba AOT versions of the functions above, overwriting them
    from storagetank_cc import (ode)
except ImportError:
    # fall back to using the python version
    # print('failed to import from storagetank_cc.pyd, falling back to pure python functions')
    pass