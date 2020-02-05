import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.patches
from cea.osmose.auxiliary_functions import calc_h_from_T_w
from cea.osmose.exergy_functions import calc_Ex_Qc

DETAILED_PLOTS = True


def main(run_folder_path):
    print(run_folder_path)
    ## Read files
    files_in_path = os.listdir(run_folder_path)
    balance_file = [file for file in files_in_path if 'balance' in file][0]
    balance_df = read_file_as_df(balance_file, run_folder_path)
    output_file = [file for file in files_in_path if 'output' in file][0]
    output_df = read_file_as_df(output_file, run_folder_path)
    stream_file = [file for file in files_in_path if 'stream' in file][0]
    streams_df = read_file_as_df(stream_file, run_folder_path)


    ## Check balance
    # air
    m_a_in_df, m_a_out_df = calc_layer_balance(balance_df, 'Bui_air_bal')
    plot_values_all_timesteps('Bui_air_bal_in', m_a_in_df, 'Air flow [kg/s/m2]', output_df, run_folder_path)
    m_a_in_min = output_df['m_ve_min'].combine(output_df['m_a_in_inf'],max)
    air_in_ratio = m_a_in_df.sum(axis=1)/m_a_in_min
    # water
    m_w_in_df, m_w_out_df = calc_layer_balance(balance_df, 'Bui_water_bal')
    # sensible heat
    Q_sen_in_df, Q_sen_out_df = calc_layer_balance(balance_df, 'Bui_energy_bal')
    # electricity
    el_in_df, el_out_df = calc_layer_balance(balance_df, 'Electricity')
    el_usages = el_out_df.sum(axis=1)
    el_aux_dict, el_LD_HP = calc_el_aux(balance_df)
    # plot_values_all_timesteps('Electricity_out', el_out_df, 'Electricity Usages [kWh/m2]', output_df, folder_path)
    plot_values_all_timesteps('Electricity_in', el_in_df, 'Electricity Supply [kWh/m2]', output_df, run_folder_path)

    ## Calculation
    # exergy
    exergy_req, exergy_reheat_req = calc_exergy(balance_df, output_df, run_folder_path)
    exergy_LD_OAU = calc_exergy_LD_OAU(output_df) if 'LD' in run_folder_path else 0.0
    exergy_recovered_df = calc_exergy_recovered_OAU_EX(streams_df, output_df)
    # Q
    Qsc_dict = calc_Qsc_room(output_df, Q_sen_in_df, Q_sen_out_df, run_folder_path)
    Qsc_total_theoretical, SHR_theoretical = calc_Qsc_theoretical(output_df)
    Q_chiller_total, Q_r_chiller_total, Q_coil_dict,\
    Q_reheat_dict, Q_exhaust = calc_Q_heat_cascade(run_folder_path, output_df, streams_df)
    # cooling efficiency
    OAU_cooling_eff = (Qsc_dict['OAU_Qsc']/Q_coil_dict['OAU_Qc_coil']).fillna(0)
    plot_stacked_bars({'cooling eff': OAU_cooling_eff}, len(output_df.index), 'OAU cooling eff', 'Qsc/Qc_coil [kW]', run_folder_path)
    # COP
    cop_total = Qsc_dict['Qsc_total'] / el_usages
    data_dict = {'COP': cop_total}
    plot_stacked_bars(data_dict, len(output_df.index), 'COP', 'COP [kW]', run_folder_path)
    # Temperatures
    if 'base' not in run_folder_path:
        calc_chiller_T(output_df, run_folder_path) # not relevant in base
    T_SA_dict = draw_T_SA(output_df, run_folder_path)
    T_offcoil_dict = draw_T_offcoil(output_df, run_folder_path)

    ## Write total.csv
    total_dict = {'COP': cop_total,
                  'air in ratio': air_in_ratio,
                  'OAU cooling eff': OAU_cooling_eff,
                  'exergy_kWh': exergy_req,
                  'exergy_LD_kWh': exergy_LD_OAU,
                  'exergy_reheat_kWh': exergy_reheat_req,
                  'exergy_recovered_kWh': exergy_recovered_df['total'],
                  'electricity_kWh': el_usages,
                  'electricity_aux_scu_kWh': el_aux_dict['el_aux_scu_kWh'],
                  'electricity_aux_rau_kWh': el_aux_dict['el_aux_rau_kWh'],
                  'electricity_aux_oau_kWh': el_aux_dict['el_aux_oau_kWh'],
                  'electricity_aux_kWh': el_aux_dict['el_aux_kWh'],
                  'electricity_LD_HP_kWh': el_LD_HP,
                  'Q_chiller_kWh': Q_chiller_total,
                  'Q_r_chiller_kWh': Q_r_chiller_total,
                  'Q_exhaust_kWh': Q_exhaust,
                  'Qsc_theoretical': Qsc_total_theoretical,
                  'SHR_theoretical': SHR_theoretical,
                  'Af_m2': output_df['Af_m2']}
    for key in ['SU_Qh', 'SU_Qh_reheat', 'SU_qt_hot']:
        if output_df[key].sum() != 0.0 :
            total_dict[key] = output_df[key]
            # warnings
            plot_stacked_bars({key: output_df[key]}, len(output_df.index), key, 'Qh [kW]', run_folder_path)
            print('SU in use: ', key)
            if output_df[key].sum() > 10:
                print('value: ', output_df[key].sum())

    # add all dicts to total_dict
    for dict in [Qsc_dict, Q_reheat_dict, Q_coil_dict, T_SA_dict, T_offcoil_dict]:
        total_dict.update(dict)

    # save to csv
    total_df = pd.DataFrame(total_dict)
    total_df.loc['sum'] = total_df.sum()
    total_df.to_csv(os.path.join(run_folder_path, 'total.csv'))

    return

