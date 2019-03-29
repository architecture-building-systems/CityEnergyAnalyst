from __future__ import division
import numpy as np
import pandas as pd
import os
from cea.utilities.physics import calc_rho_air
from cea.plots.demand.comfort_chart import p_w_from_rh_p_and_ws, p_ws_from_t, hum_ratio_from_p_w_and_p

BUILDINGS_DEMANDS_COLUMNS = ['Name', 'Qww_sys_kWh', 'Qcdata_sys_kWh',
                             'Qcs_sen_ahu_kWh', 'Qcs_sen_aru_kWh', 'Qcs_sen_scu_kWh', 'Qcs_sen_sys_kWh',
                             'Qcs_lat_ahu_kWh', 'Qcs_lat_aru_kWh', 'Qcs_lat_sys_kWh',
                             'Qcs_sys_ahu_kWh', 'Qcs_sys_aru_kWh', 'Qcs_sys_scu_kWh',
                             'people', 'x_int', 'T_int_C', 'T_ext_C']

TSD_COLUMNS = ['T_int', 'T_ext', 'rh_ext', 'w_int', 'x_int', 'x_ve_inf', 'x_ve_mech', 'people', 'I_sol_and_I_rad',
               'Q_gain_lat_peop', 'Q_gain_sen_peop',
               'Q_gain_sen_vent', 'g_dhu_ld', 'm_ve_inf', 'm_ve_mech', 'm_ve_rec', 'm_ve_required', 'm_ve_window']

Q_GAIN_ENV = ['Q_gain_sen_base', 'Q_gain_sen_roof', 'Q_gain_sen_wall', 'Q_gain_sen_wind']

# 'Q_loss_sen_base','Q_loss_sen_roof', 'Q_loss_sen_wall', 'Q_loss_sen_wind']

Q_GAIN_INT = ['Q_gain_sen_app', 'Q_gain_sen_data', 'Q_gain_sen_light', 'Q_gain_sen_pro', 'Q_loss_sen_ref']

TSD_COLUMNS.extend(Q_GAIN_ENV)
TSD_COLUMNS.extend(Q_GAIN_INT)

H_WE_Jperkg = 2466e3  # (J/kg) Latent heat of vaporization of water [section 6.3.6 in ISO 52016-1:2007]
floor_height_m = 2.5  # FIXME: read from CEA
v_CO2_Lpers = 0.0048  # [L/s/person]
rho_CO2_kgperm3 = 1.98  # [kg/m3]
CO2_env_ppm = 400 / 1e6  # [m3 CO2/m3]
CO2_ve_min_ppm = 1200 / 1e6  # [m3 CO2/m3]

CO2_room_max_ppm = 900 / 1e6
CO2_room_min_ppm = 400 / 1e6
CO2_room_ppm = 1200 / 1e6

Pair_Pa = 101325
Ra_JperkgK = 286.9
Rw_JperkgK = 461.5

RH_max = 80  # %
RH_min = 40  # %
# T_offcoil # TODO: move to config or set as a function
T_low_C = 8.1
T_high_C = 14.1
T_interval = 0.65  # 0.5

N_m_ve_max = 3


# T_low_C = 14.5
# T_high_C = 18
# T_interval = 0.65 #0.5
# SS553_lps_m2 = 0.6


