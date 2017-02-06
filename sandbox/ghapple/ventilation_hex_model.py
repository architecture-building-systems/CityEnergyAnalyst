# coding=utf-8
"""
=========================================
air Heat exchanger unit
=========================================
"""
def calc_hex(rel_humidity_ext, gv, temp_ext, temp_zone_prev, timestep):
    """
    Calculates air properties of mechanical ventilation system with heat exchanger
    Modeled after 2.4.2 in SIA 2044

    rel_humidity_ext : (%)
    gv : globalvar
    qv_mech : required air volume flow (kg/s)
    temp_ext : external temperature at time t (°C)
    temp_zone_prev : ventilation zone air temperature at time t-1 (°C)

    t2, w2 : temperature and moisture content of inlet air after heat exchanger
    """
    # TODO add literature

    # FIXME: dynamic HEX efficiency
    # Properties of heat recovery and required air incl. Leakage
    # qv_mech = qv_mech * 1.0184  # in m3/s corrected taking into account leakage # TODO: add source
    # Veff = gv.Vmax * qv_mech / qv_mech_dim  # Eq. (85) in SIA 2044
    # nrec = gv.nrec_N - gv.C1 * (Veff - 2)  # heat exchanger coefficient # TODO: add source
    nrec = gv.nrec_N  # for now use constant efficiency for heat recovery

    # State No. 1
    w1 = calc_w(temp_ext, rel_humidity_ext)  # outdoor moisture (kg/kg)

    # State No. 2
    # inlet air temperature after HEX calculated from zone air temperature at time step t-1 (°C)
    t2 = temp_ext + nrec * (temp_zone_prev - temp_ext)
    w2 = min(w1, calc_w(t2, 100))  # inlet air moisture (kg/kg), Eq. (4.24) in [1]

    # TODO: document
    # bypass heat exchanger if use is not beneficial
    if temp_zone_prev > temp_ext and not gv.is_heating_season(timestep):
        t2 = temp_ext
        w2 = w1
        # print('bypass HEX cooling')
    elif temp_zone_prev < temp_ext and gv.is_heating_season(timestep):
        t2 = temp_ext
        w2 = w1
        # print('bypass HEX heating')

    return t2, w2
