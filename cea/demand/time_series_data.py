"""
This module defines the `TimeSeriesData` dataclass, which is used to store the time series data for the demand
calculations.
"""
from dataclasses import dataclass, field
from enum import StrEnum
import numpy as np
import numpy.typing as npt
from cea.constants import HOURS_IN_YEAR


class AHUStatus(StrEnum):
    """Enum for AHU (Air Handling Unit) system status values."""
    UNKNOWN = "unknown"
    NO_SYSTEM = "no system"
    ON_OVER_HEATING = "On:over heating"
    ON = "On"
    OFF = "Off"
    SYSTEM_OFF = "system off"


class ARUStatus(StrEnum):
    """Enum for ARU (Air Recirculation Unit) system status values."""
    UNKNOWN = "unknown"
    NO_SYSTEM = "no system"
    OFF = "Off"
    ON = "On"
    ON_T = "On:T"  # Temperature control only
    ON_T_R = "On:T/R"  # Temperature and Recirculation
    ON_R = "On:R"  # Recirculation only
    SYSTEM_OFF = "system off"


class SENStatus(StrEnum):
    """Enum for SEN (Sensible heat recovery) system status values."""
    UNKNOWN = "unknown"
    ON = "On"
    OFF = "Off"
    NO_SYSTEM = "no system"
    SYSTEM_OFF = "system off"


def empty_array():
    """
    Creates an empty numpy array of size HOURS_IN_YEAR, filled with NaNs.
    """
    return np.full(HOURS_IN_YEAR, np.nan)


def empty_char_array():
    """
    Creates an empty numpy chararray of size HOURS_IN_YEAR, filled with 'unknown'.
    
    Uses numpy chararray for consistency with the codebase's numpy-based time series data.
    Memory usage: ~175KB per array (itemsize=20 * 8760 hours), which is acceptable
    for the performance benefits of vectorized operations.
    """
    arr = np.chararray(HOURS_IN_YEAR, itemsize=20)
    arr[:] = AHUStatus.UNKNOWN  # Using enum default value
    return arr


@dataclass
class Weather:
    """
    Weather data for the simulation.
    """

    T_ext: npt.NDArray[np.float64]
    """Dry bulb temperature (ambient temperature) [C]"""

    T_ext_wetbulb: npt.NDArray[np.float64]
    """Wet bulb temperature [C]"""

    rh_ext: npt.NDArray[np.float64]
    """Relative humidity [%]"""

    T_sky: npt.NDArray[np.float64]
    """Sky temperature [C]"""

    u_wind: npt.NDArray[np.float64]
    """Wind speed [m/s]"""


@dataclass
class Occupancy:
    """
    Data related to building occupancy.
    """

    people: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Number of people"""

    ve_lps: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Ventilation rate [l/s]"""

    Qs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible heat gain from people [W]"""

    w_int: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Internal moisture gains [kg/s]"""


