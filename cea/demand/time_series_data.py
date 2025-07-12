"""
This module defines the `TimeSeriesData` dataclass, which is used to store the time series data for the demand
calculations.
"""
from typing_extensions import Annotated
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
    arr[:] = AHUStatus.UNKNOWN.value  # Using enum default value
    return arr


@dataclass
class Weather:
    """
    Weather data for the simulation.
    """
    T_ext: Annotated[npt.NDArray[np.float64], "Ambient temperature [C]"]
    T_ext_wetbulb: Annotated[npt.NDArray[np.float64], "Ambient wetbulb temperature [C]"]
    rh_ext: Annotated[npt.NDArray[np.float64], "Ambient relative humidity [%]"]
    T_sky: Annotated[npt.NDArray[np.float64], "Sky temperature [C]"]
    u_wind: Annotated[npt.NDArray[np.float64], "Wind speed [m/s]"]


@dataclass
class People:
    """
    Data related to building occupancy.
    """
    people: Annotated[npt.NDArray[np.float64], "Number of people"] = field(default_factory=empty_array)
    ve_lps: Annotated[npt.NDArray[np.float64], "Ventilation per person [lps]"] = field(default_factory=empty_array)
    Qs: Annotated[npt.NDArray[np.float64], "Sensible heat gain from people [W]"] = field(default_factory=empty_array)
    w_int: Annotated[npt.NDArray[np.float64], "Internal moisture gains [kg/s]"] = field(default_factory=empty_array)


@dataclass
class ElectricalLoads:
    """
    Data related to electrical loads.
    """
    Eaux: Annotated[npt.NDArray[np.float64], "Auxiliary electricity consumption [Wh]"] = field(default_factory=empty_array)
    Eaux_hs: Annotated[npt.NDArray[np.float64], "Auxiliary electricity consumption for heating systems [Wh]"] = field(default_factory=empty_array)
    Eaux_cs: Annotated[npt.NDArray[np.float64], "Auxiliary electricity consumption for cooling systems [Wh]"] = field(default_factory=empty_array)
    Eaux_ww: Annotated[npt.NDArray[np.float64], "Auxiliary electricity consumption for hot water systems [Wh]"] = field(default_factory=empty_array)
    Eaux_fw: Annotated[npt.NDArray[np.float64], "Auxiliary electricity consumption for freshwater systems [Wh]"] = field(default_factory=empty_array)
    Ehs_lat_aux: Annotated[npt.NDArray[np.float64], "Auxiliary electricity consumption for latent heating [Wh]"] = field(default_factory=empty_array)
    Eve: Annotated[npt.NDArray[np.float64], "Auxiliary electricity consumption for ventilation [Wh]"] = field(default_factory=empty_array)
    GRID: Annotated[npt.NDArray[np.float64], "Electricity demand from the grid [Wh]"] = field(default_factory=empty_array)
    GRID_a: Annotated[npt.NDArray[np.float64], "Electricity demand from the grid for appliances [Wh]"] = field(default_factory=empty_array)
    GRID_l: Annotated[npt.NDArray[np.float64], "Electricity demand from the grid for lighting [Wh]"] = field(default_factory=empty_array)
    GRID_v: Annotated[npt.NDArray[np.float64], "Electricity demand from the grid for ventilation [Wh]"] = field(default_factory=empty_array)
    GRID_ve: Annotated[npt.NDArray[np.float64], "Electricity demand from the grid for ventilation [Wh]"] = field(default_factory=empty_array)
    GRID_data: Annotated[npt.NDArray[np.float64], "Electricity demand from the grid for data centers [Wh]"] = field(default_factory=empty_array)
    GRID_pro: Annotated[npt.NDArray[np.float64], "Electricity demand from the grid for process [Wh]"] = field(default_factory=empty_array)
    GRID_aux: Annotated[npt.NDArray[np.float64], "Electricity demand from the grid for auxiliary [Wh]"] = field(default_factory=empty_array)
    GRID_ww: Annotated[npt.NDArray[np.float64], "Electricity demand from the grid for hot water [Wh]"] = field(default_factory=empty_array)
    GRID_hs: Annotated[npt.NDArray[np.float64], "Electricity demand from the grid for heating [Wh]"] = field(default_factory=empty_array)
    GRID_cs: Annotated[npt.NDArray[np.float64], "Electricity demand from the grid for cooling [Wh]"] = field(default_factory=empty_array)
    GRID_cdata: Annotated[npt.NDArray[np.float64], "Electricity demand from the grid for data center cooling [Wh]"] = field(default_factory=empty_array)
    GRID_cre: Annotated[npt.NDArray[np.float64], "Electricity demand from the grid for refrigeration [Wh]"] = field(default_factory=empty_array)
    PV: Annotated[npt.NDArray[np.float64], "Photovoltaic electricity production [Wh]"] = field(default_factory=empty_array)
    Eal: Annotated[npt.NDArray[np.float64], "Electricity demand for lighting [Wh]"] = field(default_factory=empty_array)
    Edata: Annotated[npt.NDArray[np.float64], "Electricity demand for data centers [Wh]"] = field(default_factory=empty_array)
    Epro: Annotated[npt.NDArray[np.float64], "Electricity demand for process [Wh]"] = field(default_factory=empty_array)
    E_sys: Annotated[npt.NDArray[np.float64], "Total electricity demand [Wh]"] = field(default_factory=empty_array)
    E_ww: Annotated[npt.NDArray[np.float64], "Electricity demand for hot water [Wh]"] = field(default_factory=empty_array)
    E_hs: Annotated[npt.NDArray[np.float64], "Electricity demand for heating [Wh]"] = field(default_factory=empty_array)
    E_cs: Annotated[npt.NDArray[np.float64], "Electricity demand for cooling [Wh]"] = field(default_factory=empty_array)
    E_cre: Annotated[npt.NDArray[np.float64], "Electricity demand for refrigeration [Wh]"] = field(default_factory=empty_array)
    E_cdata: Annotated[npt.NDArray[np.float64], "Electricity demand for data center cooling [Wh]"] = field(default_factory=empty_array)
    Ea: Annotated[npt.NDArray[np.float64], "Electricity demand for appliances [Wh]"] = field(default_factory=empty_array)
    El: Annotated[npt.NDArray[np.float64], "Electricity demand for lighting [Wh]"] = field(default_factory=empty_array)
    Ev: Annotated[npt.NDArray[np.float64], "Electricity demand for ventilation [Wh]"] = field(default_factory=empty_array)


