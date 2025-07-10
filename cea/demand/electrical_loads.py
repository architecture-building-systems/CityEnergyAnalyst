# -*- coding: utf-8 -*-
"""
Electrical loads
"""
from __future__ import annotations
from typing import TYPE_CHECKING

import numpy as np

from cea.constants import HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.constants import HOURS_IN_YEAR, P_WATER_KGPERM3
from cea.demand import control_heating_cooling_systems, constants
from cea.utilities import physics

if TYPE_CHECKING:
    from cea.demand.building_properties.building_properties_row import BuildingPropertiesRow

__author__ = "Jimeno A. Fonseca, Gabriel Happle"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# import constants
MIN_HEIGHT_THAT_REQUIRES_PUMPING = constants.MIN_HEIGHT_THAT_REQUIRES_PUMPING
P_WATER = P_WATER_KGPERM3
P_FAN = constants.P_FAN
F_SR = constants.F_SR
DELTA_P_1 = constants.DELTA_P_1
EFFI = constants.EFFI
HOURS_OP = constants.HOURS_OP
GR = constants.GR


def calc_Eal_Epro(tsd, schedules):
    """
    Calculate final internal electrical loads (without auxiliary loads)

    :param tsd: Time series data of building
    :type tsd: Dict[str, numpy.ndarray]

    :param schedules: The list of schedules defined for the project - in the same order as `list_uses`
    :type schedules: List[numpy.ndarray]

    :returns: `tsd` with new keys: `['Eaf', 'Elf', 'Ealf']`
    :rtype: Dict[str, numpy.ndarray]
    """

    # calculate final electrical consumption due to appliances and lights in W
    tsd['Ea'] = schedules['Ea_W']
    tsd['El'] = schedules['El_W']
    tsd['Ev'] = schedules['Ev_W']
    tsd['Eal'] = schedules['El_W'] + schedules['Ea_W']
    tsd['Epro'] = schedules['Epro_W']

    return tsd


def calc_E_sys(tsd):
    """
    Calculate the compound of end use electrical loads

    :param tsd: Time series data of building
    :type tsd: Dict[str, numpy.ndarray]

    """
    tsd['E_sys'] = np.nansum([tsd['Eve'], tsd['Ea'], tsd['El'], tsd['Edata'], tsd['Epro'],tsd['Eaux'],tsd['Ev']],0)
    # assuming a small loss
    return tsd


def calc_Ef(bpr: BuildingPropertiesRow, tsd):
    """
    Calculate the compound of final electricity loads
    with contain the end-use demand,

    :param tsd: Time series data of building
    :type tsd: Dict[str, numpy.ndarray]

    :param bpr: building properties
    :type bpr: cea.demand.building_properties.BuildingProperties

    """
    # GET SYSTEMS EFFICIENCIES
    energy_source = bpr.supply['source_el']
    scale_technology = bpr.supply['scale_el']
    total_el_demand = np.nansum([tsd['Eve'],tsd['Ea'],tsd['El'],tsd['Edata'],tsd['Epro'],tsd['Eaux'],tsd['Ev'],
                                    tsd['E_ww'], tsd['E_cs'],tsd['E_hs'], tsd['E_cdata'], tsd['E_cre']],0)

    if scale_technology == "CITY":
        if energy_source == "GRID":
            tsd['GRID'] = total_el_demand
            tsd['GRID_a'] = tsd['Ea']
            tsd['GRID_l'] = tsd['El']
            tsd['GRID_v'] = tsd['Ev']
            tsd['GRID_ve'] = tsd['Eve']
            tsd['GRID_data'] = tsd['Edata']
            tsd['GRID_pro'] = tsd['Epro']
            tsd['GRID_aux'] = tsd['Eaux']
            tsd['GRID_ww'] = tsd['E_ww']
            tsd['GRID_cs'] = tsd['E_cs']
            tsd['GRID_hs'] = tsd['E_hs']
            tsd['GRID_cdata'] = tsd['E_cdata']
            tsd['GRID_cre'] = tsd['E_cre']
        else:
            raise Exception('check potential error in input database of LCA infrastructure / ELECTRICITY')
    elif scale_technology == "NONE":
        tsd['GRID'] = np.zeros(HOURS_IN_YEAR)
        tsd['GRID_a'] = np.zeros(HOURS_IN_YEAR)
        tsd['GRID_l'] = np.zeros(HOURS_IN_YEAR)
        tsd['GRID_v'] = np.zeros(HOURS_IN_YEAR)
        tsd['GRID_ve'] = np.zeros(HOURS_IN_YEAR)
        tsd['GRID_data'] = np.zeros(HOURS_IN_YEAR)
        tsd['GRID_pro'] = np.zeros(HOURS_IN_YEAR)
        tsd['GRID_aux'] = np.zeros(HOURS_IN_YEAR)
        tsd['GRID_ww'] = np.zeros(HOURS_IN_YEAR)
        tsd['GRID_cs'] = np.zeros(HOURS_IN_YEAR)
        tsd['GRID_hs'] = np.zeros(HOURS_IN_YEAR)
        tsd['GRID_cdata'] = np.zeros(HOURS_IN_YEAR)
        tsd['GRID_cre'] = np.zeros(HOURS_IN_YEAR)
    else:
        raise Exception('check potential error in input database of LCA infrastructure / ELECTRICITY')

    return tsd


