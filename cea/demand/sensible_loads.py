"""
Sensible space heating and space cooling loads
EN-13970
"""

from __future__ import annotations
import numpy as np
from cea.demand import control_heating_cooling_systems, constants
from cea.demand.time_series_data import empty_array
from cea.constants import HOURS_IN_YEAR, BOLTZMANN, KELVIN_OFFSET
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cea.demand.building_properties.building_properties_row import BuildingPropertiesRow
    from cea.demand.time_series_data import TimeSeriesData

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Shanshan Hsieh", "Daren Thomas", "Martin Mosteiro", "Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

B_F = constants.B_F
D = constants.D
C_A = constants.C_A


# capacity of emission/control system


def calc_Qhs_Qcs_sys_max(Af, prop_HVAC):
    # TODO: Documentation
    # Refactored from CalcThermalLoads

    IC_max = -prop_HVAC['Qcsmax_Wm2'] * Af
    IH_max = prop_HVAC['Qhsmax_Wm2'] * Af
    return IC_max, IH_max


# solar and heat gains


def calc_Qgain_sen(t, tsd, bpr: BuildingPropertiesRow):
    # TODO

    # internal loads
    tsd.solar.I_sol_and_I_rad[t], tsd.solar.I_rad[t], tsd.solar.I_sol[t] = calc_I_sol(t, bpr, tsd)

    return tsd


def calc_I_sol(t, bpr: BuildingPropertiesRow, tsd: TimeSeriesData):
    """
    This function calculates the net solar radiation (incident - reflected - re-irradiated) according to ISO 13790
    see Eq. (23) in 11.3.1

    :param t: hour of the year
    :param bpr: building properties object
    :param tsd: time series dataframe
    :return:
        I_sol_net: vector of net solar radiation to the building
        I_rad: vector solar radiation re-irradiated to the sky.
        I_sol_gross : vector of incident radiation to the building.
    """

    # calc irradiation to the sky
    I_rad = calc_I_rad(t, tsd, bpr)  # according to section 11.3.2 in ISO 13790 I_rad is a positive term

    # get incident radiation
    I_sol_gross = bpr.solar.I_sol[t]

    I_sol_net = I_sol_gross - I_rad  # Eq. (43) in 11.3.1, I_rad gets subtracted here

    return I_sol_net, I_rad, I_sol_gross  # vector in W


def calc_I_rad(t, tsd: TimeSeriesData, bpr: BuildingPropertiesRow):
    """
    This function calculates the solar radiation re-irradiated from a building to the sky according to ISO 13790
    See Eq. (46) in 11.3.5

    :param t: hour of the year
    :param tsd: time series dataframe
    :param bpr:  building properties object
    :return:
        I_rad: vector solar radiation re-irradiated to the sky.
    """

    temp_s_prev = tsd.rc_model_temperatures.theta_c[t - 1]
    if np.isnan(tsd.rc_model_temperatures.theta_c[t - 1]):
        temp_s_prev = tsd.weather.T_ext[t - 1]

    # theta_ss is the arithmetic average of the surface temperature and the sky temperature, in °C.
    theta_ss = 0.5 * (tsd.weather.T_sky[t] + temp_s_prev)  # [see 11.4.6 in ISO 13790]

    # delta_theta_er is the average difference between outdoor air temperature and sky temperature
    delta_theta_er = tsd.weather.T_ext[t] - tsd.weather.T_sky[t]  # [see 11.3.5 in ISO 13790]

    Fform_wall, Fform_win, Fform_roof, Fform_underside = 0.5, 0.5, 1, 1  # 50% re-irradiated by vertical surfaces and 100% by horizontal
    I_rad_win = tsd.thermal_resistance.RSE_win[t] * bpr.envelope.U_win * calc_hr(bpr.envelope.e_win, theta_ss) * bpr.envelope.Awin_ag * delta_theta_er
    I_rad_roof = tsd.thermal_resistance.RSE_roof[t] * bpr.envelope.U_roof * calc_hr(bpr.envelope.e_roof, theta_ss) * bpr.envelope.Aroof * delta_theta_er
    I_rad_wall = tsd.thermal_resistance.RSE_wall[t] * bpr.envelope.U_wall * calc_hr(bpr.envelope.e_wall, theta_ss) * bpr.envelope.Awall_ag * delta_theta_er
    I_rad_underside = tsd.thermal_resistance.RSE_underside[t] * bpr.envelope.U_base * calc_hr(bpr.envelope.e_underside, theta_ss) * bpr.envelope.Aunderside * delta_theta_er
    I_rad = Fform_wall * I_rad_wall + Fform_win * I_rad_win + Fform_roof * I_rad_roof + Fform_underside * I_rad_underside

    return I_rad


def calc_hr(emissivity, theta_ss):
    """
    This function calculates the external radiative heat transfer coefficient according to ISO 13790
    see Eq. (51) in section 11.4.6

    :param emissivity: emissivity of the considered surface
    :param theta_ss: delta of temperature between building surface and the sky.
    :return:
        hr: radiative heat transfer coefficient of external surfaces

    """
    return 4.0 * emissivity * BOLTZMANN * (theta_ss + KELVIN_OFFSET) ** 3.0

