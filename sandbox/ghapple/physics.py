import control



def calc_theta_m_t(theta_m_prev, c_m, h_tr_3, h_tr_em, phi_m_tot):

    # (C.4) in [C.3 ISO 13790]

    theta_m_t = (theta_m_prev((c_m/3600)-0.5*(h_tr_3+h_tr_em))) + phi_m_tot / ((c_m/3600)+0.5*(h_tr_3+h_tr_em))

    return theta_m_t


def calc_phi_m_tot(phi_m, h_tr_em, theta_e, h_tr_3, phi_st, h_tr_w, h_tr_1, phi_ia, phi_hc_nd, h_ve_adj, h_tr_2 ):

    # (C.5) in [C.3 ISO 13790]
    # h_ve = h_ve_adj and theta_sup = theta_e [9.3.2 ISO 13790]

    phi_m_tot = phi_m + h_tr_em*theta_e + \
                h_tr_3*(phi_st + h_tr_w*theta_e+h_tr_1*(((phi_ia+phi_hc_nd)/h_ve_adj)+theta_e))/h_tr_2


    return phi_m_tot


def calc_h_tr_1(h_ve_adj, h_tr_is):

    # (C.6) in [C.3 ISO 13790]

    h_tr_1 = 1/(1/h_ve_adj + 1/h_tr_is)

    return h_tr_1


def calc_h_tr_2(h_tr_1, h_tr_w):

    # (C.7) in [C.3 ISO 13790]

    h_tr_2 = h_tr_1 + h_tr_w

    return h_tr_2


def calc_h_tr_3(h_tr_2, h_tr_ms):

    # (C.8) in [C.3 ISO 13790]

    h_tr_3 = 1/(1/h_tr_2 + 1/h_tr_ms)

    return h_tr_3


def calc_theta_m(theta_m_t, theta_m_prev):

    # (C.9) in [C.3 ISO 13790]
    theta_m = (theta_m_t+theta_m_prev)/2

    return theta_m


def calc_theta_s(h_tr_ms, theta_m, phi_st, h_tr_w, theta_e, h_tr_1, phi_ia, phi_hc_nd, h_ve_adj):

    # (C.10) in [C.3 ISO 13790]
    # h_ve = h_ve_adj and theta_sup = theta_e [9.3.2 ISO 13790]
    theta_s = (h_tr_ms*theta_m+phi_st+h_tr_w*theta_e+h_tr_1*(theta_e+(phi_ia+phi_hc_nd)/h_ve_adj)) / \
              (h_tr_ms+h_tr_w+h_tr_1)

    return theta_s


def calc_theta_air(h_tr_is, theta_s, h_ve_adj, theta_e, phi_ia, phi_hc_nd):
    # (C.11) in [C.3 ISO 13790]
    # h_ve = h_ve_adj and theta_sup = theta_e [9.3.2 ISO 13790]

    theta_air = (h_tr_is * theta_s + h_ve_adj * theta_e + phi_ia + phi_hc_nd) / (h_tr_is + h_ve_adj)

    return theta_air

def calc_theta_op(theta_air, theta_s):

    # (C.12) in [C.3 ISO 13790]
    theta_op = 0.3 * theta_air + 0.7 * theta_s

    return theta_op


def calc_temperatures_crank_nicholson( phi_hc_nd, building_thermal_prop ):

    # calculates air temperature and operative temperature for a given heating/cooling load
    # section C.3 in [C.3 ISO 13790]

    # TODO: get properties
    phi_m = None
    h_tr_em = None
    theta_e = None
    h_tr_3 = None
    phi_st = None
    h_tr_w = None
    h_tr_1 = None
    phi_ia = None
    h_ve_adj = None
    h_tr_2 = None
    theta_m_prev = None
    c_m = None
    h_tr_ms = None
    h_tr_is = None


    phi_m_tot = calc_phi_m_tot(phi_m, h_tr_em, theta_e, h_tr_3, phi_st, h_tr_w, h_tr_1, phi_ia, phi_hc_nd, h_ve_adj,
                               h_tr_2)

    theta_m_t = calc_theta_m_t(theta_m_prev, c_m, h_tr_3, h_tr_em, phi_m_tot)

    theta_m = calc_theta_m(theta_m_t, theta_m_prev)

    theta_s = calc_theta_s(h_tr_ms, theta_m, phi_st, h_tr_w, theta_e, h_tr_1, phi_ia, phi_hc_nd, h_ve_adj)

    theta_air = calc_theta_air(h_tr_is, theta_s, h_ve_adj, theta_e, phi_ia, phi_hc_nd)

    theta_op = calc_theta_op(theta_air, theta_s)

    return theta_m_t, theta_air, theta_op