def calc_exergy_LD_OAU(output_df):
    T_ref = output_df['T_OA'].values
    Qc_ER = output_df['Q_LD_HP'].values - output_df['Q_LD_de'].values
    T_SA = output_df['T_OAU_SA'].values
    T_OA1 = np.where(output_df['T_OAU_OA1'] >= output_df['T_OA'], output_df['T_OA'] - 0.1, output_df['T_OAU_OA1'])
    Ex_ER = np.vectorize(calc_Ex_Qc)(Qc_ER, T_SA, T_ref)
    Qc_de = output_df['Q_LD_de'].values

    Ex_de = np.vectorize(calc_Ex_Qc)(Qc_de, T_SA, T_ref)
    Ex_LD = Ex_ER + Ex_de
    return Ex_LD


def calc_el_aux(balance_df):
    el_aux_kWh_dict = {}
    el_df = balance_df.filter(like='Electricity_in')
    el_aux_columns = [i for i in el_df.columns if 'chiller' not in i]
    el_aux_df = el_df[el_aux_columns]
    el_aux_kWh_dict['el_aux_kWh'] = el_aux_df.sum(axis=1)
    el_aux_scu_columns = [i for i in el_aux_columns if 'scu' in i]
    el_aux_scu_df =  el_df[el_aux_scu_columns]
    el_aux_kWh_dict['el_aux_scu_kWh'] = el_aux_scu_df.sum(axis=1)
    el_aux_rau_columns = [i for i in el_aux_columns if 'rau' in i]
    el_aux_rau_df =  el_df[el_aux_rau_columns]
    el_aux_kWh_dict['el_aux_rau_kWh'] = el_aux_rau_df.sum(axis=1)
    el_aux_oau_columns = [i for i in el_aux_columns if 'OAU' in i]
    el_aux_oau_df =  el_df[el_aux_oau_columns]
    el_aux_kWh_dict['el_aux_oau_kWh'] = el_aux_oau_df.sum(axis=1)
    # check balance
    diff = (el_aux_kWh_dict['el_aux_scu_kWh'] + el_aux_kWh_dict['el_aux_rau_kWh']
            + el_aux_kWh_dict['el_aux_oau_kWh']) - el_aux_kWh_dict['el_aux_kWh']
    if diff.sum() > 1E-3 :
        ValueError('el_aux not balanced')

    if 'Electricity_in_HP_LD_LD_HP_el' in el_df.columns:
        el_LD_HP_kWh = el_df['Electricity_in_HP_LD_LD_HP_el']
    else:
        el_LD_HP_kWh = el_aux_kWh_dict['el_aux_kWh'].copy()*0
    return el_aux_kWh_dict, el_LD_HP_kWh


