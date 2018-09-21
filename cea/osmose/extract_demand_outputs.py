from __future__ import division
import numpy as np
import pandas as pd
import os
from cea.utilities.physics import calc_rho_air

BUILDINGS_DEMANDS_COLUMNS = ['Name', 'Qww_sys_kWh', 'Qcdata_sys_kWh',
                             'Qcs_sen_ahu_kWh', 'Qcs_sen_aru_kWh', 'Qcs_sen_scu_kWh', 'Qcs_sen_sys_kWh',
                             'Qcs_lat_ahu_kWh', 'Qcs_lat_aru_kWh', 'Qcs_lat_sys_kWh',
                             'Qcs_sys_ahu_kWh', 'Qcs_sys_aru_kWh', 'Qcs_sys_scu_kWh',
                             'people', 'x_int', 'T_int_C', 'T_ext_C']

TSD_COLUMNS = ['T_ext', 'rh_ext', 'Q_gain_lat_peop', 'Q_gain_sen_peop', 'Q_gain_sen_vent',
               'g_dhu_ld', 'm_ve_inf', 'm_ve_mech', 'm_ve_rec', 'm_ve_required', 'm_ve_window']

Q_GAIN_ENV = ['Q_gain_sen_base', 'Q_gain_sen_roof', 'Q_gain_sen_wall', 'Q_gain_sen_wind', 'Q_loss_sen_ref']

# 'Q_loss_sen_base','Q_loss_sen_roof', 'Q_loss_sen_wall', 'Q_loss_sen_wind']

Q_GAIN_INT = ['Q_gain_sen_app', 'Q_gain_sen_data', 'Q_gain_sen_light', 'Q_gain_sen_pro']

TSD_COLUMNS.extend(Q_GAIN_ENV)
TSD_COLUMNS.extend(Q_GAIN_INT)

H_WE_Jperkg = 2466e3  # (J/kg) Latent heat of vaporization of water [section 6.3.6 in ISO 52016-1:2007]
floor_height_m = 2.5  # FIXME: read from CEA
v_CO2_Lpers = 0.0048  # [L/s/person]
rho_CO2_kgperm3 = 1.98  # [kg/m3]


def main():
    building_names = ['B001', 'B002', 'B007']
    Ve_lps = {'B001': 18.24, 'B002': 15.6, 'B007': 13.53}
    Af_m2 = {'B001': 28495.062, 'B002': 28036.581, 'B007': 30743.113}
    SS553_lps_m2 = 0.6

    for name in building_names:
        # read demand output
        demand_df = pd.read_csv(path_to_demand_output(name)['csv'], usecols=(BUILDINGS_DEMANDS_COLUMNS))
        tsd_df = pd.read_excel(path_to_demand_output(name)['xls'], usecols=(TSD_COLUMNS))

        # reduce to 24 hours
        start_t = 3217
        end_t = (start_t + 24)
        reduced_demand_df = demand_df[start_t:end_t]
        reduced_tsd_df = tsd_df[start_t:end_t]
        output_df = pd.concat([demand_df[start_t:end_t], tsd_df[start_t:end_t]], axis=1)

        ## building size
        output_df.loc[:, 'Af_m2'] = Af_m2[name]
        output_df.loc[:, 'Vf_m3'] = floor_height_m * Af_m2[name]

        ## humidity gain
        output_df['w_gain_kgpers'] = (reduced_demand_df[
                                          'Qcs_lat_sys_kWh'] / H_WE_Jperkg) / 3.6  # FIXME: check unit with Gabriel
        ## heat gain
        output_df['Q_gain_kWh'] = abs(reduced_demand_df['Qcs_sen_sys_kWh'])
        # environment
        output_df['Q_gain_env_kWh'] = reduced_tsd_df.loc[:, Q_GAIN_ENV].sum(axis=1)
        # internal (appliances, lighting...)
        output_df['Q_gain_int_kWh'] = reduced_tsd_df.loc[:, Q_GAIN_INT].sum(axis=1)
        # occupant
        output_df['Q_gain_occ_kWh'] = reduced_tsd_df['Q_gain_sen_peop']

        ## CO2 gain
        max_ppl = demand_df['people'].max()
        output_df['v_CO2_occupant_m3pers'] = calc_co2_from_occupants(demand_df['people'])

        output_df['profile'] = reduced_demand_df['people'] / max_ppl
        # reduced_demand_df['m_exhaust_min_kgpers'] = reduced_demand_df['people'] * Ve_lps[name] * calc_rho_air(
        #     24) / 1000
        # reduced_demand_df['m_exhaust_min_kgpers'] = reduced_demand_df['profile'] * Ve_lps[name] * calc_rho_air(
        #     24) / 1000

        # exhaust rate from SS553
        output_df['m_exhaust_min_kgpers'] = output_df['profile'] * Af_m2[
            name] * SS553_lps_m2 * calc_rho_air(24) / 1000

        output_df['hour'] = range(1, 25)

        output_df = output_df.round(4)
        output_df.T.ix[1:].to_csv(path_to_osmose_project(name), header=False)

    return


def calc_co2_from_occupants(occupants):
    # from Jeremie's thesis
    v_CO2_m3pers = v_CO2_Lpers / 1000
    v_CO2_m3pers = v_CO2_m3pers * occupants
    return v_CO2_m3pers


def path_to_demand_output(building_name):
    case = 'WTP_CBD_m'
    path_to_file = {}
    path_to_folder = 'C:\\CEA_cases\\%s\\outputs\\data\\demand' % case
    path_to_file['csv'] = os.path.join(path_to_folder, '%s.%s' % (building_name, 'csv'))
    path_to_file['xls'] = os.path.join(path_to_folder, '%s.%s' % (building_name, 'xls'))
    return path_to_file


def path_to_osmose_project(building_name):
    format = 'csv'
    path_to_folder = 'C:\\OSMOSE_projects\\hcs_windows\\Projects'
    path_to_file = os.path.join(path_to_folder, '%s_from_cea.%s' % (building_name, format))
    return path_to_file


if __name__ == '__main__':
    main()