def calc_hc(wind_speed):
    """
    This function calculates the convective heat transfer coefficient for external surfaces according to ISO 6946
    Eq. (C.6) in section C.1

    :param wind_speed: wind speed at this time step from weather file.
    :return:
        hc: convective heat transfer coefficient of external surfaces

    """
    return 4.0 + 4.0 * wind_speed

def calc_Qhs_sys_Qcs_sys(tsd: TimeSeriesData):


    # Calc requirements of generation systems (both cooling and heating do not have a storage):
    tsd.heating_loads.Qhs = tsd.heating_loads.Qhs_sen_sys
    tsd.heating_loads.Qhs_sys = tsd.heating_loads.Qhs + tsd.heating_loads.Qhs_em_ls + tsd.heating_loads.Qhs_dis_ls  # no latent is considered because it is already added a

    # electricity from the adiabatic system. --> TODO
    tsd.cooling_loads.Qcs = tsd.cooling_loads.Qcs_sen_sys + tsd.cooling_loads.Qcs_lat_sys
    tsd.cooling_loads.Qcs_sys = tsd.cooling_loads.Qcs + tsd.cooling_loads.Qcs_em_ls + tsd.cooling_loads.Qcs_dis_ls

    # split  Qhs_sys into different heating units (disaggregation of losses)
    frac_ahu = [ahu / sys if sys > 0 else 0 for ahu, sys in zip(tsd.heating_loads.Qhs_sen_ahu, tsd.heating_loads.Qhs_sen_sys)]
    tsd.heating_loads.Qhs_sys_ahu = tsd.heating_loads.Qhs_sen_ahu + (tsd.heating_loads.Qhs_em_ls + tsd.heating_loads.Qhs_dis_ls) * frac_ahu

    frac_aru = [aru / sys if sys > 0 else 0 for aru, sys in zip(tsd.heating_loads.Qhs_sen_aru, tsd.heating_loads.Qhs_sen_sys)]
    tsd.heating_loads.Qhs_sys_aru = tsd.heating_loads.Qhs_sen_aru + (tsd.heating_loads.Qhs_em_ls + tsd.heating_loads.Qhs_dis_ls) * frac_aru

    frac_shu = [shu / sys if sys > 0 else 0 for shu, sys in zip(tsd.heating_loads.Qhs_sen_shu, tsd.heating_loads.Qhs_sen_sys)]
    tsd.heating_loads.Qhs_sys_shu = tsd.heating_loads.Qhs_sen_shu + (tsd.heating_loads.Qhs_em_ls + tsd.heating_loads.Qhs_dis_ls) * frac_shu

    # split Qcs_sys into different cooling units (disaggregation of losses)
    frac_ahu = [ahu / sys if sys < 0 else 0 for ahu, sys in zip(tsd.cooling_loads.Qcs_sen_ahu, tsd.cooling_loads.Qcs_sen_sys)]
    tsd.cooling_loads.Qcs_sys_ahu = tsd.cooling_loads.Qcs_sen_ahu + tsd.cooling_loads.Qcs_lat_ahu + (tsd.cooling_loads.Qcs_em_ls + tsd.cooling_loads.Qcs_dis_ls) * frac_ahu

    frac_aru = [aru / sys if sys < 0 else 0 for aru, sys in zip(tsd.cooling_loads.Qcs_sen_aru, tsd.cooling_loads.Qcs_sen_sys)]
    tsd.cooling_loads.Qcs_sys_aru = tsd.cooling_loads.Qcs_sen_aru + tsd.cooling_loads.Qcs_lat_aru + (tsd.cooling_loads.Qcs_em_ls + tsd.cooling_loads.Qcs_dis_ls) * frac_aru

    frac_scu = [scu / sys if sys < 0 else 0 for scu, sys in zip(tsd.cooling_loads.Qcs_sen_scu, tsd.cooling_loads.Qcs_sen_sys)]
    tsd.cooling_loads.Qcs_sys_scu = tsd.cooling_loads.Qcs_sen_scu + (tsd.cooling_loads.Qcs_em_ls + tsd.cooling_loads.Qcs_dis_ls) * frac_scu

    return tsd


# temperature of emission/control system


