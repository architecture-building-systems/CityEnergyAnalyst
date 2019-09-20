import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt



def main(building, TECHS, file_name, building_result_path):
    if file_name == 'outputs.csv':
        output_df = read_outputs_df(building_result_path)
        # calculations
        # balance
        calc_m_a(output_df, building_result_path)
        calc_m_w(output_df, building_result_path)
        el_total = calc_el(output_df, building_result_path)
        calc_Q_sen(output_df, building_result_path)
        # other quantities
        calc_Qh_reheat(output_df, building_result_path)
        calc_Qc_coil(output_df, building_result_path)
        Qsc_total = calc_Qsc(output_df, building_result_path)
        draw_T_SA(output_df, building_result_path)
        draw_T_offcoil(output_df, building_result_path)
        # write total.csv
        Af_m2 = output_df['Af_m2']
        write_total_csv(Qsc_total, el_total, Af_m2, building_result_path)

    return


def write_total_csv(Qsc_total, el_total, Af_m2, folder_path):
    COP_total = Qsc_total / el_total
    output_dict = {
        'Qsc_total_kW': Qsc_total,
        'el_total_kW': el_total,
        'Af_m2': Af_m2,
        'el_per_Af_W_per_m2': el_total * 1000 / Af_m2,
        'COP': COP_total
    }
    df = pd.DataFrame(output_dict)
    df.loc['sum'] = df.sum()
    file_name = os.path.join(folder_path, 'total.csv')
    df.to_csv(file_name)


def read_outputs_df(folder_path):
    # get outputs.csv
    file_name = 'outputs.csv'
    path_to_file = os.path.join(folder_path, file_name)
    # read csv
    outputs_df = pd.read_csv(path_to_file, header=None).T
    # set column
    outputs_df.columns = outputs_df.iloc[0]
    outputs_df = outputs_df[1:]
    return outputs_df

def calc_m_a(output_df, folder_path):
    m_a_in_df = output_df.filter(like='m_a_in')
    m_a_out_df = output_df.filter(like='m_a_out')
    # balance
    m_a_sum = (m_a_in_df.sum(axis=1) - m_a_out_df.sum(axis=1)).sum()
    if m_a_sum > 1E-3:
        print (m_a_sum)
    else:
        print ('air flow balanced!')
    # plot air flow
    m_a_in_OAU_vent = output_df.filter(like='m_OAU_vent').sum(axis=1)
    m_a_in_OAU_bypass = output_df['m_a_in_OAU_bypass']
    data_dict = {'coil': m_a_in_OAU_vent.values, 'bypass': m_a_in_OAU_bypass.values}
    timesteps = len(output_df.index)
    plot_stacked_bars(data_dict, timesteps, 'OAU_air_flow', 'air flow [kg/s]', folder_path)
    return m_a_in_df, m_a_out_df


def calc_m_w(output_df, folder_path):
    m_w_in_OAU_df = output_df.filter(like='m_w_in_OAU')
    m_w_out_OAU_df = output_df.filter(like='m_w_out_OAU')
    m_w_out_RAU_df = output_df.filter(like='m_w_out_RAU')

    # balance
    all_in = output_df.filter(like='m_w_in')
    all_out = output_df.filter(like='m_w_out')
    m_w_sum = (all_in.sum(axis=1) - all_out.sum(axis=1)).sum()
    if m_w_sum > 1E-3:
        print (m_w_sum)
    else:
        print ('humidity balanced!')
    # plot water flow
    m_w_total_dict = {'RAU': m_w_out_RAU_df.sum(axis=1).sum(),
                      'OAU': m_w_out_OAU_df.sum(axis=1).sum() - m_w_in_OAU_df.sum(axis=1).sum()}
    draw_pie(m_w_total_dict, "Humidity Removal", folder_path)

    return

