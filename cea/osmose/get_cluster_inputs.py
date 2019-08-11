import pandas as pd
import numpy as np
from cea.utilities import epwreader
import os
from cea.osmose.extract_demand_outputs import path_to_demand_output, path_to_total_demand, calc_w_from_rh
from sklearn import preprocessing

cases = ['ABU_CBD_m_WP1_HOT']

output_folder = 'C:\\Users\\Shanshan\\Documents\\0_Shanshan_Hsieh\\WP2\\Typical_days'

for case in cases:
    # read weather file
    weather_folder = 'C:\\CEA_cases\\weather\\Weather_Converter'
    file_name = 'ABU_DHABI_TC-hourEPW.epw'
    weather_path = os.path.join(weather_folder,file_name)
    weather_data = epwreader.epw_reader(weather_path)
    weather_data = weather_data[['glohorrad_Whm2', 'drybulb_C', 'relhum_percent']]
    # read demand results
    tsd_df = pd.read_excel(path_to_demand_output('B001', case)['xls'])
    # read total demand
    total_demand_df = pd.read_csv(path_to_total_demand(case)).set_index('Name')
    Af_m2 = total_demand_df['Af_m2']['B001']
    people = preprocessing.normalize([tsd_df['people'].values])
    # create output_df
    output_df = pd.DataFrame()
    output_df['GI'] = weather_data['glohorrad_Whm2'].values
    output_df['T_ext'] = weather_data['drybulb_C'].values
    output_df['people'] = people
    output_df['w_ext'] = np.vectorize(calc_w_from_rh)(weather_data['relhum_percent'], weather_data['drybulb_C'])
    # save output_df
    output_name = case.split('_')[0] + '_' + case.split('_')[4] + '_parameters.csv'
    output_path = os.path.join(output_folder, output_name)
    output_df.to_csv(output_path)
    print (output_path)