@dataclass
class HeatingLoads:
    """
    Data related to heating loads.
    """
    Qhs_sen_rc: Annotated[npt.NDArray[np.float64], "Sensible heating load from RC model [Wh]"] = field(default_factory=empty_array)
    Qhs_sen_shu: Annotated[npt.NDArray[np.float64], "Sensible heating load from SHU [Wh]"] = field(default_factory=empty_array)
    Qhs_sen_ahu: Annotated[npt.NDArray[np.float64], "Sensible heating load from AHU [Wh]"] = field(default_factory=empty_array)
    Qhs_lat_ahu: Annotated[npt.NDArray[np.float64], "Latent heating load from AHU [Wh]"] = field(default_factory=empty_array)
    Qhs_sen_aru: Annotated[npt.NDArray[np.float64], "Sensible heating load from ARU [Wh]"] = field(default_factory=empty_array)
    Qhs_lat_aru: Annotated[npt.NDArray[np.float64], "Latent heating load from ARU [Wh]"] = field(default_factory=empty_array)
    Qhs_sen_sys: Annotated[npt.NDArray[np.float64], "Total sensible heating load [Wh]"] = field(default_factory=empty_array)
    Qhs_lat_sys: Annotated[npt.NDArray[np.float64], "Total latent heating load [Wh]"] = field(default_factory=empty_array)
    Qhs_em_ls: Annotated[npt.NDArray[np.float64], "Emission losses from heating systems [Wh]"] = field(default_factory=empty_array)
    Qhs_dis_ls: Annotated[npt.NDArray[np.float64], "Distribution losses from heating systems [Wh]"] = field(default_factory=empty_array)
    Qhs_sys_shu: Annotated[npt.NDArray[np.float64], "Heating load from SHU [Wh]"] = field(default_factory=empty_array)
    Qhs_sys_ahu: Annotated[npt.NDArray[np.float64], "Heating load from AHU [Wh]"] = field(default_factory=empty_array)
    Qhs_sys_aru: Annotated[npt.NDArray[np.float64], "Heating load from ARU [Wh]"] = field(default_factory=empty_array)
    DH_hs: Annotated[npt.NDArray[np.float64], "District heating demand for heating [Wh]"] = field(default_factory=empty_array)
    Qhs: Annotated[npt.NDArray[np.float64], "Total heating demand [Wh]"] = field(default_factory=empty_array)
    Qhs_sys: Annotated[npt.NDArray[np.float64], "Total heating system demand [Wh]"] = field(default_factory=empty_array)
    QH_sys: Annotated[npt.NDArray[np.float64], "Total heating system demand including hot water [Wh]"] = field(default_factory=empty_array)
    DH_ww: Annotated[npt.NDArray[np.float64], "District heating demand for hot water [Wh]"] = field(default_factory=empty_array)
    Qww_sys: Annotated[npt.NDArray[np.float64], "Hot water system demand [Wh]"] = field(default_factory=empty_array)
    Qww: Annotated[npt.NDArray[np.float64], "Hot water demand [Wh]"] = field(default_factory=empty_array)
    Qhpro_sys: Annotated[npt.NDArray[np.float64], "Process heating demand [Wh]"] = field(default_factory=empty_array)