@dataclass
class ElectricalLoads:
    """
    Data related to electrical loads.
    """

    Eaux: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use auxiliary electricity consumption [Wh]"""

    Eaux_hs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use auxiliary electricity consumption for heating systems [Wh]"""

    Eaux_cs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use auxiliary electricity consumption for cooling systems [Wh]"""

    Eaux_ww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use auxiliary electricity consumption for domestic hot water systems [Wh]"""

    Eaux_fw: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use auxiliary electricity consumption for fresh water systems [Wh]"""

    Ehs_lat_aux: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use auxiliary electricity consumption for latent heating in heating systems [Wh]"""

    Eve: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use auxiliary electricity consumption for ventilation systems [Wh]"""

    Eal: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use electricity consumption of appliances and lighting [Wh]"""

    Edata: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use electricity consumption of data centers [Wh]"""

    Epro: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use electricity consumption of industrial processes [Wh]"""

    E_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use total electricity consumption [Wh]"""

    E_ww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use electricity consumption of domestic hot water [Wh]"""

    E_hs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use electricity consumption of space heating [Wh]"""

    E_cs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use electricity consumption of space cooling [Wh]"""

    E_cre: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use electricity consumption of refrigeration [Wh]"""

    E_cdata: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use electricity consumption of data center cooling [Wh]"""

    Ea: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use electricity consumption of appliances [Wh]"""

    El: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use electricity consumption of lighting [Wh]"""

    Ev: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use electricity consumption of electric vehicles [Wh]"""

    GRID: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Grid electricity consumption [Wh]"""

    GRID_a: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Grid electricity consumption for appliances [Wh]"""

    GRID_l: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Grid electricity consumption for lighting [Wh]"""

    GRID_v: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Grid electricity consumption for electric vehicles [Wh]"""

    GRID_ve: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Grid electricity consumption for ventilation systems [Wh]"""

    GRID_data: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Grid electricity consumption for data centers [Wh]"""

    GRID_pro: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Grid electricity consumption for industrial processes [Wh]"""

    GRID_aux: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Grid electricity consumption for auxiliary loads [Wh]"""

    GRID_ww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Grid electricity consumption for domestic hot water [Wh]"""

    GRID_hs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Grid electricity consumption for space heating [Wh]"""

    GRID_cs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Grid electricity consumption for space cooling [Wh]"""

    GRID_cdata: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Grid electricity consumption for data center cooling [Wh]"""

    GRID_cre: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Grid electricity consumption for refrigeration [Wh]"""

    PV: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Photovoltaic electricity consumption [Wh]"""



@dataclass
class HeatingLoads:
    """
    Data related to heating loads.
    """

    Qhs_sen_rc: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """RC sensible heating demand [Wh]"""

    Qhs_sen_shu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible heating unit (SHU) sensible heating demand [Wh]"""

    Qhs_sen_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Air handling unit (AHU) sensible heating demand [Wh]"""

    Qhs_sen_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Air recirculation unit (ARU) sensible heating demand [Wh]"""

    Qhs_sen_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total sensible heating demand [Wh]"""

    Qhs_lat_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Air handling unit (AHU) latent heating demand [Wh]"""

    Qhs_lat_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Air recirculation unit (ARU) latent heating demand [Wh]"""

    Qhs_lat_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total latent heating load [Wh]"""

    Qhs_sys_shu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible heating unit (SHU) system heating demand (sensible + latent) [Wh]"""

    Qhs_sys_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Air handling unit (AHU) system heating demand (sensible + latent) [Wh]"""

    Qhs_sys_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Air recirculation unit (ARU) system heating demand (sensible + latent) [Wh]"""

    Qhs_em_ls: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Space heating system emission losses [Wh]"""

    Qhs_dis_ls: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Space heating system distribution losses [Wh]"""

    Qhs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use space heating demand [Wh]"""

    Qhs_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total space heating demand (including emission and distribution losses) [Wh]"""

    Qww_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total heating demand for domestic hot water (including emission and distribution losses) [Wh]"""

    Qww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Domestic hot water heating demand [Wh]"""

    Qhpro_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Process heating demand [Wh]"""

    QH_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total heating demand (including space heating, domestic hot water and process heating) [Wh]"""

    DH_hs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """District heating demand for space heating [Wh]"""

    DH_ww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """District heating demand for domestic hot water [Wh]"""


@dataclass
class CoolingLoads:
    """
    Data related to cooling loads.
    """

    Qcs_sen_rc: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """RC model sensible cooling demand[Wh]"""

    Qcs_sen_scu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible cooling unit (SCU) sensible cooling demand[Wh]"""

    Qcs_sen_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Air handling unit (AHU) sensible cooling demand [Wh]"""

    Qcs_sen_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Air recirculation unit (ARU) sensible cooling demand [Wh]"""

    Qcs_lat_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Air handling unit (AHU) latent cooling demand [Wh]"""

    Qcs_lat_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Air recirculation unit (ARU) latent cooling demand [Wh]"""

    Qcs_sen_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total sensible cooling demand for all systems [Wh]"""

    Qcs_lat_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total latent cooling demand for all systems [Wh]"""

    Qcs_em_ls: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Cooling system emission losses [Wh]"""

    Qcs_dis_ls: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Cooling system distribution losses [Wh]"""

    Qcs_sys_scu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible cooling unit (SCU) system total cooling demand (sensible + latent) [Wh]"""

    Qcs_sys_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Air handling unit (AHU) system total cooling demand (sensible + latent) [Wh]"""

    Qcs_sys_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Air recirculation unit (ARU) system total cooling demand (sensible + latent) [Wh]"""

    Qcs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total space cooling demand [Wh]"""

    Qcs_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total end-use space cooling demand (including distribution and emission losses) [Wh]"""

    QC_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total cooling demand (including refrigeration and data centers) [Wh]"""

    Qcre_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use refrigeration demand [Wh]"""

    Qcre: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Cooling demand for refrigeration [Wh]"""

    DC_cs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """District cooling demand for space cooling [Wh]"""

    DC_cre: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """District cooling demand for refrigeration [Wh]"""

    DC_cdata: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """District cooling demand for data centers [Wh]"""

    Qcdata_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use data center cooling demand [Wh]"""

    Qcdata: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Data center cooling demand [Wh]"""

    Qcpro_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """End-use process cooling demand [Wh]"""