def calc_temperatures_emission_systems(bpr: BuildingPropertiesRow, tsd: TimeSeriesData) -> TimeSeriesData:
    """
    Calculate temperature of emission systems.
    Using radiator function also for cooling ('radiators.calc_radiator')
    Modified from legacy

    Gabriel Happle, Feb. 2018

    :param bpr: Building Properties
    :type bpr: BuildingPropertiesRow
    :param tsd: Time series data of building
    :type tsd: cea.demand.time_series_data.TimeSeriesData
    :return: modifies tsd
    """

    from cea.technologies import radiators, heating_coils

    #
    # TEMPERATURES HEATING SYSTEMS
    #
    if not control_heating_cooling_systems.has_heating_system(bpr.hvac["class_hs"]):
        # if no heating system
        # FIXME: Disable property instead of setting to empty array?
        tsd.heating_system_temperatures.Ths_sys_sup_ahu = empty_array()
        tsd.heating_system_temperatures.Ths_sys_re_ahu = empty_array()
        tsd.heating_system_mass_flows.mcphs_sys_ahu = np.zeros(HOURS_IN_YEAR)
        tsd.heating_system_temperatures.Ths_sys_sup_aru = empty_array()
        tsd.heating_system_temperatures.Ths_sys_re_aru = empty_array()
        tsd.heating_system_mass_flows.mcphs_sys_aru = np.zeros(HOURS_IN_YEAR)
        tsd.heating_system_temperatures.Ths_sys_sup_shu = empty_array()
        tsd.heating_system_temperatures.Ths_sys_re_shu = empty_array()
        tsd.heating_system_mass_flows.mcphs_sys_shu = np.zeros(HOURS_IN_YEAR)

    elif control_heating_cooling_systems.has_radiator_heating_system(bpr):
        # if radiator heating system
        Ta_heating_0 = np.nanmax(tsd.rc_model_temperatures.ta_hs_set)
        Qhs_sys_0 = np.nanmax(tsd.heating_loads.Qhs_sys)  # in W

        tsd.heating_system_temperatures.Ths_sys_sup_ahu = empty_array()
        tsd.heating_system_temperatures.Ths_sys_re_ahu = empty_array()
        tsd.heating_system_mass_flows.mcphs_sys_ahu = np.zeros(HOURS_IN_YEAR)
        tsd.heating_system_temperatures.Ths_sys_sup_aru = empty_array()
        tsd.heating_system_temperatures.Ths_sys_re_aru = empty_array()
        tsd.heating_system_mass_flows.mcphs_sys_aru = np.zeros(HOURS_IN_YEAR)

        Ths_sup, Ths_re, mcphs = np.vectorize(radiators.calc_radiator)(tsd.heating_loads.Qhs_sys, tsd.rc_model_temperatures.T_int, Qhs_sys_0, Ta_heating_0,
                                                                       bpr.building_systems['Ths_sup_shu_0'],
                                                                       bpr.building_systems['Ths_re_shu_0'])

        tsd.heating_system_temperatures.Ths_sys_sup_shu = Ths_sup
        tsd.heating_system_temperatures.Ths_sys_re_shu = Ths_re
        tsd.heating_system_mass_flows.mcphs_sys_shu = mcphs

    elif control_heating_cooling_systems.has_central_ac_heating_system(bpr):

        # ahu
        # consider losses according to loads of systems
        frac_ahu = [ahu / sys if sys > 0 else 0 for ahu, sys in zip(tsd.heating_loads.Qhs_sen_ahu, tsd.heating_loads.Qhs_sen_sys)]
        qhs_sys_ahu = tsd.heating_loads.Qhs_sen_ahu + (tsd.heating_loads.Qhs_em_ls + tsd.heating_loads.Qhs_dis_ls) * frac_ahu

        Qhs_sys_ahu_0 = np.nanmax(qhs_sys_ahu)  # in W

        index = np.where(qhs_sys_ahu == Qhs_sys_ahu_0)
        ma_sup_0 = tsd.heating_system_mass_flows.ma_sup_hs_ahu[index[0][0]]
        Ta_sup_0 = tsd.heating_system_temperatures.ta_sup_hs_ahu[index[0][0]] + KELVIN_OFFSET
        Ta_re_0 = tsd.heating_system_temperatures.ta_re_hs_ahu[index[0][0]] + KELVIN_OFFSET
        Ths_sup, Ths_re, mcphs = np.vectorize(heating_coils.calc_heating_coil)(qhs_sys_ahu, Qhs_sys_ahu_0, tsd.heating_system_temperatures.ta_sup_hs_ahu,
                                                                               tsd.heating_system_temperatures.ta_re_hs_ahu,
                                                                               bpr.building_systems['Ths_sup_ahu_0'],
                                                                               bpr.building_systems['Ths_re_ahu_0'],
                                                                               tsd.heating_system_mass_flows.ma_sup_hs_ahu, ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0)
        tsd.heating_system_temperatures.Ths_sys_sup_ahu = Ths_sup  # in C
        tsd.heating_system_temperatures.Ths_sys_re_ahu = Ths_re  # in C
        tsd.heating_system_mass_flows.mcphs_sys_ahu = mcphs

        # ARU
        # consider losses according to loads of systems
        frac_aru = [aru / sys if sys > 0 else 0 for aru, sys in zip(tsd.heating_loads.Qhs_sen_aru, tsd.heating_loads.Qhs_sen_sys)]
        qhs_sys_aru = tsd.heating_loads.Qhs_sen_aru + (tsd.heating_loads.Qhs_em_ls + tsd.heating_loads.Qhs_dis_ls) * frac_aru

        Qhs_sys_aru_0 = np.nanmax(qhs_sys_aru)  # in W

        index = np.where(qhs_sys_aru == Qhs_sys_aru_0)
        ma_sup_0 = tsd.heating_system_mass_flows.ma_sup_hs_aru[index[0][0]]
        Ta_sup_0 = tsd.heating_system_temperatures.ta_sup_hs_aru[index[0][0]] + KELVIN_OFFSET
        Ta_re_0 = tsd.heating_system_temperatures.ta_re_hs_aru[index[0][0]] + KELVIN_OFFSET
        Ths_sup, Ths_re, mcphs = np.vectorize(heating_coils.calc_heating_coil)(qhs_sys_aru, Qhs_sys_aru_0,
                                                                               tsd.heating_system_temperatures.ta_sup_hs_aru,
                                                                               tsd.heating_system_temperatures.ta_re_hs_aru,
                                                                               bpr.building_systems['Ths_sup_aru_0'],
                                                                               bpr.building_systems['Ths_re_aru_0'],
                                                                               tsd.heating_system_mass_flows.ma_sup_hs_aru, ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0)
        tsd.heating_system_temperatures.Ths_sys_sup_aru = Ths_sup  # in C
        tsd.heating_system_temperatures.Ths_sys_re_aru = Ths_re  # in C
        tsd.heating_system_mass_flows.mcphs_sys_aru = mcphs

        # SHU
        tsd.heating_system_temperatures.Ths_sys_sup_shu = empty_array()
        tsd.heating_system_temperatures.Ths_sys_re_shu = empty_array()
        tsd.heating_system_mass_flows.mcphs_sys_shu = np.zeros(HOURS_IN_YEAR)

    elif control_heating_cooling_systems.has_floor_heating_system(bpr):

        Ta_heating_0 = np.nanmax(tsd.rc_model_temperatures.ta_hs_set)
        Qhs_sys_0 = np.nanmax(tsd.heating_loads.Qhs_sys)  # in W

        tsd.heating_system_temperatures.Ths_sys_sup_ahu = empty_array()
        tsd.heating_system_temperatures.Ths_sys_re_ahu = empty_array()
        tsd.heating_system_mass_flows.mcphs_sys_ahu = np.zeros(HOURS_IN_YEAR)
        tsd.heating_system_temperatures.Ths_sys_sup_aru = empty_array()
        tsd.heating_system_temperatures.Ths_sys_re_aru = empty_array()
        tsd.heating_system_mass_flows.mcphs_sys_aru = np.zeros(HOURS_IN_YEAR)

        Ths_sup, Ths_re, mcphs = np.vectorize(radiators.calc_radiator)(tsd.heating_loads.Qhs_sys, tsd.rc_model_temperatures.T_int, Qhs_sys_0, Ta_heating_0,
                                                                       bpr.building_systems['Ths_sup_shu_0'],
                                                                       bpr.building_systems['Ths_re_shu_0'])
        tsd.heating_system_temperatures.Ths_sys_sup_shu = Ths_sup
        tsd.heating_system_temperatures.Ths_sys_re_shu = Ths_re
        tsd.heating_system_mass_flows.mcphs_sys_shu = mcphs

    else:
        raise Exception('Heating system not defined in function: "calc_temperatures_emission_systems"')


    #
    # TEMPERATURES COOLING SYSTEMS
    #
    if not control_heating_cooling_systems.has_cooling_system(bpr.hvac["class_cs"]):
        # if no cooling system

        tsd.cooling_system_temperatures.Tcs_sys_sup_ahu = empty_array()
        tsd.cooling_system_temperatures.Tcs_sys_re_ahu = empty_array()
        tsd.cooling_system_mass_flows.mcpcs_sys_ahu = np.zeros(HOURS_IN_YEAR)
        tsd.cooling_system_temperatures.Tcs_sys_sup_aru = empty_array()
        tsd.cooling_system_temperatures.Tcs_sys_re_aru = empty_array()
        tsd.cooling_system_mass_flows.mcpcs_sys_aru = np.zeros(HOURS_IN_YEAR)
        tsd.cooling_system_temperatures.Tcs_sys_sup_scu = empty_array()
        tsd.cooling_system_temperatures.Tcs_sys_re_scu = empty_array()
        tsd.cooling_system_mass_flows.mcpcs_sys_scu = np.zeros(HOURS_IN_YEAR)

    elif control_heating_cooling_systems.has_central_ac_cooling_system(bpr):

        # AHU
        # consider losses according to loads of systems
        frac_ahu = [ahu / sys if sys < 0 else 0 for ahu, sys in zip(tsd.cooling_loads.Qcs_sen_ahu, tsd.cooling_loads.Qcs_sen_sys)]
        qcs_sys_ahu = tsd.cooling_loads.Qcs_sen_ahu + tsd.cooling_loads.Qcs_lat_ahu + (tsd.cooling_loads.Qcs_em_ls + tsd.cooling_loads.Qcs_dis_ls) * frac_ahu

        Qcs_sys_ahu_0 = np.nanmin(qcs_sys_ahu)  # in W

        index = np.where(qcs_sys_ahu == Qcs_sys_ahu_0)
        ma_sup_0 = tsd.cooling_system_mass_flows.ma_sup_cs_ahu[index[0][0]]
        Ta_sup_0 = tsd.cooling_system_temperatures.ta_sup_cs_ahu[index[0][0]] + KELVIN_OFFSET
        Ta_re_0 = tsd.cooling_system_temperatures.ta_re_cs_ahu[index[0][0]] + KELVIN_OFFSET
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(heating_coils.calc_cooling_coil)(qcs_sys_ahu, Qcs_sys_ahu_0, tsd.cooling_system_temperatures.ta_sup_cs_ahu,
                                                                               tsd.cooling_system_temperatures.ta_re_cs_ahu,
                                                                               bpr.building_systems['Tcs_sup_ahu_0'],
                                                                               bpr.building_systems['Tcs_re_ahu_0'],
                                                                               tsd.cooling_system_mass_flows.ma_sup_cs_ahu, ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0)
        tsd.cooling_system_temperatures.Tcs_sys_sup_ahu = Tcs_sup  # in C
        tsd.cooling_system_temperatures.Tcs_sys_re_ahu = Tcs_re  # in C
        tsd.cooling_system_mass_flows.mcpcs_sys_ahu = mcpcs

        # ARU
        # consider losses according to loads of systems
        frac_aru = [aru / sys if sys < 0 else 0 for aru, sys in zip(tsd.cooling_loads.Qcs_sen_aru, tsd.cooling_loads.Qcs_sen_sys)]
        qcs_sys_aru = tsd.cooling_loads.Qcs_sen_aru + tsd.cooling_loads.Qcs_lat_aru + (tsd.cooling_loads.Qcs_em_ls + tsd.cooling_loads.Qcs_dis_ls) * frac_aru

        Qcs_sys_aru_0 = np.nanmin(qcs_sys_aru)  # in W

        index = np.where(qcs_sys_aru == Qcs_sys_aru_0)
        ma_sup_0 = tsd.cooling_system_mass_flows.ma_sup_cs_aru[index[0][0]]
        Ta_sup_0 = tsd.cooling_system_temperatures.ta_sup_cs_aru[index[0][0]] + KELVIN_OFFSET
        Ta_re_0 = tsd.cooling_system_temperatures.ta_re_cs_aru[index[0][0]] + KELVIN_OFFSET
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(heating_coils.calc_cooling_coil)(qcs_sys_aru, Qcs_sys_aru_0, tsd.cooling_system_temperatures.ta_sup_cs_aru,
                                                                               tsd.cooling_system_temperatures.ta_re_cs_aru,
                                                                               bpr.building_systems['Tcs_sup_aru_0'],
                                                                               bpr.building_systems['Tcs_re_aru_0'],
                                                                               tsd.cooling_system_mass_flows.ma_sup_cs_aru, ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0)
        tsd.cooling_system_temperatures.Tcs_sys_sup_aru = Tcs_sup  # in C
        tsd.cooling_system_temperatures.Tcs_sys_re_aru = Tcs_re  # in C
        tsd.cooling_system_mass_flows.mcpcs_sys_aru = mcpcs

        # SCU
        tsd.cooling_system_temperatures.Tcs_sys_sup_scu = empty_array()
        tsd.cooling_system_temperatures.Tcs_sys_re_scu = empty_array()
        tsd.cooling_system_mass_flows.mcpcs_sys_scu = np.zeros(HOURS_IN_YEAR)

    elif control_heating_cooling_systems.has_local_ac_cooling_system(bpr):

        # AHU
        tsd.cooling_system_temperatures.Tcs_sys_sup_ahu = empty_array()
        tsd.cooling_system_temperatures.Tcs_sys_re_ahu = empty_array()
        tsd.cooling_system_mass_flows.mcpcs_sys_ahu = np.zeros(HOURS_IN_YEAR)

        # ARU
        # consider losses according to loads of systems
        qcs_sys_aru = tsd.cooling_loads.Qcs_sen_aru + tsd.cooling_loads.Qcs_lat_aru + (tsd.cooling_loads.Qcs_em_ls + tsd.cooling_loads.Qcs_dis_ls)
        qcs_sys_aru = np.nan_to_num(qcs_sys_aru)

        # Calc nominal temperatures of systems
        Qcs_sys_aru_0 = np.nanmin(qcs_sys_aru)  # in W

        index = np.where(qcs_sys_aru == Qcs_sys_aru_0)
        ma_sup_0 = tsd.cooling_system_mass_flows.ma_sup_cs_aru[index[0][0]]
        Ta_sup_0 = tsd.cooling_system_temperatures.ta_sup_cs_aru[index[0][0]] + KELVIN_OFFSET
        Ta_re_0 = tsd.cooling_system_temperatures.ta_re_cs_aru[index[0][0]] + KELVIN_OFFSET
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(heating_coils.calc_cooling_coil)(qcs_sys_aru, Qcs_sys_aru_0,
                                                                               tsd.cooling_system_temperatures.ta_sup_cs_aru,
                                                                               tsd.cooling_system_temperatures.ta_re_cs_aru,
                                                                               bpr.building_systems['Tcs_sup_aru_0'],
                                                                               bpr.building_systems['Tcs_re_aru_0'],
                                                                               tsd.cooling_system_mass_flows.ma_sup_cs_aru, ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0)
        tsd.cooling_system_temperatures.Tcs_sys_sup_aru = Tcs_sup  # in C
        tsd.cooling_system_temperatures.Tcs_sys_re_aru = Tcs_re  # in C
        tsd.cooling_system_mass_flows.mcpcs_sys_aru = mcpcs

        # SCU
        tsd.cooling_system_temperatures.Tcs_sys_sup_scu = empty_array()
        tsd.cooling_system_temperatures.Tcs_sys_re_scu = empty_array()
        tsd.cooling_system_mass_flows.mcpcs_sys_scu = np.zeros(HOURS_IN_YEAR)

    elif control_heating_cooling_systems.has_3for2_cooling_system(bpr):

        # AHU
        # consider losses according to loads of systems
        frac_ahu = [ahu/sys if sys < 0 else 0 for ahu, sys in zip(tsd.cooling_loads.Qcs_sen_ahu,tsd.cooling_loads.Qcs_sen_sys)]
        qcs_sys_ahu = tsd.cooling_loads.Qcs_sen_ahu + tsd.cooling_loads.Qcs_lat_ahu + (tsd.cooling_loads.Qcs_em_ls + tsd.cooling_loads.Qcs_dis_ls) * frac_ahu
        qcs_sys_ahu = np.nan_to_num(qcs_sys_ahu)

        Qcs_sys_ahu_0 = np.nanmin(qcs_sys_ahu)  # in W

        index = np.where(qcs_sys_ahu == Qcs_sys_ahu_0)
        ma_sup_0 = tsd.cooling_system_mass_flows.ma_sup_cs_ahu[index[0][0]]
        Ta_sup_0 = tsd.cooling_system_temperatures.ta_sup_cs_ahu[index[0][0]] + KELVIN_OFFSET
        Ta_re_0 = tsd.cooling_system_temperatures.ta_re_cs_ahu[index[0][0]] + KELVIN_OFFSET
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(heating_coils.calc_cooling_coil)(qcs_sys_ahu, Qcs_sys_ahu_0,
                                                                               tsd.cooling_system_temperatures.ta_sup_cs_ahu,
                                                                               tsd.cooling_system_temperatures.ta_re_cs_ahu,
                                                                               bpr.building_systems['Tcs_sup_ahu_0'],
                                                                               bpr.building_systems['Tcs_re_ahu_0'],
                                                                               tsd.cooling_system_mass_flows.ma_sup_cs_ahu, ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0)
        tsd.cooling_system_temperatures.Tcs_sys_sup_ahu = Tcs_sup  # in C
        tsd.cooling_system_temperatures.Tcs_sys_re_ahu = Tcs_re  # in C
        tsd.cooling_system_mass_flows.mcpcs_sys_ahu = mcpcs

        # ARU
        # consider losses according to loads of systems
        frac_aru = [aru / sys if sys < 0 else 0 for aru, sys in zip(tsd.cooling_loads.Qcs_sen_aru, tsd.cooling_loads.Qcs_sen_sys)]
        qcs_sys_aru = tsd.cooling_loads.Qcs_sen_aru + tsd.cooling_loads.Qcs_lat_aru + (tsd.cooling_loads.Qcs_em_ls + tsd.cooling_loads.Qcs_dis_ls) * frac_aru
        qcs_sys_aru = np.nan_to_num(qcs_sys_aru)

        # Calc nominal temperatures of systems
        Qcs_sys_aru_0 = np.nanmin(qcs_sys_aru)  # in W

        index = np.where(qcs_sys_aru == Qcs_sys_aru_0)
        ma_sup_0 = tsd.cooling_system_mass_flows.ma_sup_cs_aru[index[0][0]]
        Ta_sup_0 = tsd.cooling_system_temperatures.ta_sup_cs_aru[index[0][0]] + KELVIN_OFFSET
        Ta_re_0 = tsd.cooling_system_temperatures.ta_re_cs_aru[index[0][0]] + KELVIN_OFFSET
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(heating_coils.calc_cooling_coil)(qcs_sys_aru, Qcs_sys_aru_0,
                                                                               tsd.cooling_system_temperatures.ta_sup_cs_aru,
                                                                               tsd.cooling_system_temperatures.ta_re_cs_aru,
                                                                               bpr.building_systems['Tcs_sup_aru_0'],
                                                                               bpr.building_systems['Tcs_re_aru_0'],
                                                                               tsd.cooling_system_mass_flows.ma_sup_cs_aru, ma_sup_0,
                                                                               Ta_sup_0, Ta_re_0)
        tsd.cooling_system_temperatures.Tcs_sys_sup_aru = Tcs_sup  # in C
        tsd.cooling_system_temperatures.Tcs_sys_re_aru = Tcs_re  # in C
        tsd.cooling_system_mass_flows.mcpcs_sys_aru = mcpcs

        # SCU
        # consider losses according to loads of systems
        frac_scu = [scu / sys if sys < 0 else 0 for scu, sys in zip(tsd.cooling_loads.Qcs_sen_scu, tsd.cooling_loads.Qcs_sen_sys)]
        qcs_sys_scu = tsd.cooling_loads.Qcs_sen_scu + (tsd.cooling_loads.Qcs_em_ls + tsd.cooling_loads.Qcs_dis_ls) * frac_scu
        qcs_sys_scu = np.nan_to_num(qcs_sys_scu)

        Qcs_sys_scu_0 = np.nanmin(qcs_sys_scu)  # in W
        Ta_cooling_0 = np.nanmin(tsd.rc_model_temperatures.ta_cs_set)

        Tcs_sup, Tcs_re, mcpcs = np.vectorize(radiators.calc_radiator)(qcs_sys_scu, tsd.rc_model_temperatures.T_int, Qcs_sys_scu_0, Ta_cooling_0,
                                                                       bpr.building_systems['Tcs_sup_scu_0'],
                                                                       bpr.building_systems['Tcs_re_scu_0'])
        tsd.cooling_system_temperatures.Tcs_sys_sup_scu = Tcs_sup  # in C
        tsd.cooling_system_temperatures.Tcs_sys_re_scu = Tcs_re  # in C
        tsd.cooling_system_mass_flows.mcpcs_sys_scu = mcpcs

    elif control_heating_cooling_systems.has_ceiling_cooling_system(bpr) or \
            control_heating_cooling_systems.has_floor_cooling_system(bpr):

        # SCU
        # consider losses according to loads of systems
        qcs_sys_scu = tsd.cooling_loads.Qcs_sen_scu + (tsd.cooling_loads.Qcs_em_ls + tsd.cooling_loads.Qcs_dis_ls)
        qcs_sys_scu = np.nan_to_num(qcs_sys_scu)

        Qcs_sys_scu_0 = np.nanmin(qcs_sys_scu)  # in W
        Ta_cooling_0 = np.nanmin(tsd.rc_model_temperatures.ta_cs_set)

        # use radiator for ceiling cooling calculation
        Tcs_sup, Tcs_re, mcpcs = np.vectorize(radiators.calc_radiator)(qcs_sys_scu, tsd.rc_model_temperatures.T_int, Qcs_sys_scu_0, Ta_cooling_0,
                                                                       bpr.building_systems['Tcs_sup_scu_0'],
                                                                       bpr.building_systems['Tcs_re_scu_0'])

        tsd.cooling_system_temperatures.Tcs_sys_sup_scu = Tcs_sup  # in C
        tsd.cooling_system_temperatures.Tcs_sys_re_scu = Tcs_re  # in C
        tsd.cooling_system_mass_flows.mcpcs_sys_scu = mcpcs

        # AHU
        tsd.cooling_system_temperatures.Tcs_sys_sup_ahu = empty_array()
        tsd.cooling_system_temperatures.Tcs_sys_re_ahu = empty_array()
        tsd.cooling_system_mass_flows.mcpcs_sys_ahu = np.zeros(HOURS_IN_YEAR)

        # ARU
        tsd.cooling_system_temperatures.Tcs_sys_sup_aru = empty_array()
        tsd.cooling_system_temperatures.Tcs_sys_re_aru = empty_array()
        tsd.cooling_system_mass_flows.mcpcs_sys_aru = np.zeros(HOURS_IN_YEAR)

    else:
        raise Exception('Cooling system not defined in function: "calc_temperatures_emission_systems"')

    return tsd

