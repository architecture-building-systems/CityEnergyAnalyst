from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

import pandas as pd
from typing_extensions import Annotated


class PipeTransmittanceValues(NamedTuple):
    a: float
    b: float
    c: float

@dataclass(frozen=True)
class BuildingPropertiesRow:
    """
    Encapsulate the data of a single row in the DataSets of BuildingProperties.
    This class meant to be read-only.
    """
    name: str

    geometry: dict
    typology: dict

    comfort: dict
    internal_loads: dict

    envelope: EnvelopeProperties
    hvac: dict
    supply: dict

    building_systems: pd.Series

    rc_model: RCModelProperties
    solar: SolarProperties

    @property
    def year(self) -> int:
        """Return the year of construction of the building."""
        return self.typology['year']

    @classmethod
    def from_dataframes(cls, name: str, geometry: dict, envelope: dict, typology: dict, hvac: dict,
                        rc_model: dict, comfort: dict, internal_loads: dict,
                        solar: dict, supply: dict):
        """Create a new instance of BuildingPropertiesRow - meant to be called by BuildingProperties[building_name].
        Each of the arguments is a pandas Series object representing a row in the corresponding DataFrame."""

        geometry['floor_height'] = cls.get_floor_height(geometry)
        building_systems = _get_properties_building_systems(geometry, hvac, typology['year'])

        return cls(name=name, geometry=geometry, typology=typology,
                   comfort=comfort, internal_loads=internal_loads,
                   envelope= EnvelopeProperties.from_dict(envelope), hvac=hvac, supply=supply,
                   building_systems=building_systems,
                   rc_model=RCModelProperties.from_dict(rc_model), solar=SolarProperties.from_dict(solar))

    @staticmethod
    def get_floor_height(geometry: dict) -> float:
        return geometry['height_ag'] / geometry['floors_ag']


