# -*- coding: utf-8 -*-
"""
=========================================
blinds
=========================================

"""
from __future__ import division

def calc_blinds_reflection(radiation, shading_type, g_gl):

    rf_sh = calc_blinds_reflectivity(shading_type)
    gl = calc_blinds_activation(radiation, g_gl, rf_sh)
    return gl

def calc_blinds_activation(radiation, g_gl, Rf_sh):
    # activate blinds when I =300 W/m2
    if radiation > 300:  # in w/m2
        return g_gl * Rf_sh
    else:
        return g_gl

def calc_blinds_reflectivity(shading_type):
    # 0 for not, 1 for Rollo, 2 for Venetian blinds, 3 for Solar control glass
    rf_sh = {'T0': 1, 'T1': 0.08, 'T2': 0.15, 'T3': 0.1}
    return rf_sh[shading_type]