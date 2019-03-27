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
import math

import numpy as np
import pandas as pd

from cea.utilities.dbf import dbf_to_dataframe

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def main(locator,
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
         phi_5_max,
         Fb,
         HP_ETA_EX_COOL,
         HP_AUXRATIO
         ):
    length_and_width_df = get_building_length_and_width(locator,
                                                        buildings_names
                                                        )
    Y_dic = calculate_pipe_transmittance(locator,
        buildings_names
    )
    fforma_dic = calculate_form_factor(
        length_and_width_df,
        footprint,
        buildings_names
    )
    (
        eff_cs_dic,
        source_cs_dic,
        scale_cs_dic,
        dTcs_C_dic,
        Qcsmax_Wm2_dic,
        Tc_sup_air_ahu_C_dic,
        Tc_sup_air_aru_C_dic,
        dT_Qcs_dic,
        temperature_difference_df
    ) = get_hvac_data(
        buildings_names,
        buildings_cardinal,
        cooling_generation_df,
        emission_systems_cooling_df,
        emission_systems_controller_df,
        generation_cooling_code_dic,
        emissions_cooling_type_dic,
        emissions_controller_type_dic
    )
    (
        gen_efficiency_mean_dic,
        sto_efficiency,
        em_efficiency_mean_dic,
        dis_efficiency_mean_dic,
        comparison_gen_mean_dic,
        comparison_em_mean_dic,
        comparison_dis_mean_dic_dic
    ) = calculate_hvac_efficiencies(
        buildings_names,
        set_temperatures_dic,
        T_ext_cea_df,
        wet_bulb_temperature_df,
        prediction_horizon,
        date_and_time_prediction,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        length_and_width_df,
        generation_cooling_code_dic,
        supply_temperature_df,
        emissions_cooling_type_dic,
        Y_dic,
        fforma_dic,
        eff_cs_dic,
        source_cs_dic,
        scale_cs_dic,
        dTcs_C_dic,
        dT_Qcs_dic,
        temperature_difference_df,
        phi_5_max,
        Fb,
        HP_ETA_EX_COOL,
        HP_AUXRATIO
    )
    write_building_system_ahu_types(locator,
                                    buildings_names,
                                    supply_temperature_df,
                                    emissions_cooling_type_dic,
                                    Tc_sup_air_ahu_C_dic,
                                    gen_efficiency_mean_dic,
                                    sto_efficiency,
                                    dis_efficiency_mean_dic
                                    )
    write_building_system_aru_types(locator,
                                    buildings_names,
                                    supply_temperature_df,
                                    emissions_cooling_type_dic,
                                    Tc_sup_air_aru_C_dic,
                                    gen_efficiency_mean_dic,
                                    sto_efficiency,
                                    dis_efficiency_mean_dic
                                    )
    write_building_hvac_generic_types(locator,
                                      buildings_names,
                                      supply_temperature_df,
                                      emissions_cooling_type_dic,
                                      gen_efficiency_mean_dic,
                                      sto_efficiency,
                                      dis_efficiency_mean_dic
                                      )

    return (
        Qcsmax_Wm2_dic,
        em_efficiency_mean_dic,
    )


def get_building_length_and_width(locator,
                                  buildings_names
                                  ):
    # Function taken from calc_bounding_box_geom in the CEA file building_properties.py
    # Get data
    geometry_shapefile_path = locator.get_zone_geometry()

    # Calculate
    import shapefile
    sf = shapefile.Reader(geometry_shapefile_path)
    shapes = sf.shapes()
    len_shapes = len(shapes)
    length_and_width = []
    for shape in range(len_shapes):
        bbox = shapes[shape].bbox
        coords_bbox = [coord for coord in bbox]
        delta1 = abs(coords_bbox[0] - coords_bbox[2])
        delta2 = abs(coords_bbox[1] - coords_bbox[3])
        if delta1 >= delta2:
            Lw = delta2
            Ll = delta1
            length_and_width.append([Ll, Lw])
        else:
            Lw = delta1
            Ll = delta2
            length_and_width.append([Ll, Lw])

    for i in range(len(buildings_names)):
        length_and_width[i].insert(0, buildings_names[i])

    length_and_width_df = pd.DataFrame(
        length_and_width,
        columns=[
            'Name',
            'Ll',
            'Lw'
        ]
    )
    length_and_width_df.set_index('Name', inplace=True)

    return length_and_width_df


