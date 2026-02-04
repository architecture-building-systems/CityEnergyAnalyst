# -*- coding: utf-8 -*-
"""
This module contains functions for calculating the effect of blinds on solar gains through windows.
It is part of a larger workflow for insolation of windows that is found in building_solar.calc_Isol_daysim

Authors: Justin McCarty, Jimeno Fonseca
Last Update: 8 October 2025, Justin McCarty
"""

from enum import StrEnum


class ShadingLocation(StrEnum):
    """Location of shading device relative to the window."""
    INTERIOR = "interior"
    EXTERIOR = "exterior"


def calc_blinds_activation(radiation_wm2, g_gl, Rf_sh, shading_location=ShadingLocation.INTERIOR, shading_setpoint_Wm2=300):
    """
    This function calculates the blind operation according to ISO 13790.

    :param radiation_wm2: radiation_wm2 in [W/m2]
    :param g_gl: window g value
    :param Rf_sh: shading factor
    :param shading_location: location of shading device (ShadingLocation.INTERIOR or ShadingLocation.EXTERIOR) (optional, default: ShadingLocation.INTERIOR)
    :param shading_setpoint_Wm2: radiation_wm2 setpoint for shading in [W/m2] (optional, default: 300 W/m2)

    :return: g_gl if no shading, g_gl*Rf_sh if shading is active
    """

    if shading_location == ShadingLocation.INTERIOR:
        return loss_for_interior_shading(radiation_wm2, g_gl, Rf_sh, shading_setpoint_Wm2)
    elif shading_location == ShadingLocation.EXTERIOR:
        # shading losses calculated before radiation_wm2 enters the window so only loss after that is the g factor
        # loss is calculated outside of this function
        return g_gl
    else:
        # Fallback for invalid values (should not happen with proper typing)
        raise ValueError(f"Invalid shading location: {shading_location}. Must be ShadingLocation.INTERIOR or ShadingLocation.EXTERIOR")
    
    
def loss_for_interior_shading(radiation_wm2, g_gl, Rf_sh, shading_setpoint_Wm2):
    """Calculate the loss for interior shading.

    Args:
        radiation_wm2 (float): The solar radiation incident on the window [W/m2].
        g_gl (float): The g-value of the window (glazing).
        Rf_sh (float): The shading factor.
        shading_setpoint_Wm2 (float): The shading setpoint [W/m2].

    Returns:
        float: The adjusted g-value considering shading.
    """
    if radiation_wm2 > shading_setpoint_Wm2:  # in w/m2
        return g_gl * Rf_sh
    else:
        return g_gl