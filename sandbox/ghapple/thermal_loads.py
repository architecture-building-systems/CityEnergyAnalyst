from __future__ import division
import cea.globalvar
import numpy
import cea.functions as functions
import hvac_kaempf



def calc_h_ve(q_m_mech, q_m_arg, q_m_lea, gv):

    """ Hve / Hea
    -- q_m_mech: air mass flow from mechanical ventilation (kg/s)
    -- q_m_arg: air mass flow from windows (kg/s)
    -- q_m_lea: air mass flow from leakages (kg/s)

    returns Hve in W/K"""

    c_p_air = gv.Cpa  # (kJ/(kg*K))

    return (q_m_mech + q_m_arg + q_m_lea)*c_p_air*1000  # (W/K)


def calc_temp_air_flow(q_m_mech, q_m_arg, q_m_lea, temp_ext, temp_sup_mech, h_ve, gv):

    c_p_air = gv.Cpa

    return ((q_m_mech*temp_sup_mech + (q_m_lea + q_m_arg)*temp_ext)*c_p_air*1000)/h_ve


def calc_heating_cooling_hvac_timestep(inputs):

    """this function is executed for the case of heating or cooling with a HVAC system
    by coupling the R-C model of ISO 13790 with the HVAC model of Kaempf
    """

    # first guess of mechanical ventilation mass flow rate and supply temperature for ventilation losses
    m_ve_mech = m_ve_req # required air mass flow rate
    h_ve = m_ve_mech # h
    temp_ve_sup = numpy.mean([temp_air_prev, temp_ext])

    h_tr_1, h_tr_2, h_tr_3 = functions.calc_Htr(h_ve, h_tr_is, h_tr_ms, h_tr_w )

    temp_m, temp_a, q_hs_sen, q_cs_sen, uncomfort, temp_op, i_m_tot \
        = functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set, temp_cs_set, h_tr_em,
                      h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st, h_ve, h_tr_w, i_ia, i_m, cm, area_f, Losses,
                      temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max, flag_season)

    q_ve_loss = m_ve_mech*gv.Cpa*(temp_a - temp_ve_sup)
    q_hs_sen_load_HVAC = q_hs_sen - q_ve_loss
    q_cs_sen_load_HVAC = q_cs_sen - q_ve_loss

    # iterative loop to determine air mass flows and supply temperatures of the hvac system
    while abs(m_ve_hvac - m_ve_mech) > tolerance

    hvac_kaempf.calc_HVAC()

    functions.calc_TL(system_heating, system_cooling, temp_m_prev, temp_ext, temp_hs_set, temp_cs_set, h_tr_em,
                      h_tr_ms, h_tr_is, h_tr_1, h_tr_2, h_tr_3, i_st, h_ve, h_tr_w, i_ia, i_m, cm, area_f, Losses,
                      temp_hs_set_corr, temp_cs_set_corr, i_c_max, i_h_max, flag_season)








# TESTING
if __name__ == '__main__':

    gv =  cea.globalvar.GlobalVariables()

    q_m_mech = 10
    q_m_arg = 0
    q_m_lea = 0

    temp_ext = 5
    temp_sup_mech = 15

    h_ve = calc_h_ve(q_m_mech, q_m_arg, q_m_lea, gv)

    print(h_ve)

    temp_air = calc_temp_air_flow(q_m_mech, q_m_arg, q_m_lea, temp_ext, temp_sup_mech, h_ve, gv)

    print(temp_air)