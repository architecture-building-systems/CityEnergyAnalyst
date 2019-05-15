import pandas as pd
import numpy as np
from cea.osmose import extract_demand_outputs as extract
from cea.osmose import settings as settings
import os


def main(case, timesteps):
    building_name = 'B001'
    start_t = extract.get_start_t(case, timesteps)
    tsd_df = pd.read_excel(extract.path_to_demand_output(building_name, case)['xls'])
    # reduce to 24 or 168 hours
    end_t = (start_t + timesteps)
    # reduced_demand_df = demand_df[start_t:end_t]
    reduced_tsd_df = tsd_df[start_t:end_t]
    reduced_tsd_df = reduced_tsd_df.reset_index()
    # climate df
    output_climate = pd.DataFrame()
    ## output climate
    output_climate['T_ext'] = reduced_tsd_df['T_ext']
    output_climate['rh_ext'] = np.where((reduced_tsd_df['rh_ext'] / 100) >= 1, 0.99,
                                        reduced_tsd_df['rh_ext'] / 100) * 100
    output_climate.to_csv(path_to_climate_output(case, start_t, end_t))

    return


def path_to_climate_output(case, start_t, end_t):
    path_to_folder = settings.result_destination
    file_name = case.split('_')[0] + '_' + str(start_t) + '_' + str(end_t)
    path_to_file = os.path.join(path_to_folder, '%s.%s' % (file_name, 'csv'))
    return path_to_file


if __name__ == '__main__':
    cases = ['WTP_CBD_m_WP1_OFF', 'ABU_CBD_m_WP1_OFF','HKG_CBD_m_WP1_OFF', 'MDL_CBD_m_WP1_OFF']
    timesteps = 168
    for case in cases:
        main(case, timesteps)
