# -*- coding: utf-8 -*-
"""
Electrical loads
"""
from __future__ import division
import numpy as np
from cea.utilities import physics
from cea.technologies import heatpumps
from cea.demand import control_heating_cooling_systems, constants

__author__ = "Jimeno A. Fonseca, Gabriel Happle"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# import constants
H_F = constants.H_F
P_WATER = constants.P_WATER
C_P_W = constants.C_P_W
P_FAN = constants.P_FAN
F_SR = constants.F_SR
DELTA_P_1 = constants.DELTA_P_1
EFFI = constants.EFFI
HOURS_OP = constants.HOURS_OP
GR = constants.GR


def calc_Eint(tsd, bpr, schedules):
    """
    Calculate final internal electrical loads (without auxiliary loads)

    :param tsd: Timestep data
    :type tsd: Dict[str, numpy.ndarray]

    :param bpr: building properties
    :type bpr: cea.demand.thermal_loads.BuildingPropertiesRow

    :param schedules: The list of schedules defined for the project - in the same order as `list_uses`
    :type schedules: List[numpy.ndarray]

    :returns: `tsd` with new keys: `['Eaf', 'Elf', 'Ealf', 'Edataf', 'Eref', 'Eprof']`
    :rtype: Dict[str, numpy.ndarray]
    """

    # calculate final electrical consumption due to appliances and lights in W
    tsd['Eaf'] = schedules['Ea'] * bpr.internal_loads['Ea_Wm2']
    tsd['Elf'] = schedules['El'] * bpr.internal_loads['El_Wm2']
    tsd['Ealf'] = tsd['Elf'] + tsd['Eaf']

    # calculate other electrical loads in W
    if 'COOLROOM' in bpr.occupancy:
        tsd['Eref'] = schedules['Ere'] * bpr.internal_loads['Ere_Wm2'] * bpr.occupancy['COOLROOM']
    else:
        tsd['Eref'] = np.zeros(8760)

    if 'SERVERROOM' in bpr.occupancy:
        tsd['Edataf'] = schedules['Ed'] * bpr.internal_loads['Ed_Wm2'] * bpr.occupancy['SERVERROOM']
    else:
        tsd['Edataf'] = np.zeros(8760)

    if 'INDUSTRIAL' in bpr.occupancy:
        tsd['Eprof'] = schedules['Epro'] * bpr.internal_loads['Epro_Wm2'] * bpr.occupancy['INDUSTRIAL']
        tsd['Ecaf'] = np.zeros(8760) # not used in the current version but in the optimization part
    else:
        tsd['Eprof'] = np.zeros(8760)
        tsd['Ecaf'] = np.zeros(8760) # not used in the current version but in the optimization part

    return tsd