@dataclass
class CoolingLoads:
    """
    Data related to cooling loads.
    """
    Qcs_sen_rc: Annotated[npt.NDArray[np.float64], "Sensible cooling load from RC model [Wh]"] = field(default_factory=empty_array)
    Qcs_sen_scu: Annotated[npt.NDArray[np.float64], "Sensible cooling load from SCU [Wh]"] = field(default_factory=empty_array)
    Qcs_sen_ahu: Annotated[npt.NDArray[np.float64], "Sensible cooling load from AHU [Wh]"] = field(default_factory=empty_array)
    Qcs_lat_ahu: Annotated[npt.NDArray[np.float64], "Latent cooling load from AHU [Wh]"] = field(default_factory=empty_array)
    Qcs_sen_aru: Annotated[npt.NDArray[np.float64], "Sensible cooling load from ARU [Wh]"] = field(default_factory=empty_array)
    Qcs_lat_aru: Annotated[npt.NDArray[np.float64], "Latent cooling load from ARU [Wh]"] = field(default_factory=empty_array)
    Qcs_sen_sys: Annotated[npt.NDArray[np.float64], "Total sensible cooling load [Wh]"] = field(default_factory=empty_array)
    Qcs_lat_sys: Annotated[npt.NDArray[np.float64], "Total latent cooling load [Wh]"] = field(default_factory=empty_array)
    Qcs_em_ls: Annotated[npt.NDArray[np.float64], "Emission losses from cooling systems [Wh]"] = field(default_factory=empty_array)
    Qcs_dis_ls: Annotated[npt.NDArray[np.float64], "Distribution losses from cooling systems [Wh]"] = field(default_factory=empty_array)
    Qcs_sys_scu: Annotated[npt.NDArray[np.float64], "Cooling load from SCU [Wh]"] = field(default_factory=empty_array)
    Qcs_sys_ahu: Annotated[npt.NDArray[np.float64], "Cooling load from AHU [Wh]"] = field(default_factory=empty_array)
    Qcs_sys_aru: Annotated[npt.NDArray[np.float64], "Cooling load from ARU [Wh]"] = field(default_factory=empty_array)
    DC_cs: Annotated[npt.NDArray[np.float64], "District cooling demand for cooling [Wh]"] = field(default_factory=empty_array)
    Qcs: Annotated[npt.NDArray[np.float64], "Total cooling demand [Wh]"] = field(default_factory=empty_array)
    Qcs_sys: Annotated[npt.NDArray[np.float64], "Total cooling system demand [Wh]"] = field(default_factory=empty_array)
    QC_sys: Annotated[npt.NDArray[np.float64], "Total cooling system demand including refrigeration and data centers [Wh]"] = field(default_factory=empty_array)
    DC_cre: Annotated[npt.NDArray[np.float64], "District cooling demand for refrigeration [Wh]"] = field(default_factory=empty_array)
    Qcre_sys: Annotated[npt.NDArray[np.float64], "Refrigeration system demand [Wh]"] = field(default_factory=empty_array)
    Qcre: Annotated[npt.NDArray[np.float64], "Refrigeration demand [Wh]"] = field(default_factory=empty_array)
    DC_cdata: Annotated[npt.NDArray[np.float64], "District cooling demand for data centers [Wh]"] = field(default_factory=empty_array)
    Qcdata_sys: Annotated[npt.NDArray[np.float64], "Data center system demand [Wh]"] = field(default_factory=empty_array)
    Qcdata: Annotated[npt.NDArray[np.float64], "Data center demand [Wh]"] = field(default_factory=empty_array)
    Qcpro_sys: Annotated[npt.NDArray[np.float64], "Process cooling demand [Wh]"] = field(default_factory=empty_array)