def extract_cea_outputs_to_osmose_main(case, start_t, timesteps, specified_buildings):
    # read total demand
    total_demand_df = pd.read_csv(path_to_total_demand(case)).set_index('Name')
    if specified_buildings != []:
        building_names = specified_buildings
    else:
        building_names = total_demand_df.index

    for name in building_names:
        # read demand output
        # demand_df = pd.read_csv(path_to_demand_output(name)['csv'], usecols=(BUILDINGS_DEMANDS_COLUMNS))
        tsd_df = pd.read_excel(path_to_demand_output(name, case)['xls'])

        # reduce to 24 or 168 hours
        end_t = (start_t + timesteps)
        # reduced_demand_df = demand_df[start_t:end_t]
        reduced_tsd_df = tsd_df[start_t:end_t]
        reduced_tsd_df = reduced_tsd_df.reset_index()
        output_df = reduced_tsd_df
        output_df1 = pd.DataFrame()
        output_hcs = pd.DataFrame()

        ## output to building.lua
        # de-activate inf when no occupant
        # reduced_tsd_df.ix[output_df.people == 0, 'm_ve_inf'] = 0
        output_df1['m_ve_inf'] = reduced_tsd_df['m_ve_inf']  # kg/s
        ## heat gain
        calc_sensible_gains(output_df, reduced_tsd_df)
        output_df1['Q_gain_total_kWh'] = reduced_tsd_df['Q_gain_total_kWh']
        output_df1['Q_gain_occ_kWh'] = reduced_tsd_df['Q_gain_occ_kWh']
        ## humidity gain
        output_df1['w_gain_occ_kgpers'] = reduced_tsd_df['w_int']
        # output_df1['w_gain_infil_kgpers'] = reduced_tsd_df['m_ve_inf'] * reduced_tsd_df['w_ext'] / 1000
        output_df1['w_gain_infil_kgpers'] = reduced_tsd_df['m_ve_inf'] * reduced_tsd_df['x_ve_inf']
        output_df1 = output_df1.round(4)  # osmose does not read more decimals (observation)
        # output_df1 = output_df1.drop(output_df.index[range(7)])

        ## output to hcs_out
        # change units
        output_hcs['T_ext'] = reduced_tsd_df['T_ext']
        output_hcs['T_ext_wb'] = reduced_tsd_df['T_ext_wetbulb']
        output_hcs['T_RA'] = reduced_tsd_df['T_int']
        if ('OFF' in case) or ('RET' in case) or ('HOT' in case):
            output_hcs['w_RA'] = 10.29  # 24C with 55% RH
        elif 'RES' in case:
            output_hcs['w_RA'] = 13.1  # 28C with 55% RH
        output_hcs['rh_ext'] = np.where((reduced_tsd_df['rh_ext'] / 100) >= 1, 0.99, reduced_tsd_df['rh_ext'] / 100)
        output_hcs['w_ext'] = np.vectorize(calc_w_from_rh)(reduced_tsd_df['rh_ext'],
                                                           reduced_tsd_df['T_ext'])  # g/kg d.a.
        ## building size
        output_hcs.loc[:, 'Af_m2'] = total_demand_df['Af_m2'][name]
        output_hcs.loc[:, 'Vf_m3'] = floor_height_m * total_demand_df['Af_m2'][name]
        ## CO2 gain
        calc_CO2_gains(output_hcs, reduced_tsd_df)
        output_df1['v_CO2_in_infil_occupant_m3pers'] = reduced_tsd_df['v_CO2_infil_window_m3pers'] + reduced_tsd_df[
            'v_CO2_occupant_m3pers']
        output_hcs['V_CO2_max_m3'] = reduced_tsd_df['V_CO2_max_m3']
        output_hcs['V_CO2_min_m3'] = reduced_tsd_df['V_CO2_min_m3']
        output_hcs['v_CO2_in_infil_occupant_m3pers'] = reduced_tsd_df['v_CO2_infil_window_m3pers'] + reduced_tsd_df[
            'v_CO2_occupant_m3pers']

        output_hcs['CO2_ext_ppm'] = CO2_env_ppm  # TODO: get actual profile?
        output_hcs['CO2_max_ppm'] = CO2_room_max_ppm
        output_hcs['m_ve_req'] = reduced_tsd_df['m_ve_required']
        output_hcs['rho_air'] = np.vectorize(calc_rho_air)(reduced_tsd_df['T_ext'])
        reduced_tsd_df['rho_air_int'] = np.vectorize(calc_moist_air_density)(reduced_tsd_df['T_int'] + 273.15,
                                                                             reduced_tsd_df['x_int'])
        output_hcs['M_dry_air'] = np.vectorize(calc_m_dry_air)(output_hcs['Vf_m3'], reduced_tsd_df['rho_air_int'],
                                                               reduced_tsd_df['x_int'])
        output_hcs['CO2_ve_min_ppm'] = CO2_ve_min_ppm
        output_hcs['m_ve_min'] = np.vectorize(
            calc_m_exhaust_from_CO2)(output_hcs['CO2_ve_min_ppm'], output_hcs['CO2_ext_ppm'],
                                     output_hcs['v_CO2_in_infil_occupant_m3pers'], output_hcs['rho_air'])
        output_hcs['m_ve_max'] = output_hcs['m_ve_min'] * N_m_ve_max
        output_hcs['rh_max'] = RH_max
        output_hcs['rh_min'] = RH_min
        output_hcs['w_max'] = np.vectorize(calc_w_from_rh)(output_hcs['rh_max'], reduced_tsd_df['T_int'])
        output_hcs['w_min'] = np.vectorize(calc_w_from_rh)(output_hcs['rh_min'], reduced_tsd_df['T_int'])
        output_hcs['m_w_max'] = np.vectorize(calc_m_w_in_air)(reduced_tsd_df['T_int'], output_hcs['w_max'],
                                                              output_hcs['Vf_m3'])
        output_hcs['m_w_min'] = (np.vectorize(calc_m_w_in_air)(reduced_tsd_df['T_int'], output_hcs['w_min'],
                                                               output_hcs['Vf_m3'])).min()

        output_hcs = output_hcs.round(4)  # osmose does not read more decimals (observation)
        # output_hcs = output_hcs.drop(output_df.index[range(7)])

        # a set of off coil temperatures for oau
        T_OAU_offcoil = np.arange(T_low_C, T_high_C, T_interval)
        output_hcs_dict = {}
        output_hcs_copy = output_hcs.copy()
        for i in range(T_OAU_offcoil.size):
            # output hcs
            output_hcs['T_OAU_offcoil' + str(i + 1)] = T_OAU_offcoil[i]
            # output hcs_in
            output_hcs_dict[i] = output_hcs_copy
            output_hcs_dict[i]['T_OAU_offcoil'] = T_OAU_offcoil[i]
            file_name_extension = 'hcs_in' + str(i + 1)
            output_hcs_dict[i].T.to_csv(path_to_osmose_project_hcs(name, file_name_extension), header=False)
            # output input_T1
            input_T_df = pd.DataFrame()
            input_T_df['OAU_T_SA'] = output_hcs_dict[i]['T_OAU_offcoil']
            input_T_df['T_ext_C'] = reduced_tsd_df['T_ext']
            input_T_df.T.to_csv(path_to_osmose_project_inputT(str(i + 1)), header=False)
        # output input_T0
        input_T0_df = pd.DataFrame()
        input_T0_df['T_ext_C'] = reduced_tsd_df['T_ext']
        input_T0_df['OAU_T_SA'] = 12.6
        input_T0_df.T.to_csv(path_to_osmose_project_inputT(str(0)), header=False)

        # write outputs
        output_df1.T.to_csv(path_to_osmose_project_bui(name), header=False)
        output_hcs.T.to_csv(path_to_osmose_project_hcs(name, 'hcs'), header=False)

        # output_df.loc[:, 'Mf_air_kg'] = output_df['Vf_m3']*calc_rho_air(24)

        # add hour of the day
        # output_df['hour'] = range(1, 1 + timesteps)
        # TODO: delete the first few hours without demand (howwwwww?)
        # output_df = output_df.round(4)  # osmose does not read more decimals (observation)
        # output_df = output_df.reset_index()
        # output_df = output_df.drop(['index'], axis=1)
        # output_df = output_df.drop(output_df.index[range(7)])

    return building_names


