from __future__ import annotations
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import numpy.typing as npt

    from cea.demand.building_properties.building_properties_row import BuildingPropertiesRow
    from cea.demand.time_series_data import TimeSeriesData

# constants in standards
P_ATM = 101325  # (Pa) atmospheric pressure [section 6.3.6 in ISO 52016-1:2017]
RHO_A = 1.204  # (kg/m3) density of air at 20°C and 0m height [section 6.3.6 in ISO 52016-1:2017]
H_WE = 2466e3  # (J/kg) Latent heat of vaporization of water [section 6.3.6 in ISO 52016-1:2017]

# constants
DELTA_T = 3600  # (s/h)


def calc_humidification_moisture_load(bpr: BuildingPropertiesRow, tsd: TimeSeriesData, t: int) -> float:
    """
    (71) in ISO 52016-1:2017

    Gabriel Happle, Feb. 2018

    :param bpr: Building Properties
    :type bpr: BuildingPropertiesRow
    :param tsd: Time series data of building
    :type tsd: cea.demand.time_series_data.TimeSeriesData
    :param t: time step / hour of the year
    :type t: int
    :return: humidification load (kg/s)
    :rtype: float
    """

    # get air flows
    m_ve_mech = tsd.ventilation_mass_flows.m_ve_mech[t]
    m_ve_inf = tsd.ventilation_mass_flows.m_ve_inf[t] + tsd.ventilation_mass_flows.m_ve_window[t]
    x_ve_mech = tsd.moisture.x_ve_mech[t]
    x_ve_inf = tsd.moisture.x_ve_inf[t]

    # get set points
    x_set_min = calc_min_moisture_set_point(bpr, tsd, t)

    # get internal gains
    g_int = tsd.occupancy.w_int[t]  # gains from occupancy

    # zone humidity at previous time step
    x_int_a_prev = tsd.moisture.x_int[t - 1]

    # zone volume
    vol_int_a = bpr.rc_model.Af * bpr.geometry['floor_height']

    # calculate
    g_hu_ld = m_ve_mech * (x_set_min - x_ve_mech) + m_ve_inf * (x_set_min - x_ve_inf) - g_int + \
                    (RHO_A * vol_int_a) / DELTA_T * (x_set_min - x_int_a_prev)

    g_hu_ld = np.max([g_hu_ld, 0])

    return g_hu_ld


def calc_dehumidification_moisture_load(bpr: BuildingPropertiesRow, tsd: TimeSeriesData, t: int) -> float:
    """
    (72) in ISO 52016-1:2017

    Gabriel Happle, Feb. 2018

    :param bpr: Building Properties
    :type bpr: BuildingPropertiesRow
    :param tsd: Time series data of building
    :type tsd: cea.demand.time_series_data.TimeSeriesData
    :param t: time step / hour of the year
    :type t: int
    :return: dehumidification load (kg/s)
    :rtype: float
    """

    # get air flows
    m_ve_mech = tsd.ventilation_mass_flows.m_ve_mech[t]
    m_ve_inf = tsd.ventilation_mass_flows.m_ve_inf[t] + tsd.ventilation_mass_flows.m_ve_window[t]
    x_ve_mech = tsd.moisture.x_ve_mech[t]
    x_ve_inf = tsd.moisture.x_ve_inf[t]

    # get set points
    x_set_max = calc_max_moisture_set_point(bpr, tsd, t)

    # get internal gains
    g_int = tsd.occupancy.w_int[t]  # gains from occupancy

    # zone humidity at previous time step
    x_int_a_prev = tsd.moisture.x_int[t-1]

    # zone volume
    vol_int_a = bpr.rc_model.Af * bpr.geometry['floor_height']

    # calculate
    g_dhu_ld = -m_ve_mech * (x_set_max - x_ve_mech) - m_ve_inf * (x_set_max - x_ve_inf) + g_int - \
                     (RHO_A * vol_int_a) / DELTA_T * (x_set_max - x_int_a_prev)

    g_dhu_ld = np.max([g_dhu_ld, 0])

    # dehumidification load is positive value according to standard
    return g_dhu_ld


def calc_min_moisture_set_point(bpr: BuildingPropertiesRow, tsd: TimeSeriesData, t: int) -> float:
    """
    (75) in ISO 52016-1:2017

    Gabriel Happle, Feb. 2018

    :param bpr: Building Properties
    :type bpr: BuildingPropertiesRow
    :param tsd: Time series data of building
    :type tsd: cea.demand.time_series_data.TimeSeriesData
    :param t: time step / hour of the year
    :type t: int
    :return: min moisture set point (kg/kg_dry_air)
    :rtype: float
    """

    # from bpr get set point for humidification
    phi_int_set_hu = bpr.comfort['RH_min_pc']

    t_int = tsd.rc_model_temperatures.T_int[t]

    p_sat_int = calc_saturation_pressure(t_int)

    x_set_min = 0.622 * (phi_int_set_hu / 100 * p_sat_int) / (
        P_ATM - phi_int_set_hu / 100 * p_sat_int)

    return x_set_min


