# -*- coding: utf-8 -*-
"""
Electrical loads
"""
from __future__ import division
import numpy as np
from cea.utilities import physics
from cea.technologies import heatpumps

__author__ = "Jimeno A. Fonseca, Gabriel Happle"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_Eint(tsd, bpr, schedules):
    """
    Calculate final internal electrical loads (without auxiliary loads)

    :param tsd: Timestep data
    :type tsd: Dict[str, numpy.ndarray]

    :param bpr: building properties
    :type bpr: cea.demand.thermal_loads.BuildingPropertiesRow

    :param list_uses: The list of uses used in the project
    :type list_uses: list

    :param schedules: The list of schedules defined for the project - in the same order as `list_uses`
    :type schedules: List[numpy.ndarray]

    :param building_uses: for each use in `list_uses`, the percentage of that use for this building.
        Sum of values is 1.0
    :type building_uses: Dict[str, numpy.ndarray]

    :param internal_loads: list of internal loads defined in the archetypes for each occupancy type
    :type internal_loads: Dict[str, list[float]]

    :returns: `tsd` with new keys: `['Eaf', 'Elf', 'Ealf', 'Edataf', 'Eref', 'Eprof']`
    :rtype: Dict[str, numpy.ndarray]
    """

    # calculate final electrical consumption due to appliances and lights in W
    tsd['Eaf'] = schedules['Ea'] * bpr.internal_loads['Ea_Wm2'] * bpr.rc_model['Aef']
    tsd['Elf'] = schedules['El'] * bpr.internal_loads['El_Wm2'] * bpr.rc_model['Aef']
    tsd['Ealf'] = tsd['Elf'] + tsd['Eaf']

    # calculate other electrical loads in W
    if 'COOLROOM' in bpr.occupancy:
        tsd['Eref'] = schedules['Ere'] * bpr.internal_loads['Ere_Wm2'] * bpr.rc_model['Aef']* bpr.occupancy['COOLROOM']
    else:
        tsd['Eref'] = np.zeros(8760)

    if 'SERVERROOM' in bpr.occupancy:
        tsd['Edataf'] = schedules['Ed'] * bpr.internal_loads['Ed_Wm2'] * bpr.rc_model['Aef']* bpr.occupancy['SERVERROOM']
    else:
        tsd['Edataf'] = np.zeros(8760)

    if 'INDUSTRIAL' in bpr.occupancy:
        tsd['Eprof'] = schedules['Epro'] * bpr.internal_loads['Epro_Wm2'] * bpr.rc_model['Aef']* bpr.occupancy['INDUSTRIAL']
        tsd['Ecaf'] = np.zeros(8760) # not used in the current version but in the optimization part
    else:
        tsd['Eprof'] = np.zeros(8760)
        tsd['Ecaf'] = np.zeros(8760) # not used in the current version but in the optimization part

    return tsd

def calc_Eauxf(Ll, Lw, Mww, Qcsf, Qcsf_0, Qhsf, Qhsf_0, Qww, Qwwf, Qwwf_0, Tcs_re, Tcs_sup,
               Ths_re, Ths_sup, Vw, Year, fforma, gv, nf_ag, sys_e_cooling,
               sys_e_heating, Ehs_lat_aux, tsd):
    Eaux_cs = np.zeros(8760)
    Eaux_ve = np.zeros(8760)
    Eaux_fw = np.zeros(8760)
    Eaux_hs = np.zeros(8760)
    Imax = 2 * (Ll + Lw / 2 + gv.hf + (nf_ag) + 10) * fforma
    deltaP_des = Imax * gv.deltaP_l * (1 + gv.fsr)
    if Year >= 2000:
        b = 1
    else:
        b = 1.2
    Eaux_ww = np.vectorize(calc_Eauxf_ww)(Qww, Qwwf, Qwwf_0, Imax, deltaP_des, b, Mww)
    if sys_e_heating != "T0":
        Eaux_hs = np.vectorize(calc_Eauxf_hs_dis)(Qhsf, Qhsf_0, Imax, deltaP_des, b, Ths_sup, Ths_re, gv.Cpw)
    if sys_e_cooling != "T0":
        Eaux_cs = np.vectorize(calc_Eauxf_cs_dis)(Qcsf, Qcsf_0, Imax, deltaP_des, b, Tcs_sup, Tcs_re, gv.Cpw)
    if nf_ag > 5:  # up to 5th floor no pumping needs
        Eaux_fw = calc_Eauxf_fw(Vw, nf_ag, gv)

    Eaux_ve = np.vectorize(calc_Eauxf_ve)(tsd, gv)

    Eauxf = Eaux_hs + Eaux_cs + Eaux_ve + Eaux_ww + Eaux_fw + Ehs_lat_aux

    return Eauxf, Eaux_hs, Eaux_cs, Eaux_ve, Eaux_ww, Eaux_fw