def calc_exergy_recovered_OAU_EX(stream_df, output_df):
    T_OA_K = output_df['T_OA'] + 273.15
    recover_streams_df = stream_df.filter(like='OAU_EX')
    for column in recover_streams_df.filter(like='T'):
        T_stream_K = recover_streams_df[column] + 273.15
        recover_streams_df[column+'_carnot'] = 1 - T_OA_K/T_stream_K

    exergy_recovered = pd.DataFrame()
    for column in recover_streams_df.filter(like='Hout'):
        Q_recovered = recover_streams_df[column]
        Tin_carnot = recover_streams_df[column.split('Hout')[0] + 'Tin_carnot']
        Tout_carnot = recover_streams_df[column.split('Hout')[0] + 'Tout_carnot']
        exergy_recovered[column.split('_Hout')[0]] = (abs(Tin_carnot) + abs(Tout_carnot))*Q_recovered/2

    exergy_recovered['total'] = exergy_recovered.sum(axis=1)
    return exergy_recovered


def calc_Q_heat_cascade(folder_path, output_df, streams_df):
    """
    streams_df balance
    Q_coil_OAU + Q_coil_RAU + Q_coil_SCU = Q_chiller + Q_reheat + Q_exhaust
    :param folder_path:
    :param output_df:
    :param streams_df:
    :return:
    """
    # qt_hot
    Q_coil_dict = calc_Q_coil(output_df, folder_path)
    Q_r_chillers = output_df.filter(like='Q_r_chiller_').sum(axis=1)
    qt_hot_total = Q_coil_dict['Qc_coil_total'] + Q_r_chillers
    # qt_cold
    Q_exhaust = output_df.filter(like='qt_cold_OAU_EX_').sum(axis=1)
    Q_reheat_dict, Q_reheat_total = calc_Q_reheat(output_df, folder_path)
    Qc_chillers = streams_df.filter(like='chiller').filter(like='qt_cold_Hout').sum(axis=1)  # TODO: REMOVE
    Q_chillers = output_df.filter(like='Q_chiller_').sum(axis=1)
    qt_cold_total = Q_exhaust + Q_reheat_total + Qc_chillers
    # check balance again
    dQ = (qt_hot_total - qt_cold_total).round(3)
    if max(dQ) > 1.5: # below that might be rounding errors in postCompute
        print('Qc_coil and Q_chiller not balanced', dQ)
    return Qc_chillers, Q_r_chillers, Q_coil_dict, Q_reheat_dict, Q_exhaust


def read_file_as_df(file_name, folder_path):
    # get outputs.csv
    path_to_file = os.path.join(folder_path, file_name)
    # print(path_to_file)
    # read csv
    file_df = pd.read_csv(path_to_file, header=None).T
    # set column
    file_df.columns = file_df.iloc[0]
    file_df = file_df[1:]
    # to numeric
    file_df = file_df.apply(pd.to_numeric, errors='coerce')
    return file_df

def calc_layer_balance(balance_df, layer):
    layer_in_df = balance_df.filter(like= layer + '_in')
    # print (layer_in_df.columns)
    layer_out_df = balance_df.filter(like= layer + '_out')
    # print (layer_out_df.columns)
    layer_diff = (layer_in_df.sum(axis=1) - layer_out_df.sum(axis=1)).sum()
    if abs(layer_diff) > 1E-3:
        print (layer, ' might not be balanced: ', layer_diff)

    return layer_in_df, layer_out_df


def calc_exergy(balance_df, output_df, folder_path):
    # total exergy
    el_chillers_df = balance_df.filter(like='Electricity_in_chillers').sum(axis=1)
    if el_chillers_df.sum() > 0.0:
        ex_chillers = el_chillers_df * output_df['g_value_chillers'].values[0]
        # ex_chillers = el_chillers_df * 0.45
        el_r_chillers_df = balance_df.filter(like='Electricity_out_r_chillers').sum(axis=1)
        if 'g_value_rchillers' in output_df.columns:
            ex_r_chillers = el_r_chillers_df * output_df['g_value_rchillers'].values[0]
        else:
            ex_r_chillers = 0.0
        Ex = ex_chillers - ex_r_chillers
        data_dict = {'Ex': Ex}
        timesteps = len(output_df.index)
        plot_stacked_bars(data_dict, timesteps, 'exergy', 'exergy [kW]', folder_path)

        # reheating electricity
        Qh_reheat = output_df.filter(like='Qh_reheat_OAU').sum(axis=1) + output_df.filter(like='Qh_reheat_RAU').sum(axis=1)
        T_reheat = 50 + 273.15 # FIXME: approximation
        T_OA = output_df['T_OA'] + 273.15
        carnot_reheat = 1 - T_OA/T_reheat
        ex_Qh_reheat = Qh_reheat * carnot_reheat
        Ex_reheat = Ex + ex_Qh_reheat
    else:
        Ex = el_chillers_df
        Ex_reheat = el_chillers_df

    # if 'LD' in folder_path:
    #     Ex = Ex + output_df['el_out_LD_HP']*0.59

    return Ex, Ex_reheat


