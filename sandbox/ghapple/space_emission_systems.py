# -*- coding: utf-8 -*-
"""

Space emission systems (heating and cooling)
EN 15316-2
prEN 15316-2:2014

"""


from __future__ import division
import numpy as np
from sandbox.ghapple import helpers as h

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def calc_q_em_ls(q_em_out, delta_theta_int_inc, theta_int_inc, theta_e_comb):

    """
    Eq. (8) in [prEN 15316-2:2014]

    :param q_em_out: heating power of emission system (W)
    :param delta_theta_int_inc: delta temperature caused by all losses (K)
    :param theta_int_inc: equivalent room temperature (°C)
    :param theta_e_comb: ?comb? outdoor temperature (°C)
    :return:
    """

    q_em_ls = q_em_out * (delta_theta_int_inc / (theta_int_inc-theta_e_comb))

    return q_em_ls