def calculate_pipe_transmittance(locator,
                                 buildings_names
                                 ):
    # Get data
    age_df = dbf_to_dataframe(locator.get_building_age())
    age_df.set_index('Name', inplace=True)

    Y_dic = {}
    for building in buildings_names:
        age_built = age_df.loc[building, 'built']
        age_HVAC = age_df.loc[building, 'HVAC']

        # Calculate
        if age_built >= 1995 or age_HVAC > 1995:
            Y_dic[building] = 0.2
        elif 1985 <= age_built < 1995:
            Y_dic[building] = 0.3
            if age_HVAC == age_built:
                print(
                        'Incorrect HVAC renovation year for '
                        + building
                        + ': if HVAC has not been renovated, the year should be set to 0'
                )
                quit()
        else:
            Y_dic[building] = 0.4

    return Y_dic


def calculate_form_factor(
        length_and_width_df,
        footprint,
        buildings_names
):
    fforma_dic = {}
    for building in buildings_names:
        fforma_dic[building] = (
                footprint[building]
                / (length_and_width_df.loc[building]['Lw'] * length_and_width_df.loc[building]['Ll'])
        )

    return fforma_dic


def get_hvac_data(
        buildings_names,
        buildings_cardinal,
        cooling_generation_df,
        emission_systems_cooling_df,
        emission_systems_controller_df,
        generation_cooling_code_dic,
        emissions_cooling_type_dic,
        emissions_controller_type_dic
):
    eff_cs_dic = {}
    source_cs_dic = {}
    scale_cs_dic = {}
    dTcs_C_dic = {}
    Qcsmax_Wm2_dic = {}
    Tc_sup_air_ahu_C_dic = {}
    Tc_sup_air_aru_C_dic = {}
    dT_Qcs_dic = {}
    temperature_difference_df = pd.DataFrame(
        np.zeros((buildings_cardinal, 3)),
        buildings_names,
        ['ahu', 'aru', 'scu']
    )

    for building in buildings_names:
        # Supply system
        gen_cooling_code = generation_cooling_code_dic[building]

        eff_cs_dic[building] = cooling_generation_df.loc[gen_cooling_code, 'eff_cs']
        source_cs_dic[building] = cooling_generation_df.loc[gen_cooling_code, 'source_cs']
        scale_cs_dic[building] = cooling_generation_df.loc[gen_cooling_code, 'scale_cs']

        # Emissions system
        emissions_cooling_type = emissions_cooling_type_dic[building]

        dTcs_C_dic[building] = emission_systems_cooling_df.loc[emissions_cooling_type, 'dTcs_C']
        Qcsmax_Wm2_dic[building] = emission_systems_cooling_df.loc[emissions_cooling_type, 'Qcsmax_Wm2']
        Tc_sup_air_ahu_C_dic[building] = emission_systems_cooling_df.loc[emissions_cooling_type, 'Tc_sup_air_ahu_C']
        Tc_sup_air_aru_C_dic[building] = emission_systems_cooling_df.loc[emissions_cooling_type, 'Tc_sup_air_aru_C']
        for sys in ['ahu', 'aru', 'scu']:
            temperature_difference_df.loc[building][sys] = (
                emission_systems_cooling_df.loc[emissions_cooling_type, 'dTcs0_' + sys + '_C']
            )

        dT_Qcs_dic[building] = emission_systems_controller_df.loc[emissions_controller_type_dic[building]]['dT_Qcs']

    return (
        eff_cs_dic,
        source_cs_dic,
        scale_cs_dic,
        dTcs_C_dic,
        Qcsmax_Wm2_dic,
        Tc_sup_air_ahu_C_dic,
        Tc_sup_air_aru_C_dic,
        dT_Qcs_dic,
        temperature_difference_df
    )


