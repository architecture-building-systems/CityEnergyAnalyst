import pandas as pd
import numpy as np
import os
from geopandas import GeoDataFrame as Gdf
from simpledbf import Dbf5
from cea.osmose.extract_demand_outputs import extract_cea_outputs_to_osmose_main, path_to_osmose_project_bui, \
    path_to_osmose_project_hcs
from cea.osmose.wp1 import write_string_to_txt, osmose_one_run, write_osmose_general_inputs
from cea.osmose import settings
osmose_project_data_path = settings.osmose_project_data_path
path_to_district_folder = settings.path_to_district_folder
result_destination = settings.result_destination

RESET_INPUTS = True

def extract_demand_output_district_to_osmose(path_to_district_folder, timesteps, season, specified_building):

    if RESET_INPUTS:
        ## 1. Prepare district info and file connections
        geometry_df, occupancy_df = prepare_district_info(path_to_district_folder)

        ## 2. Write input parameters to
        periods = 1
        timesteps_calc = write_input_parameter_to_osmose(geometry_df, occupancy_df, season, specified_building, timesteps)
        write_osmose_general_inputs(result_destination, periods, timesteps_calc)

    ## 3. Run osmose
    for tech in settings.TECHS:
        # result_path, run_folder = osmose_one_run('N_base')
        result_path, run_folder = osmose_one_run(tech)
        print(result_path, run_folder)

def prepare_district_info(path_to_district_folder):
    # read building function and GFA from district
    occupancy_df = reard_dbf_from_cea_input(path_to_district_folder, 'occupancy')
    occupancy_df = occupancy_df.set_index('Name')
    # calculate Aftech
    geometry_df = get_building_Af_from_geometry(path_to_district_folder)
    # gather all info in district_df
    district_df = occupancy_df[['HOTEL', 'OFFICE', 'RETAIL']]
    district_df['Af_m2'] = geometry_df['Af']
    path_to_district_demand_folder = os.path.join(path_to_district_folder, 'outputs\\data\\demand\\')
    # output: path_to_case
    write_string_to_txt(path_to_district_folder, osmose_project_data_path, 'path_to_case.txt')
    # output: building_info.csv
    district_df.to_csv(os.path.join(path_to_district_demand_folder, 'building_info.csv'))
    # output: path_to_district_demand.txt (path to save osmose outputs)
    write_string_to_txt(os.path.join(path_to_district_demand_folder, 'district_cooling_demand.csv'),
                        osmose_project_data_path, 'path_to_district_demand.txt')
    return geometry_df, occupancy_df


