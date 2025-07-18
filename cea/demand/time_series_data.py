"""
This module defines the `TimeSeriesData` dataclass, which is used to store the time series data for the demand
calculations.
"""
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import numpy.typing as npt
from cea.constants import HOURS_IN_YEAR


class AHUStatus(str, Enum):
    """Enum for AHU (Air Handling Unit) system status values."""
    UNKNOWN = "unknown"
    NO_SYSTEM = "no system"
    ON_OVER_HEATING = "On:over heating"
    ON = "On"
    OFF = "Off"
    SYSTEM_OFF = "system off"


class ARUStatus(str, Enum):
    """Enum for ARU (Air Recirculation Unit) system status values."""
    UNKNOWN = "unknown"
    NO_SYSTEM = "no system"
    OFF = "Off"
    ON = "On"
    ON_T = "On:T"  # Temperature control only
    ON_T_R = "On:T/R"  # Temperature and Recirculation
    ON_R = "On:R"  # Recirculation only
    SYSTEM_OFF = "system off"


class SENStatus(str, Enum):
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
    return np.zeros(HOURS_IN_YEAR) * np.nan


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
    """Ambient temperature [C]"""

    T_ext_wetbulb: npt.NDArray[np.float64]
    """Ambient wetbulb temperature [C]"""

    rh_ext: npt.NDArray[np.float64]
    """Ambient relative humidity [%]"""

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
    """Ventilation per person [lps]"""

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
    """Auxiliary electricity consumption [Wh]"""

    Eaux_hs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Auxiliary electricity consumption for heating systems [Wh]"""

    Eaux_cs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Auxiliary electricity consumption for cooling systems [Wh]"""

    Eaux_ww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Auxiliary electricity consumption for hot water systems [Wh]"""

    Eaux_fw: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Auxiliary electricity consumption for freshwater systems [Wh]"""

    Ehs_lat_aux: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Auxiliary electricity consumption for latent heating [Wh]"""

    Eve: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Auxiliary electricity consumption for ventilation [Wh]"""

    GRID: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand from the grid [Wh]"""

    GRID_a: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand from the grid for appliances [Wh]"""

    GRID_l: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand from the grid for lighting [Wh]"""

    GRID_v: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand from the grid for electric vehicles [Wh]"""

    GRID_ve: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand from the grid for ventilation [Wh]"""

    GRID_data: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand from the grid for data centers [Wh]"""

    GRID_pro: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand from the grid for process [Wh]"""

    GRID_aux: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand from the grid for auxiliary [Wh]"""

    GRID_ww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand from the grid for hot water [Wh]"""

    GRID_hs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand from the grid for heating [Wh]"""

    GRID_cs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand from the grid for cooling [Wh]"""

    GRID_cdata: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand from the grid for data center cooling [Wh]"""

    GRID_cre: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand from the grid for refrigeration [Wh]"""

    PV: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Photovoltaic electricity production [Wh]"""

    Eal: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand for lighting [Wh]"""

    Edata: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand for data centers [Wh]"""

    Epro: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand for process [Wh]"""

    E_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total electricity demand [Wh]"""

    E_ww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand for hot water [Wh]"""

    E_hs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand for heating [Wh]"""

    E_cs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand for cooling [Wh]"""

    E_cre: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand for refrigeration [Wh]"""

    E_cdata: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand for data center cooling [Wh]"""

    Ea: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand for appliances [Wh]"""

    El: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand for lighting [Wh]"""

    Ev: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Electricity demand for ventilation [Wh]"""