@dataclass
class HeatingSystemTemperatures:
    """
    Data related to heating system temperatures.
    """

    ta_re_hs_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return air temperature from air handling unit (AHU) [C]"""

    ta_sup_hs_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply air temperature from air handling unit (AHU) [C]"""

    ta_re_hs_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return air temperature from air recirculation units (ARU) [C]"""

    ta_sup_hs_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply air temperature from air recirculation units (ARU) [C]"""

    Ths_sys_re_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature from air handling unit (AHU) [C]"""

    Ths_sys_re_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature from air recirculation units (ARU) [C]"""

    Ths_sys_re_shu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature from sensible heating units (SHU) [C]"""

    Ths_sys_sup_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature to air handling unit (AHU) [C]"""

    Ths_sys_sup_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature to air recirculation units (ARU) [C]"""

    Ths_sys_sup_shu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature to sensible heating units (SHU) [C]"""

    Ths_sys_sup: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature from heating system [C]"""

    Ths_sys_re: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature to heating system [C]"""

    Tww_sys_sup: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature from domestic hot water system [C]"""

    Tww_sys_re: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature to domestic hot water system [C]"""

    Tww_re: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature to domestic hot water system [C]"""


@dataclass
class HeatingSystemMassFlows:
    """
    Data related to heating system mass flows.
    """

    ma_sup_hs_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply air mass flow from air handling unit (AHU) [kg/s]"""

    ma_sup_hs_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply air mass flow from air recirculation units (ARU) [kg/s]"""

    mcphs_sys_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Capacity flow rate (mass flow * specific heat capacity) of the hot water delivered to air handling unit (AHU) [kW/C]"""

    mcphs_sys_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Capacity flow rate (mass flow * specific heat capacity) of the hot water delivered to air recirculation units (ARU) [kW/C]"""

    mcphs_sys_shu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Capacity flow rate (mass flow * specific heat capacity) of the hot water delivered to sensible heating units (SHU) [kW/C]"""

    mcphs_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Capacity flow rate (mass flow * specific heat capacity) of the hot water delivered to space heating systems [kW/C]"""

    mcpww_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Capacity flow rate (mass flow * specific heat capacity) of the domestic hot water delivered [kW/C]"""

    mcptw: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Capacity flow rate (mass flow * specific heat capacity) of fresh water [kW/C]"""

    mww_kgs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Mass flow rate of domestic hot water [kg/s]"""


