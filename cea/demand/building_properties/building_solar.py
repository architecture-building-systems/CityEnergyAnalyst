"""
Building solar properties
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from cea.constants import HOURS_IN_YEAR
from cea.demand.sensible_loads import calc_hr, calc_hc
from cea.technologies import blinds

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator


class BuildingSolar:
    """
    Groups building solar properties used for the calc-thermal-loads functions.
    """

    def __init__(self, locator: InputLocator, building_names: list[str], prop_rc_model, prop_envelope, weather_data):
        """
        Read building solar properties from input files and construct a new BuildingSolar object.

        :param locator: an InputLocator for locating the input files
        :param building_names: list of buildings to read properties for
        """
        self._prop_solar = self.get_prop_solar(
            locator, building_names, prop_rc_model, prop_envelope, weather_data).set_index('name').loc[building_names]

    def __getitem__(self, building_name: str) -> dict:
        """Get comfort properties of a building by name"""
        if building_name not in self._prop_solar.index:
            raise KeyError(f"Building solar properties for {building_name} not found")
        return self._prop_solar.loc[building_name].to_dict()


    def get_prop_solar(self, locator, building_names, prop_rc_model, prop_envelope, weather_data):
        """
        Gets the sensible solar gains from calc_Isol_daysim and stores in a dataframe containing building 'name' and
        I_sol (incident solar gains).

        :param locator: an InputLocator for locating the input files
        :param building_names: List of buildings
        :param prop_rc_model: RC model properties of a building by name.
        :param prop_envelope: dataframe containing the building envelope properties.
        :return: dataframe containing the sensible solar gains for each building by name called result.
        :rtype: Dataframe
        """

        # create result data frame
        list_Isol = []

        # for every building
        for building_name in building_names:
            thermal_resistance_surface = dict(zip(['RSE_wall', 'RSE_roof', 'RSE_win', 'RSE_underside'],
                                                get_thermal_resistance_surface(prop_envelope.loc[building_name],
                                                                                weather_data)))
            I_sol = calc_Isol_daysim(building_name, locator, prop_envelope, prop_rc_model, thermal_resistance_surface)
            list_Isol.append(I_sol)

        result = pd.DataFrame({'name': list(building_names), 'I_sol': list_Isol})

        return result


def calc_Isol_daysim(building_name, locator: InputLocator, prop_envelope, prop_rc_model, thermal_resistance_surface)-> pd.Series:
    """
    Reads Daysim geometry and radiation results and calculates the sensible solar heat loads based on the surface area
    and building envelope properties.

    :param building_name: Name of the building (e.g. B154862)
    :param locator: an InputLocator for locating the input files
    :param prop_envelope: contains the building envelope properties.
    :param prop_rc_model: RC model properties of a building by name.
    :param thermal_resistance_surface: Thermal resistance of building element.

    :return: I_sol: numpy array containing the sensible solar heat loads for roof, walls and windows.
    :rtype: np.array

    """

    # read daysim radiation
    radiation_data = pd.read_csv(locator.get_radiation_building(building_name))

    # sum wall
    # solar incident on all walls [W]
    I_sol_wall = (radiation_data['walls_east_kW'] +
                  radiation_data['walls_west_kW'] +
                  radiation_data['walls_north_kW'] +
                  radiation_data['walls_south_kW']) * 1000  # in W

    # sensible gain on all walls [W]
    I_sol_wall = I_sol_wall * \
                 prop_envelope.loc[building_name, 'a_wall'] * \
                 thermal_resistance_surface['RSE_wall'] * \
                 prop_envelope.loc[building_name, 'U_wall']

    # sum roof
    # solar incident on all roofs [W]
    I_sol_roof = radiation_data['roofs_top_kW'] * 1000  # in W

    # sensible gain on all roofs [W]
    I_sol_roof = I_sol_roof * \
                 prop_envelope.loc[building_name, 'a_roof'] * \
                 thermal_resistance_surface['RSE_roof'] * \
                 prop_envelope.loc[building_name, 'U_roof']

    # sum window, considering shading
    I_sol_win = (radiation_data['windows_east_kW'] +
                 radiation_data['windows_west_kW'] +
                 radiation_data['windows_north_kW'] +
                 radiation_data['windows_south_kW']) * 1000  # in W

    Fsh_win = np.vectorize(blinds.calc_blinds_activation)(I_sol_win,
                                                          prop_envelope.loc[building_name, 'G_win'],
                                                          prop_envelope.loc[building_name, 'rf_sh'])

    I_sol_win = I_sol_win * \
                Fsh_win * \
                (1 - prop_envelope.loc[building_name, 'F_F'])
    
    #dummy values for base because there's no radiation calculated for bottom-oriented surfaces yet.
    I_sol_underside = np.zeros_like(I_sol_win) * thermal_resistance_surface['RSE_underside'] 

    # sum
    I_sol = I_sol_wall + I_sol_roof + I_sol_win + I_sol_underside

    return I_sol


def get_thermal_resistance_surface(prop_envelope, weather_data):
    '''
    This function defines the surface resistance of external surfaces RSE according to ISO 6946 Eq. (A.1).
    '''

    # define surface thermal resistances according to ISO 6946
    h_c = np.vectorize(calc_hc)(weather_data['windspd_ms'].values)
    # generate an array of 0.5 * (sky_temp(t) + air_temp(t-1))
    theta_ss = 0.5 * (
            weather_data['skytemp_C'].values +
            np.array([weather_data['drybulb_C'].values[0]] +
                     list(weather_data['drybulb_C'].values[0:HOURS_IN_YEAR - 1])))
    thermal_resistance_surface_wall = (h_c + calc_hr(prop_envelope.e_wall, theta_ss)) ** -1
    thermal_resistance_surface_win = (h_c + calc_hr(prop_envelope.e_win, theta_ss)) ** -1
    thermal_resistance_surface_roof = (h_c + calc_hr(prop_envelope.e_roof, theta_ss)) ** -1
    thermal_resistance_surface_underside = np.zeros_like(h_c)

    return thermal_resistance_surface_wall, thermal_resistance_surface_roof, thermal_resistance_surface_win, thermal_resistance_surface_underside