def calc_m_w(balance_df, folder_path):
    all_in = balance_df.filter(like='Bui_water_bal_out')
    all_out = balance_df.filter(like='Bui_water_bal_in')
    m_w_sum = (all_in.sum(axis=1) - all_out.sum(axis=1)).sum()
    if m_w_sum > 1E-3:
        print ('humidity not balanced ', m_w_sum)
    else:
        print ('\n humidity balanced! \n')


    m_w_in_OAU_df = balance_df.filter(like='m_w_in_OAU')
    m_w_out_OAU_df = balance_df.filter(like='m_w_out_OAU')
    m_w_out_RAU_df = balance_df.filter(like='m_w_out_RAU')

    # balance
    all_in = balance_df.filter(like='m_w_in')
    all_out = balance_df.filter(like='m_w_out')
    m_w_sum = (all_in.sum(axis=1) - all_out.sum(axis=1)).sum()
    if m_w_sum > 1E-3:
        print ('humidity balance not right: ', m_w_sum)
    else:
        print ('humidity balanced!')
    # plot water flow
    m_w_total_dict = {'RAU': m_w_out_RAU_df.sum(axis=1).sum(),
                      'OAU': m_w_out_OAU_df.sum(axis=1).sum() - m_w_in_OAU_df.sum(axis=1).sum()}
    draw_pie(m_w_total_dict, "Humidity Removal", folder_path)
    m_w_total_df = pd.DataFrame.from_dict(m_w_total_dict, orient='index').T
    draw_percent_stacked_bar(m_w_total_df, folder_path, title='Humidity Removal')

    return

def calc_Q_reheat(output_df, folder_path):
    Qh_reheat_OAU_df = output_df.filter(like='Qh_reheat_OAU')
    Qh_reheat_RAU_df = output_df.filter(like='Qh_reheat_RAU')
    Qh_reheat_total = Qh_reheat_OAU_df.sum(axis=1) + Qh_reheat_RAU_df.sum(axis=1)
    data_dict = {'OAU_Qh_reheat': Qh_reheat_OAU_df.sum(axis=1), 'RAU_Qh_reheat': Qh_reheat_RAU_df.sum(axis=1)}
    if Qh_reheat_OAU_df.sum(axis=1).sum() + Qh_reheat_RAU_df.sum(axis=1).sum() > 0.0:
        timesteps = len(output_df.index)
        plot_stacked_bars(data_dict, timesteps, 'Reheat', 'Qh [kW]', folder_path)
    return data_dict, Qh_reheat_total

def calc_Q_coil(output_df, folder_path):
    Qc_coil_RAU = output_df.filter(like='Qc_coil_RAU').sum(axis=1)
    Qc_coil_OAU = output_df.filter(like='Qc_coil_OAU').sum(axis=1)
    Qc_coil_SCU = output_df.filter(like='Qc_sen_out_SCU').sum(axis=1)
    Qc_coil_total = Qc_coil_RAU + Qc_coil_OAU + Qc_coil_SCU
    if DETAILED_PLOTS:
        # plot stacked bars
        data_dict = {'RAU_Qc_coil': Qc_coil_RAU, 'OAU_Qc_coil': Qc_coil_OAU, 'SCU_Qc_coil': Qc_coil_SCU,
                     'Qc_coil_total': Qc_coil_total}
        plot_stacked_bars(data_dict, len(output_df.index), 'Cooling coils', 'Qc [W]', folder_path)
        # plot pie
        pie_data_dict = {'RAU': Qc_coil_RAU.sum(), 'OAU': Qc_coil_OAU.sum(), 'SCU': Qc_coil_SCU.sum()}
        draw_pie(pie_data_dict, "Qc per unit", folder_path)
    return data_dict