def _get_properties_building_systems(geometry: dict, hvac: dict, age: int) -> pd.Series:
    """
    Method for defining the building system properties, specifically the nominal supply and return temperatures,
    equivalent pipe lengths and transmittance losses. The systems considered include an ahu (air
    handling unit, rsu(air recirculation unit), and scu/shu (sensible cooling / sensible heating unit).
    Note: it is assumed that building with less than a floor and less than 2 floors underground do not require
    heating and cooling, and are not considered when calculating the building system properties.

    :return: building_systems dict containing the following information:

        Pipe Lengths:

            - Lcww_dis: length of hot water piping in the distribution circuit [m]
            - Lsww_dis: length of hot water piping in the circulation circuit [m]
            - Lvww_dis: length of hot water piping in the distribution circuit in the basement (?) [m]
            - Lvww_c: length of piping in the heating system circulation circuit in the basement (?) [m]
            - Lv: length vertical lines (heating and cooling distribution) [m]

        Heating Supply Temperatures:

            - Ths_sup_ahu_0: heating supply temperature from AHU (C)
            - Ths_sup_aru_0: heating supply temperature from ARU (C)
            - Ths_sup_shu_0: heating supply temperature from SHU (C)

        Heating Return Temperatures:

            - Ths_re_ahu_0: heating return temperature to AHU (C)
            - Ths_re_aru_0: heating return temperature to ARU (C)
            - Ths_re_shu_0: heating return temperature to SHU (C)

        Cooling Supply Temperatures:

            - Tcs_sup_ahu_0: cooling supply temperature from AHU (C)
            - Tcs_sup_aru_0: cooling supply temperature from ARU (C)
            - Tcs_sup_scu_0: cooling supply temperature from SCU (C)

        Cooling Return Temperatures:

            - Tcs_re_ahu_0: cooling return temperature to AHU (C)
            - Tcs_re_aru_0: cooling return temperature to ARU (C)
            - Tcs_re_scu_0: cooling return temperature to SCU (C)

        Domestic hot water supply temperature??:

            - Tww_sup_0: domestic hot water supply temperature (C)

        Thermal losses in pipes:

            - Y: Linear trasmissivity coefficient of piping depending on year of construction [W/m.K]

        Form Factor Adjustment:

            - fforma: form factor (comparison between real and rectangular surface)

    :rtype: dict


    """
    # geometry properties.

    Ll = geometry['Blength']
    Lw = geometry['Bwidth']
    nf_ag = geometry['floors_ag']
    nf_bg = geometry['floors_bg']
    phi_pipes = _calculate_pipe_transmittance_values(age)

    # nominal temperatures
    Ths_sup_ahu_0 = float(hvac['Tshs0_ahu_C'])
    Ths_re_ahu_0 = float(Ths_sup_ahu_0 - hvac['dThs0_ahu_C'])
    Ths_sup_aru_0 = float(hvac['Tshs0_aru_C'])
    Ths_re_aru_0 = float(Ths_sup_aru_0 - hvac['dThs0_aru_C'])
    Ths_sup_shu_0 = float(hvac['Tshs0_shu_C'])
    Ths_re_shu_0 = float(Ths_sup_shu_0 - hvac['dThs0_shu_C'])
    Tcs_sup_ahu_0 = hvac['Tscs0_ahu_C']
    Tcs_re_ahu_0 = Tcs_sup_ahu_0 + hvac['dTcs0_ahu_C']
    Tcs_sup_aru_0 = hvac['Tscs0_aru_C']
    Tcs_re_aru_0 = Tcs_sup_aru_0 + hvac['dTcs0_aru_C']
    Tcs_sup_scu_0 = hvac['Tscs0_scu_C']
    Tcs_re_scu_0 = Tcs_sup_scu_0 + hvac['dTcs0_scu_C']

    Tww_sup_0 = hvac['Tsww0_C']
    # Identification of equivalent lengths
    # FIXME: Explain and move magic numbers to constants file e.g. 0.0325, 0.0125, 0.0625, etc.
    fforma = _calc_form(geometry)  # factor form comparison real surface and rectangular
    Lv = (2 * Ll + 0.0325 * Ll * Lw + 6) * fforma  # length vertical lines
    if nf_ag < 2 and nf_bg < 2:  # it is assumed that building with less than a floor and less than 2 floors udnerground do not have
        Lcww_dis = 0
        Lvww_c = 0
    else:
        Lcww_dis = 2 * (
                Ll + 2.5 + nf_ag * geometry['floor_height']) * fforma  # length hot water piping circulation circuit
        Lvww_c = (2 * Ll + 0.0125 * Ll * Lw) * fforma  # length piping heating system circulation circuit

    Lsww_dis = 0.038 * Ll * Lw * nf_ag * geometry[
        'floor_height'] * fforma  # length hot water piping distribution circuit
    Lvww_dis = (Ll + 0.0625 * Ll * Lw) * fforma  # length piping heating system distribution circuit

    building_systems = pd.Series({'Lcww_dis': Lcww_dis,
                                  'Lsww_dis': Lsww_dis,
                                  'Lv': Lv,
                                  'Lvww_c': Lvww_c,
                                  'Lvww_dis': Lvww_dis,
                                  'Ths_sup_ahu_0': Ths_sup_ahu_0,
                                  'Ths_re_ahu_0': Ths_re_ahu_0,
                                  'Ths_sup_aru_0': Ths_sup_aru_0,
                                  'Ths_re_aru_0': Ths_re_aru_0,
                                  'Ths_sup_shu_0': Ths_sup_shu_0,
                                  'Ths_re_shu_0': Ths_re_shu_0,
                                  'Tcs_sup_ahu_0': Tcs_sup_ahu_0,
                                  'Tcs_re_ahu_0': Tcs_re_ahu_0,
                                  'Tcs_sup_aru_0': Tcs_sup_aru_0,
                                  'Tcs_re_aru_0': Tcs_re_aru_0,
                                  'Tcs_sup_scu_0': Tcs_sup_scu_0,
                                  'Tcs_re_scu_0': Tcs_re_scu_0,
                                  'Tww_sup_0': Tww_sup_0,
                                  'Y': phi_pipes,
                                  'fforma': fforma})
    return building_systems


def _calculate_pipe_transmittance_values(building_year: int) -> PipeTransmittanceValues:
    """linear transmissivity coefficients of piping W/(m.K)"""
    if building_year >= 1995:
        phi_pipes = [0.2, 0.3, 0.3]
    # elif 1985 <= self.age['built'] < 1995 and self.age['HVAC'] == 0:
    elif 1985 <= building_year < 1995:
        phi_pipes = [0.3, 0.4, 0.4]
    else:
        phi_pipes = [0.4, 0.4, 0.4]
    return PipeTransmittanceValues(*phi_pipes)


def _calc_form(geometry: dict):
    factor = geometry['footprint'] / (geometry['Bwidth'] * geometry['Blength'])
    return factor