def write_input_parameter_to_osmose(geometry_df, occupancy_df, season, specified_building, timesteps):
    print('writing parameters to osmose')

    Af_per_function, Af_buildings = calc_Af_per_function(geometry_df, occupancy_df)
    # write outputs for each function (input parameters to osmose)
    m_ve_min_df = pd.DataFrame()
    for case in ['WTP_CBD_m_WP1_OFF', 'WTP_CBD_m_WP1_HOT', 'WTP_CBD_m_WP1_RET']:
        print(case)
        output_building, \
        output_hcs, \
        timesteps_calc = extract_cea_outputs_to_osmose_main(case, timesteps, season,
                                                            specified_building,
                                                            problem_type='district') #extrapolate demand from a specified building
        # get file and extrapolate
        building_Af_m2 = output_hcs['Af_m2'][0]
        Af_multiplication_factor = Af_per_function[case.split('_')[4]] / building_Af_m2
        # save multiplication factor of each building to csv
        df = pd.DataFrame()
        df['mult'] = Af_buildings[case.split('_')[4]] / building_Af_m2
        df_T = df.T
        file_path = os.path.join('',*[osmose_project_data_path, specified_building[0] + '_' + case.split('_')[4] + '_mult.csv'])
        df_T.to_csv(file_path, header=None, index=False)

        # save specified building original values
        output_building.T.to_csv(path_to_osmose_project_bui(specified_building[0] + '_' + case.split('_')[4]), header=False)  # save files
        output_hcs.T.to_csv(path_to_osmose_project_hcs(specified_building[0] + '_' + case.split('_')[4], 'hcs'), header=False)  # save files
        output_hcs_original = output_hcs.copy()
        T_OAU_offcoil_df = output_hcs_original[[column for column in output_hcs.columns if 'T_OAU_offcoil' in column]]
        output_hcs_original.drop(columns=[column for column in output_hcs.columns if 'T_OAU_offcoil' in column], inplace=True)
        # save output_hcs for each T_OAU_offcoil
        for i, column in enumerate(T_OAU_offcoil_df.columns):
            new_hcs_df = output_hcs_original.copy()
            new_hcs_df['T_OAU_offcoil'] = T_OAU_offcoil_df[column]
            file_name_extension = 'hcs_in' + str(i + 1)
            new_hcs_df.T.to_csv(path_to_osmose_project_hcs(specified_building[0] + '_' + case.split('_')[4], file_name_extension),
                                header=False)
        ## TODO: this part might be redundant
        ## output_building (scaled to Af)
        columns_with_scalar_values = [column for column in output_building.columns if 'Tww' not in column]
        scalar_df = output_building[columns_with_scalar_values] * Af_multiplication_factor
        output_building.update(scalar_df)
        output_building.T.to_csv(path_to_osmose_project_bui('B_' + case.split('_')[4]), header=False)  # save files
        ## output_hcs (scaled to Af)
        columns_with_scalar_values = [column for column in output_hcs.columns
                                      if ('v_' in column or 'V_' in column or 'm_' in column or 'M_' in column or
                                          'Af_m2' in column or 'Vf_m3' in column)]
        scalar_df = output_hcs[columns_with_scalar_values] * Af_multiplication_factor
        output_hcs.update(scalar_df)
        # get m_ve_min
        m_ve_min_df['m_ve_min_'+case.split('_')[-1]] = output_hcs['m_ve_min']
        m_ve_min_df['T_ext_wb'] = output_hcs['T_ext_wb']
        output_hcs.T.to_csv(path_to_osmose_project_hcs('B_' + case.split('_')[4], 'hcs'), header=False)  # save files
        # remove T_OAU_offcoil
        T_OAU_offcoil_df = output_hcs[[column for column in output_hcs.columns if 'T_OAU_offcoil' in column]]
        output_hcs.drop(columns=[column for column in output_hcs.columns if 'T_OAU_offcoil' in column], inplace=True)
        # save output_hcs for each T_OAU_offcoil
        for i, column in enumerate(T_OAU_offcoil_df.columns):
            new_hcs_df = output_hcs.copy()
            new_hcs_df['T_OAU_offcoil'] = T_OAU_offcoil_df[column]
            file_name_extension = 'hcs_in' + str(i + 1)
            new_hcs_df.T.to_csv(path_to_osmose_project_hcs('B_' + case.split('_')[4], file_name_extension),
                                header=False)
    m_ve_min_df.T.to_csv(path_to_osmose_project_hcs('m_ve_min', 'all'), header=False)
    return timesteps_calc

def calc_Af_per_function(geometry_df, occupancy_df):
    Af_per_function = {}
    Af_buildings_per_function = {}
    for function in ['HOTEL', 'OFFICE', 'RETAIL']:
        buildings = occupancy_df[function][occupancy_df[function] == 1].index
        Af_per_function[function[:3]] = geometry_df['Af'][buildings].sum()
        Af_buildings_per_function[function[:3]] = geometry_df.loc[buildings,'Af']
    return Af_per_function, Af_buildings_per_function


def get_building_Af_from_geometry(path_to_district_folder):
    geometry_df = reard_dbf_from_cea_input(path_to_district_folder, 'geometry')
    geometry_df['footprint'] = geometry_df.area
    geometry_df['GFA'] = geometry_df['footprint'] * (
            geometry_df['floors_bg'] + geometry_df['floors_ag'])  # gross floor area
    geometry_df = geometry_df.set_index('Name')
    architecture_df = reard_dbf_from_cea_input(path_to_district_folder, 'architecture')
    architecture_df = architecture_df.set_index('Name')
    geometry_df['Af'] = geometry_df['GFA'] * architecture_df['Hs_ag']
    return geometry_df


def reard_dbf_from_cea_input(path_to_district_folder, file_name):
    file_paths = {'occupancy': 'inputs\\building-properties\\occupancy.dbf',
                  'geometry': 'inputs\\building-geometry\\zone.dbf',
                  'architecture': 'inputs\\building-properties\\architecture.dbf'}
    if file_name == 'geometry':
        df = Gdf.from_file(os.path.join(path_to_district_folder, file_paths[file_name]))
    else:
        dbf = Dbf5(os.path.join(path_to_district_folder, file_paths[file_name]))
        df = dbf.to_dataframe()
    return df



if __name__ == '__main__':
    timesteps = settings.timesteps
    season = 'Summer'
    specified_building = ['B005'] # building to get demand
    extract_demand_output_district_to_osmose(path_to_district_folder, timesteps, season, specified_building)