def calc_CO2_gains(output_hcs, reduced_tsd_df):
    reduced_tsd_df['CO2_ext_ppm'] = CO2_env_ppm  # m3 CO2/m3
    # from occupants
    reduced_tsd_df['v_CO2_occupant_m3pers'] = calc_co2_from_occupants(reduced_tsd_df['people'])
    # from inlet air
    reduced_tsd_df['rho_air'] = np.vectorize(calc_rho_air)(reduced_tsd_df['T_ext'])  # kg/m3
    reduced_tsd_df['v_in_infil_window'] = (reduced_tsd_df['m_ve_inf'] + reduced_tsd_df['m_ve_window']) / \
                                          reduced_tsd_df['rho_air']
    reduced_tsd_df['v_CO2_infil_window_m3pers'] = reduced_tsd_df['v_in_infil_window'] * reduced_tsd_df['CO2_ext_ppm']
    reduced_tsd_df['V_CO2_max_m3'] = output_hcs['Vf_m3'] * CO2_room_max_ppm
    reduced_tsd_df['V_CO2_min_m3'] = output_hcs['Vf_m3'] * CO2_room_min_ppm
    return np.nan


def calc_sensible_gains(output_df, reduced_tsd_df):
    # radiation
    reduced_tsd_df['Q_gain_rad_kWh'] = reduced_tsd_df['I_sol_and_I_rad'] / 1000
    # environment
    reduced_tsd_df['Q_gain_env_kWh'] = reduced_tsd_df.loc[:, Q_GAIN_ENV].sum(axis=1) / 1000
    # internal (appliances, lighting...)
    reduced_tsd_df['Q_gain_int_kWh'] = reduced_tsd_df.loc[:, Q_GAIN_INT].sum(axis=1) / 1000
    # occupant
    reduced_tsd_df['Q_gain_occ_kWh'] = reduced_tsd_df['Q_gain_sen_peop'] / 1000
    # total
    reduced_tsd_df['Q_gain_total_kWh'] = reduced_tsd_df['Q_gain_rad_kWh'] + reduced_tsd_df['Q_gain_env_kWh'] + \
                                         reduced_tsd_df[
                                             'Q_gain_int_kWh'] + reduced_tsd_df['Q_gain_occ_kWh']
    return np.nan