def calc_max_moisture_set_point(bpr: BuildingPropertiesRow, tsd: TimeSeriesData, t: int) -> float:
    """
    (76) in ISO 52016-1:2017

    Gabriel Happle, Feb. 2018

    :param bpr: Building Properties
    :type bpr: BuildingPropertiesRow
    :param tsd: Time series data of building
    :type tsd: cea.demand.time_series_data.TimeSeriesData
    :param t: time step / hour of the year
    :type t: int
    :return: max moisture set point (kg/kg_dry_air)
    :rtype: float
    """

    # from bpr get set point for humidification
    phi_int_set_dhu = bpr.comfort['RH_max_pc']

    t_int = tsd.rc_model_temperatures.T_int[t]

    p_sat_int = calc_saturation_pressure(t_int)

    x_set_max = 0.622 * (phi_int_set_dhu / 100 * p_sat_int) / (
        P_ATM - phi_int_set_dhu / 100 * p_sat_int)

    return x_set_max


def calc_saturation_pressure(theta: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    """
    (77) in ISO 52016-1:2017

    Gabriel Happle, Feb. 2018

    :param theta: air temperature (C)
    :type theta: float
    :return: saturation pressure (Pa)
    """

    p_sat_int = 611.2 * np.exp(17.62 * theta / (243.12 + theta))

    return p_sat_int


def calc_required_moisture_mech_vent_hu(tsd: TimeSeriesData, t: int) -> npt.NDArray[np.float64]:
    # (78) in ISO 52016-1:2017

    x_a_e = tsd.moisture.x_ve_mech[t]  # external air moisture content (after possible HEX)
    g_hu_ld = tsd.moisture.g_hu_ld[t]
    m_ve_mech = tsd.ventilation_mass_flows.m_ve_mech[t]

    x_a_sup_hu_req = x_a_e + g_hu_ld / m_ve_mech

    return x_a_sup_hu_req


def calc_required_moisture_mech_vent_dhu(tsd: TimeSeriesData, t: int) -> npt.NDArray[np.float64]:
    # (79) in ISO 52016-1:2017

    x_a_e = tsd.moisture.x_ve_mech[t]  # external air moisture content (after possible HEX)
    g_dhu_ld = tsd.moisture.g_dhu_ld[t]
    m_ve_mech = tsd.ventilation_mass_flows.m_ve_mech[t]

    x_a_sup_dhu_req = x_a_e - g_dhu_ld / m_ve_mech

    return x_a_sup_dhu_req


def calc_moisture_in_zone_central(bpr: BuildingPropertiesRow, tsd: TimeSeriesData, t: int):
    """


    Gabriel Happle, Feb. 2018

    :param bpr: Building Properties
    :type bpr: BuildingPropertiesRow
    :param tsd: Time series data of building
    :type tsd: cea.demand.time_series_data.TimeSeriesData
    :param t: time step / hour of the year
    :type t: int
    :return: dehumidification load (kg/s)
    :rtype: float
    """

    # (80) in ISO 52016-1:2017

    # zone volume
    vol_int_a_ztc = bpr.rc_model.Af * bpr.geometry['floor_height']

    # get air flows
    m_ve_mech = tsd.ventilation_mass_flows.m_ve_mech[t]
    m_ve_inf = tsd.ventilation_mass_flows.m_ve_inf[t] + tsd.ventilation_mass_flows.m_ve_window[t]
    x_ve_mech = tsd.moisture.x_ve_mech[t]
    x_ve_mech_sup = tsd.moisture.x_ve_mech[t] # TODO: THAT IS FIXED! get supply moisture >= required moisture ----> can not be lower than dew point moisture at 6C
    x_ve_inf = tsd.moisture.x_ve_inf[t]

    # get internal gains
    g_int_ztc_t = tsd.occupancy.w_int[t]  # gains from occupancy

    # zone humidity at previous time step
    x_int_a_ztc_t_1 = tsd.moisture.x_int[t - 1] if not np.isnan(tsd.moisture.x_int[t - 1]) else\
        convert_rh_to_moisture_content(tsd.weather.rh_ext[t-1], tsd.weather.T_ext[t - 1])

    # get (de)humidification loads
    # g_hu_ld_ztc_t = tsd.moisture.g_hu_ld[t]
    # g_dhu_ld_ztc_t = tsd.moisture.g_dhu_ld[t]

    # sum ventilation moisture + (de)humidification
    x_int_a = (m_ve_mech * x_ve_mech_sup + m_ve_inf * x_ve_inf + g_int_ztc_t + (
        RHO_A * vol_int_a_ztc) / DELTA_T * x_int_a_ztc_t_1) / \
              ((m_ve_mech + m_ve_inf) + (RHO_A * vol_int_a_ztc) / DELTA_T)

    # (81) in ISO 52016-1:2017
    g_hu_dhu_central = m_ve_mech * (x_ve_mech_sup - x_ve_mech)

    g_hu_central = np.max(g_hu_dhu_central, 0)
    g_dhu_central = np.max(-g_hu_dhu_central, 0)

    # (82) in ISO 52016-1:2017
    phi_hu_ld_central = H_WE * g_hu_central

    # (83) in ISO 52016-1:2017
    phi_dhu_ld_central = H_WE * g_dhu_central

    # set results
    tsd.moisture.x_int[t] = x_int_a
    tsd.moisture.qh_lat_central[t] = phi_hu_ld_central
    tsd.moisture.qc_lat_central[t] = phi_dhu_ld_central

    return


def calc_moisture_content_in_zone_local(bpr: BuildingPropertiesRow, tsd: TimeSeriesData, t: int):
    """
    (84) in ISO 52016-1:2017

    Gabriel Happle, Feb. 2018

    :param bpr: Building Properties
    :type bpr: BuildingPropertiesRow
    :param tsd: Time series data of building
    :type tsd: cea.demand.time_series_data.TimeSeriesData
    :param t: time step / hour of the year
    :type t: int
    :return: writes zone internal moisture content to tsd
    :rtype: None
    """

    # zone volume
    vol_int_a_ztc = bpr.rc_model.Af * bpr.geometry['floor_height']

    # get air flows
    m_ve_mech = tsd.ventilation_mass_flows.m_ve_mech[t]
    m_ve_inf = tsd.ventilation_mass_flows.m_ve_inf[t] + tsd.ventilation_mass_flows.m_ve_window[t]
    x_ve_mech = tsd.moisture.x_ve_mech[t]
    x_ve_inf = tsd.moisture.x_ve_inf[t]

    # get internal gains
    g_int_ztc_t = tsd.occupancy.w_int[t]  # gains from occupancy

    # zone humidity at previous time step
    x_int_a_ztc_t_1 = tsd.moisture.x_int[t-1]

    # get (de)humidification loads
    g_hu_ld_ztc_t = tsd.moisture.g_hu_ld[t]
    g_dhu_ld_ztc_t = tsd.moisture.g_dhu_ld[t]

    # sum ventilation moisture + (de)humidification
    x_int_a_t = (m_ve_mech * x_ve_mech + m_ve_inf * x_ve_inf +
                 g_hu_ld_ztc_t + g_dhu_ld_ztc_t + g_int_ztc_t + (
                     RHO_A * vol_int_a_ztc) / DELTA_T * x_int_a_ztc_t_1) / \
                ((m_ve_mech + m_ve_inf) + (RHO_A * vol_int_a_ztc) / DELTA_T)

    if x_int_a_t < 0:
        raise Exception("Bug in moisture balance in zone. Negative moisture content detected.")

    tsd.moisture.x_int[t] = x_int_a_t
    return


def total_moisture_in_zone(bpr: BuildingPropertiesRow, x_int: float) -> float:
    """
    calculate total mass of moisture in zone

    Gabriel Happle, Feb. 2018

    :param bpr: Building Properties
    :type bpr: BuildingPropertiesRow
    :param x_int: moisture content in zone (kg/kg_dry_air)
    :type x_int: float
    :return: total mass of moisture in zone (kg)
    :rtype: float
    """

    # air mass in zone
    m_air_zone = bpr.rc_model.Af * bpr.geometry['floor_height'] * RHO_A

    # return total mass of water in kg
    return m_air_zone * x_int


def convert_rh_to_moisture_content(rh: npt.NDArray[np.float64], theta: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    """
    convert relative humidity to moisture content

    Gabriel Happle, Feb. 2018

    :param rh: relative humidity (%)
    :type rh: float
    :param theta: temperature (C)
    :type theta: float
    :return: moisture content (kg/kg_dry_air)
    :rtype: float
    """

    p_sat = calc_saturation_pressure(theta)

    x = 0.622 * rh/100 * p_sat / P_ATM

    return x


def calc_moisture_content_airflows(tsd: TimeSeriesData, t: int):
    """
    convert relative humidity of ventilation airflows to moisture content

    Gabriel Happle, Feb. 2018

    :param tsd: Time series data of building
    :type tsd: cea.demand.time_series_data.TimeSeriesData
    :param t: time step / hour of the year
    :type t: int
    :return: adds moisture content of ventilation air flows to tsd
    :rtype: None
    """

    rh_ext = tsd.weather.rh_ext[t]
    theta_ext = tsd.weather.T_ext[t]

    tsd.moisture.x_ve_inf[t] = convert_rh_to_moisture_content(rh_ext, theta_ext)
    tsd.moisture.x_ve_mech[t] = convert_rh_to_moisture_content(rh_ext, theta_ext)

    return


def calc_Qgain_lat(tsd: TimeSeriesData, X_gh: npt.NDArray[np.float64]) -> TimeSeriesData:
    # TODO: Documentation
    # Refactored from CalcThermalLoads

    # calc yearly humidity gains based on occupancy schedule and specific humidity gains for each occupancy type in the
    KG_PER_GRAM = 0.001
    HOURS_PER_SEC = 1 / 3600

    tsd.occupancy.w_int = X_gh * KG_PER_GRAM * HOURS_PER_SEC # kg/s
    tsd.energy_balance_dashboard.Q_gain_lat_peop = tsd.occupancy.w_int * H_WE # (J/s = W)

    return tsd