def calc_Eauxf(tsd, bpr, Qwwf_0, Vw):
    """
    Auxiliary electric loads
    from Legacy

    :param tsd: Time series data of building
    :type tsd: dict
    :param bpr: Building Properties Row object
    :type bpr: cea.demand.thermal_loads.BuildingPropertiesRow
    :param Qwwf_0:
    :param Vw:
    :param gv:
    :return:
    """
    # TODO: documentation

    Ll = bpr.geometry['Blength']
    Lw = bpr.geometry['Bwidth']
    Mww = tsd['mww']
    Qcsf = tsd['Qcsf']
    Qhsf = tsd['Qhsf']
    Qww = tsd['Qww']
    Qwwf = tsd['Qwwf']
    Tcs_re_ahu = tsd['Tcsf_re_ahu']
    Tcs_sup_ahu = tsd['Tcsf_sup_ahu']
    Tcs_re_aru = tsd['Tcsf_re_aru']
    Tcs_sup_aru = tsd['Tcsf_sup_aru']
    Tcs_re_scu = tsd['Tcsf_re_scu']
    Tcs_sup_scu = tsd['Tcsf_sup_scu']
    Ths_re_ahu = tsd['Thsf_re_ahu']
    Ths_sup_ahu = tsd['Thsf_sup_ahu']
    Ths_re_aru = tsd['Thsf_re_aru']
    Ths_sup_aru = tsd['Thsf_sup_aru']
    Ths_re_shu = tsd['Thsf_re_shu']
    Ths_sup_shu = tsd['Thsf_sup_shu']

    Year = bpr.age['built']
    fforma = bpr.building_systems['fforma']
    nf_ag = bpr.geometry['floors_ag']
    Ehs_lat_aux = tsd['Ehs_lat_aux']

    # split up the final demands according to the fraction of energy
    frac_heat_ahu = [ahu / sys if sys > 0 else 0 for ahu, sys in zip(tsd['Qhs_sen_ahu'], tsd['Qhs_sen_sys'])]
    Qhsf_ahu = Qhsf * frac_heat_ahu
    Qhsf_0_ahu = np.nanmax(Qhsf_ahu)
    frac_heat_aru = [aru / sys if sys > 0 else 0 for aru, sys in zip(tsd['Qhs_sen_aru'], tsd['Qhs_sen_sys'])]
    Qhsf_aru = Qhsf * frac_heat_aru
    Qhsf_0_aru = np.nanmax(Qhsf_aru)
    frac_heat_shu = [shu / sys if sys > 0 else 0 for shu, sys in zip(tsd['Qhs_sen_shu'], tsd['Qhs_sen_sys'])]
    Qhsf_shu = Qhsf * frac_heat_shu
    Qhsf_0_shu = np.nanmax(Qhsf_shu)
    frac_cool_ahu = [ahu / sys if sys < 0 else 0 for ahu, sys in zip(tsd['Qcs_sen_ahu'], tsd['Qcs_sen_sys'])]
    Qcsf_ahu = Qcsf * frac_cool_ahu
    Qcsf_0_ahu = np.nanmin(Qcsf_ahu)
    frac_cool_aru = [aru / sys if sys < 0 else 0 for aru, sys in zip(tsd['Qcs_sen_aru'], tsd['Qcs_sen_sys'])]
    Qcsf_aru = Qcsf * frac_cool_aru
    Qcsf_0_aru = np.nanmin(Qcsf_aru)
    frac_cool_scu = [scu / sys if sys < 0 else 0 for scu, sys in zip(tsd['Qcs_sen_scu'], tsd['Qcs_sen_sys'])]
    Qcsf_scu = Qcsf * frac_cool_scu
    Qcsf_0_scu = np.nanmin(Qcsf_scu)

    Eaux_cs = np.zeros(8760)
    Eaux_fw = np.zeros(8760)
    Eaux_hs = np.zeros(8760)
    Imax = 2 * (Ll + Lw / 2 + H_F + (nf_ag) + 10) * fforma
    deltaP_des = Imax * DELTA_P_1 * (1 + F_SR)
    if Year >= 2000:
        b = 1
    else:
        b = 1.2
    Eaux_ww = np.vectorize(calc_Eauxf_ww)(Qww, Qwwf, Qwwf_0, deltaP_des, b, Mww)

    if control_heating_cooling_systems.has_heating_system(bpr):

        # for all subsystems
        Eaux_hs_ahu = np.vectorize(calc_Eauxf_hs_dis)(Qhsf_ahu, Qhsf_0_ahu, deltaP_des, b, Ths_sup_ahu, Ths_re_ahu)
        Eaux_hs_aru = np.vectorize(calc_Eauxf_hs_dis)(Qhsf_aru, Qhsf_0_aru, deltaP_des, b, Ths_sup_aru, Ths_re_aru)
        Eaux_hs_shu = np.vectorize(calc_Eauxf_hs_dis)(Qhsf_shu, Qhsf_0_shu, deltaP_des, b, Ths_sup_shu, Ths_re_shu)
        Eaux_hs = Eaux_hs_ahu + Eaux_hs_aru + Eaux_hs_shu  # sum up

    if control_heating_cooling_systems.has_cooling_system(bpr):

        # for all subsystems
        Eaux_cs_ahu = np.vectorize(calc_Eauxf_cs_dis)(Qcsf_ahu, Qcsf_0_ahu, deltaP_des, b, Tcs_sup_ahu, Tcs_re_ahu)
        Eaux_cs_aru = np.vectorize(calc_Eauxf_cs_dis)(Qcsf_aru, Qcsf_0_aru, deltaP_des, b, Tcs_sup_aru, Tcs_re_aru)
        Eaux_cs_scu = np.vectorize(calc_Eauxf_cs_dis)(Qcsf_scu, Qcsf_0_scu, deltaP_des, b, Tcs_sup_scu, Tcs_re_scu)
        Eaux_cs = Eaux_cs_ahu + Eaux_cs_aru + Eaux_cs_scu  # sum up

    if nf_ag > 5:  # up to 5th floor no pumping needs
        Eaux_fw = calc_Eauxf_fw(Vw, nf_ag)

    Eaux_ve = calc_Eauxf_ve(tsd)
    Eaux_ve = np.nan_to_num(Eaux_ve)

    Eauxf = Eaux_hs + Eaux_cs + Eaux_ve + Eaux_ww + Eaux_fw + Ehs_lat_aux

    return Eauxf, Eaux_hs, Eaux_cs, Eaux_ve, Eaux_ww, Eaux_fw