def calc_m_w_in_air(Troom_C, w_gperkg, Vf_m3):
    Troom_K = Troom_C + 273.15
    w_kgperkg = w_gperkg / 1000
    rho_ma_kgperm3 = calc_moist_air_density(Troom_K, w_kgperkg)
    m_dry_air_kg = calc_m_dry_air(Vf_m3, rho_ma_kgperm3, w_kgperkg)
    m_w_kgpers = m_dry_air_kg * w_kgperkg / 3600
    return m_w_kgpers


def calc_m_dry_air(Vf_m3, rho_ma_kgperm3, w_kgperkg):
    m_moist_air_kg = Vf_m3 * rho_ma_kgperm3
    m_dry_air_kg = m_moist_air_kg / (1 + w_kgperkg)
    return m_dry_air_kg


def calc_moist_air_density(Troom_K, w_kgperkg):
    term1 = (Pair_Pa / (Ra_JperkgK * Troom_K)) * (1 + w_kgperkg)
    term2 = (1 + w_kgperkg * Rw_JperkgK / Ra_JperkgK)
    rho_ma_kgperm3 = term1 / term2
    return rho_ma_kgperm3


def calc_co2_from_occupants(occupants):
    # from Jeremie's thesis
    v_CO2_m3pers = v_CO2_Lpers / 1000
    v_CO2_m3pers = v_CO2_m3pers * occupants
    return v_CO2_m3pers


def calc_w_from_rh(rh, t):
    rh = rh / 100
    pws = p_ws_from_t(t)
    pw = p_w_from_rh_p_and_ws(rh, pws)
    p = 101325  # [Pa]
    w = hum_ratio_from_p_w_and_p(pw, p)
    return w * 1000  # g/kg d.a.


def calc_m_exhaust_from_CO2(CO2_room, CO2_ext, CO2_gain_m3pers, rho_air):
    # assuming m_exhaust = m_ve_mech - m_ve_inf
    m_exhaust_kgpers = CO2_gain_m3pers * rho_air / (CO2_room - CO2_ext)
    return m_exhaust_kgpers


##  Paths (TODO: connected with cea.config and inputLocator)


def path_to_demand_output(building_name, case):
    path_to_file = {}
    path_to_folder = 'C:\\CEA_cases\\%s\\outputs\\data\\demand' % case
    path_to_file['csv'] = os.path.join(path_to_folder, '%s.%s' % (building_name, 'csv'))
    path_to_file['xls'] = os.path.join(path_to_folder, '%s.%s' % (building_name, 'xls'))
    return path_to_file


def path_to_total_demand(case):
    path_to_file = {}
    path_to_folder = 'C:\\CEA_cases\\%s\\outputs\\data\\demand' % case
    path_to_file = os.path.join(path_to_folder, 'Total_demand.%s' % ('csv'))
    return path_to_file


def path_to_osmose_project_bui(building_name):
    format = 'csv'
    path_to_folder = 'C:\\OSMOSE_projects\\hcs_windows\\Projects'
    path_to_file = os.path.join(path_to_folder, '%s_from_cea.%s' % (building_name, format))
    return path_to_file


def path_to_osmose_project_hcs(building_name, extension):
    format = 'csv'
    path_to_folder = 'C:\\OSMOSE_projects\\hcs_windows\\Projects'
    path_to_file = os.path.join(path_to_folder, '%s_from_cea_%s.%s' % (building_name, extension, format))
    return path_to_file


def path_to_osmose_project_inputT(number):
    format = 'csv'
    path_to_folder = 'C:\\OSMOSE_projects\\hcs_windows\\Projects'
    path_to_file = os.path.join(path_to_folder, 'input_T%s.%s' % (number, format))
    return path_to_file


if __name__ == '__main__':
    case = 'WTP_CBD_m_WP1_HOT'
    start_t = 5040  # 5/16: 3240, Average Annual 7/30-8/5: 5040-5207
    timesteps = 168  # 168 (week)
    extract_cea_outputs_to_osmose_main(case, start_t, timesteps)