@dataclass
class CoolingSystemTemperatures:
    """
    Data related to cooling system temperatures.
    """

    ta_re_cs_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return air temperature to air handling units (AHU) [C]"""

    ta_sup_cs_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply air temperature from air handling units (AHU) [C]"""

    ta_re_cs_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return air temperature to air recirculation units (ARU) [C]"""

    ta_sup_cs_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply air temperature from air recirculation units (ARU) [C]"""

    Tcs_sys_re_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature to air handling units (AHU) [C]"""

    Tcs_sys_re_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature from air recirculation units (ARU) [C]"""

    Tcs_sys_re_scu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature to sensible cooling units (SCU) [C]"""

    Tcs_sys_sup_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature from air handling units (AHU) [C]"""

    Tcs_sys_sup_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature from air recirculation units (ARU) [C]"""

    Tcs_sys_sup_scu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature from sensible cooling units (SCU) [C]"""

    Tcs_sys_sup: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature from cooling system [C]"""

    Tcs_sys_re: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature to cooling system [C]"""

    Tcdata_sys_re: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature to data center cooling system [C]"""

    Tcdata_sys_sup: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature from data center cooling system [C]"""

    Tcre_sys_re: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature to refrigeration cooling system [C]"""

    Tcre_sys_sup: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature from refrigeration cooling system [C]"""


@dataclass
class CoolingSystemMassFlows:
    """
    Data related to cooling system mass flows.
    """

    ma_sup_cs_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply air mass flow from air handling units (AHU) [kg/s]"""

    ma_sup_cs_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply air mass flow from air recirculation units (ARU) [kg/s]"""

    mcpcs_sys_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Capacity flow rate (mass flow * specific heat capacity) of the chilled water delivered to air handling units (AHU) [kW/C]"""

    mcpcs_sys_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Capacity flow rate (mass flow * specific heat capacity) of the chilled water delivered to air recirculation units (ARU) [kW/C]"""

    mcpcs_sys_scu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Capacity flow rate (mass flow * specific heat capacity) of the chilled water delivered to sensible cooling units (SCU) [kW/C]"""

    mcpcs_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Capacity flow rate (mass flow * specific heat Capacity) of the chilled water delivered to space cooling systems [kW/C]."""

    mcpcre_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Capacity flow rate (mass flow * specific heat Capacity) of the chilled water delivered to refrigeration systems [kW/C]."""

    mcpcdata_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Capacity flow rate (mass flow * specific heat Capacity) of the chilled water delivered to data center cooling systems [kW/C]."""


@dataclass
class RCModelTemperatures:
    """
    Data related to the RC model temperatures.
    """

    T_int: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Internal air temperature [C]"""

    theta_m: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Temperature of the thermal mass node (RC model) [C]"""

    theta_c: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Temperature of the surface node (RC model) [C]"""

    theta_o: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Operative temperature in building (RC model) [C]"""

    theta_ve_mech: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Temperature of the mechanical ventilation [C]"""

    ta_hs_set: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Heating system setpoint air temperature [C]"""

    ta_cs_set: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Cooling system setpoint air temperature [C]"""


@dataclass
class Moisture:
    """
    Data related to moisture.
    """

    x_int: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Moisture content in internal air [kg/kg_dry_air]"""

    x_ve_inf: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Moisture content in air from infiltration [kg/kg_dry_air]"""

    x_ve_mech: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Moisture content in air from mechanical ventilation [kg/kg_dry_air]"""

    g_hu_ld: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Humidification load [kg/s]"""

    g_dhu_ld: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Dehumidification load [kg/s]"""

    qh_lat_central: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Latent heating load from central humidification [Wh]"""

    qc_lat_central: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Latent cooling load from central dehumidification [Wh]"""