# space heating/cooling losses


def calc_Qhs_Qcs_loss(bpr: BuildingPropertiesRow, tsd: TimeSeriesData) -> TimeSeriesData:
    """
    Calculate distribution losses of emission systems.

    Modified from legacy:
        calculates distribution losses based on ISO 15316

    Gabriel Happle, Feb. 2018

    :param bpr: Building Properties
    :type bpr: BuildingPropertiesRow
    :param tsd: Time series data of building
    :type tsd: cea.demand.time_series_data.TimeSeriesData
    :return: modifies tsd
    """

    # look up properties
    Y = bpr.building_systems['Y'][0]
    Lv = bpr.building_systems['Lv']

    tsh_ahu = bpr.building_systems['Ths_sup_ahu_0']
    trh_ahu = bpr.building_systems['Ths_re_ahu_0']
    tsh_aru = bpr.building_systems['Ths_sup_aru_0']
    trh_aru = bpr.building_systems['Ths_re_aru_0']
    tsh_shu = bpr.building_systems['Ths_sup_shu_0']
    trh_shu = bpr.building_systems['Ths_re_shu_0']

    tsc_ahu = bpr.building_systems['Tcs_sup_ahu_0']
    trc_ahu = bpr.building_systems['Tcs_re_ahu_0']
    tsc_aru = bpr.building_systems['Tcs_sup_aru_0']
    trc_aru = bpr.building_systems['Tcs_re_aru_0']
    tsc_scu = bpr.building_systems['Tcs_sup_scu_0']
    trc_scu = bpr.building_systems['Tcs_re_scu_0']

    tair = tsd.rc_model_temperatures.T_int
    text = tsd.weather.T_ext

    # Calculate tamb in basement according to EN
    tamb = tair - B_F * (tair - text)

    if np.any(tsd.heating_loads.Qhs_sen_ahu > 0):
        frac_ahu = [ahu / sys if sys > 0 else 0 for ahu, sys in zip(tsd.heating_loads.Qhs_sen_ahu, tsd.heating_loads.Qhs_sen_sys)]
        qhs_sen_ahu_incl_em_ls = tsd.heating_loads.Qhs_sen_ahu + tsd.heating_loads.Qhs_em_ls * frac_ahu
        qhs_sen_ahu_incl_em_ls = np.nan_to_num(qhs_sen_ahu_incl_em_ls)
        Qhs_d_ls_ahu = ((tsh_ahu + trh_ahu) / 2 - tamb) * (
        qhs_sen_ahu_incl_em_ls / np.nanmax(qhs_sen_ahu_incl_em_ls)) * (Lv * Y)

    else:
        Qhs_d_ls_ahu = np.zeros(HOURS_IN_YEAR)

    if np.any(tsd.heating_loads.Qhs_sen_aru > 0):
        frac_aru = [aru / sys if sys > 0 else 0 for aru, sys in zip(tsd.heating_loads.Qhs_sen_aru, tsd.heating_loads.Qhs_sen_sys)]
        qhs_sen_aru_incl_em_ls = tsd.heating_loads.Qhs_sen_aru + tsd.heating_loads.Qhs_em_ls * frac_aru
        qhs_sen_aru_incl_em_ls = np.nan_to_num(qhs_sen_aru_incl_em_ls)
        Qhs_d_ls_aru = ((tsh_aru + trh_aru) / 2 - tamb) * (
        qhs_sen_aru_incl_em_ls / np.nanmax(qhs_sen_aru_incl_em_ls)) * (
                           Lv * Y)
    else:
        Qhs_d_ls_aru = np.zeros(HOURS_IN_YEAR)

    if np.any(tsd.heating_loads.Qhs_sen_shu > 0):
        frac_shu = [shu / sys if sys > 0 else 0 for shu, sys in zip(tsd.heating_loads.Qhs_sen_shu, tsd.heating_loads.Qhs_sen_sys)]
        qhs_sen_shu_incl_em_ls = tsd.heating_loads.Qhs_sen_shu + tsd.heating_loads.Qhs_em_ls * frac_shu
        qhs_sen_shu_incl_em_ls = np.nan_to_num(qhs_sen_shu_incl_em_ls)
        qhs_d_ls_shu = ((tsh_shu + trh_shu) / 2 - tamb) * (
        qhs_sen_shu_incl_em_ls / np.nanmax(qhs_sen_shu_incl_em_ls)) * (
                           Lv * Y)
    else:
        qhs_d_ls_shu = np.zeros(HOURS_IN_YEAR)

    if np.any(tsd.cooling_loads.Qcs_sen_ahu < 0):
        frac_ahu = [ahu / sys if sys < 0 else 0 for ahu, sys in zip(tsd.cooling_loads.Qcs_sen_ahu, tsd.cooling_loads.Qcs_sen_sys)]
        qcs_sen_ahu_incl_em_ls = tsd.cooling_loads.Qcs_sen_ahu + tsd.cooling_loads.Qcs_lat_ahu + tsd.cooling_loads.Qcs_em_ls * frac_ahu
        qcs_sen_ahu_incl_em_ls = np.nan_to_num(qcs_sen_ahu_incl_em_ls)
        qcs_d_ls_ahu = ((tsc_ahu + trc_ahu) / 2 - tamb) * (qcs_sen_ahu_incl_em_ls / np.nanmin(qcs_sen_ahu_incl_em_ls))\
                       * (Lv * Y)
    else:
        qcs_d_ls_ahu = np.zeros(HOURS_IN_YEAR)

    if np.any(tsd.cooling_loads.Qcs_sen_aru < 0):
        frac_aru = [aru / sys if sys < 0 else 0 for aru, sys in zip(tsd.cooling_loads.Qcs_sen_aru, tsd.cooling_loads.Qcs_sen_sys)]
        qcs_sen_aru_incl_em_ls = tsd.cooling_loads.Qcs_sen_aru + tsd.cooling_loads.Qcs_lat_aru + tsd.cooling_loads.Qcs_em_ls * frac_aru
        qcs_sen_aru_incl_em_ls = np.nan_to_num(qcs_sen_aru_incl_em_ls)
        qcs_d_ls_aru = ((tsc_aru + trc_aru) / 2 - tamb) * (qcs_sen_aru_incl_em_ls / np.nanmin(qcs_sen_aru_incl_em_ls))\
                        * (Lv * Y)
    else:
        qcs_d_ls_aru = np.zeros(HOURS_IN_YEAR)

    if np.any(tsd.cooling_loads.Qcs_sen_scu < 0):
        frac_scu = [scu / sys if sys < 0 else 0 for scu, sys in zip(tsd.cooling_loads.Qcs_sen_scu, tsd.cooling_loads.Qcs_sen_sys)]
        qcs_sen_scu_incl_em_ls = tsd.cooling_loads.Qcs_sen_scu + tsd.cooling_loads.Qcs_em_ls * frac_scu
        qcs_sen_scu_incl_em_ls = np.nan_to_num(qcs_sen_scu_incl_em_ls)
        Qcs_d_ls_scu = ((tsc_scu + trc_scu) / 2 - tamb) * (qcs_sen_scu_incl_em_ls / np.nanmin(qcs_sen_scu_incl_em_ls)) * (
        Lv * Y)
    else:
        Qcs_d_ls_scu = np.zeros(HOURS_IN_YEAR)

    tsd.heating_loads.Qhs_dis_ls = Qhs_d_ls_ahu + Qhs_d_ls_aru + qhs_d_ls_shu
    tsd.cooling_loads.Qcs_dis_ls = qcs_d_ls_ahu + qcs_d_ls_aru + Qcs_d_ls_scu

    return tsd