def calculate_hvac_efficiencies(
        buildings_names,
        set_temperatures_dic,
        T_ext_cea_df,
        wet_bulb_temperature_df,
        prediction_horizon,
        date_and_time_prediction,
        occupancy_per_building_cardinal,
        occupancy_per_building_list,
        length_and_width_df,
        generation_cooling_code_dic,
        supply_temperature_df,
        emissions_cooling_type_dic,
        Y_dic,
        fforma_dic,
        eff_cs_dic,
        source_cs_dic,
        scale_cs_dic,
        dTcs_C_dic,
        dT_Qcs_dic,
        temperature_difference_df,
        phi_5_max,
        Fb,
        HP_ETA_EX_COOL,
        HP_AUXRATIO
):
    gen_efficiency_mean_dic = {}
    em_efficiency_mean_dic = {}
    dis_efficiency_mean_dic = {}
    comparison_gen_mean_dic = {}
    comparison_em_mean_dic = {}
    comparison_dis_mean_dic_dic = {}

    for building in buildings_names:
        # Calculate each efficiency type
        gen_efficiency_df = get_generation_efficiency(
            date_and_time_prediction,
            prediction_horizon,
            building,
            generation_cooling_code_dic[building],
            eff_cs_dic[building],
            source_cs_dic[building],
            scale_cs_dic[building],
            supply_temperature_df,
            T_ext_cea_df,
            wet_bulb_temperature_df,
            HP_ETA_EX_COOL,
            HP_AUXRATIO
        )
        sto_efficiency = get_storage_efficiency()
        em_efficiency_df = get_emission_efficiency(
            dTcs_C_dic[building],
            dT_Qcs_dic[building],
            building,
            set_temperatures_dic,
            T_ext_cea_df,
            emissions_cooling_type_dic[building],
            prediction_horizon,
            date_and_time_prediction,
            occupancy_per_building_cardinal,
            occupancy_per_building_list
        )
        dis_efficiency_dic = get_distribution_efficiency(
            em_efficiency_df,
            phi_5_max,
            supply_temperature_df,
            temperature_difference_df.loc[building],
            set_temperatures_dic,
            T_ext_cea_df,
            length_and_width_df,
            fforma_dic[building],
            Y_dic[building],
            Fb,
            building,
            prediction_horizon,
            date_and_time_prediction,
            occupancy_per_building_cardinal,
            occupancy_per_building_list
        )

        # Calculate the mean efficiencies, when needed
        (
            gen_efficiency_mean_dic[building],
            em_efficiency_mean_dic[building],
            dis_efficiency_mean_dic[building]
        ) = calculate_mean_efficiencies(
            gen_efficiency_df,
            em_efficiency_df,
            dis_efficiency_dic
        )

        # Compare the mean difference between the efficiency values and the mean efficiency
        (
            comparison_gen_df,
            comparison_em_df,
            comparison_dis_dic,
            comparison_gen_mean_dic[building],
            comparison_em_mean_dic[building],
            comparison_dis_mean_dic_dic[building]
        ) = calculate_comparisons_mean(
            gen_efficiency_mean_dic[building],
            em_efficiency_mean_dic[building],
            dis_efficiency_mean_dic[building],
            gen_efficiency_df,
            em_efficiency_df,
            dis_efficiency_dic,
            date_and_time_prediction
        )

    return (
        gen_efficiency_mean_dic,
        sto_efficiency,
        em_efficiency_mean_dic,
        dis_efficiency_mean_dic,
        comparison_gen_mean_dic,
        comparison_em_mean_dic,
        comparison_dis_mean_dic_dic
    )


def get_generation_efficiency(
        date_and_time_prediction,
        prediction_horizon,
        building,
        gen_cooling_code,
        eff_cs,
        source_cs,
        scale_cs,
        supply_temperature_df,
        T_ext_cea_df,
        wet_bulb_temperature_df,
        HP_ETA_EX_COOL,
        HP_AUXRATIO
):
    gen_efficiency_df = pd.DataFrame(
        np.zeros((3, prediction_horizon)),
        ['ahu', 'aru', 'scu'],
        date_and_time_prediction
    )

    if scale_cs == 'DISTRICT':
        for sys in ['ahu', 'aru', 'scu']:
            for time in date_and_time_prediction:
                gen_efficiency_df.loc[sys][time] = eff_cs
    elif scale_cs == 'NONE':
        raise ValueError('No supply air cooling supply system')
    elif scale_cs == 'BUILDING':
        if source_cs == 'GRID':
            supply_temperature_kelvin_dic = {}
            for sys in ['ahu', 'aru', 'scu']:
                supply_temperature_kelvin_dic[sys] = supply_temperature_df.loc[building][sys] + 273.15

            if gen_cooling_code in {'T2', 'T3'}:
                for time in date_and_time_prediction:
                    if gen_cooling_code == 'T2':
                        string_object_time = datetime.datetime.strftime(time, '%Y-%m-%d %H:%M:%S')
                        t_source_t = T_ext_cea_df[string_object_time] + 273
                    if gen_cooling_code == 'T3':
                        t_source_t = wet_bulb_temperature_df.loc[time]['wet_bulb_temperature'] + 273
                    for sys in ['ahu', 'aru', 'scu']:
                        if not math.isnan(supply_temperature_kelvin_dic[sys]):
                            gen_efficiency_df.loc[sys][time] = (
                                    HP_ETA_EX_COOL
                                    * HP_AUXRATIO
                                    * supply_temperature_kelvin_dic[sys]
                                    / (t_source_t - supply_temperature_kelvin_dic[sys])
                            )
                        else:
                            gen_efficiency_df.loc[sys][time] = np.nan
    else:
        raise NotImplementedError('Unknown cooling supply system')

    return gen_efficiency_df