@dataclass
class HeatingSystemTemperatures:
    """
    Data related to heating system temperatures.
    """
    ta_re_hs_ahu: Annotated[npt.NDArray[np.float64], "Return air temperature from AHU [C]"] = field(default_factory=empty_array)
    ta_sup_hs_ahu: Annotated[npt.NDArray[np.float64], "Supply air temperature from AHU [C]"] = field(default_factory=empty_array)
    ta_re_hs_aru: Annotated[npt.NDArray[np.float64], "Return air temperature from ARU [C]"] = field(default_factory=empty_array)
    ta_sup_hs_aru: Annotated[npt.NDArray[np.float64], "Supply air temperature from ARU [C]"] = field(default_factory=empty_array)
    Ths_sys_re_ahu: Annotated[npt.NDArray[np.float64], "Return water temperature from AHU [C]"] = field(default_factory=empty_array)
    Ths_sys_re_aru: Annotated[npt.NDArray[np.float64], "Return water temperature from ARU [C]"] = field(default_factory=empty_array)
    Ths_sys_re_shu: Annotated[npt.NDArray[np.float64], "Return water temperature from SHU [C]"] = field(default_factory=empty_array)
    Ths_sys_sup_ahu: Annotated[npt.NDArray[np.float64], "Supply water temperature to AHU [C]"] = field(default_factory=empty_array)
    Ths_sys_sup_aru: Annotated[npt.NDArray[np.float64], "Supply water temperature to ARU [C]"] = field(default_factory=empty_array)
    Ths_sys_sup_shu: Annotated[npt.NDArray[np.float64], "Supply water temperature to SHU [C]"] = field(default_factory=empty_array)
    Ths_sys_sup: Annotated[npt.NDArray[np.float64], "Supply water temperature to heating system [C]"] = field(default_factory=empty_array)
    Ths_sys_re: Annotated[npt.NDArray[np.float64], "Return water temperature from heating system [C]"] = field(default_factory=empty_array)
    Tww_sys_sup: Annotated[npt.NDArray[np.float64], "Supply water temperature to hot water system [C]"] = field(default_factory=empty_array)
    Tww_sys_re: Annotated[npt.NDArray[np.float64], "Return water temperature from hot water system [C]"] = field(default_factory=empty_array)
    Tww_re: Annotated[npt.NDArray[np.float64], "Return water temperature from hot water system [C]"] = field(default_factory=empty_array)


@dataclass
class HeatingSystemMassFlows:
    """
    Data related to heating system mass flows.
    """
    ma_sup_hs_ahu: Annotated[npt.NDArray[np.float64], "Supply air mass flow from AHU [kg/s]"] = field(default_factory=empty_array)
    ma_sup_hs_aru: Annotated[npt.NDArray[np.float64], "Supply air mass flow from ARU [kg/s]"] = field(default_factory=empty_array)
    mcphs_sys_ahu: Annotated[npt.NDArray[np.float64], "Water mass flow rate in AHU [kg/s]"] = field(default_factory=empty_array)
    mcphs_sys_aru: Annotated[npt.NDArray[np.float64], "Water mass flow rate in ARU [kg/s]"] = field(default_factory=empty_array)
    mcphs_sys_shu: Annotated[npt.NDArray[np.float64], "Water mass flow rate in SHU [kg/s]"] = field(default_factory=empty_array)
    mcphs_sys: Annotated[npt.NDArray[np.float64], "Water mass flow rate in heating system [kg/s]"] = field(default_factory=empty_array)
    mcpww_sys: Annotated[npt.NDArray[np.float64], "Water mass flow rate in hot water system [kg/s]"] = field(default_factory=empty_array)
    mcptw: Annotated[npt.NDArray[np.float64], "Tap water mass flow rate [kg/s]"] = field(default_factory=empty_array)
    mww_kgs: Annotated[npt.NDArray[np.float64], "Hot water mass flow rate [kg/s]"] = field(default_factory=empty_array)