def calc_chiller_T(output_df, folder_path):
    Q_chiller_total_df = pd.DataFrame()

    if output_df.filter(like='T_oau_chw').columns.size > 0:
        Q_oau_chiller = output_df.filter(like='Q_oau_chiller')
        Q_chiller_total_df = pd.concat([Q_chiller_total_df, Q_oau_chiller], axis=1, sort=False)
        draw_T_chw_pie(Q_oau_chiller,'OAU chiller usages', folder_path)
    if output_df.filter(like='T_rau_chw').columns.size > 0:
        Q_rau_chiller = output_df.filter(like='Q_rau_chiller')
        Q_chiller_total_df = pd.concat([Q_chiller_total_df, Q_rau_chiller], axis=1, sort=False)
        draw_T_chw_pie(Q_rau_chiller, 'RAU chiller usages', folder_path)
    if output_df.filter(like='T_chw').columns.size > 0:
        Q_chiller = output_df.filter(like='Q_chiller')
        Q_chiller_total_df = pd.concat([Q_chiller_total_df, Q_chiller], axis=1, sort=False)
        draw_T_chw_pie(Q_chiller, 'LT chiller usages', folder_path)

    file_name = os.path.join(folder_path, 'Q_chiller.csv')
    Q_chiller_total_df.to_csv(file_name)
    return


def draw_T_chw_pie(Q_df, name, folder_path):
    pie_data_dict = {}
    for chiller in Q_df.columns:
        if ('RAU' in name) or ('OAU' in name):
            label = chiller.split('_')[3]  # find temperature
        else:
            label = chiller.split('_')[2]  # find temperature
        T_values = [8.1, 8.75, 9.4, 10.05, 10.7, 11.35, 12.0, 12.65, 13.3, 13.95]
        T = T_values[int(label) - 1]
        pie_data_dict[T] = Q_df[chiller].sum()
    # draw_pie(pie_data_dict, name, folder_path)
    df = pd.DataFrame.from_dict(pie_data_dict, orient='index').sort_index().T
    draw_percent_stacked_bar(df, folder_path, title=name)


def calc_Qsc_room(output_df, Q_sen_in_df, Q_sen_out_df, folder_path):
    # Qsc
    m_a_inf = output_df['m_a_in_inf'].astype('float').round(4)
    m_a_out = output_df.filter(like='m_a_out').sum(axis=1).round(4)
    ratio_exclude_inf = (1.0 - m_a_inf/m_a_out).round(3)

    Qsc_OAU_OUT = output_df.filter(like='Qsc_OAU_OUT').sum(axis=1)
    Qsc_OAU_IN = output_df.filter(like='Qsc_OAU_IN').sum(axis=1)
    Qsc_OAU = Qsc_OAU_OUT - Qsc_OAU_IN
    Qsc_OAU_exclude_inf = Qsc_OAU_OUT * ratio_exclude_inf - Qsc_OAU_IN
    Qsc_RAU = output_df.filter(like='Qsc_RAU_OUT').sum(axis=1) - output_df.filter(like='Qsc_RAU_IN').sum(axis=1)
    Qsc_SCU = output_df.filter(like='Qsc_SCU').sum(axis=1)

    # plot
    if DETAILED_PLOTS:
        Qsc_total_dict = {'RAU': Qsc_RAU, 'OAU': Qsc_OAU, 'SCU': Qsc_SCU}
        timesteps = len(output_df.index)
        plot_stacked_bars(Qsc_total_dict, timesteps, 'Space Cooling provided by each unit', 'Qsc [kW]', folder_path)
        # pie
        pie_data_dict = {'RAU': Qsc_RAU.sum(), 'OAU': Qsc_OAU.sum(), 'SCU': Qsc_SCU.sum()}
        draw_pie(pie_data_dict, "Qsc per unit", folder_path)
        pie_data_df = pd.DataFrame.from_dict(pie_data_dict, orient='index').T
        draw_percent_stacked_bar(pie_data_df, folder_path, title='Qsc per unit')

    Qsc_dict = {}
    OAU_Qsc_sen_out = Q_sen_out_df.filter(like='hcs').sum(axis=1) * ratio_exclude_inf
    OAU_Qsc_sen_in = Q_sen_in_df.filter(like='hcs').sum(axis=1)
    Qsc_dict['OAU_Qsc_sen'] = OAU_Qsc_sen_out.round(4) - OAU_Qsc_sen_in.round(4)
    Qsc_dict['OAU_Qsc_lat'] = Qsc_OAU_exclude_inf - Qsc_dict['OAU_Qsc_sen']
    Qsc_dict['RAU_Qsc_sen']= Q_sen_out_df.filter(like='rau').sum(axis=1) - Q_sen_in_df.filter(like='rau').sum(axis=1)
    Qsc_dict['RAU_Qsc_lat'] = Qsc_RAU - Qsc_dict['RAU_Qsc_sen']
    Qsc_dict['SCU_Qsc_sen'] = Q_sen_out_df.filter(like='scu').sum(axis=1)
    Qsc_dict['OAU_Qsc'] = Qsc_OAU
    Qsc_dict['RAU_Qsc'] = Qsc_RAU
    Qsc_dict['SCU_Qsc'] = Qsc_SCU
    Qsc_dict['Qsc_total'] = Qsc_SCU + Qsc_RAU + Qsc_OAU
    Qsc_dict['SHR'] = (Qsc_dict['OAU_Qsc_sen'] + Qsc_dict['RAU_Qsc_sen'] + Qsc_dict['SCU_Qsc_sen']) / Qsc_dict['Qsc_total']

    return Qsc_dict


