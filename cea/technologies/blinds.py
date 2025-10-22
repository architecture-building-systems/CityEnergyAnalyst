# -*- coding: utf-8 -*-
"""
This module contains functions for calculating the effect of blinds on solar gains through windows.
It is part of a larger workflow for insolation of windows that is found in building_solar.calc_Isol_daysim

Authors: Justin McCarty, Jimeno Fonseca
Last Update: 8 October 2025, Justin McCarty
"""





def calc_blinds_activation(radiation_wm2, g_gl, Rf_sh, shading_location='interior', shading_setpoint_Wm2=300):
    """
    This function calculates the blind operation according to ISO 13790.

    :param radiation_wm2: radiation_wm2 in [W/m2]
    :param g_gl: window g value
    :param Rf_sh: shading factor
    :param shading_location: location of shading device ('interior' or 'exterior' only) (optional, default: 'interior')
    :param shading_setpoint_Wm2: radiation_wm2 setpoint for shading in [W/m2] (optional, default: 300 W/m2)

    :return: g_gl if no shading, g_gl*Rf_sh if shading is active
    """

    if shading_location == 'interior':
        return loss_for_interior_shading(radiation_wm2, g_gl, Rf_sh, shading_setpoint_wm2)
    elif shading_location == 'exterior':
        # shading losses calculated before radiation_wm2 enters the window so only loss after that is the g factor
        # loss is calculated outside of this function
        return g_gl
    else:
        print(f"Warning: Unrecognized shading location '{shading_location}'. Assuming 'interior'.")
        return loss_for_interior_shading(radiation_wm2, g_gl, Rf_sh, shading_setpoint_Wm2)
    
    
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