@dataclass(frozen=True)
class EnvelopeProperties:
    # Construction properties
    Cm_Af: Annotated[float, "Internal heat capacity [J/m2K]"]

    # Leakage properties
    n50: Annotated[float, "Air tightness at 50 Pa [1/h]"]

    # Roof properties
    e_roof: Annotated[float, "Emissivity of roof [-]"]
    a_roof: Annotated[float, "Solar absorptance of roof [-]"]
    U_roof: Annotated[float, "U-value of roof [W/m2K]"]

    # Wall properties
    e_wall: Annotated[float, "Emissivity of wall [-]"]
    a_wall: Annotated[float, "Solar absorptance of wall [-]"]
    U_wall: Annotated[float, "U-value of wall [W/m2K]"]

    # Window properties
    e_win: Annotated[float, "Emissivity of windows [-]"]
    G_win: Annotated[float, "Solar heat gain coefficient of windows [-]"]
    U_win: Annotated[float, "U-value of windows [W/m2K]"]

    # Floor properties
    U_base: Annotated[float, "U-value of floor [W/m2K]"]

    # Shading properties
    rf_sh: Annotated[float, "Roof shading factor [-]"]

    # Additional properties
    e_underside: Annotated[float, "Emissivity of underside [-]"]

    # Derived fields
    A_op: Annotated[float, "Opaque area above ground [m2]"]
    win_wall: Annotated[float, "Window to wall ratio [-]"]

    # FIXME: These fields does not neccessarily describe the building envelope
    Es: Annotated[float, "Heated/cooled share [-]"]
    occupied_bg: Annotated[float, "Basement occupation factor [-]"]

    @classmethod
    def from_dict(cls, envelope: dict):
        # Calculate derived fields
        A_op = envelope['Awin_ag'] + envelope['Awall_ag']
        envelope['A_op'] = A_op
        envelope['win_wall'] = envelope['Awin_ag'] / A_op if A_op != 0 else 0.0
        envelope['e_underside'] = 0.0  # dummy value for emissivity of underside

        field_names = cls.__annotations__.keys()
        filtered_envelope = {k: envelope[k] for k in field_names if k in envelope}
        return cls(**filtered_envelope)


@dataclass(frozen=True)
class SolarProperties:
    I_sol: Annotated[pd.Series, "Isolated solar [kWh]"]

    @classmethod
    def from_dict(cls, solar: dict):
        return cls(I_sol=solar['I_sol'])


@dataclass(frozen=True)
class RCModelProperties:
    # --- Area properties ---
    Atot: Annotated[float, "Area of all surfaces facing the building zone [m2]"]
    Af: Annotated[float, "Conditioned floor area (areas that are heated or cooled) [m2]"]
    GFA_m2: Annotated[float, "Gross floor area [m2]"]
    footprint: Annotated[float, "Building footprint area [m2]"]
    Aroof: Annotated[float, "Roof area [m2]"]
    Aunderside: Annotated[float, "Underside area [m2]"]
    Awall_ag: Annotated[float, "Above ground wall area [m2]"]
    Awin_ag: Annotated[float, "Above ground window area [m2]"]
    Am: Annotated[float, "Effective mass area [m2]"]
    Aef: Annotated[float, "Electrified area (share of gross floor area that is electrified) [m2]"]
    Aocc: Annotated[float, "Occupied floor area [m2]"]
    Aop_bg: Annotated[float, "Area of opaque surfaces below ground [m2]"]
    Hs_ag: Annotated[float, "Share of above-ground gross floor area that is conditioned [m2/m2]"]

    # --- Thermal properties ---
    Cm: Annotated[float, "Internal heat capacity [J/K]"]
    Hg: Annotated[float, "Steady-state thermal transmission coefficient to the ground [W/K]"]
    HD: Annotated[float, "Direct thermal transmission coefficient to the external environment [W/K]"]

    # --- Heat transfer coefficients ---
    Htr_is: Annotated[float, "Thermal transmission coefficient between air and surface nodes in RC-model [W/K]"]
    Htr_em: Annotated[float, "Thermal transmission coefficient between exterior and thermal mass nodes in RC-model [W/K]"]
    Htr_ms: Annotated[float, "Thermal transmission coefficient between surface and thermal mass nodes in RC-model [W/K]"]
    Htr_op: Annotated[float, "Thermal transmission coefficient for opaque surfaces in RC-model [W/K]"]
    Htr_w: Annotated[float, "Thermal transmission coefficient for windows in RC-model [W/K]"]

    # FIXME: Decide if these fields should be in envelope or rc_model
    # --- U-values (Duplicated Envelope properties) ---
    U_wall: Annotated[float, "U-value of wall [W/m2K]"]
    U_roof: Annotated[float, "U-value of roof [W/m2K]"]
    U_win: Annotated[float, "U-value of windows [W/m2K]"]
    U_base: Annotated[float, "U-value of floor [W/m2K]"]

    @classmethod
    def from_dict(cls, rc_model: dict):
        field_names = cls.__annotations__.keys()
        filtered_envelope = {k: rc_model[k] for k in field_names if k in rc_model}
        return cls(**filtered_envelope)