def calc_Eauxf_hs_dis(Qhsf, Qhsf0, Imax, deltaP_des, b, ts, tr, cpw):
    # the power of the pump in Watts
    if Qhsf > 0 and (ts - tr) != 0:
        fctr = 1.05
        qV_des = Qhsf / ((ts - tr) * cpw * 1000)
        Phy_des = 0.2278 * deltaP_des * qV_des
        feff = (1.25 * (200 / Phy_des) ** 0.5) * fctr * b
        # Ppu_dis = Phy_des*feff
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


def calc_Eauxf_cs_dis(Qcsf, Qcsf0, Imax, deltaP_des, b, ts, tr, cpw):
    # refrigerant R-22 1200 kg/m3
    # for Cooling system
    # the power of the pump in Watts
    if Qcsf < 0 and (ts - tr) != 0:
        fctr = 1.10
        qV_des = Qcsf / ((ts - tr) * cpw * 1000)  # kg/s
        Phy_des = 0.2778 * deltaP_des * qV_des
        feff = (1.25 * (200 / Phy_des) ** 0.5) * fctr * b
        # Ppu_dis = Phy_des*feff
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


def calc_Eauxf_ve(tsd, gv):
    """
    calculation of auxiliary electricity consumption of mechanical ventilation and AC fans
    
    :param tsd: Time series data of building
    :type tsd: dict
    :param gv: global variables
    :type gv: cea.globalvar.GlobalVariables
    :return: electrical energy for fans of mechanical ventilation in [Wh/h]
    :rtype: float
    """

    # TODO: DOCUMENTATION
    # FIXME: Why only energy demand for AC? Also other mechanical ventilation should have auxiliary energy demand
    # FIXME: What are the units

    # m_ve_mech is

    fan_power = gv.Pfan  # specific fan consumption in W/m3/h, see globalvar.py

    # mechanical ventilation system air flow [m3/s] = outdoor air + recirculation air
    q_ve_mech = tsd['m_ve_mech']/physics.calc_rho_air(tsd['theta_ve_mech']) \
        + tsd['m_ve_recirculation']/physics.calc_rho_air(tsd['T_int'])

    Eve_aux = fan_power * q_ve_mech * 3600

    return Eve_aux


def calc_Eauxf_ww(Qww, Qwwf, Qwwf0, Imax, deltaP_des, b, qV_des):
    if Qww > 0:
        # for domestichotwater
        # the power of the pump in Watts
        Phy_des = 0.2778 * deltaP_des * qV_des
        feff = (1.25 * (200 / Phy_des) ** 0.5) * b
        # Ppu_dis = Phy_des*feff
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


def calc_Eauxf_fw(freshw, nf, gv):
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
            Energy_hourWh = (gv.hf * (nf - 5)) / 0.6 * gv.Pwater * gv.gr * (flowday / gv.hoursop) / gv.effi
            for t in range(1, gv.hoursop + 1):
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
            tsource = (tsd['T_ext'] + 273)
        if bpr.supply['type_cs'] == 'T3':
            tsource = (tsd['T_ext_wetbulb'] + 273)
        tsd['Egenf_cs'] = np.vectorize(heatpumps.HP_air_air)(tsd['mcpcsf'], (tsd['Tcsf_sup'] + 273),
                                                             (tsd['Tcsf_re'] + 273), tsource, gv)

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