def calc_el(output_df, folder_path):
    el_reheat_df = output_df.filter(like='el_reheat')
    el_fan_RAU_df = output_df.filter(like='el_fan_RAU')
    el_fan_OAU_df = output_df.filter(like='el_fan_OAU')
    el_SCU_df = output_df.filter(like='el_pump_SCU')
    el_ht_chiller = output_df.filter(like='el_HTchiller')
    el_chillers_df = output_df.filter(like='el_chiller')
    el_oau_chillers_df = output_df.filter(like='el_oau_chiller')
    el_rau_chillers_df = output_df.filter(like='el_rau_chiller')
    el_CT = output_df.filter(like='el_CT')


    # calculate el balance
    el_all = output_df.filter(like='el')
    el_su = output_df.filter(like='SU_el')
    el_total = el_su.sum(axis=1)
    el_sum = (el_all.sum(axis=1) - el_total - el_total).sum()
    if el_sum > 1E-3:
        print (el_sum)
    else:
        print('el balanced!')

    # plot el
    el_total_dict = {'Reheat': el_reheat_df.sum(axis=1).sum(),
                     'OAU fan': el_fan_OAU_df.sum(axis=1).sum(),
                     'RAU fan': el_fan_RAU_df.sum(axis=1).sum(),
                     'SCU pump': el_SCU_df.sum()[0],
                     'Chillers': el_chillers_df.sum(axis=1).sum() + el_oau_chillers_df.sum(
                         axis=1).sum() + el_rau_chillers_df.sum(axis=1).sum() + el_ht_chiller.sum()[0],
                     'Cooling Towers': el_CT.sum()[0]}
    print ('total electricity consumption: ', el_total.sum())
    draw_pie(el_total_dict, "Electricity Usages", folder_path)

    return el_total

def calc_Qh_reheat(output_df, folder_path):
    Qh_reheat_OAU_df = output_df.filter(like='Qh_reheat_OAU')
    Qh_reheat_RAU_df = output_df.filter(like='Qh_reheat_RAU')
    data_dict = {'OAU reheat': Qh_reheat_OAU_df.sum(axis=1), 'RAU reheat': Qh_reheat_RAU_df.sum(axis=1)}
    timesteps = len(output_df.index)
    plot_stacked_bars(data_dict, timesteps, 'Reheat', 'Qh [kW]', folder_path)
    return

def calc_Qc_coil(output_df, folder_path):
    Qc_coil_RAU = output_df.filter(like='Qc_coil_RAU').sum(axis=1)
    Qc_coil_OAU = output_df.filter(like='Qc_coil_OAU').sum(axis=1)
    Qc_coil_SCU = output_df.filter(like='Qc_sen_out_SCU').sum(axis=1)
    # Qc coil
    data_dict = {'RAU': Qc_coil_RAU, 'OAU': Qc_coil_OAU, 'SCU': Qc_coil_SCU}
    timesteps = len(output_df.index)
    plot_stacked_bars(data_dict, timesteps, 'Cooling for each unit', 'Qc [W]', folder_path)
    # pie
    pie_data_dict = {'RAU': Qc_coil_RAU.sum(), 'OAU': Qc_coil_OAU.sum(), 'SCU': Qc_coil_SCU.sum()}
    draw_pie(pie_data_dict, "Qc per unit", folder_path)
    return

def calc_Qsc(output_df, folder_path):
    Qsc_OAU = output_df.filter(like='Qsc_OAU_OUT').sum(axis=1) - output_df.filter(like='Qsc_OAU_IN').sum(axis=1)
    Qsc_RAU = output_df.filter(like='Qsc_RAU_OUT').sum(axis=1) - output_df.filter(like='Qsc_RAU_IN').sum(axis=1)
    Qsc_SCU = output_df.filter(like='Qsc_SCU').sum(axis=1)
    Qsc_total = Qsc_SCU + Qsc_RAU + Qsc_OAU
    Qsc_dict = {'RAU': Qsc_RAU, 'OAU': Qsc_OAU, 'SCU': Qsc_SCU}
    timesteps = len(output_df.index)
    plot_stacked_bars(Qsc_dict, timesteps, 'Space Cooling provided by each unit', 'Qsc [kW]', folder_path)
    # pie
    pie_data_dict = {'RAU': Qsc_RAU.sum(), 'OAU': Qsc_OAU.sum(), 'SCU': Qsc_SCU.sum()}
    draw_pie(pie_data_dict, "Qsc per unit", folder_path)
    return Qsc_total


