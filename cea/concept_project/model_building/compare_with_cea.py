import pandas as pd
import os


def main_compare_with_cea(
        scenario_data_path,
        scenario,
        buildings_names,
        time_start,
        time_end
):
    thermal_room_load_cea_dic = {}
    thermal_between_generation_emission_cea_dic = {}
    electric_grid_load_cea_dic = {}
    T_int_cea_dic = {}
    for building in buildings_names:
        # Get data
        building_demand_cea_build_df = pd.read_csv(
            os.path.join(scenario_data_path, scenario, 'outputs', 'data', 'demand', building + '.csv')
        )
        building_demand_cea_build_df.set_index('DATE', inplace=True)
        building_demand_cea_build_df.index = pd.to_datetime(building_demand_cea_build_df.index)

        # Thermal room loads
        Qhs_sen_sys_kWh = building_demand_cea_build_df.loc[time_start:time_end, 'Qhs_sen_sys_kWh']
        Qcs_sen_sys_kWh = building_demand_cea_build_df.loc[time_start:time_end, 'Qcs_sen_sys_kWh'].abs()
        Qhs_lat_sys_kWh = building_demand_cea_build_df.loc[time_start:time_end, 'Qhs_lat_sys_kWh']
        Qcs_lat_sys_kWh = building_demand_cea_build_df.loc[time_start:time_end, 'Qcs_lat_sys_kWh'].abs()

        thermal_room_load_cea_build_df = (
                (
                        Qhs_sen_sys_kWh
                        + Qcs_sen_sys_kWh
                        + Qhs_lat_sys_kWh
                        + Qcs_lat_sys_kWh
                ) * 1000  # From kWh to Wh
        )

        # Thermal loads between generation/conversion, and distribution and emission
        Qhs_sys_kWh = building_demand_cea_build_df.loc[time_start:time_end, 'Qhs_sys_kWh']
        Qcs_sys_kWh = building_demand_cea_build_df.loc[time_start:time_end, 'Qcs_sys_kWh'].abs()

        thermal_between_generation_emission_build_df = (Qhs_sys_kWh + Qcs_sys_kWh) * 1000

        # Electric grid loads
        E_hs_kWh = building_demand_cea_build_df.loc[time_start:time_end, 'E_hs_kWh']
        E_cs_kWh = building_demand_cea_build_df.loc[time_start:time_end, 'E_cs_kWh'].abs()

        electric_grid_load_cea_build_df = (E_hs_kWh + E_cs_kWh) * 1000  # From kWh to Wh

        # Temperatures
        T_int_build_df = building_demand_cea_build_df.loc[time_start:time_end, 'T_int_C']
        if building == buildings_names[0]:
            T_ext_cea_df = building_demand_cea_build_df.loc[time_start:time_end, 'T_ext_C']

        # Add the data to the dictionary that includes all the buildings data
        thermal_room_load_cea_dic[building] = thermal_room_load_cea_build_df
        thermal_between_generation_emission_cea_dic[building] = thermal_between_generation_emission_build_df
        electric_grid_load_cea_dic[building] = electric_grid_load_cea_build_df
        T_int_cea_dic[building] = T_int_build_df

    return (
        T_int_cea_dic,
        T_ext_cea_df,
        thermal_room_load_cea_dic,
        thermal_between_generation_emission_cea_dic,
        electric_grid_load_cea_dic
    )