def calc_Eaux(tsd):
    """
    Calculate the compound of total auxiliary electricity loads

    :param tsd: Time series data of building
    :type tsd: Dict[str, numpy.ndarray]

    """
    tsd['Eaux'] = np.nansum([tsd['Eaux_fw'], tsd['Eaux_ww'], tsd['Eaux_cs'], tsd['Eaux_hs'], tsd['Ehs_lat_aux']],0)

    return tsd


def calc_Eaux_fw(tsd, bpr: BuildingPropertiesRow, schedules):
    """
    Calculate auxiliary electricity consumption (Eaux_fw) to distribute fresh water (fw) in the building.

    :param tsd: Time series data of building
    :type tsd: Dict[str, numpy.ndarray]

    :param bpr: building properties
    :type bpr: cea.demand.building_properties.BuildingProperties
    """

    tsd['vfw_m3perh'] = schedules['Vw_lph'] / 1000  # m3/h

    height_ag = bpr.geometry['height_ag']
    if height_ag > MIN_HEIGHT_THAT_REQUIRES_PUMPING:  # pumping required for buildings above 15m (or 5 floors)
        # pressure losses
        effective_height = (height_ag - MIN_HEIGHT_THAT_REQUIRES_PUMPING)
        deltaP_kPa = DELTA_P_1 * effective_height
        b = 1  # assuming a good pumping system
        tsd['Eaux_fw'] = np.vectorize(calc_Eauxf_fw)(tsd['vfw_m3perh'], deltaP_kPa, b)
    else:
        tsd['Eaux_fw'] = np.zeros(HOURS_IN_YEAR)
    return tsd


def calc_Eaux_ww(tsd, bpr: BuildingPropertiesRow):
    """
    Calculate auxiliary electricity consumption (Eaux_ww) to distribute hot water (ww) in the building.

    :param tsd: Time series data of building
    :type tsd: Dict[str, numpy.ndarray]

    :param bpr: building properties
    :type bpr: cea.demand.building_properties.BuildingProperties
    """
    Ll = bpr.geometry['Blength']
    Lw = bpr.geometry['Bwidth']
    Mww = tsd['mww_kgs']
    Qww = tsd['Qww']
    Year = bpr.year
    nf_ag = bpr.geometry['floors_ag']
    fforma = bpr.building_systems['fforma']

    # pressure losses
    deltaP_fittings_gen_kPa = 16  # equation F.4 -standard values
    l_w_dis_col = 2 * (max(Ll, Lw) + 2.5 + nf_ag * bpr.geometry['floor_height']) * fforma  # equation F.5
    deltaP_kPa = DELTA_P_1 * l_w_dis_col + deltaP_fittings_gen_kPa
    if Year >= 2000:
        b = 1
    else:
        b = 2

    tsd['Eaux_ww'] = np.vectorize(calc_Eauxf_ww)(Qww, deltaP_kPa, b, Mww)

    return tsd