def calc_Qsc_theoretical(output_df):
    # TODO: calculate the whole part in extract_demand_outputs.py
    # sensible gains
    Q_sen_gains = output_df['Qc_sen_in_gain']   # solar, occupants, appliances, lighting, infiltration

    # latent gains
    h_fg = 2501  # kJ/kg
    Q_lat_gains = output_df['m_w_in_gain'] * h_fg  # occupants, infiltration

    # from the required fresh air
    Q_lat_gain_ve_min = output_df['m_ve_min'] * (output_df['w_OA'] - output_df['w_RA'])/1000 * h_fg
    h_OA = np.vectorize(calc_h_from_T_w)(output_df['T_OA'], output_df['w_OA'])
    h_RA = np.vectorize(calc_h_from_T_w)(output_df['T_RA'], output_df['w_RA'])
    Q_sen_gain_ve_min = output_df['m_ve_min'] * (h_OA - h_RA) - Q_lat_gain_ve_min

    # total
    Qsc_total_theoretical = Q_sen_gain_ve_min + Q_lat_gain_ve_min + Q_sen_gains + Q_lat_gains
    SHR_theoretical = (Q_sen_gain_ve_min + Q_sen_gains) / Qsc_total_theoretical

    return Qsc_total_theoretical, SHR_theoretical

def draw_T_SA(output_df, folder_path):
    T_RAU_SA_df = output_df.filter(like='T_RAU_SA')
    T_OAU_SA_df = output_df.filter(like='T_OAU_SA')
    T_dict = {
        'RAU T_SA': [T_RAU_SA_df.sum(axis=1), '#ffa535'],
        'OAU T_SA': [T_OAU_SA_df.sum(axis=1), '#5e0c5b']
    }
    plot_temperatures(T_dict, output_df, folder_path, 'T_supply')
    T_dict_output = {}
    for key in T_dict.keys():
        T_dict_output[key] = T_dict[key][0]
    return T_dict_output

def draw_T_offcoil(output_df, folder_path):
    T_RAU_RA1_df = output_df.filter(like='T_RAU_RA1')
    T_RAU_chw_df = output_df.filter(like='T_rau_chw')
    T_OAU_OA1_df = output_df.filter(like='T_OAU_offcoil')
    T_OAU_chw_df = output_df.filter(like='T_oau_chw')
    T_dict = {
        'RAU T_offcoil': [T_RAU_RA1_df.sum(axis=1), '#ffc071'],
        # 'RAU T_chw': [T_RAU_chw_df.sum(axis=1), '#664215'],
        'OAU T_offcoil': [T_OAU_OA1_df.sum(axis=1), '#b770b4'],
        # 'OAU T_chw': [T_OAU_chw_df.sum(axis=1), '#510a4e']
    }
    plot_temperatures(T_dict, output_df, folder_path, 'T_chw')
    T_dict_output = {}
    for key in T_dict.keys():
        T_dict_output[key] = T_dict[key][0]
    return T_dict_output