@dataclass
class HeatingLoads:
    """
    Data related to heating loads.
    """

    Qhs_sen_rc: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible heating load from RC model [Wh]"""

    Qhs_sen_shu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible heating load from SHU [Wh]"""

    Qhs_sen_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible heating load from AHU [Wh]"""

    Qhs_lat_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Latent heating load from AHU [Wh]"""

    Qhs_sen_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible heating load from ARU [Wh]"""

    Qhs_lat_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Latent heating load from ARU [Wh]"""

    Qhs_sen_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total sensible heating load [Wh]"""

    Qhs_lat_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total latent heating load [Wh]"""

    Qhs_em_ls: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Emission losses from heating systems [Wh]"""

    Qhs_dis_ls: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Distribution losses from heating systems [Wh]"""

    Qhs_sys_shu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Heating load from SHU [Wh]"""

    Qhs_sys_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Heating load from AHU [Wh]"""

    Qhs_sys_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Heating load from ARU [Wh]"""

    DH_hs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """District heating demand for heating [Wh]"""

    Qhs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total heating demand [Wh]"""

    Qhs_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total heating system demand [Wh]"""

    QH_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total heating system demand including hot water [Wh]"""

    DH_ww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """District heating demand for hot water [Wh]"""

    Qww_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Hot water system demand [Wh]"""

    Qww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Hot water demand [Wh]"""

    Qhpro_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Process heating demand [Wh]"""


@dataclass
class CoolingLoads:
    """
    Data related to cooling loads.
    """

    Qcs_sen_rc: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible cooling load from RC model [Wh]"""

    Qcs_sen_scu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible cooling load from SCU [Wh]"""

    Qcs_sen_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible cooling load from AHU [Wh]"""

    Qcs_lat_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Latent cooling load from AHU [Wh]"""

    Qcs_sen_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Sensible cooling load from ARU [Wh]"""

    Qcs_lat_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Latent cooling load from ARU [Wh]"""

    Qcs_sen_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total sensible cooling load [Wh]"""

    Qcs_lat_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total latent cooling load [Wh]"""

    Qcs_em_ls: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Emission losses from cooling systems [Wh]"""

    Qcs_dis_ls: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Distribution losses from cooling systems [Wh]"""

    Qcs_sys_scu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Cooling load from SCU [Wh]"""

    Qcs_sys_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Cooling load from AHU [Wh]"""

    Qcs_sys_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Cooling load from ARU [Wh]"""

    DC_cs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """District cooling demand for cooling [Wh]"""

    Qcs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total cooling demand [Wh]"""

    Qcs_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total cooling system demand [Wh]"""

    QC_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total cooling system demand including refrigeration and data centers [Wh]"""

    DC_cre: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """District cooling demand for refrigeration [Wh]"""

    Qcre_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Refrigeration system demand [Wh]"""

    Qcre: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Refrigeration demand [Wh]"""

    DC_cdata: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """District cooling demand for data centers [Wh]"""

    Qcdata_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Data center system demand [Wh]"""

    Qcdata: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Data center demand [Wh]"""

    Qcpro_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Process cooling demand [Wh]"""


@dataclass
class HeatingSystemTemperatures:
    """
    Data related to heating system temperatures.
    """

    ta_re_hs_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return air temperature from AHU [C]"""

    ta_sup_hs_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply air temperature from AHU [C]"""

    ta_re_hs_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return air temperature from ARU [C]"""

    ta_sup_hs_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply air temperature from ARU [C]"""

    Ths_sys_re_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature from AHU [C]"""

    Ths_sys_re_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature from ARU [C]"""

    Ths_sys_re_shu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature from SHU [C]"""

    Ths_sys_sup_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature to AHU [C]"""

    Ths_sys_sup_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature to ARU [C]"""

    Ths_sys_sup_shu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature to SHU [C]"""

    Ths_sys_sup: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature to heating system [C]"""

    Ths_sys_re: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature from heating system [C]"""

    Tww_sys_sup: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature to hot water system [C]"""

    Tww_sys_re: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature from hot water system [C]"""

    Tww_re: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature from hot water system [C]"""


@dataclass
class HeatingSystemMassFlows:
    """
    Data related to heating system mass flows.
    """

    ma_sup_hs_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply air mass flow from AHU [kg/s]"""

    ma_sup_hs_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply air mass flow from ARU [kg/s]"""

    mcphs_sys_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Water mass flow rate in AHU [kg/s]"""

    mcphs_sys_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Water mass flow rate in ARU [kg/s]"""

    mcphs_sys_shu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Water mass flow rate in SHU [kg/s]"""

    mcphs_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Water mass flow rate in heating system [kg/s]"""

    mcpww_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Water mass flow rate in hot water system [kg/s]"""

    mcptw: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Tap water mass flow rate [kg/s]"""

    mww_kgs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Hot water mass flow rate [kg/s]"""


