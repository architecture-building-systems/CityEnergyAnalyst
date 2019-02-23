from simpledbf import Dbf5
import pandas as pd
import numpy as np
import os


def main_preliminary_functions_hvac_efficiencies(scenario, scenario_data_path, buildings_names, footprint,
                                                 buildings_cardinal, cooling_generation_df, emission_systems_cooling_df,
                                                 emission_systems_controller_df, generation_cooling_code_dic,
                                                 emissions_cooling_type_dic, emissions_controller_type_dic):

    length_and_width_df = get_building_length_and_width(scenario_data_path, scenario, buildings_names)
    Y_dic = calculate_pipe_transmittance(scenario_data_path, scenario, buildings_names)
    fforma_dic = calculate_form_factor(length_and_width_df, footprint, buildings_names)
    eff_cs_dic, source_cs_dic, scale_cs_dic, dTcs_C_dic, Qcsmax_Wm2_dic, Tc_sup_air_ahu_C_dic, \
        Tc_sup_air_aru_C_dic, dT_Qcs_dic, temperature_difference_df = get_hvac_data(
            buildings_names, buildings_cardinal, cooling_generation_df, emission_systems_cooling_df,
            emission_systems_controller_df, generation_cooling_code_dic, emissions_cooling_type_dic,
            emissions_controller_type_dic)

    return length_and_width_df, Y_dic, fforma_dic, eff_cs_dic, source_cs_dic, scale_cs_dic, dTcs_C_dic, \
        Qcsmax_Wm2_dic, Tc_sup_air_ahu_C_dic, Tc_sup_air_aru_C_dic, dT_Qcs_dic, temperature_difference_df


def get_building_length_and_width(scenario_data_path, scenario, buildings_names):
    # Function taken from calc_bounding_box_geom in the CEA file building_properties.py
    # Get data
    geometry_shapefile_path = os.path.join(scenario_data_path, scenario, 'inputs', 'building-geometry', 'zone.shp')

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

    length_and_width_df = pd.DataFrame(length_and_width, columns=['Name', 'Ll', 'Lw'])
    length_and_width_df.set_index('Name', inplace=True)

    return length_and_width_df


def calculate_pipe_transmittance(scenario_data_path, scenario, buildings_names):
    # Get data
    dbf = Dbf5(os.path.join(scenario_data_path, scenario, 'inputs', 'building-properties', 'age.dbf'))
    age_df = dbf.to_dataframe()
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
                print 'Incorrect HVAC renovation year for ' + building + ': if HVAC has not been renovated, ' \
                                                                         'the year should be set to 0'
                quit()
        else:
            Y_dic[building] = 0.4

    return Y_dic


def calculate_form_factor(length_and_width_df, footprint, buildings_names):
    fforma_dic = {}
    for building in buildings_names:
        fforma_dic[building] = footprint[building] / (
                    length_and_width_df.loc[building]['Lw'] * length_and_width_df.loc[building]['Ll'])

    return fforma_dic


def get_hvac_data(buildings_names, buildings_cardinal, cooling_generation_df, emission_systems_cooling_df,
                  emission_systems_controller_df, generation_cooling_code_dic, emissions_cooling_type_dic,
                  emissions_controller_type_dic):
    eff_cs_dic = {}
    source_cs_dic = {}
    scale_cs_dic = {}
    dTcs_C_dic = {}
    Qcsmax_Wm2_dic = {}
    Tc_sup_air_ahu_C_dic = {}
    Tc_sup_air_aru_C_dic = {}
    dT_Qcs_dic = {}
    temperature_difference_df = pd.DataFrame(np.zeros((buildings_cardinal, 3)), buildings_names, ['ahu', 'aru', 'scu'])

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
            temperature_difference_df.loc[building][sys] = emission_systems_cooling_df.loc[
                emissions_cooling_type, 'dTcs0_' + sys + '_C']

        dT_Qcs_dic[building] = emission_systems_controller_df.loc[emissions_controller_type_dic[building]]['dT_Qcs']

    return eff_cs_dic, source_cs_dic, scale_cs_dic, dTcs_C_dic, Qcsmax_Wm2_dic, Tc_sup_air_ahu_C_dic, \
        Tc_sup_air_aru_C_dic, dT_Qcs_dic, temperature_difference_df