@dataclass
class CoolingSystemTemperatures:
    """
    Data related to cooling system temperatures.
    """
    ta_re_cs_ahu: Annotated[npt.NDArray[np.float64], "Return air temperature from AHU [C]"] = field(default_factory=empty_array)
    ta_sup_cs_ahu: Annotated[npt.NDArray[np.float64], "Supply air temperature from AHU [C]"] = field(default_factory=empty_array)
    ta_re_cs_aru: Annotated[npt.NDArray[np.float64], "Return air temperature from ARU [C]"] = field(default_factory=empty_array)
    ta_sup_cs_aru: Annotated[npt.NDArray[np.float64], "Supply air temperature from ARU [C]"] = field(default_factory=empty_array)
    Tcs_sys_re_ahu: Annotated[npt.NDArray[np.float64], "Return water temperature from AHU [C]"] = field(default_factory=empty_array)
    Tcs_sys_re_aru: Annotated[npt.NDArray[np.float64], "Return water temperature from ARU [C]"] = field(default_factory=empty_array)
    Tcs_sys_re_scu: Annotated[npt.NDArray[np.float64], "Return water temperature from SCU [C]"] = field(default_factory=empty_array)
    Tcs_sys_sup_ahu: Annotated[npt.NDArray[np.float64], "Supply water temperature to AHU [C]"] = field(default_factory=empty_array)
    Tcs_sys_sup_aru: Annotated[npt.NDArray[np.float64], "Supply water temperature to ARU [C]"] = field(default_factory=empty_array)
    Tcs_sys_sup_scu: Annotated[npt.NDArray[np.float64], "Supply water temperature to SCU [C]"] = field(default_factory=empty_array)
    Tcs_sys_sup: Annotated[npt.NDArray[np.float64], "Supply water temperature to cooling system [C]"] = field(default_factory=empty_array)
    Tcs_sys_re: Annotated[npt.NDArray[np.float64], "Return water temperature from cooling system [C]"] = field(default_factory=empty_array)
    Tcdata_sys_re: Annotated[npt.NDArray[np.float64], "Return water temperature from data center cooling system [C]"] = field(default_factory=empty_array)
    Tcdata_sys_sup: Annotated[npt.NDArray[np.float64], "Supply water temperature to data center cooling system [C]"] = field(default_factory=empty_array)
    Tcre_sys_re: Annotated[npt.NDArray[np.float64], "Return water temperature from refrigeration cooling system [C]"] = field(default_factory=empty_array)
    Tcre_sys_sup: Annotated[npt.NDArray[np.float64], "Supply water temperature to refrigeration cooling system [C]"] = field(default_factory=empty_array)


@dataclass
class CoolingSystemMassFlows:
    """
    Data related to cooling system mass flows.
    """
    ma_sup_cs_ahu: Annotated[npt.NDArray[np.float64], "Supply air mass flow from AHU [kg/s]"] = field(default_factory=empty_array)
    ma_sup_cs_aru: Annotated[npt.NDArray[np.float64], "Supply air mass flow from ARU [kg/s]"] = field(default_factory=empty_array)
    mcpcs_sys_ahu: Annotated[npt.NDArray[np.float64], "Water mass flow rate in AHU [kg/s]"] = field(default_factory=empty_array)
    mcpcs_sys_aru: Annotated[npt.NDArray[np.float64], "Water mass flow rate in ARU [kg/s]"] = field(default_factory=empty_array)
    mcpcs_sys_scu: Annotated[npt.NDArray[np.float64], "Water mass flow rate in SCU [kg/s]"] = field(default_factory=empty_array)
    mcpcs_sys: Annotated[npt.NDArray[np.float64], "Water mass flow rate in cooling system [kg/s]"] = field(default_factory=empty_array)
    mcpcre_sys: Annotated[npt.NDArray[np.float64], "Water mass flow rate in refrigeration system [kg/s]"] = field(default_factory=empty_array)
    mcpcdata_sys: Annotated[npt.NDArray[np.float64], "Water mass flow rate in data center cooling system [kg/s]"] = field(default_factory=empty_array)


