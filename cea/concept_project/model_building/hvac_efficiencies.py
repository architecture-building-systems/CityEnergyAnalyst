import pandas as pd
import math
import numpy as np
from datetime import datetime


def main_hvac_efficiencies(buildings_names, set_temperatures_dic, T_ext_cea_df, wet_bulb_temperature_df,
                           prediction_horizon, date_and_time_prediction, occupancy_per_building_cardinal,
                           occupancy_per_building_list, length_and_width_df, generation_cooling_code_dic,
                           supply_temperature_df, emissions_cooling_type_dic, Y_dic, fforma_dic, eff_cs_dic,
                           source_cs_dic, scale_cs_dic, dTcs_C_dic, dT_Qcs_dic, temperature_difference_df, phi_5_max,
                           Fb, HP_ETA_EX_COOL, HP_AUXRATIO):

    gen_efficiency_mean_dic = {}
    em_efficiency_mean_dic = {}
    dis_efficiency_mean_dic = {}
    comparison_gen_mean_dic = {}
    comparison_em_mean_dic = {}
    comparison_dis_mean_dic_dic = {}

    for building in buildings_names:
        # Calculate each efficiency type
        gen_efficiency_df = get_generation_efficiency(date_and_time_prediction, prediction_horizon, building,
                                                      generation_cooling_code_dic[building], eff_cs_dic[building],
                                                      source_cs_dic[building], scale_cs_dic[building],
                                                      supply_temperature_df, T_ext_cea_df, wet_bulb_temperature_df,
                                                      HP_ETA_EX_COOL, HP_AUXRATIO
                                                      )
        sto_efficiency = get_storage_efficiency()
        em_efficiency_df = get_emission_efficiency(dTcs_C_dic[building], dT_Qcs_dic[building], building,
                                                   set_temperatures_dic, T_ext_cea_df,
                                                   emissions_cooling_type_dic[building],
                                                   prediction_horizon, date_and_time_prediction,
                                                   occupancy_per_building_cardinal,
                                                   occupancy_per_building_list)
        dis_efficiency_dic = get_distribution_efficiency(em_efficiency_df, phi_5_max, supply_temperature_df,
                                                         temperature_difference_df.loc[building],
                                                         set_temperatures_dic, T_ext_cea_df, length_and_width_df,
                                                         fforma_dic[building], Y_dic[building], Fb, building,
                                                         prediction_horizon, date_and_time_prediction,
                                                         occupancy_per_building_cardinal,
                                                         occupancy_per_building_list)

        # Calculate the mean efficiencies, when needed
        gen_efficiency_mean_dic[building], em_efficiency_mean_dic[building], dis_efficiency_mean_dic[
            building] = calculate_mean_efficiencies(
            gen_efficiency_df, em_efficiency_df, dis_efficiency_dic)

        # Compare the mean difference between the efficiency values and the mean efficiency
        comparison_gen_df, comparison_em_df, comparison_dis_dic, comparison_gen_mean_dic[building], \
            comparison_em_mean_dic[building], comparison_dis_mean_dic_dic[building] = calculate_comparisons_mean(
            gen_efficiency_mean_dic[building], em_efficiency_mean_dic[building], dis_efficiency_mean_dic[building],
            gen_efficiency_df, em_efficiency_df,
            dis_efficiency_dic, date_and_time_prediction)

    return gen_efficiency_mean_dic, sto_efficiency, em_efficiency_mean_dic, dis_efficiency_mean_dic, \
        comparison_gen_mean_dic, comparison_em_mean_dic, comparison_dis_mean_dic_dic


def get_generation_efficiency(date_and_time_prediction, prediction_horizon, building, gen_cooling_code, eff_cs,
                              source_cs, scale_cs, supply_temperature_df, T_ext_cea_df, wet_bulb_temperature_df,
                              HP_ETA_EX_COOL, HP_AUXRATIO):

    gen_efficiency_df = pd.DataFrame(np.zeros((3, prediction_horizon)), ['ahu', 'aru', 'scu'], date_and_time_prediction)

    if scale_cs == 'DISTRICT':
        for sys in ['ahu', 'aru', 'scu']:
            for time in date_and_time_prediction:
                gen_efficiency_df.loc[sys][time] = eff_cs
    elif scale_cs == 'NONE':
        print('Error: no supply air cooling supply system')
        quit()
    elif scale_cs == 'BUILDING':
        if source_cs == 'GRID':
            supply_temperature_kelvin_dic = {}
            for sys in ['ahu', 'aru', 'scu']:
                supply_temperature_kelvin_dic[sys] = supply_temperature_df.loc[building][sys] + 273.15

            if gen_cooling_code in {'T2', 'T3'}:
                for time in date_and_time_prediction:
                    if gen_cooling_code == 'T2':
                        string_object_time = datetime.strftime(time, '%Y-%m-%d %H:%M:%S')
                        t_source_t = T_ext_cea_df[string_object_time] + 273
                    if gen_cooling_code == 'T3':
                        t_source_t = wet_bulb_temperature_df.loc[time]['wet_bulb_temperature'] + 273
                    for sys in ['ahu', 'aru', 'scu']:
                        if not math.isnan(supply_temperature_kelvin_dic[sys]):
                            gen_efficiency_df.loc[sys][time] = HP_ETA_EX_COOL * HP_AUXRATIO * \
                                                               supply_temperature_kelvin_dic[sys] / (
                                                               t_source_t - supply_temperature_kelvin_dic[sys])
                        else:
                            gen_efficiency_df.loc[sys][time] = np.nan
    else:
        print('Error: Cooling supply system is incorrect')
        quit()

    return gen_efficiency_df