@dataclass
class VentilationMassFlows:
    """
    Data related to ventilation mass flows.
    """

    m_ve_window: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Mass flow of window ventilation [kg/s]"""

    m_ve_mech: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Mass flow of mechanical ventilation [kg/s]"""

    m_ve_rec: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Mass flow of heat recovery ventilation [kg/s]"""

    m_ve_inf: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Mass flow of infiltration [kg/s]"""

    m_ve_required: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Required mass flow of ventilation [kg/s]"""


@dataclass
class EnergyBalanceDashboard:
    """
    Data related to the energy balance dashboard.
    """

    Q_gain_sen_light: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible heat gain from lighting [Wh]"""

    Q_gain_sen_app: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible heat gain from appliances [Wh]"""

    Q_gain_sen_peop: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible heat gain from people [Wh]"""

    Q_gain_sen_data: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible heat gain from data centers [Wh]"""

    Q_loss_sen_ref: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible heat loss from refrigeration [Wh]"""

    Q_gain_sen_wall: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible heat gain from walls [Wh]"""

    Q_gain_sen_base: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible heat gain from basement [Wh]"""

    Q_gain_sen_roof: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible heat gain from roof [Wh]"""

    Q_gain_sen_wind: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible heat gain from windows [Wh]"""

    Q_gain_sen_vent: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible heat gain from ventilation [Wh]"""

    Q_gain_lat_peop: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Latent heat gain from people [Wh]"""

    Q_gain_sen_pro: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible heat gain from process [Wh]"""


@dataclass
class Solar:
    """
    Data related to solar radiation.
    """

    I_sol: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Incident solar radiation on the building envelope [Wh/m2]"""

    I_rad: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Vector solar radiation re-irradiated to the sky [Wh/m2]"""

    I_sol_and_I_rad: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Net radiative heat gain on the building envelope [Wh/m2]"""


@dataclass
class ThermalResistance:
    """
    Data related to thermal resistance.
    """

    RSE_wall: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Thermal resistance of the walls [m2K/W]"""

    RSE_roof: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Thermal resistance of the roof [m2K/W]"""

    RSE_win: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Thermal resistance of the windows [m2K/W]"""

    RSE_underside: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Thermal resistance of the underside [m2K/W]"""


@dataclass
class FuelSource:
    """
    Data related to fuel sources.
    """

    SOLAR_ww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Solar thermal energy use for domestic hot water [Wh]"""

    SOLAR_hs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Solar thermal energy use for space heating [Wh]"""

    NG_hs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Natural gas use for space heating [Wh]"""

    COAL_hs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Coal use for space heating [Wh]"""

    OIL_hs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Oil use for space heating [Wh]"""

    WOOD_hs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Wood use for space heating [Wh]"""

    NG_ww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Natural gas use for domestic hot water [Wh]"""

    COAL_ww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Coal use for domestic hot water [Wh]"""

    OIL_ww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Oil use for domestic hot water [Wh]"""

    WOOD_ww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Wood use for domestic hot water [Wh]"""


@dataclass
class Water:
    """
    Data related to water consumption.
    """

    vfw_m3perh: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Fresh water consumption [m3/h]"""

    vww_m3perh: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Hot water consumption [m3/h]"""


# TODO: Check if SystemStatus is used anywhere - comprehensive analysis shows all fields are write-only/unused
@dataclass
class SystemStatus:
    """
    Data related to system status.
    """

    sys_status_ahu: np.chararray = field(default_factory=empty_char_array)
    """Status of the AHU (AHUStatus values)"""

    sys_status_aru: np.chararray = field(default_factory=empty_char_array)
    """Status of the ARU (ARUStatus values)"""

    sys_status_sen: np.chararray = field(default_factory=empty_char_array)
    """Status of the sensible heat recovery (SENStatus values)"""


