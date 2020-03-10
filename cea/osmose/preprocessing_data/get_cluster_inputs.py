import pandas as pd
import numpy as np
from cea.utilities import epwreader
import os
from cea.utilities.physics import calc_rho_air
from cea.osmose.extract_demand_outputs import path_to_demand_output, path_to_total_demand, calc_sensible_gains, \
    calc_Q_sen_gain_inf_kWh, get_humidity_ratio_assumptions, calc_co2_from_occupants, calc_m_exhaust_from_CO2, \
    calc_w_from_rh
from sklearn import preprocessing
from cea.osmose.auxiliary_functions import calc_h_from_T_w

H_WE_Jperkg = 2466e3  # (J/kg) Latent heat of vaporization of water [section 6.3.6 in ISO 52016-1:2007]

# cases = ['HKG_CBD_m_WP1_RET','HKG_CBD_m_WP1_HOT','HKG_CBD_m_WP1_OFF']
cases = ['WTP_CBD_m_WP1_RET','WTP_CBD_m_WP1_HOT','WTP_CBD_m_WP1_OFF']

output_folder = 'C:\\Users\\Shanshan\\Documents\\0_Shanshan_Hsieh\\WP2\\Typical_hours'

weather_files = {'ABU': 'ABU_DHABI_TC-hourEPW.epw',
                 'HKG': 'Hong_Kong_SAR_CH-hourEPW.epw',
                 'MDL': 'Mandalay_BM-hourEPW.epw',
                 'WTP': 'SGP_Singapore.486980_IWEC.epw'}

for case in cases:
    # read weather file
    weather_folder = 'C:\\CEA_cases\\0_weather_databases\\Weather_Converter'
    file_name = weather_files[case.split('_')[0]]
    weather_path = os.path.join(weather_folder,file_name)
    weather_data = epwreader.epw_reader(weather_path)
    weather_data = weather_data[['glohorrad_Whm2', 'drybulb_C', 'relhum_percent']]
    # read demand results
    tsd_df = pd.read_excel(path_to_demand_output('B001', case)['xls'])
    # read total demand
    total_demand_df = pd.read_csv(path_to_total_demand(case)).set_index('Name')
    Af_m2 = total_demand_df['Af_m2']['B001']
    people = preprocessing.normalize([tsd_df['people'].values])

    w_RA_gperkg = get_humidity_ratio_assumptions(case)
    ## sensible heat gain
    tsd_df = calc_sensible_gains(tsd_df)
    Q_sen_gain_inf_kWh = np.vectorize(calc_Q_sen_gain_inf_kWh)(tsd_df['T_ext'],
                                                               tsd_df['T_int'],
                                                               tsd_df['m_ve_inf'], w_RA_gperkg)

    ## humidity gain
    Q_lat_gain_occupant_kWh = tsd_df['w_int'] * H_WE_Jperkg / 1000 # to kW
    # output_building['w_gain_infil_kgpers'] = reduced_demand_df['m_ve_inf'] * reduced_demand_df['w_ext'] / 1000
    Q_lat_gain_infil_kWh = tsd_df['m_ve_inf'] * tsd_df['x_ve_inf'] * H_WE_Jperkg / 1000 # to kW
    # minimum ventilation air flow
    CO2_ve_min_ppm = 1200 / 1e6  # [m3 CO2/m3]
    CO2_env_ppm = 400 / 1e6  # [m3 CO2/m3]
    # from occupants
    tsd_df['v_CO2_occupant_m3pers'] = calc_co2_from_occupants(tsd_df['people'])
    # from inlet air
    rho_air = np.vectorize(calc_rho_air)(tsd_df['T_ext'])  # kg/m3
    tsd_df['v_in_infil_window'] = (tsd_df['m_ve_inf'] + tsd_df['m_ve_window']) / rho_air
    tsd_df['v_CO2_infil_window_m3pers'] = tsd_df['v_in_infil_window'] * CO2_env_ppm
    tsd_df['v_CO2_in_infil_occupant_m3pers'] = tsd_df['v_CO2_infil_window_m3pers'] + tsd_df['v_CO2_occupant_m3pers']
    tsd_df['m_ve_in_calc'] = np.vectorize(
        calc_m_exhaust_from_CO2)(CO2_ve_min_ppm, CO2_env_ppm, tsd_df['v_CO2_in_infil_occupant_m3pers'], rho_air)
    m_ve_min = np.where(
        (tsd_df['T_ext'] <= tsd_df['T_int']) & (tsd_df['Q_gain_occ_kWh'] <= 0.0), 0, tsd_df['m_ve_in_calc'])
    w_ext = np.vectorize(calc_w_from_rh)(tsd_df['rh_ext'], tsd_df['T_ext'])
    h_ext = calc_h_from_T_w(tsd_df['T_ext'], w_ext)
    w_int = np.vectorize(calc_w_from_rh)(55, tsd_df['T_ext']) # 55 is an assumption
    h_int = calc_h_from_T_w(tsd_df['T_int'], w_int)
    Q_vet_kWh = m_ve_min * (h_ext - h_int)  # could be positive or negative


    # create output_df
    output_df = pd.DataFrame()
    output_df['Q_vet_kWh'] = Q_vet_kWh
    output_df['Q_sen_gain_kWh'] = tsd_df['Q_gain_total_kWh'] + Q_sen_gain_inf_kWh
    output_df['Q_lat_gain_kWh'] = Q_lat_gain_occupant_kWh + Q_lat_gain_infil_kWh
    output_df['Q_dhw_kWh'] = tsd_df['Qww_sys'] / 1000
    output_df['GI'] = weather_data['glohorrad_Whm2'].values
    output_df['T_ext'] = weather_data['drybulb_C'].values
    output_df['people'] = people[0]
    output_df['w_ext'] = np.vectorize(calc_w_from_rh)(weather_data['relhum_percent'], weather_data['drybulb_C'])
    # save output_df
    output_name = case.split('_')[0] + '_' + case.split('_')[4] + '_parameters.csv'
    output_path = os.path.join(output_folder, output_name)
    output_df.to_csv(output_path)
    print (output_path)