def calc_Eauxf_hs_dis(Qhsf, Qhsf0, deltaP_des, b, ts, tr):
    # TODO: documentation of legacy

    # the power of the pump in Watts
    if Qhsf > 0 and (ts - tr) != 0:
        fctr = 1.05
        qV_des = Qhsf / ((ts - tr) * C_P_W * 1000)
        Phy_des = 0.2278 * deltaP_des * qV_des

        if Qhsf / Qhsf0 > 0.67:
            Ppu_dis_hy_i = Phy_des
            feff = (1.25 * (200 / Ppu_dis_hy_i) ** 0.5) * fctr * b
            Eaux_hs = Ppu_dis_hy_i * feff
        else:
            Ppu_dis_hy_i = 0.0367 * Phy_des
            feff = (1.25 * (200 / Ppu_dis_hy_i) ** 0.5) * fctr * b
            Eaux_hs = Ppu_dis_hy_i * feff
    else:
        Eaux_hs = 0.0
    return Eaux_hs  # in #W


def calc_Eauxf_cs_dis(Qcsf, Qcsf0, deltaP_des, b, ts, tr):
    # TODO: documentation of legacy

    # refrigerant R-22 1200 kg/m3
    # for Cooling system
    # the power of the pump in Watts
    if Qcsf < 0 and (ts - tr) != 0:
        fctr = 1.10
        qV_des = Qcsf / ((ts - tr) * C_P_W * 1000)  # kg/s
        Phy_des = 0.2778 * deltaP_des * qV_des

        # the power of the pump in Watts
        if Qcsf < 0:
            if Qcsf / Qcsf0 > 0.67:
                Ppu_dis_hy_i = Phy_des
                feff = (1.25 * (200 / Ppu_dis_hy_i) ** 0.5) * fctr * b
                Eaux_cs = Ppu_dis_hy_i * feff
            else:
                Ppu_dis_hy_i = 0.0367 * Phy_des
                feff = (1.25 * (200 / Ppu_dis_hy_i) ** 0.5) * fctr * b
                Eaux_cs = Ppu_dis_hy_i * feff
    else:
        Eaux_cs = 0.0
    return Eaux_cs  # in #W


def calc_Eauxf_ve(tsd):
    """
    calculation of auxiliary electricity consumption of mechanical ventilation and AC fans
    
    :param tsd: Time series data of building
    :type tsd: dict
    :return: electrical energy for fans of mechanical ventilation in [Wh/h]
    :rtype: float
    """

    # TODO: DOCUMENTATION
    # FIXME: Why only energy demand for AC? Also other mechanical ventilation should have auxiliary energy demand
    # FIXME: What are the units

    # m_ve_mech is

    fan_power = P_FAN  # specific fan consumption in W/m3/h, see globalvar.py

    # mechanical ventilation system air flow [m3/s] = outdoor air + recirculation air
    q_ve_mech = tsd['m_ve_mech']/physics.calc_rho_air(tsd['theta_ve_mech']) \
        + tsd['m_ve_rec']/physics.calc_rho_air(tsd['T_int'])

    Eve_aux = fan_power * q_ve_mech * 3600

    return Eve_aux