def calc_Eaux_Qhs_Qcs(tsd, bpr: BuildingPropertiesRow):
    """
    Auxiliary electric loads
    from Legacy
    Following EN 15316-3-2:2007 Annex F

    :param tsd: Time series data of building
    :type tsd: Dict[str, numpy.ndarray]

    :param bpr: building properties
    :type bpr: cea.demand.building_properties.BuildingProperties
    :return:
    """
    # TODO: documentation

    Ll = bpr.geometry['Blength']
    Lw = bpr.geometry['Bwidth']
    fforma = bpr.building_systems['fforma']
    Qcs_sys = tsd['Qcs_sys']
    Qhs_sys = tsd['Qhs_sys']
    Tcs_re_ahu = tsd['Tcs_sys_re_ahu']
    Tcs_sup_ahu = tsd['Tcs_sys_sup_ahu']
    Tcs_re_aru = tsd['Tcs_sys_re_aru']
    Tcs_sup_aru = tsd['Tcs_sys_sup_aru']
    Tcs_re_scu = tsd['Tcs_sys_re_scu']
    Tcs_sup_scu = tsd['Tcs_sys_sup_scu']
    Ths_re_ahu = tsd['Ths_sys_re_ahu']
    Ths_sup_ahu = tsd['Ths_sys_sup_ahu']
    Ths_re_aru = tsd['Ths_sys_re_aru']
    Ths_sup_aru = tsd['Ths_sys_sup_aru']
    Ths_re_shu = tsd['Ths_sys_re_shu']
    Ths_sup_shu = tsd['Ths_sys_sup_shu']

    Year = bpr.year
    nf_ag = bpr.geometry['floors_ag']

    # split up the final demands according to the fraction of energy
    frac_heat_ahu = [ahu / sys if sys > 0 else 0 for ahu, sys in zip(tsd['Qhs_sen_ahu'], tsd['Qhs_sen_sys'])]
    Qhs_sys_ahu = Qhs_sys * frac_heat_ahu
    Qhs_sys_0_ahu = np.nanmax(Qhs_sys_ahu)
    frac_heat_aru = [aru / sys if sys > 0 else 0 for aru, sys in zip(tsd['Qhs_sen_aru'], tsd['Qhs_sen_sys'])]
    Qhs_sys_aru = Qhs_sys * frac_heat_aru
    Qhs_sys_0_aru = np.nanmax(Qhs_sys_aru)
    frac_heat_shu = [shu / sys if sys > 0 else 0 for shu, sys in zip(tsd['Qhs_sen_shu'], tsd['Qhs_sen_sys'])]
    Qhs_sys_shu = Qhs_sys * frac_heat_shu
    Qhs_sys_0_shu = np.nanmax(Qhs_sys_shu)
    frac_cool_ahu = [ahu / sys if sys < 0 else 0 for ahu, sys in zip(tsd['Qcs_sen_ahu'], tsd['Qcs_sen_sys'])]
    Qcs_sys_ahu = Qcs_sys * frac_cool_ahu
    Qcs_sys_0_ahu = np.nanmin(Qcs_sys_ahu)
    frac_cool_aru = [aru / sys if sys < 0 else 0 for aru, sys in zip(tsd['Qcs_sen_aru'], tsd['Qcs_sen_sys'])]
    Qcs_sys_aru = Qcs_sys * frac_cool_aru
    Qcs_sys_0_aru = np.nanmin(Qcs_sys_aru)
    frac_cool_scu = [scu / sys if sys < 0 else 0 for scu, sys in zip(tsd['Qcs_sen_scu'], tsd['Qcs_sen_sys'])]
    Qcs_sys_scu = Qcs_sys * frac_cool_scu
    Qcs_sys_0_scu = np.nanmin(Qcs_sys_scu)

    # pressure losses
    deltaP_fittings_gen_kPa = 16  # equation F.4 -standard values
    l_w_dis_col = 2 * (max(Ll, Lw) + 2.5 + nf_ag * bpr.geometry['floor_height']) * fforma  # equation F.5
    deltaP_kPa = DELTA_P_1 * l_w_dis_col + deltaP_fittings_gen_kPa
    if Year >= 2000:
        b = 1
    else:
        b = 2

    if control_heating_cooling_systems.has_heating_system(bpr.hvac["class_hs"]):

        # for all subsystems
        Eaux_hs_ahu = np.vectorize(calc_Eauxf_hs_dis)(Qhs_sys_ahu, Qhs_sys_0_ahu, deltaP_kPa, b, Ths_sup_ahu,
                                                      Ths_re_ahu)
        Eaux_hs_aru = np.vectorize(calc_Eauxf_hs_dis)(Qhs_sys_aru, Qhs_sys_0_aru, deltaP_kPa, b, Ths_sup_aru,
                                                      Ths_re_aru)
        Eaux_hs_shu = np.vectorize(calc_Eauxf_hs_dis)(Qhs_sys_shu, Qhs_sys_0_shu, deltaP_kPa, b, Ths_sup_shu,
                                                      Ths_re_shu)
        tsd['Eaux_hs'] = Eaux_hs_ahu + Eaux_hs_aru + Eaux_hs_shu  # sum up
    else:
        tsd['Eaux_hs'] = np.zeros(HOURS_IN_YEAR)

    if control_heating_cooling_systems.has_cooling_system(bpr.hvac["class_cs"]):

        # for all subsystems
        Eaux_cs_ahu = np.vectorize(calc_Eauxf_cs_dis)(Qcs_sys_ahu, Qcs_sys_0_ahu, deltaP_kPa, b, Tcs_sup_ahu,
                                                      Tcs_re_ahu)
        Eaux_cs_aru = np.vectorize(calc_Eauxf_cs_dis)(Qcs_sys_aru, Qcs_sys_0_aru, deltaP_kPa, b, Tcs_sup_aru,
                                                      Tcs_re_aru)
        Eaux_cs_scu = np.vectorize(calc_Eauxf_cs_dis)(Qcs_sys_scu, Qcs_sys_0_scu, deltaP_kPa, b, Tcs_sup_scu,
                                                      Tcs_re_scu)
        tsd['Eaux_cs'] = Eaux_cs_ahu + Eaux_cs_aru + Eaux_cs_scu  # sum up
    else:
        tsd['Eaux_cs'] = np.zeros(HOURS_IN_YEAR)

    return tsd