def has_heating_demand(building_thermal_prop, setpoints):

    # TODO get setpoints
    theta_int_h_set = None

    # step 1 in section C.4.2 in [C.3 ISO 13790]

    # set heating cooling power to zero
    phi_hc_nd = 0

    # only air temperature is used for the check
    theta_air = calc_temperatures_crank_nicholson(phi_hc_nd, building_thermal_prop)[1]

    if theta_int_h_set <= theta_air:
        return False

    elif theta_air < theta_int_h_set:
        return True


def has_cooling_demand(building_thermal_prop, setpoints):

    # TODO get setpoints
    theta_int_c_set = None

    # step 1 in section C.4.2 in [C.3 ISO 13790]

    # set heating cooling power to zero
    phi_hc_nd = 0

    # only air temperature is used for the check
    theta_air = calc_temperatures_crank_nicholson(phi_hc_nd, building_thermal_prop)[1]

    if theta_int_c_set >= theta_air:
        return False

    elif theta_air > theta_int_c_set:
        return True


def procedure_1(hoy, bpr, building_thermal_prop, setpoints):

    # building thermal properties at previous time step
    # +++++++++++++++++++++++++++++++++++++++++++++++++
    theta_m_prev = None

    # environmental properties
    # ++++++++++++++++++++++++
    theta_e = None

    # air flows
    # +++++++++
    m_ve_mech = None
    m_ve_window = None
    m_ve_leakage = None

    # air supply temperatures (HEX)
    # +++++++++++++++++++++++++++++
    temp_ve_mech = None

    # R-C-model properties
    # ++++++++++++++++++++
    phi_m = None
    phi_ia = None
    phi_st = None

    c_m = None

    h_tr_em = None
    h_tr_w = None
    h_ve_adj = None
    h_tr_ms = None
    h_tr_is = None

    h_tr_1 = calc_h_tr_1(h_ve_adj, h_tr_is)
    h_tr_2 = calc_h_tr_2(h_tr_1, h_tr_w)
    h_tr_3 = calc_h_tr_3(h_tr_2, h_tr_ms)

    # check demand
    # ++++++++++++
    if not has_heating_demand(building_thermal_prop, setpoints) and not has_cooling_demand(building_thermal_prop, setpoints):

        # no heating or cooling demand
        # calculate temperatures of building R-C-model and exit
        # --> rc_model_function_1(...)

    elif has_heating_demand (building_thermal_prop, setpoints):

        # has heating demand
        # check if heating system is turned on

        if not control.is_heating_active(hoy, bpr):

            # no heating
            # calculate temperatures of building R-C-model and exit
            # --> rc_model_function_1(...)

        elif control.is_heating_active(hoy, bpr) and control.heating_system_is_ac(bpr):

            # heating with AC
            # calculate loads and enter AC calculation
            # --> r_c_model_function_3(...)
            # --> kaempf_ac(...)
            # --> (iteration of air flows)

        elif control.is_heating_active(hoy, bpr) and control.heating_system_is_radiative(bpr):

            # heating with radiative system
            # calculate loads and emission losses
            # --> rc_model_function_2(...)

    elif has_cooling_demand(building_thermal_prop, setpoints):

        # has cooling demand
        # check if cooling system is turned on

        if not control.is_cooling_active(hoy, bpr):

            # no cooling
            # calculate temperatures of R-C-model and exit
            # --> rc_model_function_1(...)

        elif control.is_cooling_active(hoy, bpr) and control.cooling_system_is_ac(bpr):

            # cooling with AC
            # calculate load and enter AC calculation
            # --> r_c_model_function_3(...)
            # --> kaempf_ac(...)
            # --> (iteration of air flows)

        elif control.is_cooling_active(hoy, bpr) and control.cooling_system_is_radiative(bpr):

            # cooling with radiative system
            # calculate loads and emission losses
            # --> rc_model_function_2(...)

    else:
        print('Error: Unknown HVAC system status')
        return

    return












# TODO: night flushing: 9.3.3.10 in ISO 13790