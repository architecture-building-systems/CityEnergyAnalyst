# -*- coding: utf-8 -*-
"""
blinds
"""
from __future__ import division


def calc_blinds_activation(radiation, g_gl, Rf_sh):
    """
    This function calculates the blind operation according to ISO 13790.

    :param radiation: radiation in [W/m2]
    :param g_gl: window g value
    :param Rf_sh: shading factor
    """
    # activate blinds when I =300 W/m2
    if radiation > 300:  # in w/m2
        return g_gl * Rf_sh
    else:
        return g_gl