def get_storage_efficiency():
    sto_efficiency = 1
    return sto_efficiency


def get_emission_efficiency(
        dTcs_C,
        dT_Qcs,
        building,
        set_temperatures_dic,
        T_ext_cea_df,
        emissions_cooling_type,
        prediction_horizon,
        date_and_time_prediction,
        occupancy_per_building_cardinal,
        occupancy_per_building_list
):
    # TODO: Use the correct delta theta sol (c.f. HVAC efficiencies documentation)
    em_efficiency_df = pd.DataFrame(
        np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
        occupancy_per_building_list[building],
        date_and_time_prediction
    )

    for occupancy in occupancy_per_building_list[building]:
        if emissions_cooling_type == 'T0':
            for time in date_and_time_prediction:
                em_efficiency_df.loc[occupancy][time] = 1
        else:
            for time in date_and_time_prediction:
                string_object_time = datetime.datetime.strftime(time, '%Y-%m-%d %H:%M:%S')
                T_int_t = set_temperatures_dic[building].loc[occupancy][time]
                frac_t = (dTcs_C + dT_Qcs) / (T_int_t - T_ext_cea_df[string_object_time] + dTcs_C + dT_Qcs - 10)

                if frac_t < 0:
                    em_efficiency_df.loc[occupancy][time] = 1
                elif abs(T_int_t - T_ext_cea_df[string_object_time] + dTcs_C + dT_Qcs - 10) < 10 ** (-6):
                    em_efficiency_df.loc[occupancy][time] = 1
                else:
                    if 1 / (1 + frac_t) > 1:  # Check efficiency value
                        raise ValueError('Emission efficiency is greater than 1')
                    else:
                        em_efficiency_df.loc[occupancy][time] = 1 / (1 + frac_t)

    return em_efficiency_df


def get_distribution_efficiency(
        em_efficiency_df,
        phi_5_max,
        supply_temperature_df,
        temperature_difference_dic,
        set_temperatures_dic,
        T_ext_cea_df,
        length_and_width_df,
        fforma,
        Y,
        Fb,
        building,
        prediction_horizon,
        date_and_time_prediction,
        occupancy_per_building_cardinal,
        occupancy_per_building_list
):
    # Non time-dependent parts
    Ll = length_and_width_df.loc[building]['Ll']
    Lw = length_and_width_df.loc[building]['Lw']
    Lv = (2 * Ll + 0.0325 * Ll * Lw + 6) * fforma

    sys_temperatures = {}
    for sys in ['ahu', 'aru', 'scu']:
        sys_temperatures[sys] = (2 * supply_temperature_df.loc[building][sys] + temperature_difference_dic[sys]) / 2

    # Time-dependent parts
    dis_efficiency_dic = {}
    for sys in ['ahu', 'aru', 'scu']:
        dis_efficiency_sys_df = pd.DataFrame(
            np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
            occupancy_per_building_list[building],
            date_and_time_prediction
        )
        for occupancy in occupancy_per_building_list[building]:
            if math.isnan(sys_temperatures[sys]):  # Check whether AHU, ARU and SCU exist
                for time in date_and_time_prediction:
                    dis_efficiency_sys_df.loc[occupancy][time] = np.nan
            else:
                for time in date_and_time_prediction:
                    string_object_time = datetime.datetime.strftime(time, '%Y-%m-%d %H:%M:%S')
                    common_coeff = em_efficiency_df.loc[occupancy][time] * Lv * Y / phi_5_max
                    Tb = (
                            set_temperatures_dic[building].loc[occupancy][time]
                            - Fb
                            * (
                                    set_temperatures_dic[building].loc[occupancy][time]
                                    - T_ext_cea_df[string_object_time]
                            )
                    )
                    if (1 + common_coeff * (sys_temperatures[sys] - Tb)) > 1:  # Check efficiency value
                        raise ValueError('Distribution efficiency is greater than 1')
                    else:
                        dis_efficiency_sys_df.loc[occupancy][time] = 1 + common_coeff * (sys_temperatures[sys] - Tb)

        dis_efficiency_dic[sys] = dis_efficiency_sys_df

    return dis_efficiency_dic


