import pandas as pd
import numpy as np
import os
from geopandas import GeoDataFrame as Gdf
from simpledbf import Dbf5
from cea.osmose.extract_demand_outputs import extract_cea_outputs_to_osmose_main, path_to_osmose_project_bui, \
    path_to_osmose_project_hcs
from cea.osmose.wp1 import write_string_to_txt, osmose_one_run
from cea.osmose import settings
osmose_project_data_path = settings.osmose_project_data_path
path_to_district_folder = settings.path_to_district_folder

def extract_demand_output_district_to_osmose(path_to_district_folder, timesteps, season, specified_building):

    ## 1. Prepare district info and file connections
    geometry_df, occupancy_df = prepare_district_info(path_to_district_folder)

    ## 2. Write input parameters to osmose
    write_input_parameter_to_osmose(geometry_df, occupancy_df, season, specified_building, timesteps)

    ## 3. Run osmose
    result_path, run_folder = osmose_one_run('N_base')
    print(result_path, run_folder)

def prepare_district_info(path_to_district_folder):
    # read building function and GFA from district
    occupancy_df = reard_dbf_from_cea_input(path_to_district_folder, 'occupancy')
    occupancy_df = occupancy_df.set_index('Name')
    # calculate Af
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
    Af_per_function = calc_Af_per_function(geometry_df, occupancy_df)
    # write outputs for each function (input parameters to osmose)
    m_ve_min_df = pd.DataFrame()
    for case in ['WTP_CBD_m_WP1_OFF', 'WTP_CBD_m_WP1_HOT', 'WTP_CBD_m_WP1_RET']:
        output_building, output_hcs = extract_cea_outputs_to_osmose_main(case, timesteps, season, specified_building,
                                                                         problem_type='district')
        # TODO: get typical hours
        # get file and extrapolate
        building_Af_m2 = output_hcs['Af_m2'][0]
        Af_multiplication_factor = Af_per_function[case.split('_')[4]] / building_Af_m2
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

def calc_Af_per_function(geometry_df, occupancy_df):
    Af_per_function = {}
    for function in ['HOTEL', 'OFFICE', 'RETAIL']:
        buildings = occupancy_df[function][occupancy_df[function] == 1].index
        Af_per_function[function[:3]] = geometry_df['Af'][buildings].sum()
    return Af_per_function


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
    timesteps = settings.timesteps # TODO: use typical hours
    season = 'Summer'
    specified_building = ['B005'] # building to get demand
    extract_demand_output_district_to_osmose(path_to_district_folder, timesteps, season, specified_building)