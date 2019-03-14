"""
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
from __future__ import division

import datetime

import pandas as pd

from cea.optimization.flexibility_model.model_building import building_extract_cea_data
from cea.optimization.flexibility_model.model_building import building_process_hvac_efficiencies
from cea.optimization.flexibility_model.model_building import building_setup_district
from cea.optimization.flexibility_model.model_building import building_write_definitions
from cea.optimization.flexibility_model.model_building.constants import DELTA_P_DIM, DENSITY_AIR, HEAT_CAPACITY_AIR, HE_E, H_I, \
    PHI_5_MAX, FB, HP_ETA_EX_COOL, HP_AUXRATIO

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def main(locator,
         weather_path,
         scenario, region,
         parameter_set,
         time_start,
         time_end,
         time_step_ts,
         set_temperature_goal,
         constant_temperature
         ):
    # Preliminary step - time
    date_and_time_prediction = pd.date_range(start=time_start, end=time_end, freq=pd.to_timedelta(time_step_ts))
    time_step = date_and_time_prediction[1] - date_and_time_prediction[0]

    time_end_object = datetime.datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S')
    last_step_plus_1 = time_end_object + time_step
    last_step_plus_1_str = datetime.datetime.strftime(last_step_plus_1, '%Y-%m-%d %H:%M:%S')
    date_and_time_prediction_plus_1 = pd.date_range(
        start=time_start, end=last_step_plus_1_str, freq=pd.to_timedelta(time_step_ts))

    # Getting and writting general data
    (
        internal_loads_df,
        indoor_comfort_df,
        construction_envelope_systems_df,
        leakage_envelope_systems_df,
        window_envelope_systems_df,
        roofs_envelope_systems_df,
        wall_envelope_systems_df,
        shading_envelope_systems_df,
        emission_systems_heating_df,
        emission_systems_cooling_df,
        emission_systems_controller_df,
        system_controls_ini_df,
        cooling_generation_df,
        zone_occupancy_df,
        zone_df,
        architecture_df,
        technical_systems_df,
        supply_systems_df,
        weather_general_info,
        weather_timeseries_initial_df,
        occupancy_types_full,
        occupancy_types,
        buildings_names,
        building_geometry_all,
        occupancy_types_full_cardinal,
        buildings_cardinal,
        occupancy_types_cardinal,
        occupants_probability_dic,
        lighting_appliances_probability_dic,
        processes_probability_dic,
        monthly_use_probability_df,
        occupancy_density_m2_p,
        footprint,
        gross_floor_area_m2,
        floors_cardinal_df,
        total_gross_floor_area_m2,
        mean_floor_height_m,
        system_controls_df,
        supply_temperature_df,
        emissions_cooling_type_dic,
        emissions_controller_type_dic,
        generation_cooling_code_dic,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        T_int_cea_dic,
        T_ext_cea_df
    ) = building_extract_cea_data.main(locator, weather_path,
                                       region,
                                       time_start,
                                       time_end
                                       )

    (
        date_and_time,
        year,
        wet_bulb_temperature_df,
        occupancy_probability_df
    ) = building_write_definitions.main(locator, scenario,
                                        date_and_time_prediction,
                                        time_start,
                                        time_end,
                                        time_step,
                                        parameter_set,
                                        internal_loads_df,
                                        construction_envelope_systems_df,
                                        leakage_envelope_systems_df,
                                        window_envelope_systems_df,
                                        roofs_envelope_systems_df,
                                        wall_envelope_systems_df,
                                        shading_envelope_systems_df,
                                        zone_occupancy_df,
                                        architecture_df,
                                        weather_general_info,
                                        weather_timeseries_initial_df,
                                        occupancy_types,
                                        occupancy_types_cardinal,
                                        buildings_names,
                                        building_geometry_all,
                                        occupants_probability_dic,
                                        lighting_appliances_probability_dic,
                                        processes_probability_dic,
                                        monthly_use_probability_df,
                                        occupancy_density_m2_p,
                                        gross_floor_area_m2,
                                        mean_floor_height_m,
                                        DELTA_P_DIM,
                                        HE_E,
                                        H_I,
                                        DENSITY_AIR,
                                        HEAT_CAPACITY_AIR,
                                        supply_temperature_df,
                                        emissions_cooling_type_dic
                                        )

    (
        prediction_horizon,
        center_interval_temperatures_dic,
        set_setback_temperatures_dic,
        setback_boolean_dic,
        heating_boolean,
        cooling_boolean,
        set_temperatures_dic
    ) = building_setup_district.main(
        date_and_time_prediction,
        time_step,
        set_temperature_goal,
        constant_temperature,
        buildings_names,
        system_controls_df,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        occupancy_probability_df,
        indoor_comfort_df,
        T_int_cea_dic
    )

    electricity_prices_MWh = pd.read_excel(locator.get_electricity_costs(region), "ELECTRICITY")
    electricity_prices_MWh["PRICE ($/MWh)"] = electricity_prices_MWh["cost_kWh"]*1000
    electricity_prices_MWh["our_datetime"] = pd.date_range(start='1/1/2005', periods=8760)
    electricity_prices_MWh.set_index('our_datetime', inplace=True)

    (
        Qcsmax_Wm2_dic,
        em_efficiency_mean_dic,
    ) = building_process_hvac_efficiencies.main(locator,
                                                buildings_names,
                                                footprint,
                                                buildings_cardinal,
                                                cooling_generation_df,
                                                emission_systems_cooling_df,
                                                emission_systems_controller_df,
                                                generation_cooling_code_dic,
                                                emissions_cooling_type_dic,
                                                emissions_controller_type_dic,
                                                set_temperatures_dic,
                                                T_ext_cea_df,
                                                wet_bulb_temperature_df,
                                                prediction_horizon,
                                                date_and_time_prediction,
                                                occupancy_per_building_cardinal,
                                                occupancy_per_building_list,
                                                supply_temperature_df,
                                                PHI_5_MAX,
                                                FB,
                                                HP_ETA_EX_COOL,
                                                HP_AUXRATIO
                                                )

    return (
        prediction_horizon,
        date_and_time_prediction,
        date_and_time_prediction_plus_1,
        time_step,
        year,
        buildings_names,
        buildings_cardinal,
        center_interval_temperatures_dic,
        set_setback_temperatures_dic,
        setback_boolean_dic,
        heating_boolean,
        cooling_boolean,
        set_temperatures_dic,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        gross_floor_area_m2,
        total_gross_floor_area_m2,
        indoor_comfort_df,
        occupancy_density_m2_p,
        occupancy_probability_df,
        em_efficiency_mean_dic,
        Qcsmax_Wm2_dic,
        electricity_prices_MWh
    )
