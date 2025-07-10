from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from typing_extensions import Annotated


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

    rc_model: dict
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
                   rc_model=rc_model, solar=SolarProperties.from_dict(solar))

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

            - Lcww_dis: length of hot water piping in the distribution circuit (????) [m]
            - Lsww_dis: length of hot water piping in the distribution circuit (????) [m]
            - Lvww_dis: length of hot water piping in the distribution circuit (?????) [m]
            - Lvww_c: length of piping in the heating system circulation circuit (ventilated/recirc?) [m]
            - Lv: length vertical lines [m]

        Heating Supply Temperatures:

            - Ths_sup_ahu_0: heating supply temperature for AHU (C)
            - Ths_sup_aru_0: heating supply temperature for ARU (C)
            - Ths_sup_shu_0: heating supply temperature for SHU (C)

        Heating Return Temperatures:

            - Ths_re_ahu_0: heating return temperature for AHU (C)
            - Ths_re_aru_0: heating return temperature for ARU (C)
            - Ths_re_shu_0: heating return temperature for SHU (C)

        Cooling Supply Temperatures:

            - Tcs_sup_ahu_0: cooling supply temperature for AHU (C)
            - Tcs_sup_aru_0: cooling supply temperature for ARU (C)
            - Tcs_sup_scu_0: cooling supply temperature for SCU (C)

        Cooling Return Temperatures:

            - Tcs_re_ahu_0: cooling return temperature for AHU (C)
            - Tcs_re_aru_0: cooling return temperature for ARU (C)
            - Tcs_re_scu_0: cooling return temperature for SCU (C)

        Water supply temperature??:

            - Tww_sup_0: ?????

        Thermal losses in pipes:

            - Y: Linear trasmissivity coefficients of piping depending on year of construction [W/m.K]

        Form Factor Adjustment:

            - fforma: form factor comparison between real surface and rectangular ???

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


def _calculate_pipe_transmittance_values(building_year: int) -> list[float]:
    """linear trasmissivity coefficients of piping W/(m.K)"""
    if building_year >= 1995:
        phi_pipes = [0.2, 0.3, 0.3]
    # elif 1985 <= self.age['built'] < 1995 and self.age['HVAC'] == 0:
    elif 1985 <= building_year < 1995:
        phi_pipes = [0.3, 0.4, 0.4]
    else:
        phi_pipes = [0.4, 0.4, 0.4]
    return phi_pipes


def _calc_form(geometry: dict):
    factor = geometry['footprint'] / (geometry['Bwidth'] * geometry['Blength'])
    return factor


@dataclass(frozen=True)
class EnvelopeProperties:
    A_op: Annotated[float, "Opaque area above ground [m2]"]
    a_roof: Annotated[float, "Solar absorptance of roof [-]"]
    n50: Annotated[float, "Air tightness at 50 Pa [1/h]"]
    win_wall: Annotated[float, "Window to wall ratio [-]"]
    a_wall: Annotated[float, "Solar absorptance of wall [-]"]
    rf_sh: Annotated[float, "Roof shading factor [-]"]
    e_wall: Annotated[float, "Emissivity of wall [-]"]
    e_roof: Annotated[float, "Emissivity of roof [-]"]
    e_underside: Annotated[float, "Emissivity of underside [-]"]
    G_win: Annotated[float, "Solar heat gain coefficient [-]"]
    e_win: Annotated[float, "Emissivity of windows [-]"]
    U_roof: Annotated[float, "U-value of roof [W/m2K]"]
    U_wall: Annotated[float, "U-value of wall [W/m2K]"]
    U_base: Annotated[float, "U-value of basement [W/m2K]"]
    U_win: Annotated[float, "U-value of windows [W/m2K]"]
    Cm_Af: Annotated[float, "Internal heat capacity [J/m2K]"]

    # FIXME: These fields does not neccessarily describe the building envelope
    Es: Annotated[float, "Heated/cooled share [-]"]
    occupied_bg: Annotated[float, "Basement occupation factor [-]"]
    void_deck: Annotated[float, "Void deck factor [-]"]

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
    I_sol: Annotated[float, "Isolated solar [kWh]"]

    @classmethod
    def from_dict(cls, solar: dict):
        return cls(I_sol=solar['I_sol'])
