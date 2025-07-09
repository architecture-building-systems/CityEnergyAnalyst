import pandas as pd

class BuildingPropertiesRow:
    """Encapsulate the data of a single row in the DataSets of BuildingProperties. This class meant to be
    read-only."""

    def __init__(self, name, geometry, envelope, typology, hvac,
                 rc_model, comfort, internal_loads, age, solar, supply):
        """Create a new instance of BuildingPropertiesRow - meant to be called by BuildingProperties[building_name].
        Each of the arguments is a pandas Series object representing a row in the corresponding DataFrame."""

        self.name = name
        self.geometry = geometry
        self.geometry['floor_height'] = self.geometry['height_ag'] / self.geometry['floors_ag']
        envelope['Hs_ag'], envelope['Hs_bg'], envelope['Ns_ag'], envelope['Ns_bg'] = \
            split_above_and_below_ground_shares(
                envelope['Hs'], envelope['Ns'], envelope['occupied_bg'], geometry['floors_ag'], geometry['floors_bg'])
        self.architecture = EnvelopeProperties(envelope)
        self.typology = typology  # FIXME: rename to uses!
        self.hvac = hvac
        self.rc_model = rc_model
        self.comfort = comfort
        self.internal_loads = internal_loads
        self.age = age
        self.solar = SolarProperties(solar)
        self.supply = supply
        self.building_systems = self._get_properties_building_systems()

    def _get_properties_building_systems(self):

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

        # Refactored from CalcThermalLoads

        # geometry properties.

        Ll = self.geometry['Blength']
        Lw = self.geometry['Bwidth']
        nf_ag = self.geometry['floors_ag']
        nf_bg = self.geometry['floors_bg']
        phi_pipes = self._calculate_pipe_transmittance_values()

        # nominal temperatures
        Ths_sup_ahu_0 = float(self.hvac['Tshs0_ahu_C'])
        Ths_re_ahu_0 = float(Ths_sup_ahu_0 - self.hvac['dThs0_ahu_C'])
        Ths_sup_aru_0 = float(self.hvac['Tshs0_aru_C'])
        Ths_re_aru_0 = float(Ths_sup_aru_0 - self.hvac['dThs0_aru_C'])
        Ths_sup_shu_0 = float(self.hvac['Tshs0_shu_C'])
        Ths_re_shu_0 = float(Ths_sup_shu_0 - self.hvac['dThs0_shu_C'])
        Tcs_sup_ahu_0 = self.hvac['Tscs0_ahu_C']
        Tcs_re_ahu_0 = Tcs_sup_ahu_0 + self.hvac['dTcs0_ahu_C']
        Tcs_sup_aru_0 = self.hvac['Tscs0_aru_C']
        Tcs_re_aru_0 = Tcs_sup_aru_0 + self.hvac['dTcs0_aru_C']
        Tcs_sup_scu_0 = self.hvac['Tscs0_scu_C']
        Tcs_re_scu_0 = Tcs_sup_scu_0 + self.hvac['dTcs0_scu_C']

        Tww_sup_0 = self.hvac['Tsww0_C']
        # Identification of equivalent lengths
        fforma = self._calc_form()  # factor form comparison real surface and rectangular
        Lv = (2 * Ll + 0.0325 * Ll * Lw + 6) * fforma  # length vertical lines
        if nf_ag < 2 and nf_bg < 2:  # it is assumed that building with less than a floor and less than 2 floors udnerground do not have
            Lcww_dis = 0
            Lvww_c = 0
        else:
            Lcww_dis = 2 * (Ll + 2.5 + nf_ag * self.geometry['floor_height']) * fforma  # length hot water piping circulation circuit
            Lvww_c = (2 * Ll + 0.0125 * Ll * Lw) * fforma  # length piping heating system circulation circuit

        Lsww_dis = 0.038 * Ll * Lw * nf_ag * self.geometry['floor_height'] * fforma  # length hot water piping distribution circuit
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

    def _calculate_pipe_transmittance_values(self):
        """linear trasmissivity coefficients of piping W/(m.K)"""
        if self.age['year'] >= 1995:
            phi_pipes = [0.2, 0.3, 0.3]
        # elif 1985 <= self.age['built'] < 1995 and self.age['HVAC'] == 0:
        elif 1985 <= self.age['year'] < 1995:
            phi_pipes = [0.3, 0.4, 0.4]
        else:
            phi_pipes = [0.4, 0.4, 0.4]
        return phi_pipes

    def _calc_form(self):
        factor = self.geometry['footprint'] / (self.geometry['Bwidth'] * self.geometry['Blength'])
        return factor



class EnvelopeProperties(object):
    """Encapsulate a single row of the architecture input file for a building"""

    def __init__(self, envelope):
        self.A_op = envelope['Awin_ag'] + envelope['Awall_ag']
        self.a_roof = envelope['a_roof']
        self.n50 = envelope['n50']
        self.win_wall = envelope['Awin_ag'] / self.A_op if self.A_op != 0 else 0.0
        self.a_wall = envelope['a_wall']
        self.rf_sh = envelope['rf_sh']
        self.e_wall = envelope['e_wall']
        self.e_roof = envelope['e_roof']
        self.e_underside = 0.0 # dummy values for emissivity of underside (bottom surface) as 0.
        self.G_win = envelope['G_win']
        self.e_win = envelope['e_win']
        self.U_roof = envelope['U_roof']
        self.Hs_ag = envelope['Hs_ag']
        self.Hs_bg = envelope['Hs_bg']
        self.Ns_ag = envelope['Ns_ag']
        self.Ns_bg = envelope['Ns_bg']
        self.Es = envelope['Es']
        self.occupied_bg = envelope['occupied_bg']
        self.Cm_Af = envelope['Cm_Af']
        self.U_wall = envelope['U_wall']
        self.U_base = envelope['U_base']
        self.U_win = envelope['U_win']
        self.void_deck = envelope['void_deck']


class SolarProperties(object):
    """Encapsulates the solar properties of a building"""

    __slots__ = ['I_sol']

    def __init__(self, solar):
        self.I_sol = solar['I_sol']


def split_above_and_below_ground_shares(Hs, Ns, occupied_bg, floors_ag, floors_bg):
    '''
    Split conditioned (Hs) and occupied (Ns) shares of ground floor area based on whether the basement
    conditioned/occupied or not.
    For simplicity, the same share is assumed for all conditioned/occupied floors (whether above or below ground)
    '''
    share_ag = floors_ag / (floors_ag + floors_bg * occupied_bg)
    share_bg = 1 - share_ag
    Hs_ag = Hs * share_ag
    Hs_bg = Hs * share_bg
    Ns_ag = Ns * share_ag
    Ns_bg = Ns * share_bg

    return Hs_ag, Hs_bg, Ns_ag, Ns_bg

