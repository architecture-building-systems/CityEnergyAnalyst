from __future__ import division
import numpy as np
import pandas as pd
import os

BUILDINGS_DEMANDS_COLUMNS = ['Name', 'Qww_sys_kWh', 'Qcdata_sys_kWh',
                             'Qcs_sen_ahu_kWh', 'Qcs_sen_aru_kWh', 'Qcs_sen_scu_kWh', 'Qcs_sen_sys_kWh',
                             'Qcs_lat_ahu_kWh', 'Qcs_lat_aru_kWh', 'Qcs_lat_sys_kWh',
                             'Qcs_sys_ahu_kWh', 'Qcs_sys_aru_kWh', 'Qcs_sys_scu_kWh',
                             'people', 'x_int', 'T_int_C', 'T_ext_C']
H_WE_kJperkg = 2466e3 / 1000  # (J/kg) Latent heat of vaporization of water [section 6.3.6 in ISO 52016-1:2007]


def main():
    building_names = ['B001','B002','B007']

    for name in building_names:
        demand_df = pd.read_csv(path_to_demand_output(name, read=True), usecols=(BUILDINGS_DEMANDS_COLUMNS))
        reduced_demand_df = demand_df[3217:3240]
        reduced_demand_df['w_gain_g'] = (reduced_demand_df['Qcs_lat_sys_kWh'] / H_WE_kJperkg) * 1000  # FIXME: check unit with Gabriel
        reduced_demand_df['Q_gain_kWh'] = abs(reduced_demand_df['Qcs_sen_sys_kWh'])
        reduced_demand_df.T.to_csv(path_to_demand_output(name, read=False))
    return


def path_to_demand_output(building_name, read):
    case = 'WTP_CBD_m'
    format = 'csv'
    path_to_folder = 'C:\\CEA_cases\\%s\\outputs\\data\\demand' % case
    if read:
        path_to_file = os.path.join(path_to_folder, '%s.%s' % (building_name, format))
    else:
        path_to_file = os.path.join(path_to_folder, '%s_from_cea.%s' % (building_name, format))

    return path_to_file


if __name__ == '__main__':
    main()