@dataclass
class RCModelTemperatures:
    """
    Data related to the RC model temperatures.
    """
    T_int: Annotated[npt.NDArray[np.float64], "Internal air temperature [C]"] = field(default_factory=empty_array)
    theta_m: Annotated[npt.NDArray[np.float64], "Temperature of the thermal mass [C]"] = field(default_factory=empty_array)
    theta_c: Annotated[npt.NDArray[np.float64], "Temperature of the building envelope [C]"] = field(default_factory=empty_array)
    theta_o: Annotated[npt.NDArray[np.float64], "Temperature of the opaque surfaces [C]"] = field(default_factory=empty_array)
    theta_ve_mech: Annotated[npt.NDArray[np.float64], "Temperature of the mechanical ventilation [C]"] = field(default_factory=empty_array)
    ta_hs_set: Annotated[npt.NDArray[np.float64], "Heating setpoint temperature [C]"] = field(default_factory=empty_array)
    ta_cs_set: Annotated[npt.NDArray[np.float64], "Cooling setpoint temperature [C]"] = field(default_factory=empty_array)


@dataclass
class Moisture:
    """
    Data related to moisture.
    """
    x_int: Annotated[npt.NDArray[np.float64], "Internal air moisture content [kg/kg_dry_air]"] = field(default_factory=empty_array)
    x_ve_inf: Annotated[npt.NDArray[np.float64], "Infiltration air moisture content [kg/kg_dry_air]"] = field(default_factory=empty_array)
    x_ve_mech: Annotated[npt.NDArray[np.float64], "Mechanical ventilation air moisture content [kg/kg_dry_air]"] = field(default_factory=empty_array)
    g_hu_ld: Annotated[npt.NDArray[np.float64], "Humidification load [kg/s]"] = field(default_factory=empty_array)
    g_dhu_ld: Annotated[npt.NDArray[np.float64], "Dehumidification load [kg/s]"] = field(default_factory=empty_array)
    qh_lat_central: Annotated[npt.NDArray[np.float64], "Latent heat load from central humidification [Wh]"] = field(default_factory=empty_array)
    qc_lat_central: Annotated[npt.NDArray[np.float64], "Latent heat load from central dehumidification [Wh]"] = field(default_factory=empty_array)


@dataclass
class VentilationMassFlows:
    """
    Data related to ventilation mass flows.
    """
    m_ve_window: Annotated[npt.NDArray[np.float64], "Mass flow of window ventilation [kg/s]"] = field(default_factory=empty_array)
    m_ve_mech: Annotated[npt.NDArray[np.float64], "Mass flow of mechanical ventilation [kg/s]"] = field(default_factory=empty_array)
    m_ve_rec: Annotated[npt.NDArray[np.float64], "Mass flow of heat recovery ventilation [kg/s]"] = field(default_factory=empty_array)
    m_ve_inf: Annotated[npt.NDArray[np.float64], "Mass flow of infiltration [kg/s]"] = field(default_factory=empty_array)
    m_ve_required: Annotated[npt.NDArray[np.float64], "Required mass flow of ventilation [kg/s]"] = field(default_factory=empty_array)


@dataclass
class EnergyBalanceDashboard:
    """
    Data related to the energy balance dashboard.
    """
    Q_gain_sen_light: Annotated[npt.NDArray[np.float64], "Sensible heat gain from lighting [Wh]"] = field(default_factory=empty_array)
    Q_gain_sen_app: Annotated[npt.NDArray[np.float64], "Sensible heat gain from appliances [Wh]"] = field(default_factory=empty_array)
    Q_gain_sen_peop: Annotated[npt.NDArray[np.float64], "Sensible heat gain from people [Wh]"] = field(default_factory=empty_array)
    Q_gain_sen_data: Annotated[npt.NDArray[np.float64], "Sensible heat gain from data centers [Wh]"] = field(default_factory=empty_array)
    Q_loss_sen_ref: Annotated[npt.NDArray[np.float64], "Sensible heat loss from refrigeration [Wh]"] = field(default_factory=empty_array)
    Q_gain_sen_wall: Annotated[npt.NDArray[np.float64], "Sensible heat gain from walls [Wh]"] = field(default_factory=empty_array)
    Q_gain_sen_base: Annotated[npt.NDArray[np.float64], "Sensible heat gain from basement [Wh]"] = field(default_factory=empty_array)
    Q_gain_sen_roof: Annotated[npt.NDArray[np.float64], "Sensible heat gain from roof [Wh]"] = field(default_factory=empty_array)
    Q_gain_sen_wind: Annotated[npt.NDArray[np.float64], "Sensible heat gain from windows [Wh]"] = field(default_factory=empty_array)
    Q_gain_sen_vent: Annotated[npt.NDArray[np.float64], "Sensible heat gain from ventilation [Wh]"] = field(default_factory=empty_array)
    Q_gain_lat_peop: Annotated[npt.NDArray[np.float64], "Latent heat gain from people [Wh]"] = field(default_factory=empty_array)
    Q_gain_sen_pro: Annotated[npt.NDArray[np.float64], "Sensible heat gain from process [Wh]"] = field(default_factory=empty_array)