def calc_Eauxf_hs_dis(Qhs_sys, Qhs_sys0, deltaP_kPa, b, ts, tr):
    # Following EN 15316-3-2:2007 Annex F

    # the power of the pump in Watts
    Cpump = 0.97
    if Qhs_sys > 0 and (ts - tr) != 0.0:
        m_kgs = (Qhs_sys / ((ts - tr) * HEAT_CAPACITY_OF_WATER_JPERKGK))
        Phydr_kW = deltaP_kPa * (m_kgs / P_WATER_KGPERM3)
        feff = (1.5 * b) / (0.015 * (Phydr_kW) ** 0.74 + 0.4)
        epmp_eff = feff * Cpump * 1 ** -0.94
        Eaux_hs = epmp_eff * Phydr_kW * 1000
    else:
        Eaux_hs = 0.0
    return Eaux_hs  # in #W


def calc_Eauxf_cs_dis(Qcs_sys, Qcs_sys0, deltaP_kPa, b, ts, tr):
    # Following EN 15316-3-2:2007 Annex F

    # refrigerant R-22 1200 kg/m3
    # for Cooling system
    # the power of the pump in Watts
    Cpump = 0.97
    if Qcs_sys < 0 and (ts - tr) != 0:
        m_kgs = (Qcs_sys / ((ts - tr) * HEAT_CAPACITY_OF_WATER_JPERKGK))
        Phydr_kW = deltaP_kPa * (m_kgs / P_WATER_KGPERM3)
        feff = (1.5 * b) / (0.015 * (Phydr_kW) ** 0.74 + 0.4)
        epmp_eff = feff * Cpump * 1 ** -0.94
        Eaux_cs = epmp_eff * Phydr_kW * 1000
    else:
        Eaux_cs = 0.0
    return Eaux_cs  # in #W