def plot_values_all_timesteps(layer, m_a_in_df, y_axis_name, output_df, folder_path):
    # plot air flow per m2
    Af_m2 = output_df['Af_m2']
    timesteps = len(output_df.index)
    data_dict = {}
    for column in m_a_in_df.columns:
        stream_long_name = column.split(layer+'_')[1]
        model_name = stream_long_name.split('_')[0]
        column_values = m_a_in_df[column].values
        if model_name not in data_dict.keys():
            data_dict[model_name] = column_values
        else:
            repeat = True
            i = 1
            while repeat:
                model_name = model_name + '_' + stream_long_name.split('_')[i]
                if model_name not in data_dict.keys():
                    data_dict[model_name] = column_values
                    repeat = False
                else:
                    i += 1
    data_df = pd.DataFrame(data_dict).sum(axis=1) * Af_m2
    diff = (m_a_in_df.sum(axis=1) - data_df).sum()
    if diff > 1E-3:
        print('check ', layer, 'entries')
    else:
        plot_stacked_bars(data_dict, timesteps, layer, y_axis_name, folder_path)
    return data_df

#================================================
def plot_stacked_bars(data_dict, timesteps, filename, y_axis_label, folder_path):
    # libraries
    from matplotlib import rc
    # y-axis in bold
    rc('font', weight='bold')

    # color_list = ['#7f6d5f', '#557f2d', '#2d7f5e']
    color_list = plt.cm.Set2(np.linspace(0, 1, len(data_dict.keys())))

    barWidth = 1
    bottom = []
    x_ticks = np.arange(timesteps)
    stack_number = 0
    bottom = np.zeros(timesteps)
    fig, ax1 = plt.subplots(figsize=(12, 6))
    for key in data_dict.keys():
        bar = data_dict[key]
        ax1.bar(x_ticks, bar, bottom=bottom, edgecolor='white', width=barWidth, label=key,
                color=color_list[stack_number])
        stack_number += 1
        bottom = np.add(bottom, bar).tolist()

    # modify plot
    plt.xlim(1, timesteps)
    step = 8 if timesteps > 24 else 3
    plt.xticks(np.arange(0, timesteps + 1, step=step))
    plt.xlabel("Time[hr]", fontsize=14)
    plt.ylabel(y_axis_label, fontsize=14)
    plt.title(filename, fontsize=16)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize='large')
    plt.tight_layout(w_pad=1, h_pad=1.0)
    # save file
    image_path = os.path.join(folder_path, filename + '.png')
    plt.savefig(image_path)
    plt.close(fig)
    return

def draw_pie(any_dict, plt_name, folder_path):
    total = 0
    # create data
    size_of_groups = []
    label = []
    fig, ax = plt.subplots()

    # rank values and sort
    df_rank = pd.DataFrame.from_dict(any_dict, orient='index')
    df_rank = df_rank.sort_values(by=[0])
    ranked_index = df_rank.index
    # create a list with alternating values
    index_list = []
    for i in range(len(ranked_index)):
        if i == 0:
            n = i
        elif i % 2 != 0:
            n = (n + 1)*(-1)
        else:
            n = n*(-1)
        index_list.append(ranked_index[n])
    # write area to pie
    for key in index_list:
        if any_dict[key] > 0.0:
            label.append(key)
            size_of_groups.append(any_dict[key])
            total += any_dict[key]

    # Create a pieplot
    patches, \
    texts, \
    autotexts = ax.pie(size_of_groups, labels=label, autopct='%1.1f%%', pctdistance=0.85, textprops={'fontsize': 14})

    for i in range(len(texts)):
        texts[i].set_fontsize(14) # set label font size

    # plt.show()

    # add a circle at the center
    my_circle = plt.Circle((0, 0), 0.6, color='white')
    p = plt.gcf()
    p.gca().add_artist(my_circle)

    # Set chart title.
    plt.title(plt_name, fontsize=16)

    # other settings
    plt.axis('equal') # Equal aspect ratio ensures that pie is drawn as a circle
    plt.tight_layout()

    image_path = os.path.join(folder_path, plt_name + '.png')
    plt.savefig(image_path)
    plt.close(fig)

    # print(plt_name, total)
    return