def calc_Eauxf_ww(Qww, Qwwf, Qwwf0, deltaP_des, b, qV_des):
    """

    :param Qww:
    :param Qwwf:
    :param Qwwf0:
    :param Imax:
    :param deltaP_des:
    :param b:
    :param qV_des:
    :return:
    """
    # TODO: documentation

    if Qww > 0:
        # for domestichotwater
        # the power of the pump in Watts
        Phy_des = 0.2778 * deltaP_des * qV_des
        # the power of the pump in Watts

        if Qwwf / Qwwf0 > 0.67:
            Ppu_dis_hy_i = Phy_des
            feff = (1.25 * (200 / Ppu_dis_hy_i) ** 0.5) * b
            Eaux_ww = Ppu_dis_hy_i * feff
        else:
            Ppu_dis_hy_i = 0.0367 * Phy_des
            feff = (1.25 * (200 / Ppu_dis_hy_i) ** 0.5) * b
            Eaux_ww = Ppu_dis_hy_i * feff
    else:
        Eaux_ww = 0.0
    return Eaux_ww  # in #W


def calc_Eauxf_fw(freshw, nf):
    """

    :param freshw:
    :param nf:
    :return:
    """
    # TODO: documentation

    Eaux_fw = np.zeros(8760)
    # for domestic freshwater
    # the power of the pump in Watts assuming the best performance of the pump of 0.6 and an accumulation tank
    for day in range(1, 366):
        balance = 0
        t0 = (day - 1) * 24
        t24 = day * 24
        for hour in range(t0, t24):
            balance = balance + freshw[hour]
        if balance > 0:
            flowday = balance / (3600)  # in m3/s
            Energy_hourWh = (H_F * (nf - 5)) / 0.6 * P_WATER * GR * (flowday / HOURS_OP) / EFFI
            for t in range(1, HOURS_OP + 1):
                time = t0 + 11 + t
                Eaux_fw[time] = Energy_hourWh
    return Eaux_fw


def calc_heatpump_cooling_electricity(bpr, tsd, gv):
    """
    calculates electricity demand due to heatpumps/cooling units in the building for different cooling supply systems.

    :param bpr: Building Properties Row object
    :type bpr: cea.demand.thermal_loads.BuildingPropertiesRow
    :param tsd: Time series data of building
    :type tsd: dict
    :param gv: global variables
    :type gv: cea.globalvar.GlobalVariables
    :return: (updates tsd)
    """
    # if cooling supply system is hp air-air (T2) or hp water-water (T3)
    if bpr.supply['type_cs'] in {'T2', 'T3'}:
        if bpr.supply['type_cs'] == 'T2':
            t_source = (tsd['T_ext'] + 273)
        if bpr.supply['type_cs'] == 'T3':
            t_source = (tsd['T_ext_wetbulb'] + 273)

        # heat pump energy for the 3 components
        # ahu
        e_gen_f_cs_ahu = np.vectorize(heatpumps.HP_air_air)(tsd['mcpcsf_ahu'], (tsd['Tcsf_sup_ahu'] + 273),
                                                             (tsd['Tcsf_re_ahu'] + 273), t_source, gv)
        # aru
        e_gen_f_cs_aru = np.vectorize(heatpumps.HP_air_air)(tsd['mcpcsf_aru'], (tsd['Tcsf_sup_aru'] + 273),
                                                             (tsd['Tcsf_re_aru'] + 273), t_source, gv)
        # scu
        e_gen_f_cs_scu = np.vectorize(heatpumps.HP_air_air)(tsd['mcpcsf_scu'], (tsd['Tcsf_sup_scu'] + 273),
                                                             (tsd['Tcsf_re_scu'] + 273), t_source, gv)
        # sum
        tsd['Egenf_cs'] = e_gen_f_cs_ahu + e_gen_f_cs_aru + e_gen_f_cs_scu

    # if cooling supply from district network (T4, T5) or no supply (T0)
    elif bpr.supply['type_cs'] in {'T4', 'T5', 'T0'}:
        tsd['Egenf_cs'] = np.zeros(8760)

    # if cooling supply from ground source heat pump
    elif bpr.supply['type_cs'] in {'T1'}:
        tsd['Egenf_cs'] = np.zeros(8760)
        print('Warning: Soil-water HP currently not available.')

    # if unknown cooling supply
    else:
        tsd['Egenf_cs'] = np.zeros(8760)
        print('Error: Unknown Cooling system')

    return