@dataclass
class CoolingSystemTemperatures:
    """
    Data related to cooling system temperatures.
    """

    ta_re_cs_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return air temperature from AHU [C]"""

    ta_sup_cs_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply air temperature from AHU [C]"""

    ta_re_cs_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return air temperature from ARU [C]"""

    ta_sup_cs_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply air temperature from ARU [C]"""

    Tcs_sys_re_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature from AHU [C]"""

    Tcs_sys_re_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature from ARU [C]"""

    Tcs_sys_re_scu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature from SCU [C]"""

    Tcs_sys_sup_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature to AHU [C]"""

    Tcs_sys_sup_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature to ARU [C]"""

    Tcs_sys_sup_scu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature to SCU [C]"""

    Tcs_sys_sup: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature to cooling system [C]"""

    Tcs_sys_re: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature from cooling system [C]"""

    Tcdata_sys_re: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature from data center cooling system [C]"""

    Tcdata_sys_sup: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature to data center cooling system [C]"""

    Tcre_sys_re: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Return water temperature from refrigeration cooling system [C]"""

    Tcre_sys_sup: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply water temperature to refrigeration cooling system [C]"""


@dataclass
class CoolingSystemMassFlows:
    """
    Data related to cooling system mass flows.
    """

    ma_sup_cs_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply air mass flow from AHU [kg/s]"""

    ma_sup_cs_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Supply air mass flow from ARU [kg/s]"""

    mcpcs_sys_ahu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Water mass flow rate in AHU [kg/s]"""

    mcpcs_sys_aru: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Water mass flow rate in ARU [kg/s]"""

    mcpcs_sys_scu: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Water mass flow rate in SCU [kg/s]"""

    mcpcs_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Water mass flow rate in cooling system [kg/s]"""

    mcpcre_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Water mass flow rate in refrigeration system [kg/s]"""

    mcpcdata_sys: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Water mass flow rate in data center cooling system [kg/s]"""


@dataclass
class RCModelTemperatures:
    """
    Data related to the RC model temperatures.
    """

    T_int: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Internal air temperature [C]"""

    theta_m: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Temperature of the thermal mass [C]"""

    theta_c: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Temperature of the building envelope [C]"""

    theta_o: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Temperature of the opaque surfaces [C]"""

    theta_ve_mech: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Temperature of the mechanical ventilation [C]"""

    ta_hs_set: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Heating setpoint temperature [C]"""

    ta_cs_set: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Cooling setpoint temperature [C]"""


@dataclass
class Moisture:
    """
    Data related to moisture.
    """

    x_int: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Internal air moisture content [kg/kg_dry_air]"""

    x_ve_inf: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Infiltration air moisture content [kg/kg_dry_air]"""

    x_ve_mech: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Mechanical ventilation air moisture content [kg/kg_dry_air]"""

    g_hu_ld: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Humidification load [kg/s]"""

    g_dhu_ld: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Dehumidification load [kg/s]"""

    qh_lat_central: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Latent heat load from central humidification [Wh]"""

    qc_lat_central: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Latent heat load from central dehumidification [Wh]"""


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
    """Solar radiation on the building envelope [Wh/m2]"""

    I_rad: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Infrared radiation on the building envelope [Wh/m2]"""

    I_sol_and_I_rad: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Total radiation on the building envelope [Wh/m2]"""


@dataclass
class ThermalResistance:
    """
    Data related to thermal resistance.
    """

    RSE_wall: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Thermal resistance of the wall [m2K/W]"""

    RSE_roof: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Thermal resistance of the roof [m2K/W]"""

    RSE_win: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Thermal resistance of the window [m2K/W]"""

    RSE_underside: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Thermal resistance of the underside [m2K/W]"""


@dataclass
class FuelSource:
    """
    Data related to fuel sources.
    """

    SOLAR_ww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Solar energy for hot water [Wh]"""

    SOLAR_hs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Solar energy for heating [Wh]"""

    NG_hs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Natural gas for heating [Wh]"""

    COAL_hs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Coal for heating [Wh]"""

    OIL_hs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Oil for heating [Wh]"""

    WOOD_hs: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Wood for heating [Wh]"""

    NG_ww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Natural gas for hot water [Wh]"""

    COAL_ww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Coal for hot water [Wh]"""

    OIL_ww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Oil for hot water [Wh]"""

    WOOD_ww: npt.NDArray[np.float64] = field(default_factory=empty_array)
    """Wood for hot water [Wh]"""


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

    sys_status_ahu: npt.NDArray[np.bytes_] = field(default_factory=empty_char_array)
    """Status of the AHU (AHUStatus values)"""

    sys_status_aru: npt.NDArray[np.bytes_] = field(default_factory=empty_char_array)
    """Status of the ARU (ARUStatus values)"""

    sys_status_sen: npt.NDArray[np.bytes_] = field(default_factory=empty_char_array)
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