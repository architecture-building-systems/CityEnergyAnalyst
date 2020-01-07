import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from cea.osmose.compare_resutls_district import get_all_points_from_dict, path_to_all_district_plot
from cea.osmose.compare_el_usages import plot_chiller_T_Qc_scatter

COLOR_CODES = {'3for2': '#C96A50', 'coil': '#3E9AA3', 'ER0': '#E2B43F', 'IEHX': '#51443D', 'LD': '#6245A3',
               'status': '#707070',
               'HCS_base_3for2': '#C96A50', 'HCS_base_coil': '#3E9AA3', 'HCS_base_ER0': '#E2B43F',
               'HCS_base_IEHX': '#51443D', 'HCS_base_LD': '#6245A3', 'HCS_base': '#707070'}
CASE_TABLE = {'HOT': 'Hotel', 'OFF': 'Office', 'RET': 'Retail'}
T_LIST = [8.1, 8.75, 9.4, 10.05, 10.7, 11.35, 12., 12.65, 13.3, 13.95]
# T_LIST = [13.95]


def main():
    main_folder = 'E:\\OSMOSE_projects\\HCS_mk\\results'
    # main_folder = 'E:\\HCS_results_1015\\base'
    # techs = ['HCS_base', 'HCS_base_coil', 'HCS_base_3for2', 'HCS_base_ER0', 'HCS_base_IEHX', 'HCS_base_LD']
    techs = ['HCS_base_LD']
    totals_dict = read_total_csv(main_folder, techs)

    for case_name in totals_dict.keys():
        all_cop_dict, all_el_dict, all_ex_dict, all_cooling_eff = {}, {}, {}, {}
        for building_name in totals_dict[case_name].keys():
            all_cop_dict[building_name], all_el_dict[building_name], \
            all_ex_dict[building_name], all_cooling_eff[building_name] = {}, {}, {}, {}
            OAU_T_Qc_dict, RAU_T_Qc_dict = {}, {}
            for tech in totals_dict[case_name][building_name].keys():
                total_file = totals_dict[case_name][building_name][tech]
                multiplication_factor = 8760/(total_file.shape[0]-1)
                # exergy
                exergy_LD_kWh = total_file['exergy_LD_kWh'].iloc[-1] if 'exergy_LD_kWh' in total_file.columns else 0.0
                exergy_total_kWh = total_file['exergy_kWh'].iloc[-1] + exergy_LD_kWh
                Af_m2 = total_file['Af_m2'].iloc[1]
                all_ex_dict[building_name][tech] = exergy_total_kWh*multiplication_factor/Af_m2
                # COP
                el_total = total_file['electricity_kWh'].iloc[-1]
                Qsc_total = total_file['Qsc_total'].iloc[-1]
                COP = Qsc_total / el_total
                all_cop_dict[building_name][tech] = COP
                # el
                el_total = total_file['electricity_kWh'].iloc[-1]
                all_el_dict[building_name][tech] = el_total*multiplication_factor/Af_m2
                # Qsc/Qc
                Qsc_total_kWh = total_file['Qsc_total'].iloc[-1]
                Qc_coil_total_kWh = total_file['Qc_coil_total'].iloc[-1]
                cooling_efficiency = Qsc_total_kWh / Qc_coil_total_kWh
                all_cooling_eff[building_name][tech] = cooling_efficiency
                # T_Qc
                OAU_T_Qc_dict[tech], RAU_T_Qc_dict[tech] = {}, {}
                for T in T_LIST:
                    OAU_Qc_coil = total_file[total_file['OAU T_offcoil'] == T]['OAU_Qc_coil'].sum()
                    OAU_T_Qc_dict[tech][T] = OAU_Qc_coil
                    RAU_Qc_coil = total_file[total_file['RAU T_offcoil'] == T]['RAU_Qc_coil'].sum()
                    RAU_T_Qc_dict[tech][T] = RAU_Qc_coil
            ## BUILDING
            # plot T_offcoil
            tech_rank = ['HCS_base', 'HCS_base_coil', 'HCS_base_3for2', 'HCS_base_ER0', 'HCS_base_IEHX', 'HCS_base_LD']
            plot_chiller_T_Qc_scatter(OAU_T_Qc_dict, tech_rank, building_name, main_folder, case_name + '_OAU')
            plot_chiller_T_Qc_scatter(RAU_T_Qc_dict, tech_rank, building_name, main_folder, case_name + '_RAU')

        ## DISTRICT
        # plot COP
        plot_setting = {'ytick_values': 'flexible', 'ylabel': 'COP [-]', 'name': 'COP'}
        plot_scatter_all_dictrict(all_cop_dict, {}, main_folder, case_name, plot_setting)
        # plot Electricity Consumption
        plot_setting = {'ytick_values': 'flexible', 'ylabel': 'El [kWh/m2/yr]', 'name': 'electricity'}
        plot_scatter_all_dictrict(all_cop_dict, {}, main_folder, case_name, plot_setting)
        # plot EX
        plot_setting = {'ytick_values': 'flexible', 'ylabel': 'exergy [kWh/m2/yr]', 'name':'exergy'}
        plot_scatter_all_dictrict(all_ex_dict, {}, main_folder, case_name, plot_setting)
        # plot Cooling Efficiency
        plot_setting = {'ytick_values': 'flexible', 'ylabel': 'Qsc/Qc [-]', 'name': 'eff_cooling'}
        plot_scatter_all_dictrict(all_cooling_eff, {}, main_folder, case_name, plot_setting)

    return