@dataclass
class Solar:
    """
    Data related to solar radiation.
    """
    I_sol: Annotated[npt.NDArray[np.float64], "Solar radiation on the building envelope [Wh/m2]"] = field(default_factory=empty_array)
    I_rad: Annotated[npt.NDArray[np.float64], "Infrared radiation on the building envelope [Wh/m2]"] = field(default_factory=empty_array)
    I_sol_and_I_rad: Annotated[npt.NDArray[np.float64], "Total radiation on the building envelope [Wh/m2]"] = field(default_factory=empty_array)


@dataclass
class ThermalResistance:
    """
    Data related to thermal resistance.
    """
    RSE_wall: Annotated[npt.NDArray[np.float64], "Thermal resistance of the wall [m2K/W]"] = field(default_factory=empty_array)
    RSE_roof: Annotated[npt.NDArray[np.float64], "Thermal resistance of the roof [m2K/W]"] = field(default_factory=empty_array)
    RSE_win: Annotated[npt.NDArray[np.float64], "Thermal resistance of the window [m2K/W]"] = field(default_factory=empty_array)
    RSE_underside: Annotated[npt.NDArray[np.float64], "Thermal resistance of the underside [m2K/W]"] = field(default_factory=empty_array)


@dataclass
class FuelSource:
    """
    Data related to fuel sources.
    """
    SOLAR_ww: Annotated[npt.NDArray[np.float64], "Solar energy for hot water [Wh]"] = field(default_factory=empty_array)
    SOLAR_hs: Annotated[npt.NDArray[np.float64], "Solar energy for heating [Wh]"] = field(default_factory=empty_array)
    NG_hs: Annotated[npt.NDArray[np.float64], "Natural gas for heating [Wh]"] = field(default_factory=empty_array)
    COAL_hs: Annotated[npt.NDArray[np.float64], "Coal for heating [Wh]"] = field(default_factory=empty_array)
    OIL_hs: Annotated[npt.NDArray[np.float64], "Oil for heating [Wh]"] = field(default_factory=empty_array)
    WOOD_hs: Annotated[npt.NDArray[np.float64], "Wood for heating [Wh]"] = field(default_factory=empty_array)
    NG_ww: Annotated[npt.NDArray[np.float64], "Natural gas for hot water [Wh]"] = field(default_factory=empty_array)
    COAL_ww: Annotated[npt.NDArray[np.float64], "Coal for hot water [Wh]"] = field(default_factory=empty_array)
    OIL_ww: Annotated[npt.NDArray[np.float64], "Oil for hot water [Wh]"] = field(default_factory=empty_array)
    WOOD_ww: Annotated[npt.NDArray[np.float64], "Wood for hot water [Wh]"] = field(default_factory=empty_array)


@dataclass
class Water:
    """
    Data related to water consumption.
    """
    vfw_m3perh: Annotated[npt.NDArray[np.float64], "Fresh water consumption [m3/h]"] = field(default_factory=empty_array)
    vww_m3perh: Annotated[npt.NDArray[np.float64], "Hot water consumption [m3/h]"] = field(default_factory=empty_array)


@dataclass
class SystemStatus:
    """
    Data related to system status.
    """
    sys_status_ahu: Annotated[npt.NDArray[np.str_], "Status of the AHU (AHUStatus values)"] = field(default_factory=empty_char_array)
    sys_status_aru: Annotated[npt.NDArray[np.str_], "Status of the ARU (ARUStatus values)"] = field(default_factory=empty_char_array)
    sys_status_sen: Annotated[npt.NDArray[np.str_], "Status of the sensible heat recovery (SENStatus values)"] = field(default_factory=empty_char_array)


@dataclass
class TimeSeriesData:
    """
    A dataclass to store all time series data for the demand calculations.
    """
    weather: Weather
    people: People = field(default_factory=People)
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
    system_status: SystemStatus = field(default_factory=SystemStatus)
    thermal_resistance: ThermalResistance = field(default_factory=ThermalResistance)

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