def calculate_mean_efficiencies(gen_efficiency_df, em_efficiency_df, dis_efficiency_dic):
    # Calculates the mean generation/conversion efficiencies for the ahu, the aru and the scu
    gen_efficiency_mean = gen_efficiency_df.mean(axis=1, skipna=False)

    # Calculates the emission efficiency
    em_efficiency_mean_row = em_efficiency_df.mean(axis=1)
    em_efficiency_mean = em_efficiency_mean_row.mean(axis=0)

    # Calculates the mean distribution efficiencies for the ahu, the aru and the scu
    dis_efficiency_mean = {}
    for sys in ['ahu', 'aru', 'scu']:
        dis_efficiency_dic_sys = dis_efficiency_dic[sys]
        dis_efficiency_mean_sys_row = dis_efficiency_dic_sys.mean(axis=1, skipna=False)
        dis_efficiency_mean[sys] = dis_efficiency_mean_sys_row.mean(axis=0, skipna=False)

    return (
        gen_efficiency_mean,
        em_efficiency_mean,
        dis_efficiency_mean
    )


def calculate_comparisons_mean(
        gen_efficiency_mean,
        em_efficiency_mean,
        dis_efficiency_mean,
        gen_efficiency_df,
        em_efficiency_df,
        dis_efficiency_dic,
        date_and_time_prediction
):
    # Create the data frames
    comparison_gen_df = pd.DataFrame(
        np.zeros(gen_efficiency_df.shape),
        gen_efficiency_df.index,
        gen_efficiency_df.columns
    )
    comparison_em_df = pd.DataFrame(
        np.zeros(em_efficiency_df.shape),
        em_efficiency_df.index,
        em_efficiency_df.columns
    )
    comparison_dis_dic = {}
    for sys in ['ahu', 'aru', 'scu']:
        comparison_dis_dic[sys] = pd.DataFrame(
            np.zeros(dis_efficiency_dic[sys].shape),
            dis_efficiency_dic[sys].index,
            dis_efficiency_dic[sys].columns
        )
    # Fill in the data frames of the relative differences to the means
    for time in date_and_time_prediction:
        for index, row in gen_efficiency_df.iterrows():
            comparison_gen_df.loc[index][time] = (
                    abs(row[time] - gen_efficiency_mean[index])
                    / gen_efficiency_mean[index]
            )

        for index, row in em_efficiency_df.iterrows():
            comparison_em_df.loc[index][time] = (
                    abs(row[time] - em_efficiency_mean)
                    / em_efficiency_mean
            )

        for sys in ['ahu', 'aru', 'scu']:
            for index, row in dis_efficiency_dic[sys].iterrows():
                comparison_dis_dic[sys].loc[index][time] = (
                        abs(dis_efficiency_dic[sys].loc[index][time] - dis_efficiency_mean[sys])
                        / dis_efficiency_mean[sys]
                )

    # Calculate the means
    # Calculates the mean generation/conversion efficiencies relative differences to the means
    # for the ahu, the aru and the scu
    comparison_gen_mean = comparison_gen_df.mean(axis=1, skipna=False)

    # Calculates the emission efficiency relative difference to the mean
    comparison_em_mean_row = comparison_em_df.mean(axis=1)
    comparison_em_mean = comparison_em_mean_row.mean(axis=0)

    # Calculates the mean distribution efficiencies relative differences to the means for the ahu, the aru and the scu
    comparison_dis_mean_dic = {}
    for sys in ['ahu', 'aru', 'scu']:
        comparison_dis_dic_sys = comparison_dis_dic[sys]
        comparison_dis_mean_sys_row = comparison_dis_dic_sys.mean(axis=1, skipna=False)
        comparison_dis_mean_dic[sys] = comparison_dis_mean_sys_row.mean(axis=0, skipna=False)

    return (
        comparison_gen_df,
        comparison_em_df,
        comparison_dis_dic,
        comparison_gen_mean,
        comparison_em_mean,
        comparison_dis_mean_dic
    )


