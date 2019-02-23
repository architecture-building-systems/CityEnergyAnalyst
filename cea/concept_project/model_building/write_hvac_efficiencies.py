import pandas as pd
import math
import os


def main_write_hvac_efficiencies(scenario_data_path, scenario, buildings_names, supply_temperature_df,
                                 emissions_cooling_type_dic, Tc_sup_air_ahu_C_dic, Tc_sup_air_aru_C_dic,
                                 gen_efficiency_mean_dic, sto_efficiency, dis_efficiency_mean_dic):

    write_building_system_ahu_types(scenario_data_path, scenario, buildings_names, supply_temperature_df,
                                    emissions_cooling_type_dic, Tc_sup_air_ahu_C_dic, gen_efficiency_mean_dic,
                                    sto_efficiency, dis_efficiency_mean_dic)
    write_building_system_aru_types(scenario_data_path, scenario, buildings_names, supply_temperature_df,
                                    emissions_cooling_type_dic, Tc_sup_air_aru_C_dic, gen_efficiency_mean_dic,
                                    sto_efficiency, dis_efficiency_mean_dic)
    write_building_hvac_generic_types(scenario_data_path, scenario, buildings_names, supply_temperature_df,
                                      emissions_cooling_type_dic, gen_efficiency_mean_dic, sto_efficiency,
                                      dis_efficiency_mean_dic)


def write_building_system_ahu_types(scenario_data_path, scenario, buildings_names, supply_temperature_df,
                                    emissions_cooling_type_dic, Tc_sup_air_ahu_C_dic, gen_efficiency_mean_dic,
                                    sto_efficiency, dis_efficiency_mean_dic):
    ahu_types = []
    for building in buildings_names:
        if not math.isnan(supply_temperature_df.loc[building]['ahu']):
            ahu_types.append([building + '_' + emissions_cooling_type_dic[building], 'default', 'default', 'default',
                              'default', Tc_sup_air_ahu_C_dic[building], 11.5, 1,
                              gen_efficiency_mean_dic[building].loc['ahu'] * sto_efficiency *
                              dis_efficiency_mean_dic[building]['ahu'], 1, 1])

    ahu_types_df = pd.DataFrame.from_records(ahu_types,
                                             columns=['hvac_ahu_type', 'ahu_cooling_type',
                                                      'ahu_heating_type', 'ahu_dehumidification_type',
                                                      'ahu_return_air_heat_recovery_type',
                                                      'ahu_supply_air_temperature_setpoint',
                                                      'ahu_supply_air_relative_humidty_setpoint',
                                                      'ahu_fan_efficiency', 'ahu_cooling_efficiency',
                                                      'ahu_heating_efficiency', 'ahu_return_air_recovery_efficiency'])
    ahu_types_df.to_csv(
        path_or_buf=os.path.join(scenario_data_path, scenario, 'concept', 'building-definition', 'building_hvac_ahu_types.csv'), index=False)


def write_building_system_aru_types(scenario_data_path, scenario, buildings_names, supply_temperature_df,
                                    emissions_cooling_type_dic, Tc_sup_air_aru_C_dic, gen_efficiency_mean_dic,
                                    sto_efficiency, dis_efficiency_mean_dic):
    aru_types = []
    for building in buildings_names:
        if not math.isnan(supply_temperature_df.loc[building]['aru']):
            aru_types.append([building + '_' + emissions_cooling_type_dic[building], 'default', 'default', 'zone',
                              Tc_sup_air_aru_C_dic[building], 1,
                              gen_efficiency_mean_dic[building].loc['aru'] * sto_efficiency *
                              dis_efficiency_mean_dic[building]['aru'], 1])

    aru_types_df = pd.DataFrame.from_records(aru_types,
                                             columns=['hvac_tu_type', 'tu_cooling_type', 'tu_heating_type',
                                                      'tu_air_intake_type', 'tu_supply_air_temperature_setpoint',
                                                      'tu_fan_efficiency', 'tu_cooling_efficiency',
                                                      'tu_heating_efficiency'])

    aru_types_df.to_csv(
        path_or_buf=os.path.join(scenario_data_path, scenario, 'concept', 'building-definition', 'building_hvac_tu_types.csv'), index=False)


def write_building_hvac_generic_types(scenario_data_path, scenario, buildings_names, supply_temperature_df,
                                      emissions_cooling_type_dic, gen_efficiency_mean_dic, sto_efficiency,
                                      dis_efficiency_mean_dic):
    scu_types = []
    for building in buildings_names:
        if not math.isnan(supply_temperature_df.loc[building]['scu']):
            scu_types.append([building + '_' + emissions_cooling_type_dic[building], 1,
                              gen_efficiency_mean_dic[building].loc['scu'] * sto_efficiency *
                              dis_efficiency_mean_dic[building]['scu']])

    scu_types_df = pd.DataFrame.from_records(scu_types,
                                             columns=['hvac_generic_type', 'generic_heating_efficiency',
                                                      'generic_cooling_efficiency'])
    scu_types_df.to_csv(
        path_or_buf=os.path.join(scenario_data_path, scenario, 'concept', 'building-definition', 'building_hvac_generic_types.csv'),
        index=False)