def plot_scatter_all_dictrict(dict_to_plot_scatter, dict_for_label_scale, path_to_save_result, case, plot_setting):
    # get all the points
    building_lookup_key, tech_key, value = get_all_points_from_dict(dict_to_plot_scatter)

    # x axis
    x = building_lookup_key
    x_labels = list(dict_to_plot_scatter.keys())
    x_labels.sort()
    x_values = list(range(len(x_labels)))
    # y axis
    y = value
    if type(plot_setting['ytick_values']) is list:
        y_values_range = plot_setting['ytick_values']
        y_values = np.arange(min(y_values_range), max(y_values_range))
    else:
        y_values = np.arange(round(min(y)) - 2, round(max(y)) + 2)
    y_minor_values = y_values + 0.5
    y_labels = [str(v) for v in y_values]
    # marker size
    anno = tech_key
    if dict_for_label_scale:
        el_tot_list = []
        for i in range(len(anno)):
            building = x_labels[building_lookup_key[i]]
            tech = anno[i]
            #area = (all_el_total_dict[building][tech]/500)**2 # qc_load_Wh_per_Af
            area = (dict_for_label_scale[building][tech] / 110) ** 2  # el_Wh_total_per_Af
            #area = (all_el_total_dict[building][tech] / 600) ** 2  # qc_Wh_sys_per_Af
            el_tot_list.append(area)  # Wh/m2
        el_tot = tuple(el_tot_list)
        # area = el_tot
        area = tuple(map(lambda x: 100, anno))
    else:
        area = tuple(map(lambda x: 100, anno))
    # area = tuple(map(lambda x:100, anno))
    # marker colors
    anno_colors = tuple(map(lambda i: COLOR_CODES[i], anno))

    # format the plt
    plt.figure()
    if case in CASE_TABLE.keys():
        case_shown = CASE_TABLE[case]
    else:
        case_shown = case.split('_')[4]
    plt.title(case_shown, fontsize=18)
    plt.ylabel(plot_setting['ylabel'], fontsize=18)
    x_labels_shown = []
    for label in x_labels:
        A, B, C = label.split("0")
        label_shown = A + B + C if C != '' else A + B + '0'
        x_labels_shown.append(label_shown)
    plt.xticks(x_values, x_labels_shown, fontsize=18, rotation=40)
    plt.yticks(y_values, y_labels, fontsize=18)
    plt.axis([min(x_values) - 0.5, max(x_values) + 0.5,
              min(y_values) - 0.2, max(y_values) + 0.2])
    plt.scatter(x, y, c=anno_colors, s=area)
    # plt.show()
    plt.savefig(path_to_all_district_plot(case, path_to_save_result, plot_setting['name']), bbox_inches="tight")
    return np.nan


def read_total_csv(main_folder, techs):
    totals_dict = {}
    for tech in techs:
        tech_folder_path = os.path.join(main_folder, tech)
        run_folders = os.listdir(tech_folder_path)
        for run_folder in run_folders:
            if 'run' in run_folder:
                run_path = os.path.join(tech_folder_path, run_folder)
                building_name = [x for x in run_folder.split('_') if 'B' in x][0]
                case_name = [x for x in run_folder.split('_') if ('OFF' in x) or ('HOT' in x) or ('RET' in x)][0]
                # initialize dict
                if case_name not in totals_dict.keys():
                    totals_dict[case_name] = {}
                if building_name not in totals_dict[case_name].keys():
                    totals_dict[case_name][building_name] = {}
                if tech not in totals_dict[case_name][building_name].keys():
                    totals_dict[case_name][building_name][tech] = {}
                # write path in dict
                path_to_file = os.path.join(run_path, 'total.csv')
                print (case_name, building_name, tech, '\n', path_to_file)
                totals_dict[case_name][building_name][tech] = pd.read_csv(path_to_file)
    return totals_dict


if __name__ == '__main__':
    main()

