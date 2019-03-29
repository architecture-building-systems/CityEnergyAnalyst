"""
Building model class definition

MIT License

Copyright (c) 2019 TUMCREATE <https://tum-create.edu.sg/>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import numpy as np
import pandas as pd
# Using CoolProp for calculating humid air properties: http://www.coolprop.org/fluid_properties/HumidAir.html
from CoolProp.HumidAirProp import HAPropsSI as humid_air_properties
from scipy.interpolate import interp1d
from scipy.linalg import expm

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


class Building(object):
    """
    Building scenario object to store all information
    """

    def __init__(self, conn, scenario_name):
        # Load building information from database
        self.building_scenarios = pd.read_sql(
            """
            select * from building_scenarios 
            join buildings using (building_name) 
            join building_linearization_types using (linearization_type) 
            where scenario_name='{}'
            """.format(scenario_name),
            conn
        )
        self.building_parameters = pd.read_sql(
            """
            select * from building_parameter_sets 
            where parameter_set in ('constants', '{}')
            """.format(self.building_scenarios['parameter_set'][0]),
            conn
        )
        self.building_parameters = pd.Series(
            self.building_parameters['parameter_value'].values,
            self.building_parameters['parameter_name'].values
        )  # Convert to series for shorter indexing
        self.building_surfaces_adiabatic = pd.read_sql(
            """
            select * from building_surfaces_adiabatic 
            join building_surface_types using (surface_type) 
            left join building_window_types using (window_type) 
            join building_zones using (zone_name, building_name) 
            where building_name='{}'
            """.format(self.building_scenarios['building_name'][0]),
            conn
        )
        self.building_surfaces_adiabatic.index = self.building_surfaces_adiabatic['surface_name']
        self.building_surfaces_exterior = pd.read_sql(
            """
            select * from building_surfaces_exterior 
            join building_surface_types using (surface_type) 
            left join building_window_types using (window_type) 
            join building_zones using (zone_name, building_name) 
            where building_name='{}'
            """.format(self.building_scenarios['building_name'][0]),
            conn
        )
        self.building_surfaces_exterior.index = self.building_surfaces_exterior['surface_name']
        self.building_surfaces_interior = pd.read_sql(
            """
            select * from building_surfaces_interior 
            join building_surface_types using (surface_type) 
            left join building_window_types using (window_type) 
            join building_zones using (zone_name, building_name) 
            where building_name='{}'
            """.format(self.building_scenarios['building_name'][0]),
            conn
        )
        self.building_surfaces_interior.index = self.building_surfaces_interior['surface_name']
        self.building_zones = pd.read_sql(
            """
            select * from building_zones 
            join building_zone_types using (zone_type) 
            join building_internal_gain_types using (internal_gain_type) 
            left join building_blind_types using (blind_type) 
            left join building_hvac_generic_types using (hvac_generic_type) 
            left join building_hvac_ahu_types using (hvac_ahu_type) 
            left join building_hvac_tu_types using (hvac_tu_type) 
            where building_name='{}'
            """.format(self.building_scenarios['building_name'][0]),
            conn
        )
        self.building_zones.index = self.building_zones['zone_name']

        # Add constant row in disturbance vector, if any CO2 model or HVAC or window
        self.define_constant = (
                (self.building_scenarios['co2_model_type'][0] != '')
                | (self.building_zones['hvac_ahu_type'] != '').any()
                | (self.building_zones['window_type'] != '').any()
        )

        # Define index vectors
        self.index_states = pd.Index(
            pd.concat([
                self.building_zones['zone_name'] + '_temperature',
                self.building_surfaces_adiabatic['surface_name'][
                    self.building_surfaces_adiabatic['heat_capacity'] != '0'
                    ] + '_temperature',
                self.building_surfaces_exterior['surface_name'][
                    self.building_surfaces_exterior['heat_capacity'] != '0'
                    ] + '_temperature',
                self.building_surfaces_interior['surface_name'][
                    self.building_surfaces_interior['heat_capacity'] != '0'
                    ] + '_temperature',
                self.building_zones['zone_name'][
                    ((self.building_zones['hvac_ahu_type'] != '') | (self.building_zones['window_type'] != ''))
                    & (self.building_scenarios['co2_model_type'][0] != '')
                    ] + '_co2_concentration',
                self.building_zones['zone_name'][
                    (self.building_zones['hvac_ahu_type'] != '')
                    & (self.building_scenarios['humidity_model_type'][0] != '')
                    ] + '_absolute_humidity'
            ])
        )
        self.index_controls = pd.Index(
            pd.concat([
                self.building_zones['zone_name'][
                    self.building_zones['hvac_generic_type'] != ''
                    ] + '_generic_heat_thermal_power',
                self.building_zones['zone_name'][
                    self.building_zones['hvac_generic_type'] != ''
                    ] + '_generic_cool_thermal_power',
                self.building_zones['zone_name'][
                    self.building_zones['hvac_ahu_type'] != ''
                    ] + '_ahu_heat_air_flow',
                self.building_zones['zone_name'][
                    self.building_zones['hvac_ahu_type'] != ''
                    ] + '_ahu_cool_air_flow',
                self.building_zones['zone_name'][
                    self.building_zones['hvac_tu_type'] != ''
                    ] + '_tu_heat_air_flow',
                self.building_zones['zone_name'][
                    self.building_zones['hvac_tu_type'] != ''
                    ] + '_tu_cool_air_flow',
                self.building_zones['zone_name'][
                    (self.building_zones['window_type'] != '')
                ] + '_window_air_flow'
            ])
        )
        self.index_disturbances = pd.Index(
            pd.concat([
                pd.Series([
                    'ambient_air_temperature',
                    'sky_temperature',
                    'irradiation_horizontal',
                    'irradiation_east',
                    'irradiation_south',
                    'irradiation_west',
                    'irradiation_north'
                ]),
                pd.Series(self.building_zones['internal_gain_type'].unique() + '_occupancy'),
                pd.Series(self.building_zones['internal_gain_type'].unique() + '_appliances'),
                (pd.Series(['constant']) if self.define_constant else pd.Series([]))
            ])
        )
        self.index_outputs = pd.Index(
            pd.concat([
                self.building_zones['zone_name'] + '_temperature',
                self.building_zones['zone_name'][
                    ((self.building_zones['hvac_ahu_type'] != '') | (self.building_zones['window_type'] != ''))
                    & (self.building_scenarios['co2_model_type'][0] != '')
                    ] + '_co2_concentration',
                self.building_zones['zone_name'][
                    (self.building_zones['hvac_ahu_type'] != '')
                    & (self.building_scenarios['humidity_model_type'][0] != '')
                    ] + '_absolute_humidity',
                self.building_zones['zone_name'][
                    (self.building_zones['hvac_ahu_type'] != '')
                    | (self.building_zones['window_type'] != '')
                    ] + '_total_fresh_air_flow',
                self.building_zones['zone_name'][
                    (self.building_zones['hvac_ahu_type'] != '')
                ] + '_ahu_fresh_air_flow',
                self.building_zones['zone_name'][
                    (self.building_zones['window_type'] != '')
                ] + '_window_fresh_air_flow',
                self.building_zones['zone_name'][
                    self.building_zones['hvac_generic_type'] != ''
                    ] + '_generic_heat_power',
                self.building_zones['zone_name'][
                    self.building_zones['hvac_generic_type'] != ''
                    ] + '_generic_cool_power',
                self.building_zones['zone_name'][
                    self.building_zones['hvac_ahu_type'] != ''
                    ] + '_ahu_heat_electric_power',
                self.building_zones['zone_name'][
                    self.building_zones['hvac_ahu_type'] != ''
                    ] + '_ahu_cool_electric_power',
                self.building_zones['zone_name'][
                    self.building_zones['hvac_tu_type'] != ''
                    ] + '_tu_heat_electric_power',
                self.building_zones['zone_name'][
                    self.building_zones['hvac_tu_type'] != ''
                    ] + '_tu_cool_electric_power'
            ])
        )

        # Define model matrices
        self.state_matrix = pd.DataFrame(
            0.0,
            self.index_states,
            self.index_states
        )
        self.control_matrix = pd.DataFrame(
            0.0,
            self.index_states,
            self.index_controls
        )
        self.disturbance_matrix = pd.DataFrame(
            0.0,
            self.index_states,
            self.index_disturbances
        )
        self.state_output_matrix = pd.DataFrame(
            0.0,
            self.index_outputs,
            self.index_states
        )
        self.control_output_matrix = pd.DataFrame(
            0.0,
            self.index_outputs,
            self.index_controls
        )
        self.disturbance_output_matrix = pd.DataFrame(
            0.0,
            self.index_outputs,
            self.index_disturbances
        )

        # Define heat capacity vector
        self.heat_capacity_vector = pd.Series(
            0.0,
            self.index_states
        )
        for index, row in self.building_zones.iterrows():
            self.heat_capacity_vector.at[index] = (
                    self.parse_parameter(row['zone_area'])
                    * self.parse_parameter(row['zone_height'])
                    * self.parse_parameter(row['heat_capacity'])
            )
        for index, row in self.building_surfaces_adiabatic.iterrows():
            self.heat_capacity_vector.at[index] = (
                    self.parse_parameter(row['surface_area'])
                    * self.parse_parameter(row['heat_capacity'])
            )
        for index, row in self.building_surfaces_exterior.iterrows():
            self.heat_capacity_vector.at[index] = (
                    self.parse_parameter(row['surface_area'])
                    * self.parse_parameter(row['heat_capacity'])
            )
        for index, row in self.building_surfaces_interior.iterrows():
            self.heat_capacity_vector.at[index] = (
                    self.parse_parameter(row['surface_area'])
                    * self.parse_parameter(row['heat_capacity'])
            )

        # Definition of parameters / coefficients
        self.define_heat_transfer_coefficients()

        # Define heat fluxes and co2 transfers
        self.define_heat_transfer_adjacent_surfaces_zones()
        self.define_heat_transfer_ambient_air()
        self.define_heat_transfer_infiltration()
        self.define_heat_transfer_internal_gains()
        self.define_heat_transfer_hvac_generic()
        self.define_heat_transfer_hvac_ahu()
        self.define_heat_transfer_hvac_tu()
        self.define_heat_transfer_irradiation()
        self.define_heat_transfer_emission_environment()
        self.define_heat_transfer_emission_sky()
        self.define_co2_transfer_hvac_ahu()
        self.define_heat_transfer_window_air_flow()
        self.define_humidity_transfer_hvac_ahu()

        # Define outputs
        self.define_output_zone_temperature()
        self.define_output_zone_co2_concentration()
        self.define_output_zone_humidity()
        self.define_output_hvac_generic_power()
        self.define_output_hvac_ahu_electric_power()
        self.define_output_hvac_tu_electric_power()
        self.define_output_fresh_air_flow()
        self.define_output_window_fresh_air_flow()
        self.define_output_ahu_fresh_air_flow()

        # Define timeseries variables
        self.time_vector = pd.date_range(
            start=pd.to_datetime(self.building_scenarios['time_start'][0]),
            end=pd.to_datetime(self.building_scenarios['time_end'][0]),
            freq=pd.to_timedelta(self.building_scenarios['time_step'][0])
        )
        self.index_time = pd.Index(
            self.time_vector
        )

        # Load disturbance timeseries
        self.load_disturbance_timeseries(conn)

        # Define output constraint timeseries
        self.define_output_constraint_timeseries(conn)

        # Convert to time discrete model
        self.discretize_model()

    def parse_parameter(self, parameter):
        """
        - Checks if given parameter is a number.
        - If the parameter is not a number, it is assumed to be the name of a parameter from `building_parameters`
        """
        try:
            return float(parameter)
        except ValueError:
            return self.building_parameters[parameter]

    def define_heat_transfer_coefficients(self):
        # Create empty rows in dataframe
        self.building_surfaces_exterior['heat_transfer_coefficient_surface_to_sky'] = ''
        self.building_surfaces_exterior['heat_transfer_coefficient_surface_to_ground'] = ''

        # Calculate heat transfer coefficients
        for index_exterior, row_exterior in self.building_surfaces_exterior.iterrows():
            row_exterior['heat_transfer_coefficient_surface_to_sky'] = (
                    4
                    * self.parse_parameter('stefan_boltzmann_constant')
                    * self.parse_parameter(row_exterior['emissivity'])
                    * self.parse_parameter(row_exterior['sky_view_factor'])
                    * (
                            self.parse_parameter(self.building_scenarios['linearization_exterior_surface_temperature'])
                            / 2
                            + self.parse_parameter(self.building_scenarios['linearization_sky_temperature'])
                            / 2
                            + 273.15
                    ) ** 3
            )
            row_exterior['heat_transfer_coefficient_surface_to_ground'] = (
                    4
                    * self.parse_parameter('stefan_boltzmann_constant')
                    * self.parse_parameter(row_exterior['emissivity'])
                    * (1 - self.parse_parameter(row_exterior['sky_view_factor']))
                    * (
                            self.parse_parameter(self.building_scenarios['linearization_exterior_surface_temperature'])
                            / 2
                            + self.parse_parameter(self.building_scenarios['linearization_ambient_air_temperature'])
                            / 2
                            + 273.15
                    ) ** 3
            )

    def define_heat_transfer_adjacent_surfaces_zones(self):
        # Surfaces and zones
        for building_surfaces in [
            self.building_surfaces_adiabatic,
            self.building_surfaces_exterior,
            self.building_surfaces_interior
        ]:
            for index, row in building_surfaces.iterrows():
                if self.parse_parameter(row['heat_capacity']) != 0:
                    self.state_matrix.at[
                        index + '_temperature',
                        row['zone_name'] + '_temperature'
                    ] = (
                            self.state_matrix.at[index + '_temperature', row['zone_name'] + '_temperature']
                            + 1
                            / (
                                    1
                                    / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                    + self.parse_parameter(row['thermal_resistance_surface'])
                            )
                            * self.parse_parameter(row['surface_area'])
                            * (1 - self.parse_parameter(row['window_wall_ratio']))
                            / self.heat_capacity_vector[index]
                    )
                    self.state_matrix.at[
                        index + '_temperature',
                        index + '_temperature'
                    ] = (
                            self.state_matrix.at[index + '_temperature', index + '_temperature']
                            - 1
                            / (
                                    1
                                    / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                    + self.parse_parameter(row['thermal_resistance_surface'])
                            )
                            * self.parse_parameter(row['surface_area'])
                            * (1 - self.parse_parameter(row['window_wall_ratio']))
                            / self.heat_capacity_vector[index]
                    )
                    self.state_matrix.at[
                        row['zone_name'] + '_temperature',
                        index + '_temperature'
                    ] = (
                            self.state_matrix.at[
                                row['zone_name'] + '_temperature',
                                index + '_temperature'
                            ]
                            + 1
                            / (
                                    1
                                    / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                    + self.parse_parameter(row['thermal_resistance_surface'])
                            )
                            * self.parse_parameter(row['surface_area'])
                            * (1 - self.parse_parameter(row['window_wall_ratio']))
                            / self.heat_capacity_vector[row['zone_name']]
                    )
                    self.state_matrix.at[
                        row['zone_name'] + '_temperature',
                        row['zone_name'] + '_temperature'
                    ] = (
                            self.state_matrix.at[
                                row['zone_name'] + '_temperature',
                                row['zone_name'] + '_temperature'
                            ]
                            - 1
                            / (
                                    1
                                    / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                    + self.parse_parameter(row['thermal_resistance_surface'])
                            )
                            * self.parse_parameter(row['surface_area'])
                            * (1 - self.parse_parameter(row['window_wall_ratio']))
                            / self.heat_capacity_vector[row['zone_name']]
                    )

        # Interior surfaces and adjacent (second) zones
        for index, row in self.building_surfaces_interior.iterrows():
            if self.parse_parameter(row['heat_capacity']) != 0:
                self.state_matrix.at[
                    index + '_temperature',
                    row['zone_adjacent_name'] + '_temperature'
                ] = (
                        self.state_matrix.at[
                            index + '_temperature',
                            row['zone_adjacent_name'] + '_temperature'
                        ]
                        + 1
                        / (
                                1
                                / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                + self.parse_parameter(row['thermal_resistance_surface'])
                        )
                        * self.parse_parameter(row['surface_area'])
                        * (1 - self.parse_parameter(row['window_wall_ratio']))
                        / self.heat_capacity_vector[index]
                )
                self.state_matrix.at[
                    index + '_temperature',
                    index + '_temperature'
                ] = (
                        self.state_matrix.at[
                            index + '_temperature',
                            index + '_temperature'
                        ]
                        - 1
                        / (
                                1
                                / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                + self.parse_parameter(row['thermal_resistance_surface'])
                        )
                        * self.parse_parameter(row['surface_area'])
                        * (1 - self.parse_parameter(row['window_wall_ratio']))
                        / self.heat_capacity_vector[index]
                )
                self.state_matrix.at[
                    row['zone_adjacent_name'] + '_temperature',
                    index + '_temperature'
                ] = (
                        self.state_matrix.at[
                            row['zone_adjacent_name'] + '_temperature',
                            index + '_temperature'
                        ]
                        + 1
                        / (
                                1
                                / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                + self.parse_parameter(row['thermal_resistance_surface'])
                        )
                        * self.parse_parameter(row['surface_area'])
                        * (1 - self.parse_parameter(row['window_wall_ratio']))
                        / self.heat_capacity_vector[row['zone_adjacent_name']]
                )
                self.state_matrix.at[
                    row['zone_adjacent_name'] + '_temperature',
                    row['zone_adjacent_name'] + '_temperature'
                ] = (
                        self.state_matrix.at[
                            row['zone_adjacent_name'] + '_temperature',
                            row['zone_adjacent_name'] + '_temperature'
                        ]
                        - 1
                        / (
                                1
                                / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                + self.parse_parameter(row['thermal_resistance_surface'])
                        )
                        * self.parse_parameter(row['surface_area'])
                        * (1 - self.parse_parameter(row['window_wall_ratio']))
                        / self.heat_capacity_vector[row['zone_adjacent_name']]
                )
            else:
                self.state_matrix.at[
                    row['zone_name'] + '_temperature',
                    row['zone_adjacent_name'] + '_temperature'
                ] = (
                        self.state_matrix.at[
                            row['zone_name'] + '_temperature',
                            row['zone_adjacent_name'] + '_temperature'
                        ]
                        + 1
                        / (
                                2
                                * (
                                        1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                        + self.parse_parameter(row['thermal_resistance_surface'])
                                )
                        )
                        * self.parse_parameter(row['surface_area'])
                        * (1 - self.parse_parameter(row['window_wall_ratio']))
                        / self.heat_capacity_vector[row['zone_name']]
                )
                self.state_matrix.at[
                    row['zone_name'] + '_temperature',
                    row['zone_name'] + '_temperature'
                ] = (
                        self.state_matrix.at[
                            row['zone_name'] + '_temperature',
                            row['zone_name'] + '_temperature'
                        ]
                        - 1
                        / (
                                2
                                * (
                                        1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                        + self.parse_parameter(row['thermal_resistance_surface'])
                                )
                        )
                        * self.parse_parameter(row['surface_area'])
                        * (1 - self.parse_parameter(row['window_wall_ratio']))
                        / self.heat_capacity_vector[row['zone_name']]
                )
                self.state_matrix.at[
                    row['zone_adjacent_name'] + '_temperature',
                    row['zone_name'] + '_temperature'
                ] = (
                        self.state_matrix.at[
                            row['zone_adjacent_name'] + '_temperature',
                            row['zone_name'] + '_temperature'
                        ]
                        + 1
                        / (
                                2
                                * (
                                        1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                        + self.parse_parameter(row['thermal_resistance_surface'])
                                )
                        )
                        * self.parse_parameter(row['surface_area'])
                        * (1 - self.parse_parameter(row['window_wall_ratio']))
                        / self.heat_capacity_vector[row['zone_adjacent_name']]
                )
                self.state_matrix.at[
                    row['zone_adjacent_name'] + '_temperature',
                    row['zone_adjacent_name'] + '_temperature'
                ] = (
                        self.state_matrix.at[
                            row['zone_adjacent_name'] + '_temperature',
                            row['zone_adjacent_name'] + '_temperature'
                        ]
                        - 1
                        / (
                                2
                                * (
                                        1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                        + self.parse_parameter(row['thermal_resistance_surface'])
                                )
                        )
                        * self.parse_parameter(row['surface_area'])
                        * (1 - self.parse_parameter(row['window_wall_ratio']))
                        / self.heat_capacity_vector[row['zone_adjacent_name']]
                )

        # Zones and zones (through interior windows)
        for index, row in self.building_surfaces_interior.iterrows():
            if self.parse_parameter(row['window_wall_ratio']) != 0:
                self.state_matrix.at[
                    row['zone_adjacent_name'] + '_temperature',
                    row['zone_name'] + '_temperature'
                ] = (
                        self.state_matrix.at[
                            row['zone_adjacent_name'] + '_temperature',
                            row['zone_name'] + '_temperature'
                        ]
                        + 1
                        / (
                                2
                                * (
                                        1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                        + self.parse_parameter(row['thermal_resistance_window'])
                                )
                        )
                        * self.parse_parameter(row['surface_area'])
                        * self.parse_parameter(row['window_wall_ratio'])
                        / self.heat_capacity_vector[row['zone_adjacent_name']]
                )
                self.state_matrix.at[
                    row['zone_adjacent_name'] + '_temperature',
                    row['zone_adjacent_name'] + '_temperature'
                ] = (
                        self.state_matrix.at[
                            row['zone_adjacent_name'] + '_temperature',
                            row['zone_adjacent_name'] + '_temperature'
                        ]
                        - 1
                        / (
                                2
                                * (
                                        1 / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                        + self.parse_parameter(row['thermal_resistance_window'])
                                )
                        )
                        * self.parse_parameter(row['surface_area'])
                        * self.parse_parameter(row['window_wall_ratio'])
                        / self.heat_capacity_vector[row['zone_adjacent_name']]
                )
                self.state_matrix.at[
                    row['zone_name'] + '_temperature',
                    row['zone_adjacent_name'] + '_temperature'
                ] = (
                        self.state_matrix.at[
                            row['zone_name'] + '_temperature',
                            row['zone_adjacent_name'] + '_temperature'
                        ]
                        + 1
                        / (
                                2
                                * (
                                        1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                        + self.parse_parameter(row['thermal_resistance_window'])
                                )
                        )
                        * self.parse_parameter(row['surface_area'])
                        * self.parse_parameter(row['window_wall_ratio'])
                        / self.heat_capacity_vector[row['zone_name']]
                )
                self.state_matrix.at[
                    row['zone_name'] + '_temperature',
                    row['zone_name'] + '_temperature'
                ] = (
                        self.state_matrix.at[
                            row['zone_name'] + '_temperature',
                            row['zone_name'] + '_temperature'
                        ]
                        - 1
                        / (
                                2
                                * (
                                        1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                        + self.parse_parameter(row['thermal_resistance_window'])
                                )
                        )
                        * self.parse_parameter(row['surface_area'])
                        * self.parse_parameter(row['window_wall_ratio'])
                        / self.heat_capacity_vector[row['zone_name']]
                )

    def define_heat_transfer_ambient_air(self):
        # Ambient air and surfaces
        for index, row in self.building_surfaces_exterior.iterrows():
            if self.parse_parameter(row['heat_capacity']) != 0:
                self.state_matrix.at[
                    index + '_temperature',
                    index + '_temperature'
                ] = (
                        self.state_matrix.at[
                            index + '_temperature',
                            index + '_temperature'
                        ]
                        - 1
                        / (
                                1
                                / self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                + self.parse_parameter(row['thermal_resistance_surface'])
                                * (
                                        1
                                        + (
                                                self.parse_parameter(row['heat_transfer_coefficient_surface_to_sky'])
                                                + self.parse_parameter(
                                            row['heat_transfer_coefficient_surface_to_ground']
                                        )
                                        )
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_ambient'))
                        )
                        * self.parse_parameter(row['surface_area'])
                        * (1 - self.parse_parameter(row['window_wall_ratio']))
                        / self.heat_capacity_vector[index]
                )
                self.disturbance_matrix.at[
                    index + '_temperature',
                    'ambient_air_temperature'
                ] = (
                        self.disturbance_matrix.at[
                            index + '_temperature',
                            'ambient_air_temperature'
                        ]
                        + 1
                        / (
                                1
                                / self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                + self.parse_parameter(row['thermal_resistance_surface'])
                                * (
                                        1
                                        + (
                                                self.parse_parameter(row['heat_transfer_coefficient_surface_to_sky'])
                                                + self.parse_parameter(
                                            row['heat_transfer_coefficient_surface_to_ground']
                                        )
                                        )
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_ambient'))
                        )
                        * self.parse_parameter(row['surface_area'])
                        * (1 - self.parse_parameter(row['window_wall_ratio']))
                        / self.heat_capacity_vector[index]
                )
            else:
                self.state_matrix.at[
                    row['zone_name'] + '_temperature',
                    row['zone_name'] + '_temperature'
                ] = (
                        self.state_matrix.at[row['zone_name'] + '_temperature', row['zone_name'] + '_temperature']
                        - 1
                        / (
                                2
                                * self.parse_parameter(row['thermal_resistance_surface'])
                                + 1
                                / self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                + 1
                                / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                + (
                                        2
                                        * self.parse_parameter(row['thermal_resistance_surface'])
                                        + 1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                )
                                * (
                                        self.parse_parameter(row['heat_transfer_coefficient_surface_to_sky'])
                                        + self.parse_parameter(row['heat_transfer_coefficient_surface_to_ground'])
                                )
                                / self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                        )
                        * self.parse_parameter(row['surface_area'])
                        * (1 - self.parse_parameter(row['window_wall_ratio']))
                        / self.heat_capacity_vector[row['zone_name']]
                )
                self.disturbance_matrix.at[
                    row['zone_name'] + '_temperature',
                    'ambient_air_temperature'
                ] = (
                        self.disturbance_matrix.at[row['zone_name'] + '_temperature', 'ambient_air_temperature']
                        + 1
                        / (
                                2
                                * self.parse_parameter(row['thermal_resistance_surface'])
                                + 1
                                / self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                + 1
                                / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                + (
                                        2
                                        * self.parse_parameter(row['thermal_resistance_surface'])
                                        + 1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                )
                                * (
                                        self.parse_parameter(row['heat_transfer_coefficient_surface_to_sky'])
                                        + self.parse_parameter(row['heat_transfer_coefficient_surface_to_ground'])
                                )
                                / self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                        )
                        * self.parse_parameter(row['surface_area'])
                        * (1 - self.parse_parameter(row['window_wall_ratio']))
                        / self.heat_capacity_vector[row['zone_name']]
                )

        # Ambient air and zones (through windows)
        for index, row in self.building_surfaces_exterior.iterrows():
            if self.parse_parameter(row['window_wall_ratio']) != 0:
                self.state_matrix.at[
                    row['zone_name'] + '_temperature',
                    row['zone_name'] + '_temperature'
                ] = (
                        self.state_matrix.at[
                            row['zone_name'] + '_temperature',
                            row['zone_name'] + '_temperature'
                        ]
                        - 1
                        / (
                                2
                                * self.parse_parameter(row['thermal_resistance_window'])
                                + 1
                                / self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                + 1
                                / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                + (
                                        2
                                        * self.parse_parameter(row['thermal_resistance_window'])
                                        + 1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                )
                                * (
                                        self.parse_parameter(row['heat_transfer_coefficient_surface_to_sky'])
                                        + self.parse_parameter(row['heat_transfer_coefficient_surface_to_ground'])
                                )
                                / self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                        )
                        * self.parse_parameter(row['surface_area'])
                        * self.parse_parameter(row['window_wall_ratio'])
                        / self.heat_capacity_vector[row['zone_name']]
                )
                self.disturbance_matrix.at[
                    row['zone_name'] + '_temperature',
                    'ambient_air_temperature'
                ] = (
                        self.disturbance_matrix.at[
                            row['zone_name'] + '_temperature',
                            'ambient_air_temperature'
                        ]
                        + 1
                        / (
                                2
                                * self.parse_parameter(row['thermal_resistance_window'])
                                + 1
                                / self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                + 1
                                / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                + (
                                        2
                                        * self.parse_parameter(row['thermal_resistance_window'])
                                        +
                                        1 / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                )
                                * (
                                        self.parse_parameter(row['heat_transfer_coefficient_surface_to_sky'])
                                        + self.parse_parameter(row['heat_transfer_coefficient_surface_to_ground'])
                                )
                                / self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                        )
                        * self.parse_parameter(row['surface_area'])
                        * self.parse_parameter(row['window_wall_ratio'])
                        / self.heat_capacity_vector[row['zone_name']]
                )

    def define_heat_transfer_infiltration(self):
        for index, row in self.building_zones.iterrows():
            self.state_matrix.at[
                index + '_temperature',
                index + '_temperature'
            ] = (
                    self.state_matrix.at[
                        index + '_temperature',
                        index + '_temperature'
                    ]
                    - self.parse_parameter(row['infiltration_rate'])
                    * self.parse_parameter('heat_capacity_air')
                    * self.parse_parameter(row['zone_area'])
                    * self.parse_parameter(row['zone_height'])
                    / self.heat_capacity_vector[index]
            )
            self.disturbance_matrix.at[
                index + '_temperature',
                'ambient_air_temperature'
            ] = (
                    self.disturbance_matrix.at[
                        index + '_temperature',
                        'ambient_air_temperature'
                    ]
                    + self.parse_parameter(row['infiltration_rate'])
                    * self.parse_parameter('heat_capacity_air')
                    * self.parse_parameter(row['zone_area'])
                    * self.parse_parameter(row['zone_height'])
                    / self.heat_capacity_vector[index]
            )

    def define_heat_transfer_window_air_flow(self):
        for index, row in self.building_zones.iterrows():
            if row['window_type'] != '':
                self.control_matrix.at[
                    index + '_temperature',
                    index + '_window_air_flow'
                ] = (
                        self.control_matrix.at[
                            index + '_temperature',
                            index + '_window_air_flow'
                        ]
                        + self.parse_parameter('heat_capacity_air')
                        * (
                                self.parse_parameter(self.building_scenarios['linearization_ambient_air_temperature'])
                                - self.parse_parameter(
                            self.building_scenarios['linearization_zone_air_temperature_cool']
                        )
                        )
                        / self.heat_capacity_vector[index]
                )

    def define_heat_transfer_internal_gains(self):
        for index, row in self.building_zones.iterrows():
            self.disturbance_matrix.at[
                index + '_temperature',
                row['internal_gain_type'] + '_occupancy'
            ] = (
                    self.disturbance_matrix.at[
                        index + '_temperature',
                        row['internal_gain_type'] + '_occupancy'
                    ]
                    + self.parse_parameter(row['internal_gain_occupancy_factor'])
                    * self.parse_parameter(row['zone_area'])
                    / self.heat_capacity_vector[index]
            )
            self.disturbance_matrix.at[
                index + '_temperature',
                row['internal_gain_type'] + '_appliances'
            ] = (
                    self.disturbance_matrix.at[
                        index + '_temperature',
                        row['internal_gain_type'] + '_appliances'
                    ]
                    + self.parse_parameter(row['internal_gain_appliances_factor'])
                    * self.parse_parameter(row['zone_area'])
                    / self.heat_capacity_vector[index]
            )

    def define_heat_transfer_hvac_generic(self):
        for index, row in self.building_zones.iterrows():
            if row['hvac_generic_type'] != '':
                self.control_matrix.at[
                    index + '_temperature',
                    index + '_generic_heat_thermal_power'
                ] = (
                        self.control_matrix.at[
                            index + '_temperature',
                            index + '_generic_heat_thermal_power'
                        ]
                        + 1
                        / self.heat_capacity_vector[index]
                )
                self.control_matrix.at[
                    index + '_temperature',
                    index + '_generic_cool_thermal_power'
                ] = (
                        self.control_matrix.at[
                            index + '_temperature',
                            index + '_generic_cool_thermal_power'
                        ]
                        - 1
                        / self.heat_capacity_vector[index]
                )

    def define_heat_transfer_hvac_ahu(self):
        for index, row in self.building_zones.iterrows():
            if row['hvac_ahu_type'] != '':
                self.control_matrix.at[
                    index + '_temperature',
                    index + '_ahu_heat_air_flow'
                ] = (
                        self.control_matrix.at[
                            index + '_temperature',
                            index + '_ahu_heat_air_flow'
                        ]
                        + self.parse_parameter('heat_capacity_air')
                        * (
                                self.parse_parameter(row['ahu_supply_air_temperature_setpoint'])
                                - self.parse_parameter(
                            self.building_scenarios['linearization_zone_air_temperature_heat']
                        )
                        )
                        / self.heat_capacity_vector[index]
                )
                self.control_matrix.at[
                    index + '_temperature',
                    index + '_ahu_cool_air_flow'
                ] = (
                        self.control_matrix.at[
                            index + '_temperature',
                            index + '_ahu_cool_air_flow'
                        ]
                        + self.parse_parameter('heat_capacity_air')
                        * (
                                self.parse_parameter(row['ahu_supply_air_temperature_setpoint'])
                                - self.parse_parameter(
                            self.building_scenarios['linearization_zone_air_temperature_cool']
                        )
                        )
                        / self.heat_capacity_vector[index]
                )

    def define_heat_transfer_hvac_tu(self):
        for index, row in self.building_zones.iterrows():
            if row['hvac_tu_type'] != '':
                self.control_matrix.at[
                    index + '_temperature',
                    index + '_tu_heat_air_flow'
                ] = (
                        self.control_matrix.at[
                            index + '_temperature',
                            index + '_tu_heat_air_flow'
                        ]
                        + self.parse_parameter('heat_capacity_air')
                        * (
                                self.parse_parameter(row['tu_supply_air_temperature_setpoint'])
                                - self.parse_parameter(
                            self.building_scenarios['linearization_zone_air_temperature_heat']
                        )
                        )
                        / self.heat_capacity_vector[index]
                )
                self.control_matrix.at[
                    index + '_temperature',
                    index + '_tu_cool_air_flow'
                ] = (
                        self.control_matrix.at[
                            index + '_temperature',
                            index + '_tu_cool_air_flow'
                        ]
                        + self.parse_parameter('heat_capacity_air')
                        * (
                                self.parse_parameter(row['tu_supply_air_temperature_setpoint'])
                                - self.parse_parameter(
                            self.building_scenarios['linearization_zone_air_temperature_cool']
                        )
                        )
                        / self.heat_capacity_vector[index]
                )

    def define_heat_transfer_irradiation(self):
        for index_exterior, row_exterior in self.building_surfaces_exterior.iterrows():
            # Direct gains (exterior surfaces)
            if self.parse_parameter(row_exterior['heat_capacity']) != 0:
                self.disturbance_matrix.at[
                    index_exterior + '_temperature',
                    'irradiation_' + row_exterior['direction_name']
                ] = (
                        self.disturbance_matrix.at[
                            index_exterior + '_temperature',
                            'irradiation_' + row_exterior['direction_name']
                        ]
                        + 1
                        / (
                                1
                                + self.parse_parameter(row_exterior['thermal_resistance_surface'])
                                * (
                                        self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_ground']
                                )
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_sky']
                                )
                                )
                        )
                        * self.parse_parameter(row_exterior['irradiation_gain_coefficient'])
                        * self.parse_parameter(row_exterior['surface_area'])
                        * (1 - self.parse_parameter(row_exterior['window_wall_ratio']))
                        / self.heat_capacity_vector[index_exterior]
                )
            else:
                self.disturbance_matrix.at[
                    row_exterior['zone_name'] + '_temperature',
                    'irradiation_' + row_exterior['direction_name']
                ] = (
                        self.disturbance_matrix.at[
                            row_exterior['zone_name'] + '_temperature',
                            'irradiation_' + row_exterior['direction_name']
                        ]
                        + 1
                        / (
                                1
                                + (
                                        2
                                        * self.parse_parameter(row_exterior['thermal_resistance_surface'])
                                        + 1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone'))
                                * (
                                        self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_ground']
                                )
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_sky']
                                )
                                )
                        )
                        * self.parse_parameter(row_exterior['irradiation_gain_coefficient'])
                        * self.parse_parameter(row_exterior['surface_area'])
                        * (1 - self.parse_parameter(row_exterior['window_wall_ratio']))
                        / self.heat_capacity_vector[row_exterior['zone_name']]
                )

            # Indirect gains (interior surfaces, through windows)
            interior_surface_area_total = sum(
                self.parse_parameter(row_interior['surface_area'])
                * (1 - self.parse_parameter(row_interior['window_wall_ratio']))
                for index_interior, row_interior in pd.concat([
                    self.building_surfaces_interior[:][
                        self.building_surfaces_interior['zone_name'] == row_exterior['zone_name']],
                    self.building_surfaces_interior[:][
                        self.building_surfaces_interior['zone_adjacent_name'] == row_exterior['zone_name']],
                    self.building_surfaces_adiabatic[:][
                        self.building_surfaces_adiabatic['zone_name'] == row_exterior['zone_name']]
                ]).iterrows()  # For all surfaces adjacent to the zone that belongs to each exterior surface
            )
            for index_interior, row_interior in pd.concat([
                # For all surfaces adjacent to the zone that belongs to each exterior surface
                self.building_surfaces_interior[:][
                    self.building_surfaces_interior['zone_name'] == row_exterior['zone_name']
                ],
                self.building_surfaces_interior[:][
                    self.building_surfaces_interior['zone_adjacent_name'] == row_exterior['zone_name']
                ],
                self.building_surfaces_adiabatic[:][
                    self.building_surfaces_adiabatic['zone_name'] == row_exterior['zone_name']
                ]
            ]).iterrows():
                if self.parse_parameter(row_interior['heat_capacity']) != 0:
                    # Received by the wall
                    self.disturbance_matrix.at[
                        index_interior + '_temperature',
                        'irradiation_' + row_exterior['direction_name']
                    ] = (
                            self.disturbance_matrix.at[
                                index_interior + '_temperature',
                                'irradiation_' + row_exterior['direction_name']
                            ]
                            + 1
                            / (
                                    1
                                    + self.parse_parameter(row_interior['thermal_resistance_surface'])
                                    * self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                            )
                            * self.parse_parameter(row_exterior['irradiation_transfer_coefficient'])
                            * self.parse_parameter(row_exterior['surface_area'])
                            * self.parse_parameter(row_exterior['window_wall_ratio'])
                            * self.parse_parameter(row_interior['irradiation_gain_coefficient'])
                            * self.parse_parameter(row_interior['surface_area'])
                            * (1 - self.parse_parameter(row_interior['window_wall_ratio']))
                            / self.heat_capacity_vector[index_interior]
                            / interior_surface_area_total
                    )
                    # Received by the zone
                    self.disturbance_matrix.at[
                        row_interior['zone_name'] + '_temperature',
                        'irradiation_' + row_exterior['direction_name']
                    ] = (
                            self.disturbance_matrix.at[
                                row_interior['zone_name'] + '_temperature',
                                'irradiation_' + row_exterior['direction_name']
                            ]
                            + (
                                    1
                                    - 1
                                    / (
                                            1
                                            + self.parse_parameter(row_interior['thermal_resistance_surface'])
                                            * self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                    )
                            )
                            * self.parse_parameter(row_exterior['irradiation_transfer_coefficient'])
                            * self.parse_parameter(row_exterior['surface_area'])
                            * self.parse_parameter(row_exterior['window_wall_ratio'])
                            * self.parse_parameter(row_interior['irradiation_gain_coefficient'])
                            * self.parse_parameter(row_interior['surface_area'])
                            * (1 - self.parse_parameter(row_interior['window_wall_ratio']))
                            / self.heat_capacity_vector[index_interior]
                            / interior_surface_area_total
                    )
                else:
                    self.disturbance_matrix.at[
                        row_interior['zone_name'] + '_temperature',
                        'irradiation_' + row_exterior['direction_name']
                    ] = (
                            self.disturbance_matrix.at[
                                row_interior['zone_name'] + '_temperature',
                                'irradiation_' + row_exterior['direction_name']
                            ]
                            + (
                                    1
                                    - 1
                                    / (
                                            2
                                            * (
                                                    1
                                                    + self.parse_parameter(row_interior['thermal_resistance_surface'])
                                                    * self.parse_parameter(
                                                'heat_transfer_coefficient_surface_to_zone'
                                            )
                                            )
                                    )
                            )
                            * self.parse_parameter(row_exterior['irradiation_transfer_coefficient'])
                            * self.parse_parameter(row_exterior['surface_area'])
                            * self.parse_parameter(row_exterior['window_wall_ratio'])
                            * self.parse_parameter(row_interior['irradiation_gain_coefficient'])
                            * self.parse_parameter(row_interior['surface_area'])
                            * (1 - self.parse_parameter(row_interior['window_wall_ratio']))
                            / self.heat_capacity_vector[row_interior['zone_name']]
                            / interior_surface_area_total
                    )
            for index_interior, row_interior in pd.concat([
                # For all surfaces adjacent to the zone that belongs to each exterior surface that are not adiabatic
                self.building_surfaces_interior[:][
                    self.building_surfaces_interior['zone_name'] == row_exterior['zone_name']
                ],
                self.building_surfaces_interior[:][
                    self.building_surfaces_interior['zone_adjacent_name'] == row_exterior['zone_name']
                ]
            ]).iterrows():
                if self.parse_parameter(row_interior['heat_capacity']) == 0:
                    # Part of the flow is transmitted to the adjacent room
                    self.disturbance_matrix.at[
                        row_interior['zone_adjacent_name'] + '_temperature',
                        'irradiation_' + row_exterior['direction_name']
                    ] = (
                            self.disturbance_matrix.at[
                                row_interior['zone_adjacent_name'] + '_temperature',
                                'irradiation_' + row_exterior['direction_name']
                            ]
                            + 1
                            / (
                                    2
                                    * (
                                            1
                                            + self.parse_parameter(row_interior['thermal_resistance_surface'])
                                            * self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                    )
                            )
                            * self.parse_parameter(row_exterior['irradiation_transfer_coefficient'])
                            * self.parse_parameter(row_exterior['surface_area'])
                            * self.parse_parameter(row_exterior['window_wall_ratio'])
                            * self.parse_parameter(row_interior['irradiation_gain_coefficient'])
                            * self.parse_parameter(row_interior['surface_area'])
                            * (1 - self.parse_parameter(row_interior['window_wall_ratio']))
                            / self.heat_capacity_vector[row_interior['zone_adjacent_name']]
                            / interior_surface_area_total
                    )
            for index_interior, row_interior in pd.concat([
                # For all surfaces adjacent to the zone that belongs to each exterior surface that are adiabatic
                self.building_surfaces_adiabatic[:][
                    self.building_surfaces_adiabatic['zone_name'] == row_exterior['zone_name']
                ]
            ]).iterrows():
                if self.parse_parameter(row_interior['heat_capacity']) == 0:
                    # Part of the flow is transmitted to the same room through the other side of the wall
                    self.disturbance_matrix.at[
                        row_interior['zone_name'] + '_temperature',
                        'irradiation_' + row_exterior['direction_name']
                    ] = (
                            self.disturbance_matrix.at[
                                row_interior['zone_name'] + '_temperature',
                                'irradiation_' + row_exterior['direction_name']
                            ]
                            + 1
                            / (
                                    2
                                    * (
                                            1 + self.parse_parameter(row_interior['thermal_resistance_surface'])
                                            * self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                    )
                            )
                            * self.parse_parameter(row_exterior['irradiation_transfer_coefficient'])
                            * self.parse_parameter(row_exterior['surface_area'])
                            * self.parse_parameter(row_exterior['window_wall_ratio'])
                            * self.parse_parameter(row_interior['irradiation_gain_coefficient'])
                            * self.parse_parameter(row_interior['surface_area'])
                            * (1 - self.parse_parameter(row_interior['window_wall_ratio']))
                            / self.heat_capacity_vector[row_interior['zone_adjacent_name']]
                            / interior_surface_area_total
                    )

    def define_heat_transfer_emission_sky(self):
        for index_exterior, row_exterior in self.building_surfaces_exterior.iterrows():
            # Radiative heat exchange with the sky
            # Windows are considered to have the same emissivity as walls (large wavelengths)

            # Heat flow received by wall
            if self.parse_parameter(row_exterior['heat_capacity']) != 0:
                self.state_matrix.at[
                    index_exterior + '_temperature',
                    index_exterior + '_temperature'
                ] = (
                        self.state_matrix.at[
                            index_exterior + '_temperature',
                            index_exterior + '_temperature'
                        ]
                        - 1
                        / (
                                1
                                + self.parse_parameter(row_exterior['thermal_resistance_surface'])
                                * (
                                        self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_ground']
                                )
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_sky']
                                )
                                )
                        )
                        * self.parse_parameter(row_exterior['heat_transfer_coefficient_surface_to_sky'])
                        * self.parse_parameter(row_exterior['surface_area'])
                        * (1 - self.parse_parameter(row_exterior['window_wall_ratio']))
                        / self.heat_capacity_vector[index_exterior]
                )
                self.disturbance_matrix.at[
                    index_exterior + '_temperature',
                    'sky_temperature'
                ] = (
                        self.disturbance_matrix.at[
                            index_exterior + '_temperature',
                            'sky_temperature'
                        ]
                        + 1
                        / (
                                1
                                + self.parse_parameter(row_exterior['thermal_resistance_surface'])
                                * (
                                        self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_ground']
                                )
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_sky']
                                )
                                )
                        )
                        * self.parse_parameter(row_exterior['heat_transfer_coefficient_surface_to_sky'])
                        * self.parse_parameter(row_exterior['surface_area'])
                        * (1 - self.parse_parameter(row_exterior['window_wall_ratio']))
                        / self.heat_capacity_vector[index_exterior]
                )
            # Heat flow received by zone through wall
            else:
                self.state_matrix.at[
                    row_exterior['zone_name'] + '_temperature',
                    row_exterior['zone_name'] + '_temperature'
                ] = (
                        self.state_matrix.at[
                            row_exterior['zone_name'] + '_temperature',
                            row_exterior['zone_name'] + '_temperature'
                        ]
                        - 1
                        / (
                                1
                                + (
                                        2
                                        * self.parse_parameter(row_exterior['thermal_resistance_surface'])
                                        + 1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone'))
                                * (
                                        self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_ground']
                                )
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_sky']
                                )
                                )
                        )
                        * self.parse_parameter(row_exterior['heat_transfer_coefficient_surface_to_sky'])
                        * self.parse_parameter(row_exterior['surface_area'])
                        * (1 - self.parse_parameter(row_exterior['window_wall_ratio']))
                        / self.heat_capacity_vector[row_exterior['zone_name']]
                )
                self.disturbance_matrix.at[
                    row_exterior['zone_name'] + '_temperature',
                    'sky_temperature'
                ] = (
                        self.disturbance_matrix.at[
                            row_exterior['zone_name'] + '_temperature',
                            'sky_temperature'
                        ]
                        + 1
                        / (
                                1
                                + (
                                        2
                                        * self.parse_parameter(row_exterior['thermal_resistance_surface'])
                                        + 1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                )
                                * (
                                        self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_ground']
                                )
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_sky']
                                )
                                )
                        )
                        * self.parse_parameter(row_exterior['heat_transfer_coefficient_surface_to_sky'])
                        * self.parse_parameter(row_exterior['surface_area'])
                        * (1 - self.parse_parameter(row_exterior['window_wall_ratio']))
                        / self.heat_capacity_vector[row_exterior['zone_name']]
                )

            # Heat flow received by zone through windows
            if self.parse_parameter(row_exterior['window_wall_ratio']) != 0:
                self.state_matrix.at[
                    row_exterior['zone_name'] + '_temperature',
                    row_exterior['zone_name'] + '_temperature'
                ] = (
                        self.state_matrix.at[
                            row_exterior['zone_name'] + '_temperature',
                            row_exterior['zone_name'] + '_temperature'
                        ]
                        - 1
                        / (
                                1
                                + (
                                        2
                                        * self.parse_parameter(row_exterior['thermal_resistance_window'])
                                        + 1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                )
                                * (
                                        self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_ground']
                                )
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_sky']
                                )
                                )
                        )
                        * self.parse_parameter(row_exterior['heat_transfer_coefficient_surface_to_sky'])
                        * self.parse_parameter(row_exterior['surface_area'])
                        * self.parse_parameter(row_exterior['window_wall_ratio'])
                        / self.heat_capacity_vector[row_exterior['zone_name']]
                )
                self.disturbance_matrix.at[
                    row_exterior['zone_name'] + '_temperature',
                    'sky_temperature'
                ] = (
                        self.disturbance_matrix.at[
                            row_exterior['zone_name'] + '_temperature',
                            'sky_temperature'
                        ]
                        + 1
                        / (
                                1
                                + (
                                        2
                                        * self.parse_parameter(row_exterior['thermal_resistance_window'])
                                        + 1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                )
                                * (
                                        self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_ground']
                                )
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_sky']
                                )
                                )
                        )
                        * self.parse_parameter(row_exterior['heat_transfer_coefficient_surface_to_sky'])
                        * self.parse_parameter(row_exterior['surface_area'])
                        * self.parse_parameter(row_exterior['window_wall_ratio'])
                        / self.heat_capacity_vector[row_exterior['zone_name']]
                )

    def define_heat_transfer_emission_environment(self):
        for index_exterior, row_exterior in self.building_surfaces_exterior.iterrows():
            # Radiative heat exchange with the environment
            # Windows are considered to have the same emissivity as walls (large wavelengths)
            # Environment is assumed to be at ambient air temperature

            # Heat flow received by wall
            if self.parse_parameter(row_exterior['heat_capacity']) != 0:
                self.state_matrix.at[
                    index_exterior + '_temperature',
                    index_exterior + '_temperature'
                ] = (
                        self.state_matrix.at[
                            index_exterior + '_temperature',
                            index_exterior + '_temperature'
                        ]
                        - 1
                        / (
                                1
                                + self.parse_parameter(row_exterior['thermal_resistance_surface'])
                                * (
                                        self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_ground']
                                )
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_sky']
                                )
                                )
                        )
                        * self.parse_parameter(row_exterior['heat_transfer_coefficient_surface_to_ground'])
                        * self.parse_parameter(row_exterior['surface_area'])
                        * (1 - self.parse_parameter(row_exterior['window_wall_ratio']))
                        / self.heat_capacity_vector[index_exterior]
                )
                self.disturbance_matrix.at[
                    index_exterior + '_temperature',
                    'ambient_air_temperature'
                ] = (
                        self.disturbance_matrix.at[
                            index_exterior + '_temperature',
                            'ambient_air_temperature'
                        ]
                        + 1
                        / (
                                1
                                + self.parse_parameter(row_exterior['thermal_resistance_surface'])
                                * (
                                        self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_ground']
                                )
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_sky']
                                )
                                )
                        )
                        * self.parse_parameter(row_exterior['heat_transfer_coefficient_surface_to_ground'])
                        * self.parse_parameter(row_exterior['surface_area'])
                        * (1 - self.parse_parameter(row_exterior['window_wall_ratio']))
                        / self.heat_capacity_vector[index_exterior]
                )
            # Heat flow received by zone through wall
            else:
                self.state_matrix.at[
                    row_exterior['zone_name'] + '_temperature',
                    row_exterior['zone_name'] + '_temperature'
                ] = (
                        self.state_matrix.at[
                            row_exterior['zone_name'] + '_temperature',
                            row_exterior['zone_name'] + '_temperature'
                        ]
                        - 1
                        / (
                                1
                                + (
                                        2
                                        * self.parse_parameter(row_exterior['thermal_resistance_surface'])
                                        + 1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone'))
                                * (
                                        self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_ground']
                                )
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_sky']
                                )
                                )
                        )
                        * self.parse_parameter(row_exterior['heat_transfer_coefficient_surface_to_ground'])
                        * self.parse_parameter(row_exterior['surface_area'])
                        * (1 - self.parse_parameter(row_exterior['window_wall_ratio']))
                        / self.heat_capacity_vector[row_exterior['zone_name']]
                )
                self.disturbance_matrix.at[
                    row_exterior['zone_name'] + '_temperature',
                    'ambient_air_temperature'
                ] = (
                        self.disturbance_matrix.at[
                            row_exterior['zone_name'] + '_temperature',
                            'ambient_air_temperature'
                        ]
                        + 1
                        / (
                                1
                                + (
                                        2
                                        * self.parse_parameter(row_exterior['thermal_resistance_surface'])
                                        + 1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone'))
                                * (
                                        self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_ground']
                                )
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_sky']
                                )
                                )
                        )
                        * self.parse_parameter(row_exterior['heat_transfer_coefficient_surface_to_ground'])
                        * self.parse_parameter(row_exterior['surface_area'])
                        * (1 - self.parse_parameter(row_exterior['window_wall_ratio']))
                        / self.heat_capacity_vector[row_exterior['zone_name']]
                )

            # Heat flow received by zone through windows
            if self.parse_parameter(row_exterior['window_wall_ratio']) != 0:
                self.state_matrix.at[
                    row_exterior['zone_name'] + '_temperature',
                    row_exterior['zone_name'] + '_temperature'
                ] = (
                        self.state_matrix.at[
                            row_exterior['zone_name'] + '_temperature',
                            row_exterior['zone_name'] + '_temperature'
                        ]
                        - 1
                        / (
                                1
                                + (
                                        2
                                        * self.parse_parameter(row_exterior['thermal_resistance_window'])
                                        + 1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone'))
                                * (
                                        self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_ground']
                                )
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_sky']
                                )
                                )
                        )
                        * self.parse_parameter(row_exterior['heat_transfer_coefficient_surface_to_ground'])
                        * self.parse_parameter(row_exterior['surface_area'])
                        * self.parse_parameter(row_exterior['window_wall_ratio'])
                        / self.heat_capacity_vector[row_exterior['zone_name']]
                )
                self.disturbance_matrix.at[
                    row_exterior['zone_name'] + '_temperature',
                    'ambient_air_temperature'
                ] = (
                        self.disturbance_matrix.at[
                            row_exterior['zone_name'] + '_temperature',
                            'ambient_air_temperature'
                        ]
                        + 1
                        / (
                                1
                                + (
                                        2
                                        * self.parse_parameter(row_exterior['thermal_resistance_window'])
                                        + 1
                                        / self.parse_parameter('heat_transfer_coefficient_surface_to_zone')
                                )
                                * (
                                        self.parse_parameter('heat_transfer_coefficient_surface_to_ambient')
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_ground']
                                )
                                        + self.parse_parameter(
                                    row_exterior['heat_transfer_coefficient_surface_to_sky']
                                )
                                )
                        )
                        * self.parse_parameter(row_exterior['heat_transfer_coefficient_surface_to_ground'])
                        * self.parse_parameter(row_exterior['surface_area'])
                        * self.parse_parameter(row_exterior['window_wall_ratio'])
                        / self.heat_capacity_vector[row_exterior['zone_name']]
                )

    def define_co2_transfer_hvac_ahu(self):
        if self.building_scenarios['co2_model_type'][0] != '':
            for index, row in self.building_zones.iterrows():
                if (row['hvac_ahu_type'] != '') | (row['window_type'] != ''):
                    self.state_matrix.at[
                        index + '_co2_concentration',
                        index + '_co2_concentration'
                    ] = (
                            self.state_matrix.at[
                                index + '_co2_concentration',
                                index + '_co2_concentration'
                            ]
                            - (
                                    self.parse_parameter(
                                        self.building_scenarios['linearization_ventilation_rate_per_square_meter']
                                    )
                                    / self.parse_parameter(row['zone_height'])
                            )
                    )
                    if row['hvac_ahu_type'] != '':
                        self.control_matrix.at[
                            index + '_co2_concentration',
                            index + '_ahu_heat_air_flow'
                        ] = (
                                self.control_matrix.at[
                                    index + '_co2_concentration',
                                    index + '_ahu_heat_air_flow'
                                ]
                                - (
                                        self.parse_parameter(self.building_scenarios['linearization_co2_concentration'])
                                        / self.parse_parameter(row['zone_height'])
                                        / self.parse_parameter(row['zone_area']))
                        )
                        self.control_matrix.at[
                            index + '_co2_concentration',
                            index + '_ahu_cool_air_flow'
                        ] = (
                                self.control_matrix.at[
                                    index + '_co2_concentration',
                                    index + '_ahu_cool_air_flow'
                                ]
                                - (
                                        self.parse_parameter(self.building_scenarios['linearization_co2_concentration'])
                                        / self.parse_parameter(row['zone_height'])
                                        / self.parse_parameter(row['zone_area']))
                        )
                    if row['window_type'] != '':
                        self.control_matrix.at[
                            index + '_co2_concentration',
                            index + '_window_air_flow'
                        ] = (
                                self.control_matrix.at[
                                    index + '_co2_concentration',
                                    index + '_window_air_flow'
                                ]
                                - (
                                        self.parse_parameter(self.building_scenarios['linearization_co2_concentration'])
                                        / self.parse_parameter(row['zone_height'])
                                        / self.parse_parameter(row['zone_area']))
                        )
                    # self.disturbance_matrix.at[index + '_co2_concentration', 'constant'] = (
                    #         self.disturbance_matrix.at[index + '_co2_concentration', 'constant']
                    #         - (
                    #                 self.parse_parameter(self.building_scenarios['linearization_co2_concentration']
                    #                 )
                    #                 * self.parse_parameter(row['infiltration_rate']))
                    # )  # TODO: Revise infiltration
                    self.disturbance_matrix.at[
                        index + '_co2_concentration',
                        row['internal_gain_type'] + '_occupancy'
                    ] = (
                            self.disturbance_matrix.at[
                                index + '_co2_concentration',
                                row['internal_gain_type'] + '_occupancy'
                            ]
                            + (
                                    self.parse_parameter('co2_generation_rate_per_person')
                                    / self.parse_parameter(row['zone_height'])
                                    / self.parse_parameter(row['zone_area'])
                            )
                    )
                    # division by zone_area since the occupancy here is in p
                    # if iterative and robust BM, no division by zone_area since the occupancy there is in p/m2
                    self.disturbance_matrix.at[
                        index + '_co2_concentration',
                        'constant'
                    ] = (
                            self.disturbance_matrix.at[
                                index + '_co2_concentration',
                                'constant'
                            ]
                            + (
                                    self.parse_parameter(
                                        self.building_scenarios['linearization_ventilation_rate_per_square_meter']
                                    )
                                    * self.parse_parameter(self.building_scenarios['linearization_co2_concentration'])
                                    / self.parse_parameter(row['zone_height'])
                            )
                    )

    def define_humidity_transfer_hvac_ahu(self):
        if self.building_scenarios['humidity_model_type'][0] != '':
            for index, row in self.building_zones.iterrows():
                if row['hvac_ahu_type'] != '':
                    self.state_matrix.at[
                        index + '_absolute_humidity',
                        index + '_absolute_humidity'
                    ] = (
                            self.state_matrix.at[
                                index + '_absolute_humidity',
                                index + '_absolute_humidity'
                            ]
                            - (
                                    self.parse_parameter(
                                        self.building_scenarios['linearization_ventilation_rate_per_square_meter']
                                    )
                                    / self.parse_parameter(row['zone_height'])
                            )
                    )
                    self.control_matrix.at[index + '_absolute_humidity', index + '_ahu_heat_air_flow'] = (
                            self.control_matrix.at[index + '_absolute_humidity', index + '_ahu_heat_air_flow']
                            - (
                                    (
                                            self.parse_parameter(
                                                self.building_scenarios['linearization_zone_air_humidity_ratio']
                                            )
                                            - humid_air_properties(
                                        'W',
                                        'T',
                                        self.parse_parameter(row['ahu_supply_air_temperature_setpoint'])
                                        + 273.15,
                                        'R',
                                        self.parse_parameter(row['ahu_supply_air_relative_humidity_setpoint']),
                                        'P',
                                        101325
                                    )
                                    )
                                    / self.parse_parameter(row['zone_height'])
                                    / self.parse_parameter(row['zone_area'])
                            )
                    )
                    self.control_matrix.at[
                        index + '_absolute_humidity',
                        index + '_ahu_cool_air_flow'
                    ] = (
                            self.control_matrix.at[
                                index + '_absolute_humidity',
                                index + '_ahu_cool_air_flow'
                            ]
                            - (
                                    (
                                            self.parse_parameter(
                                                self.building_scenarios['linearization_zone_air_humidity_ratio']
                                            )
                                            - humid_air_properties(
                                        'W',
                                        'T',
                                        self.parse_parameter(row['ahu_supply_air_temperature_setpoint'])
                                        + 273.15,
                                        'R',
                                        self.parse_parameter(row['ahu_supply_air_relative_humidity_setpoint']),
                                        'P',
                                        101325
                                    )
                                    )
                                    / self.parse_parameter(row['zone_height'])
                                    / self.parse_parameter(row['zone_area'])
                            )
                    )
                    if row['window_type'] != '':
                        self.control_matrix.at[
                            index + '_absolute_humidity',
                            index + '_window_air_flow'
                        ] = (
                                self.control_matrix.at[
                                    index + '_absolute_humidity',
                                    index + '_window_air_flow'
                                ]
                                - (
                                        (
                                                self.parse_parameter(
                                                    self.building_scenarios['linearization_zone_air_humidity_ratio']
                                                )
                                                - self.parse_parameter(
                                            self.building_scenarios['linearization_ambient_air_humidity_ratio']
                                        )
                                        )
                                        / self.parse_parameter(row['zone_height'])
                                        / self.parse_parameter(row['zone_area'])
                                )
                        )
                    # self.disturbance_matrix.at[index + '_absolute_humidity', 'constant'] = (
                    #         self.disturbance_matrix.at[index + '_absolute_humidity', 'constant']
                    #         - (
                    #                 (self.parse_parameter(
                    #                     self.building_scenarios['linearization_zone_air_humidity_ratio'])
                    #                  - self.parse_parameter(
                    #                     self.building_scenarios['linearization_ambient_air_humidity_ratio']))
                    #                 * self.parse_parameter(row['infiltration_rate'])
                    #         )
                    # )  # TODO: Revise infiltration
                    self.disturbance_matrix.at[
                        index + '_absolute_humidity',
                        row['internal_gain_type'] + '_occupancy'
                    ] = (
                            self.disturbance_matrix.at[
                                index + '_absolute_humidity',
                                row['internal_gain_type'] + '_occupancy'
                            ]
                            + (
                                    self.parse_parameter('moisture_generation_rate_per_person')
                                    / self.parse_parameter(row['zone_height'])
                                    / self.parse_parameter(row['zone_area'])
                                    / self.parse_parameter('density_air')
                            )
                    )
                    self.disturbance_matrix.at[
                        index + '_absolute_humidity',
                        'constant'
                    ] = (
                            self.disturbance_matrix.at[
                                index + '_absolute_humidity',
                                'constant'
                            ]
                            + (
                                    self.parse_parameter(
                                        self.building_scenarios['linearization_ventilation_rate_per_square_meter']
                                    )
                                    * self.parse_parameter(
                                self.building_scenarios['linearization_zone_air_humidity_ratio']
                            )
                                    / self.parse_parameter(row['zone_height'])
                            )
                    )

    def define_output_zone_temperature(self):
        for index, row in self.building_zones.iterrows():
            self.state_output_matrix.at[
                index + '_temperature',
                index + '_temperature'
            ] = 1

    def define_output_zone_co2_concentration(self):
        if self.building_scenarios['co2_model_type'][0] != '':
            for index, row in self.building_zones.iterrows():
                if (row['hvac_ahu_type'] != '') | (row['window_type'] != ''):
                    self.state_output_matrix.at[
                        index + '_co2_concentration',
                        index + '_co2_concentration'
                    ] = 1

    def define_output_zone_humidity(self):
        if self.building_scenarios['humidity_model_type'][0] != '':
            for index, row in self.building_zones.iterrows():
                if row['hvac_ahu_type'] != '':
                    self.state_output_matrix.at[
                        index + '_absolute_humidity',
                        index + '_absolute_humidity'
                    ] = 1

    def define_output_hvac_generic_power(self):
        for index, row in self.building_zones.iterrows():
            if row['hvac_generic_type'] != '':
                self.control_output_matrix.at[
                    index + '_generic_heat_power',
                    index + '_generic_heat_thermal_power'
                ] = (
                        self.control_output_matrix.at[
                            index + '_generic_heat_power',
                            index + '_generic_heat_thermal_power'
                        ]
                        + 1
                        / self.parse_parameter(row['generic_heating_efficiency'])
                )
                self.control_output_matrix.at[
                    index + '_generic_cool_power',
                    index + '_generic_cool_thermal_power'
                ] = (
                        self.control_output_matrix.at[
                            index + '_generic_cool_power',
                            index + '_generic_cool_thermal_power'
                        ]
                        + 1
                        / self.parse_parameter(row['generic_cooling_efficiency'])
                )

    def define_output_hvac_ahu_electric_power(self):
        for index, row in self.building_zones.iterrows():
            if row['hvac_ahu_type'] != '':
                # Calculate enthalpies
                # TODO: Remove unnecessary HVAC types
                if (
                        row['ahu_cooling_type'] == 'default'
                        and row['ahu_heating_type'] == 'default'
                        and row['ahu_dehumidification_type'] == 'default'
                        and row['ahu_return_air_heat_recovery_type'] == 'default'
                ):
                    if (
                            self.parse_parameter(self.building_scenarios['linearization_ambient_air_humidity_ratio'])
                            <= humid_air_properties(
                        'W',
                        'R',
                        self.parse_parameter(row['ahu_supply_air_relative_humidity_setpoint'])
                        / 100,
                        'T',
                        self.parse_parameter(self.building_scenarios['linearization_ambient_air_temperature'])
                        + 273.15,
                        'P',
                        101325
                    )
                    ):
                        delta_enthalpy_ahu_cooling = min(
                            0,
                            humid_air_properties(
                                'H',
                                'T',
                                self.parse_parameter(row['ahu_supply_air_temperature_setpoint'])
                                + 273.15,
                                'W',
                                self.parse_parameter(
                                    self.building_scenarios['linearization_ambient_air_humidity_ratio']
                                ),
                                'P',
                                101325
                            )
                            - humid_air_properties(
                                'H',
                                'T',
                                self.parse_parameter(self.building_scenarios['linearization_ambient_air_temperature'])
                                + 273.15,
                                'W',
                                self.parse_parameter(
                                    self.building_scenarios['linearization_ambient_air_humidity_ratio']
                                ),
                                'P',
                                101325
                            )
                        )
                        delta_enthalpy_ahu_heating = max(
                            0,
                            humid_air_properties(
                                'H',
                                'T',
                                self.parse_parameter(row['ahu_supply_air_temperature_setpoint'])
                                + 273.15,
                                'W',
                                self.parse_parameter(
                                    self.building_scenarios['linearization_ambient_air_humidity_ratio']
                                ),
                                'P',
                                101325
                            )
                            - humid_air_properties(
                                'H',
                                'T',
                                self.parse_parameter(self.building_scenarios['linearization_ambient_air_temperature'])
                                + 273.15,
                                'W',
                                self.parse_parameter(
                                    self.building_scenarios['linearization_ambient_air_humidity_ratio']
                                ),
                                'P',
                                101325
                            )
                        )
                        delta_enthalpy_cooling_recovery = min(
                            0,
                            self.parse_parameter(row['ahu_return_air_heat_recovery_efficiency'])
                            * (
                                    humid_air_properties(
                                        'H',
                                        'T',
                                        self.parse_parameter(
                                            self.building_scenarios['linearization_zone_air_temperature_heat']
                                        )
                                        + 273.15,
                                        'W',
                                        self.parse_parameter(
                                            self.building_scenarios['linearization_ambient_air_humidity_ratio']
                                        ),
                                        'P',
                                        101325
                                    )
                                    - humid_air_properties(
                                'H',
                                'T',
                                self.parse_parameter(
                                    self.building_scenarios['linearization_ambient_air_temperature']
                                )
                                + 273.15,
                                'W',
                                self.parse_parameter(
                                    self.building_scenarios['linearization_ambient_air_humidity_ratio']
                                ),
                                'P',
                                101325
                            )
                            )
                        )
                        delta_enthalpy_heating_recovery = max(
                            0,
                            self.parse_parameter(row['ahu_return_air_heat_recovery_efficiency'])
                            * (
                                    humid_air_properties(
                                        'H',
                                        'T',
                                        self.parse_parameter(
                                            self.building_scenarios['linearization_zone_air_temperature_heat']
                                        )
                                        + 273.15,
                                        'W',
                                        self.parse_parameter(
                                            self.building_scenarios['linearization_ambient_air_humidity_ratio']
                                        ),
                                        'P',
                                        101325
                                    )
                                    - humid_air_properties(
                                'H',
                                'T',
                                self.parse_parameter(
                                    self.building_scenarios['linearization_ambient_air_temperature']
                                )
                                + 273.15,
                                'W',
                                self.parse_parameter(
                                    self.building_scenarios['linearization_ambient_air_humidity_ratio']),
                                'P',
                                101325
                            )
                            )
                        )
                    else:
                        delta_enthalpy_ahu_cooling = (
                                humid_air_properties(
                                    'H',
                                    'R',
                                    1,
                                    'W',
                                    humid_air_properties(
                                        'W',
                                        'T',
                                        self.parse_parameter(row['ahu_supply_air_temperature_setpoint'])
                                        + 273.15,
                                        'R',
                                        self.parse_parameter(
                                            row['ahu_supply_air_relative_humidity_setpoint']
                                        )
                                        / 100,
                                        'P',
                                        101325
                                    ),
                                    'P',
                                    101325
                                )
                                - humid_air_properties(
                            'H',
                            'T',
                            self.parse_parameter(
                                self.building_scenarios['linearization_ambient_air_temperature']
                            )
                            + 273.15,
                            'W',
                            self.parse_parameter(
                                self.building_scenarios['linearization_ambient_air_humidity_ratio']
                            ),
                            'P',
                            101325
                        )
                        )
                        delta_enthalpy_ahu_heating = (
                                humid_air_properties(
                                    'H',
                                    'T',
                                    self.parse_parameter(row['ahu_supply_air_temperature_setpoint'])
                                    + 273.15,
                                    'R',
                                    self.parse_parameter(row['ahu_supply_air_relative_humidity_setpoint'])
                                    / 100,
                                    'P',
                                    101325
                                )
                                - humid_air_properties(
                            'H',
                            'R',
                            1,
                            'W',
                            humid_air_properties(
                                'W',
                                'T',
                                self.parse_parameter(row['ahu_supply_air_temperature_setpoint'])
                                + 273.15,
                                'R',
                                self.parse_parameter(row['ahu_supply_air_relative_humidity_setpoint'])
                                / 100,
                                'P',
                                101325
                            ),
                            'P',
                            101325
                        )
                        )
                        delta_enthalpy_cooling_recovery = min(
                            0,
                            self.parse_parameter(row['ahu_return_air_heat_recovery_efficiency'])
                            * (
                                    humid_air_properties(
                                        'H',
                                        'T',
                                        self.parse_parameter(
                                            self.building_scenarios['linearization_zone_air_temperature_heat']
                                        )
                                        + 273.15,
                                        'W',
                                        self.parse_parameter(
                                            self.building_scenarios['linearization_zone_air_humidity_ratio']
                                        ),
                                        'P',
                                        101325
                                    )
                                    - humid_air_properties(
                                'H',
                                'T',
                                self.parse_parameter(
                                    self.building_scenarios['linearization_ambient_air_temperature']
                                )
                                + 273.15,
                                'W',
                                self.parse_parameter(
                                    self.building_scenarios['linearization_zone_air_humidity_ratio']
                                ),
                                'P',
                                101325
                            )
                            )
                        )
                        delta_enthalpy_heating_recovery = max(
                            0,
                            self.parse_parameter(row['ahu_return_air_heat_recovery_efficiency'])
                            * (
                                    humid_air_properties(
                                        'H',
                                        'T',
                                        self.parse_parameter(
                                            self.building_scenarios['linearization_zone_air_temperature_heat']
                                        )
                                        + 273.15,
                                        'W',
                                        self.parse_parameter(
                                            self.building_scenarios['linearization_zone_air_humidity_ratio']
                                        ),
                                        'P',
                                        101325
                                    )
                                    - humid_air_properties(
                                'H',
                                'T',
                                self.parse_parameter(
                                    self.building_scenarios['linearization_ambient_air_temperature']
                                )
                                + 273.15,
                                'W',
                                self.parse_parameter(
                                    self.building_scenarios['linearization_zone_air_humidity_ratio']
                                ),
                                'P',
                                101325
                            )
                            )
                        )

                # Matrix entries
                self.control_output_matrix.at[
                    index + '_ahu_heat_electric_power',
                    index + '_ahu_heat_air_flow'
                ] = (
                        self.control_output_matrix.at[
                            index + '_ahu_heat_electric_power',
                            index + '_ahu_heat_air_flow'
                        ]
                        + self.parse_parameter('density_air')
                        * (
                                (
                                        abs(delta_enthalpy_ahu_cooling)
                                        - abs(delta_enthalpy_cooling_recovery)
                                )
                                / self.parse_parameter(row['ahu_cooling_efficiency'])
                                + (
                                        abs(delta_enthalpy_ahu_heating)
                                        - abs(delta_enthalpy_heating_recovery)
                                )
                                / self.parse_parameter(row['ahu_heating_efficiency'])
                                + self.parse_parameter(row['ahu_fan_efficiency'])
                        )
                )
                self.control_output_matrix.at[
                    index + '_ahu_cool_electric_power',
                    index + '_ahu_cool_air_flow'
                ] = (
                        self.control_output_matrix.at[
                            index + '_ahu_cool_electric_power',
                            index + '_ahu_cool_air_flow'
                        ]
                        + self.parse_parameter('density_air')
                        * (
                                (
                                        abs(delta_enthalpy_ahu_cooling)
                                        - abs(delta_enthalpy_cooling_recovery)
                                )
                                / self.parse_parameter(row['ahu_cooling_efficiency'])
                                + (
                                        abs(delta_enthalpy_ahu_heating)
                                        - abs(delta_enthalpy_heating_recovery)
                                )
                                / self.parse_parameter(row['ahu_heating_efficiency'])
                                + self.parse_parameter(row['ahu_fan_efficiency'])
                        )
                )

    def define_output_hvac_tu_electric_power(self):
        for index, row in self.building_zones.iterrows():
            if row['hvac_tu_type'] != '':
                # Calculate enthalpies
                if (
                        row['tu_cooling_type'] == 'default'
                        and row['tu_heating_type'] == 'default'
                ):
                    if row['tu_air_intake_type'] == 'zone':
                        delta_enthalpy_tu_cooling = self.parse_parameter('heat_capacity_air') * (
                                self.parse_parameter(self.building_scenarios['linearization_zone_air_temperature_cool'])
                                - self.parse_parameter(row['tu_supply_air_temperature_setpoint'])
                        )
                        delta_enthalpy_tu_heating = self.parse_parameter('heat_capacity_air') * (
                                self.parse_parameter(self.building_scenarios['linearization_zone_air_temperature_heat'])
                                - self.parse_parameter(row['tu_supply_air_temperature_setpoint'])
                        )
                    elif row['tu_air_intake_type'] == 'ahu':
                        delta_enthalpy_tu_cooling = self.parse_parameter('heat_capacity_air') * (
                                self.parse_parameter(self.building_scenarios['ahu_supply_air_temperature_setpoint'])
                                - self.parse_parameter(row['tu_supply_air_temperature_setpoint'])
                        )
                        delta_enthalpy_tu_heating = self.parse_parameter('heat_capacity_air') * (
                                self.parse_parameter(self.building_scenarios['ahu_supply_air_temperature_setpoint'])
                                - self.parse_parameter(row['tu_supply_air_temperature_setpoint'])
                        )

                # Matrix entries
                self.control_output_matrix.at[
                    index + '_tu_heat_electric_power',
                    index + '_tu_heat_air_flow'
                ] = (
                        self.control_output_matrix.at[
                            index + '_tu_heat_electric_power',
                            index + '_tu_heat_air_flow'
                        ]
                        + self.parse_parameter('density_air')
                        * (
                                abs(delta_enthalpy_tu_heating)
                                / self.parse_parameter(row['tu_heating_efficiency'])
                                + self.parse_parameter(row['tu_fan_efficiency'])
                        )
                )
                self.control_output_matrix.at[
                    index + '_tu_cool_electric_power',
                    index + '_tu_cool_air_flow'
                ] = (
                        self.control_output_matrix.at[
                            index + '_tu_cool_electric_power',
                            index + '_tu_cool_air_flow']
                        + self.parse_parameter('density_air')
                        * (
                                abs(delta_enthalpy_tu_cooling)
                                / self.parse_parameter(row['tu_cooling_efficiency'])
                                + self.parse_parameter(row['tu_fan_efficiency'])
                        )
                )

    def define_output_fresh_air_flow(self):
        for index, row in self.building_zones.iterrows():
            if row['hvac_ahu_type'] != '':
                self.control_output_matrix.at[
                    index + '_total_fresh_air_flow',
                    index + '_ahu_heat_air_flow'
                ] = 1
                self.control_output_matrix.at[
                    index + '_total_fresh_air_flow',
                    index + '_ahu_cool_air_flow'
                ] = 1
            if row['window_type'] != '':
                self.control_output_matrix.at[
                    index + '_total_fresh_air_flow',
                    index + '_window_air_flow'
                ] = 1
            if (row['window_type'] != '') | (row['hvac_ahu_type'] != ''):
                self.disturbance_output_matrix.at[
                    index + '_total_fresh_air_flow',
                    'constant'
                ] = (
                        self.disturbance_output_matrix.at[
                            index + '_total_fresh_air_flow',
                            'constant'
                        ]
                        + self.parse_parameter(row['infiltration_rate'])
                        * self.parse_parameter(row['zone_area'])
                        * self.parse_parameter(row['zone_height'])
                )  # TODO: Revise infiltration

    def define_output_ahu_fresh_air_flow(self):
        for index, row in self.building_zones.iterrows():
            if row['hvac_ahu_type'] != '':
                self.control_output_matrix.at[
                    index + '_ahu_fresh_air_flow',
                    index + '_ahu_heat_air_flow'
                ] = 1
                self.control_output_matrix.at[
                    index + '_ahu_fresh_air_flow',
                    index + '_ahu_cool_air_flow'
                ] = 1

    def define_output_window_fresh_air_flow(self):
        for index, row in self.building_zones.iterrows():
            if row['window_type'] != '':
                self.control_output_matrix.at[
                    index + '_window_fresh_air_flow',
                    index + '_window_air_flow'
                ] = 1

    def load_disturbance_timeseries(self, conn):
        # Load weather timeseries
        weather_timeseries = pd.read_sql(
            """
            select * from weather_timeseries 
            where weather_type='{}'
            and time between '{}' and '{}'
            """.format(
                self.building_scenarios['weather_type'][0],
                self.building_scenarios['time_start'][0],
                self.building_scenarios['time_end'][0]
            ),
            conn
        )
        weather_timeseries.index = pd.to_datetime(weather_timeseries['time'])

        # Load internal gain timeseries
        building_internal_gain_timeseries = pd.read_sql(
            """
            select * from building_internal_gain_timeseries 
            where internal_gain_type in ({})
            and time between '{}' and '{}'
            """.format(
                ", ".join([
                    "'{}'".format(data_set_name) for data_set_name in self.building_zones['internal_gain_type'].unique()
                ]),
                self.building_scenarios['time_start'][0],
                self.building_scenarios['time_end'][0]
            ),
            conn
        )

        # Pivot internal gain timeseries, so there is one `_occupancy` & one `_appliances` for each `internal_gain_type`
        building_internal_gain_occupancy_timeseries = building_internal_gain_timeseries.pivot(
            index='time',
            columns='internal_gain_type',
            values='internal_gain_occupancy'
        )
        building_internal_gain_occupancy_timeseries.columns = (
                building_internal_gain_occupancy_timeseries.columns + '_occupancy'
        )
        building_internal_gain_appliances_timeseries = building_internal_gain_timeseries.pivot(
            index='time',
            columns='internal_gain_type',
            values='internal_gain_appliances'
        )
        building_internal_gain_appliances_timeseries.columns = (
                building_internal_gain_appliances_timeseries.columns + '_appliances'
        )
        building_internal_gain_timeseries = pd.concat(
            [
                building_internal_gain_occupancy_timeseries,
                building_internal_gain_appliances_timeseries
            ],
            axis='columns'
        )
        building_internal_gain_timeseries.index = pd.to_datetime(building_internal_gain_timeseries.index)

        # Reindex and construct full disturbance timeseries
        self.disturbance_timeseries = pd.concat(
            [
                weather_timeseries[[
                    'ambient_air_temperature',
                    'sky_temperature',
                    'irradiation_horizontal',
                    'irradiation_east',
                    'irradiation_south',
                    'irradiation_west',
                    'irradiation_north'
                ]].reindex(
                    index=self.time_vector, method='nearest'
                ),
                building_internal_gain_timeseries.reindex(
                    index=self.time_vector, method='nearest'
                )
            ],
            axis='columns'
        )

        # Append constant (only when it should be considered)
        if self.define_constant:
            self.disturbance_timeseries = pd.concat(
                [
                    self.disturbance_timeseries,
                    pd.Series(
                        1.0,
                        self.time_vector,
                        name='constant'
                    )
                ],
                axis='columns'
            )

        # Transpose to get correct orientation for matrix multiplication with disturbance_matrix
        self.disturbance_timeseries = self.disturbance_timeseries.transpose()

    def define_output_constraint_timeseries(self, conn):
        """
        - Generate minimum/maximum constraint timeseries based on `building_zone_constraint_profiles`
        - TODO: Make construction / interpolation simpler and more efficient
        """
        # Initialise constraint timeseries as +/- infinity
        self.output_constraint_timeseries_maximum = pd.DataFrame(
            1.0 * np.infty,
            self.index_time,
            self.index_outputs
        )
        self.output_constraint_timeseries_minimum = -self.output_constraint_timeseries_maximum

        # Outputs that are some kind of power can only be positive (greater than zero)
        self.output_constraint_timeseries_minimum.loc[
        :,
        [column for column in self.output_constraint_timeseries_minimum.columns if '_power' in column]
        ] = 0

        # Outputs that are some kind of flow can only be positive (greater than zero)
        self.output_constraint_timeseries_minimum.loc[
        :,
        [column for column in self.output_constraint_timeseries_minimum.columns if '_flow' in column]
        ] = 0

        # If a heating/cooling session is defined, the heating/cooling air flow is forced to 0
        # Comment: The cooling or heating coil may still be working, because of the dehumidification,
        # however it would not appear explicitly in the output.
        if self.building_scenarios['heating_cooling_session'][0] == 'heating':
            self.output_constraint_timeseries_maximum.loc[
            :, [column for column in self.output_constraint_timeseries_minimum.columns if '_cool' in column]
            ] = 0
        if self.building_scenarios['heating_cooling_session'][0] == 'cooling':
            self.output_constraint_timeseries_maximum.loc[
            :, [column for column in self.output_constraint_timeseries_minimum.columns if '_heat' in column]
            ] = 0

        for index_zone, row_zone in self.building_zones.iterrows():
            # For each zone, select zone_constraint_profile
            building_zone_constraint_profile = pd.read_sql(
                """
                select * from building_zone_constraint_profiles 
                where zone_constraint_profile='{}'
                """.format(row_zone['zone_constraint_profile']),
                conn
            )

            # Create index function for `from_weekday` (mapping from `row_time.weekday()` to `from_weekday`)
            constraint_profile_index_day = interp1d(
                building_zone_constraint_profile['from_weekday'],
                building_zone_constraint_profile['from_weekday'],
                kind='zero',
                fill_value='extrapolate'
            )
            for row_time in self.time_vector:
                # Create index function for `from_time` (mapping `row_time.timestamp` to `from_time`)
                constraint_profile_index_time = interp1d(
                    pd.to_datetime(
                        str(row_time.date())
                        + ' '
                        + building_zone_constraint_profile['from_time'][
                            building_zone_constraint_profile['from_weekday']
                            == constraint_profile_index_day(row_time.weekday())
                            ]
                    ).view('int64'),
                    building_zone_constraint_profile.index[
                        building_zone_constraint_profile['from_weekday']
                        == constraint_profile_index_day(row_time.weekday())
                        ].values,
                    kind='zero',
                    fill_value='extrapolate'
                )

                # Select constraint values
                self.output_constraint_timeseries_minimum.at[
                    row_time,
                    index_zone + '_temperature'
                ] = self.parse_parameter(
                    building_zone_constraint_profile['minimum_air_temperature'][
                        int(constraint_profile_index_time(row_time.to_datetime64().astype('int64')))
                    ]
                )
                self.output_constraint_timeseries_maximum.at[
                    row_time,
                    index_zone + '_temperature'
                ] = self.parse_parameter(
                    building_zone_constraint_profile['maximum_air_temperature'][
                        int(constraint_profile_index_time(row_time.to_datetime64().astype('int64')))
                    ]
                )
                if (row_zone['hvac_ahu_type'] != '') | (row_zone['window_type'] != ''):
                    if self.building_scenarios['demand_controlled_ventilation_type'][0] != '':
                        if self.building_scenarios['co2_model_type'][0] != '':
                            self.output_constraint_timeseries_maximum.at[
                                row_time,
                                index_zone + '_co2_concentration'
                            ] = (
                                self.parse_parameter(
                                    building_zone_constraint_profile['maximum_co2_concentration'][
                                        int(constraint_profile_index_time(row_time.to_datetime64().astype('int64')))
                                    ]
                                )
                            )
                            self.output_constraint_timeseries_minimum.at[
                                row_time,
                                index_zone + '_total_fresh_air_flow'
                            ] = (
                                    self.parse_parameter(
                                        building_zone_constraint_profile['minimum_fresh_air_flow_per_area'][
                                            int(constraint_profile_index_time(row_time.to_datetime64().astype('int64')))
                                        ]
                                    )
                                    * self.parse_parameter(row_zone['zone_area'])
                            )
                        else:
                            self.output_constraint_timeseries_minimum.at[
                                row_time, index_zone + '_total_fresh_air_flow'
                            ] = (
                                    self.parse_parameter(
                                        building_zone_constraint_profile['minimum_fresh_air_flow_per_person'][
                                            int(constraint_profile_index_time(row_time.to_datetime64().astype('int64')))
                                        ]
                                    )
                                    * (
                                            self.disturbance_timeseries.transpose()[
                                                self.building_zones["internal_gain_type"].loc[index_zone] + "_occupancy"
                                                ].loc[row_time] * self.parse_parameter(row_zone['zone_area'])
                                            + self.parse_parameter(
                                        building_zone_constraint_profile['minimum_fresh_air_flow_per_area'][
                                            int(constraint_profile_index_time(
                                                row_time.to_datetime64().astype('int64')
                                            ))
                                        ]
                                    )
                                            * self.parse_parameter(row_zone['zone_area'])
                                    )
                            )
                    else:
                        if row_zone['hvac_ahu_type'] != '':
                            self.output_constraint_timeseries_minimum.at[
                                row_time,
                                index_zone + '_total_fresh_air_flow'
                            ] = (
                                    self.parse_parameter(
                                        building_zone_constraint_profile['minimum_fresh_air_flow_per_area_no_dcv'][
                                            int(constraint_profile_index_time(row_time.to_datetime64().astype('int64')))
                                        ]
                                    )
                                    * self.parse_parameter(row_zone['zone_area'])
                            )
                        elif row_zone['window_type'] != '':
                            self.output_constraint_timeseries_minimum.at[
                                row_time,
                                index_zone + '_window_fresh_air_flow'
                            ] = (
                                    self.parse_parameter(
                                        building_zone_constraint_profile['minimum_fresh_air_flow_per_area_no_dcv'][
                                            int(constraint_profile_index_time(row_time.to_datetime64().astype('int64')))
                                        ]
                                    )
                                    * self.parse_parameter(row_zone['zone_area'])
                            )
                # If a ventilation system is enabled, if DCV, then CO2 or constraint on total fresh air flow.
                # If no DCV, then constant constraint on AHU or on windows if no AHU

                if self.building_scenarios['humidity_model_type'][0] != '':
                    if row_zone['hvac_ahu_type'] != '':
                        self.output_constraint_timeseries_minimum.at[
                            row_time,
                            index_zone + '_absolute_humidity'
                        ] = humid_air_properties(
                            'W',
                            'R',
                            self.parse_parameter(
                                building_zone_constraint_profile['minimum_relative_humidity'][
                                    int(constraint_profile_index_time(row_time.to_datetime64().astype('int64')))
                                ]
                            )
                            / 100,
                            'T',
                            self.parse_parameter(
                                self.building_scenarios['linearization_zone_air_temperature_cool']
                            )
                            + 273.15,
                            'P',
                            101325
                        )
                        self.output_constraint_timeseries_maximum.at[
                            row_time,
                            index_zone + '_absolute_humidity'
                        ] = humid_air_properties(
                            'W',
                            'R',
                            self.parse_parameter(
                                building_zone_constraint_profile['maximum_relative_humidity'][
                                    int(constraint_profile_index_time(row_time.to_datetime64().astype('int64')))
                                ]
                            )
                            / 100,
                            'T',
                            self.parse_parameter(
                                self.building_scenarios['linearization_zone_air_temperature_cool']
                            )
                            + 273.15,
                            'P',
                            101325
                        )

        # Transpose to align with result of state space output matrix equation
        self.output_constraint_timeseries_minimum = self.output_constraint_timeseries_minimum.transpose()
        self.output_constraint_timeseries_maximum = self.output_constraint_timeseries_maximum.transpose()

    def discretize_model(self):
        """
        - Discretization assuming zero order hold
        - Source: https://en.wikipedia.org/wiki/Discretization#Discretization_of_linear_state_space_models
        """
        state_matrix_discrete = expm(
            self.state_matrix.values
            * pd.to_timedelta(self.building_scenarios['time_step'][0]).seconds
        )
        control_matrix_discrete = (
            np.linalg.matrix_power(
                self.state_matrix.values,
                -1
            ).dot(
                state_matrix_discrete
                - np.identity(self.state_matrix.shape[0])
            ).dot(
                self.control_matrix.values
            )
        )
        disturbance_matrix_discrete = (
            np.linalg.matrix_power(
                self.state_matrix.values,
                -1
            ).dot(
                state_matrix_discrete
                - np.identity(self.state_matrix.shape[0])
            ).dot(
                self.disturbance_matrix.values
            )
        )

        self.state_matrix = pd.DataFrame(
            data=state_matrix_discrete,
            index=self.state_matrix.index,
            columns=self.state_matrix.columns
        )
        self.control_matrix = pd.DataFrame(
            data=control_matrix_discrete,
            index=self.control_matrix.index,
            columns=self.control_matrix.columns
        )
        self.disturbance_matrix = pd.DataFrame(
            data=disturbance_matrix_discrete,
            index=self.disturbance_matrix.index,
            columns=self.disturbance_matrix.columns
        )