def calc_Eve(tsd):
    """
    calculation of electricity consumption of mechanical ventilation and AC fans
    
    :param tsd: Time series data of building
    :type tsd: dict
    :return: electrical energy for fans of mechanical ventilation in [Wh/h]
    :rtype: float
    """

    # TODO: DOCUMENTATION
    # FIXME: Why only energy demand for AC? Also other mechanical ventilation should have auxiliary energy demand
    # FIXME: What are the units

    # m_ve_mech is

    fan_power = P_FAN  # specific fan consumption in W/m3/h, s

    # mechanical ventilation system air flow [m3/s] = outdoor air + recirculation air
    tsd['m_ve_rec'] = np.nan_to_num(tsd['m_ve_rec'])    # TODO:DOCUMENTATION, in heating case, m_ve_rec is nan
    q_ve_mech = tsd['m_ve_mech'] / physics.calc_rho_air(tsd['theta_ve_mech']) \
                + tsd['m_ve_rec'] / physics.calc_rho_air(tsd['T_int'])

    Eve = fan_power * q_ve_mech * 3600

    tsd['Eve'] = np.nan_to_num(Eve)

    return tsd

def calc_Eauxf_ww(Qww, deltaP_kPa, b, m_kgs):
    """
    Following EN 15316-3-2:2007 Annex F

    :param Qww: Hot water load
    :param deltaP_kPa: Pressure loss in the distribution pipes
    :param b:
    :param m_kgs: How water mass flow
    """

    # the power of the pump in Watts
    Cpump = 0.97
    if Qww > 0.0 and m_kgs != 0.0:
        Phydr_kW = deltaP_kPa * (m_kgs / P_WATER_KGPERM3)
        feff = (1.5 * b) / (0.015 * (Phydr_kW) ** 0.74 + 0.4)
        epmp_eff = feff * Cpump * 1 ** -0.94
        Eaux_ww = epmp_eff * Phydr_kW * 1000
    else:
        Eaux_ww = 0.0
    return Eaux_ww  # [W]


def calc_Eauxf_fw(Vfw_m3h, deltaP_kPa, b):
    """
    Following EN 15316-3-2:2007 Annex F
    :param Vfw_m3h: Fresh water volumetric flow rate
    :param deltaP_kPa: Pressure loss in the distribution pipes
    :return:
    """
    Cpump = 0.97
    if Vfw_m3h > 0.0:
        if deltaP_kPa < 0.0:
            raise ValueError(f"deltaP_kPa: {deltaP_kPa} is less than zero.")
        Phydr_kW = deltaP_kPa * Vfw_m3h * 1 / 3600
        feff = (1.5 * b) / (0.015 * (Phydr_kW) ** 0.74 + 0.4)
        epmp_eff = feff * Cpump * 1 ** -0.94
        Eaux_fw = epmp_eff * Phydr_kW * 1000
    else:
        Eaux_fw = 0.0
    return Eaux_fw # [W]