def calc_Q_sen(output_df, folder_path):
    # balance
    Qc_sen_in = output_df.filter(like='Qc_sen_in')
    print (Qc_sen_in.columns)
    Qc_sen_out = output_df.filter(like='Qc_sen_out')
    print (Qc_sen_out.columns)
    print((Qc_sen_in.sum(axis=1) - Qc_sen_out.sum(axis=1)).sum())

    # plotting
    Qc_sen_RAU = output_df.filter(like='Qc_sen_out_RAU').sum(axis=1) - output_df.filter(like='Qc_sen_in_RAU').sum(
        axis=1)
    Qc_sen_OAU = output_df.filter(like='Qc_sen_out_OAU').sum(axis=1) - output_df.filter(like='Qc_sen_in_OAU').sum(
        axis=1)
    Qc_sen_SCU = output_df.filter(like='Qc_sen_out_SCU').sum(axis=1)
    # Qc removed
    data_dict = {'RAU': Qc_sen_RAU, 'OAU': Qc_sen_OAU, 'SCU': Qc_sen_SCU}
    timesteps = len(output_df.index)
    plot_stacked_bars(data_dict, timesteps, 'Sensible Cooling', 'Qc [kW]', folder_path)
    # Qc gain
    Qc_gain = output_df.filter(like='Qc_sen_in_gain').sum(axis=1)
    data_dict = {'Q gain': Qc_gain}
    timesteps = len(output_df.index)
    plot_stacked_bars(data_dict, timesteps, 'Sensible Heat Gain', 'Qc [kW]', folder_path)

    return

def draw_T_SA(output_df, folder_path):
    T_RAU_SA_df = output_df.filter(like='T_RAU_SA')
    T_OAU_SA_df = output_df.filter(like='T_OAU_SA')
    T_dict = {
        'RAU T_SA': [T_RAU_SA_df.sum(axis=1), '#ffa535'],
        'OAU T_SA': [T_OAU_SA_df.sum(axis=1), '#5e0c5b']
    }
    plot_temperatures(T_dict, output_df, folder_path, 'T_supply')
    return

def draw_T_offcoil(output_df, folder_path):
    T_RAU_RA1_df = output_df.filter(like='T_RAU_RA1')
    T_RAU_chw_df = output_df.filter(like='T_rau_chw')
    T_OAU_OA1_df = output_df.filter(like='T_OAU_offcoil')
    T_OAU_chw_df = output_df.filter(like='T_oau_chw')
    T_dict = {
        'RAU T_offcoil': [T_RAU_RA1_df.sum(axis=1), '#ffc071'],
        'RAU T_chw': [T_RAU_chw_df.sum(axis=1), '#664215'],
        'OAU T_offcoil': [T_OAU_OA1_df.sum(axis=1), '#b770b4'],
        'OAU T_chw': [T_OAU_chw_df.sum(axis=1), '#510a4e']
    }
    plot_temperatures(T_dict, output_df, folder_path, 'T_chw')
    return


#================================================
def plot_stacked_bars(data_dict, timesteps, filename, y_axis_label, folder_path):
    # libraries
    from matplotlib import rc
    # y-axis in bold
    rc('font', weight='bold')

    color_list = ['#7f6d5f', '#557f2d', '#2d7f5e']

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
    for key in any_dict.keys():
        if any_dict[key] > 0.0:
            label.append(key)
            size_of_groups.append(any_dict[key])
            total += any_dict[key]
    # Create a pieplot
    patches, \
    texts, \
    autotexts = ax.pie(size_of_groups, labels=label, autopct='%1.1f%%', pctdistance=0.8, textprops={'fontsize': 14}, startangle=90)
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

    print(plt_name, total)
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

if __name__ == '__main__':
    buildings = ["B001"]
    # buildings = ["B001", "B002", "B003", "B004", "B005", "B006", "B007", "B008", "B009", "B010"]
    tech = ["HCS_coil"]
    cases = ["WTP_CBD_m_WP1_HOT"]
    result_path = "E:\\test_0805"
    for case in cases:
        folder_path = os.path.join(result_path, case)
        for building in buildings:
            building_time = building + "_1_24"
            building_result_path = 'E:\\HCS_results_0919\\WTP_CBD_m_WP1_HOT\\B001_1_24\\3for2_base'
            # building_result_path = os.path.join(building_result_path, "SU")
            print building_result_path
            file_name = 'outputs.csv'
            main(building, tech, file_name, building_result_path)