@dataclass
class TimeSeriesData:
    """
    A dataclass to store all time series data for the demand calculations.
    """
    weather: Weather
    occupancy: Occupancy = field(default_factory=Occupancy)
    electrical_loads: ElectricalLoads = field(default_factory=ElectricalLoads)
    heating_loads: HeatingLoads = field(default_factory=HeatingLoads)
    cooling_loads: CoolingLoads = field(default_factory=CoolingLoads)
    heating_system_temperatures: HeatingSystemTemperatures = field(default_factory=HeatingSystemTemperatures)
    heating_system_mass_flows: HeatingSystemMassFlows = field(default_factory=HeatingSystemMassFlows)
    cooling_system_temperatures: CoolingSystemTemperatures = field(default_factory=CoolingSystemTemperatures)
    cooling_system_mass_flows: CoolingSystemMassFlows = field(default_factory=CoolingSystemMassFlows)
    rc_model_temperatures: RCModelTemperatures = field(default_factory=RCModelTemperatures)
    moisture: Moisture = field(default_factory=Moisture)
    ventilation_mass_flows: VentilationMassFlows = field(default_factory=VentilationMassFlows)
    energy_balance_dashboard: EnergyBalanceDashboard = field(default_factory=EnergyBalanceDashboard)
    solar: Solar = field(default_factory=Solar)
    fuel_source: FuelSource = field(default_factory=FuelSource)
    water: Water = field(default_factory=Water)
    thermal_resistance: ThermalResistance = field(default_factory=ThermalResistance)

    # TODO: Check if SystemStatus is still needed - comprehensive analysis shows all fields are write-only/unused
    system_status: SystemStatus = field(default_factory=SystemStatus)


    def get_load_value(self, load_type: str):
        """
        Get the load value for a specific load type.
        """
        # TODO: This is a temporary solution to get values from the time series data.
        # It should be replaced with a more efficient solution.

        # List of all dataclass objects to search through
        load_objects = [
            self.electrical_loads,
            self.heating_loads,
            self.cooling_loads,

            self.fuel_source,

            # Load plotting variables
            self.energy_balance_dashboard,
            self.solar,
        ]
        
        # Search through each object for the attribute
        for obj in load_objects:
            if hasattr(obj, load_type):
                return getattr(obj, load_type)
        
        raise ValueError(f"Load type '{load_type}' not found in any load properties.")

    def get_mass_flow_value(self, mass_flow_type: str):
        """
        Get the mass flow value for a specific mass flow type.
        """
        load_objects = [
            self.heating_system_mass_flows,
            self.cooling_system_mass_flows,
        ]
        
        for obj in load_objects:
            if hasattr(obj, mass_flow_type):
                return getattr(obj, mass_flow_type)
        
        raise ValueError(f"Mass flow type '{mass_flow_type}' not found in any mass flow properties.")


    def get_temperature_value(self, temperature_type: str):
        """
        Get the temperture value for a specific temperture type.
        """
        load_objects = [
            self.heating_system_temperatures,
            self.cooling_system_temperatures,

            self.rc_model_temperatures,
            self.weather
        ]
        
        for obj in load_objects:
            if hasattr(obj, temperature_type):
                return getattr(obj, temperature_type)
        
        raise ValueError(f"Temperature type '{temperature_type}' not found in any temperature properties.")

    def get_moisture_value(self, moisture_type: str):
        """
        Get the moisture values for a specific moisture measurement type.
        """
        load_objects = [
            self.moisture
        ]

        for obj in load_objects:
            if hasattr(obj, moisture_type):
                return getattr(obj, moisture_type)

        raise ValueError(f"Moisture type '{moisture_type}' not found in any moisture properties.")

    def get_ventilation_mass_flow_value(self, ventilation_type: str):
        """
        Get the ventilation mass flow value for a specific ventilation type.
        """
        load_objects = [
            self.ventilation_mass_flows
        ]

        for obj in load_objects:
            if hasattr(obj, ventilation_type):
                return getattr(obj, ventilation_type)

        raise ValueError(f"Moisture type '{ventilation_type}' not found in any ventilation properties.")

    def get_occupancy_value(self, occupancy_var: str):
        """
        Get the value for a specific occupancy-related variable.
        """
        load_objects = [
            self.occupancy
        ]

        for obj in load_objects:
            if hasattr(obj, occupancy_var):
                return getattr(obj, occupancy_var)

        raise ValueError(f"Moisture type '{occupancy_var}' not found in any occupancy-related properties.")

    def get_solar_value(self, solar_irradiation_type: str):
        """
        Get the solar irradiation value for a specific solar irradiation type.
        """
        load_objects = [
            self.solar
        ]

        for obj in load_objects:
            if hasattr(obj, solar_irradiation_type):
                return getattr(obj, solar_irradiation_type)

        raise ValueError(f"Moisture type '{solar_irradiation_type}' not found in any occupancy-related properties.")