def plot_temperatures(T_dict, output_df, folder_path, title):
    # plot temperatures
    x = output_df.index
    fig, ax = plt.subplots(figsize=(12, 5))
    for key in T_dict.keys():
        ax.plot(x, T_dict[key][0], label=key, color=T_dict[key][1])
    # set x-axis limit
    plt.xlim(1, len(x))
    step = 8 if len(x) > 24 else 3
    plt.xticks(np.arange(0, len(x) + 1, step=step))
    plt.ylim(0, 30)
    # Set chart title.
    plt.title(title, fontsize=16)
    # Set x axis label.
    plt.xlabel("Time [hr]", fontsize=14)
    # Set y axis label.
    plt.ylabel("Temperature [C]", fontsize=14)
    # show legend
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize='large')
    plt.tight_layout(w_pad=1, h_pad=1.0)

    image_path = os.path.join(folder_path, title + '.png')
    fig.savefig(image_path)
    plt.close(fig)
    return


def draw_percent_stacked_bar(df, folder_path, title='stacked bar'):
    """
    df is a DataFrame with columns are the features, and the index is the building number
    :param df:
    :param folder_path:
    :param title:
    :return:
    """
    # Set figure size
    fig, ax = plt.subplots(figsize=(5, 10))
    # get raw data properties
    x_numbers = np.arange(0, len(df.index.values), 1)
    stack_names = df.columns
    # From raw value to percentage
    totals = df.sum(axis=1).values
    percent_stacks = {}
    for stack in stack_names:
        percent_stacks[stack] = [i * 100 / j for i, j in zip(df[stack].values, totals)]
    # plot
    barWidth = 0.85
    x_names = df.index.values
    color_dict = {'OAU': '#f3c030', 'RAU': '#7bbbb5', 'SCU': '#544661',
                  '8.1': '#011f4b', '8.75': '#1a355d', '9.4': '#334b6e',
                  '10.05': '#4d6281', '10.7': '#667893', '11.35': '#808fa5',
                  '12.0': '#99a5b7', '12.65': '#b2bbc9', '13.3': '#ccd2db', '13.95': '#e5e8ed'}
    bottom = [0]*len(x_numbers)
    for key in stack_names:
        ax.bar(x_numbers, percent_stacks[key], color = color_dict[str(key)], width=barWidth, bottom=bottom, label=str(key))
        bottom = [sum(i) for i in zip(bottom, percent_stacks[key])]

    # Custom x axis
    ax.tick_params(axis='both', which='major', labelsize=18)
    plt.xticks(x_numbers, x_names)
    plt.ylim(0, 100)
    plt.ylabel("[%]", fontsize=18)
    plt.title(title, fontsize=18)
    # plt.xlabel("group")
    plt.legend(bbox_to_anchor=(1.01, 0.5), loc='center left', fontsize=18)
    # Show graphic
    plt.tight_layout()
    # plt.show()
    image_path = os.path.join(folder_path, title + '.png')
    fig.savefig(image_path)
    plt.close(fig)
    return

if __name__ == '__main__':
    ## Simple folder path input

    # folder_path = "E:\\ipese_new\\osmose_mk\\results\\HCS_base_coil\\run_011"
    # main(folder_path)

    ## Loop through different technologies

    # result_path_folder = "E:\\HCS_results_1022\\HCS_base_m_out_dP"
    result_path_folder = 'C:\\Users\\Shanshan\\Documents\\WP1_results\\WP1_results_1130'
    # result_path_folder = 'E:\\results_1130\\'
    # TECHS = ['HCS_base', 'HCS_base_coil', 'HCS_base_3for2', 'HCS_base_ER0', 'HCS_base_IEHX', 'HCS_base_LD']
    TECHS = ['HCS_base_LD']

    for tech in TECHS:
        tech_folder_path = os.path.join(result_path_folder, tech)
        folders_list = os.listdir(tech_folder_path)
        for folder in folders_list:
        # for folder in ['run_007_OFF_B005_1_24']:
            if 'run' in folder:
                folder_path = os.path.join(tech_folder_path, folder)
                file_list = os.listdir(folder_path)
                # if 'total.csv' not in file_list:
                main(folder_path)