def write_building_system_ahu_types(locator,
                                    buildings_names,
                                    supply_temperature_df,
                                    emissions_cooling_type_dic,
                                    Tc_sup_air_ahu_C_dic,
                                    gen_efficiency_mean_dic,
                                    sto_efficiency,
                                    dis_efficiency_mean_dic
                                    ):
    ahu_types = []
    for building in buildings_names:
        if not math.isnan(supply_temperature_df.loc[building]['ahu']):
            ahu_types.append([
                building + '_' + emissions_cooling_type_dic[building],
                'default',
                'default',
                'default',
                'default',
                Tc_sup_air_ahu_C_dic[building],
                11.5,
                1,
                (
                        gen_efficiency_mean_dic[building].loc['ahu']
                        * sto_efficiency
                        * dis_efficiency_mean_dic[building]['ahu']
                ),
                1,
                1
            ])

    ahu_types_df = pd.DataFrame.from_records(
        ahu_types,
        columns=[
            'hvac_ahu_type',
            'ahu_cooling_type',
            'ahu_heating_type',
            'ahu_dehumidification_type',
            'ahu_return_air_heat_recovery_type',
            'ahu_supply_air_temperature_setpoint',
            'ahu_supply_air_relative_humidty_setpoint',
            'ahu_fan_efficiency',
            'ahu_cooling_efficiency',
            'ahu_heating_efficiency',
            'ahu_return_air_recovery_efficiency'
        ])
    ahu_types_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('building_hvac_ahu_types'
                                                                      ),
        index=False
    )


def write_building_system_aru_types(locator,
                                    buildings_names,
                                    supply_temperature_df,
                                    emissions_cooling_type_dic,
                                    Tc_sup_air_aru_C_dic,
                                    gen_efficiency_mean_dic,
                                    sto_efficiency,
                                    dis_efficiency_mean_dic
                                    ):
    aru_types = []
    for building in buildings_names:
        if not math.isnan(supply_temperature_df.loc[building]['aru']):
            aru_types.append([
                building + '_' + emissions_cooling_type_dic[building],
                'default',
                'default',
                'zone',
                Tc_sup_air_aru_C_dic[building],
                1,
                (
                        gen_efficiency_mean_dic[building].loc['aru']
                        * sto_efficiency
                        * dis_efficiency_mean_dic[building]['aru']
                ),
                1
            ])

    aru_types_df = pd.DataFrame.from_records(
        aru_types,
        columns=[
            'hvac_tu_type',
            'tu_cooling_type',
            'tu_heating_type',
            'tu_air_intake_type',
            'tu_supply_air_temperature_setpoint',
            'tu_fan_efficiency',
            'tu_cooling_efficiency',
            'tu_heating_efficiency'
        ])

    aru_types_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('building_hvac_tu_types'
                                                                      ),
        index=False
    )


def write_building_hvac_generic_types(locator,
                                      buildings_names,
                                      supply_temperature_df,
                                      emissions_cooling_type_dic,
                                      gen_efficiency_mean_dic,
                                      sto_efficiency,
                                      dis_efficiency_mean_dic
                                      ):
    scu_types = []
    for building in buildings_names:
        if not math.isnan(supply_temperature_df.loc[building]['scu']):
            scu_types.append([
                building + '_' + emissions_cooling_type_dic[building],
                1,
                (
                        gen_efficiency_mean_dic[building].loc['scu']
                        * sto_efficiency
                        * dis_efficiency_mean_dic[building]['scu']
                )
            ])

    scu_types_df = pd.DataFrame.from_records(
        scu_types,
        columns=[
            'hvac_generic_type',
            'generic_heating_efficiency',
            'generic_cooling_efficiency'
        ])
    scu_types_df.to_csv(
        path_or_buf=locator.get_mpc_results_building_definitions_file('building_hvac_generic_types'
                                                                      ),
        index=False
    )