def get_storage_efficiency():
    sto_efficiency = 1
    return sto_efficiency


def get_emission_efficiency(dTcs_C, dT_Qcs, building, set_temperatures_dic, T_ext_cea_df, emissions_cooling_type,
                            prediction_horizon, date_and_time_prediction, occupancy_per_building_cardinal,
                            occupancy_per_building_list):
    # TODO: Use the correct delta theta sol (c.f. HVAC efficiencies documentation)
    em_efficiency_df = pd.DataFrame(
        np.zeros((occupancy_per_building_cardinal[building], prediction_horizon)),
        occupancy_per_building_list[building], date_and_time_prediction)

    for occupancy in occupancy_per_building_list[building]:
        if emissions_cooling_type == 'T0':
            for time in date_and_time_prediction:
                em_efficiency_df.loc[occupancy][time] = 1
        else:
            for time in date_and_time_prediction:
                string_object_time = datetime.strftime(time, '%Y-%m-%d %H:%M:%S')
                T_int_t = set_temperatures_dic[building].loc[occupancy][time]
                frac_t = (dTcs_C + dT_Qcs) / (T_int_t - T_ext_cea_df[string_object_time] + dTcs_C + dT_Qcs - 10)

                if frac_t < 0:
                    em_efficiency_df.loc[occupancy][time] = 1
                elif abs(T_int_t - T_ext_cea_df[string_object_time] + dTcs_C + dT_Qcs - 10) < 10**(-6):
                    em_efficiency_df.loc[occupancy][time] = 1
                else:
                    if 1/(1 + frac_t) > 1:  # Check efficiency value
                        print('Error: emission efficiency is greater than 1')
                        quit()
                    else:
                        em_efficiency_df.loc[occupancy][time] = 1/(1 + frac_t)

    return em_efficiency_df


def get_distribution_efficiency(em_efficiency_df, phi_5_max, supply_temperature_df, temperature_difference_dic,
                                set_temperatures_dic, T_ext_cea_df, length_and_width_df, fforma, Y, Fb, building,
                                prediction_horizon, date_and_time_prediction, occupancy_per_building_cardinal,
                                occupancy_per_building_list):
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
            occupancy_per_building_list[building], date_and_time_prediction)
        for occupancy in occupancy_per_building_list[building]:
            if math.isnan(sys_temperatures[sys]):  # Check whether AHU, ARU and SCU exist
                for time in date_and_time_prediction:
                    dis_efficiency_sys_df.loc[occupancy][time] = np.nan
            else:
                for time in date_and_time_prediction:
                    string_object_time = datetime.strftime(time, '%Y-%m-%d %H:%M:%S')
                    common_coeff = em_efficiency_df.loc[occupancy][time] * Lv * Y / phi_5_max
                    Tb = set_temperatures_dic[building].loc[occupancy][time] - Fb * (
                            set_temperatures_dic[building].loc[occupancy][time] - T_ext_cea_df[string_object_time])
                    if 1 + common_coeff * (sys_temperatures[sys] - Tb) > 1:  # Check efficiency value
                        print('Error: distribution efficiency is greater than 1')
                        quit()
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

    return gen_efficiency_mean, em_efficiency_mean, dis_efficiency_mean


def calculate_comparisons_mean(gen_efficiency_mean, em_efficiency_mean, dis_efficiency_mean, gen_efficiency_df,
                               em_efficiency_df, dis_efficiency_dic, date_and_time_prediction):
    # Create the data frames
    comparison_gen_df = pd.DataFrame(np.zeros(gen_efficiency_df.shape), gen_efficiency_df.index,
                                     gen_efficiency_df.columns)
    comparison_em_df = pd.DataFrame(np.zeros(em_efficiency_df.shape), em_efficiency_df.index, em_efficiency_df.columns)
    comparison_dis_dic = {}
    for sys in ['ahu', 'aru', 'scu']:
        comparison_dis_dic[sys] = pd.DataFrame(np.zeros(dis_efficiency_dic[sys].shape), dis_efficiency_dic[sys].index,
                                               dis_efficiency_dic[sys].columns)
    # Fill in the data frames of the relative differences to the means
    for time in date_and_time_prediction:
        for index, row in gen_efficiency_df.iterrows():
            comparison_gen_df.loc[index][time] = abs(row[time] - gen_efficiency_mean[index]) / gen_efficiency_mean[
                index]

        for index, row in em_efficiency_df.iterrows():
            comparison_em_df.loc[index][time] = abs(row[time] - em_efficiency_mean) / em_efficiency_mean

        for sys in ['ahu', 'aru', 'scu']:
            for index, row in dis_efficiency_dic[sys].iterrows():
                comparison_dis_dic[sys].loc[index][time] = abs(
                    dis_efficiency_dic[sys].loc[index][time] - dis_efficiency_mean[sys]) / dis_efficiency_mean[sys]

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

    return comparison_gen_df, comparison_em_df, comparison_dis_dic, comparison_gen_mean, comparison_em_mean, \
        comparison_dis_mean_dic
