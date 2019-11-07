import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap, Normalize
from cea.osmose.plots.plot_curves_to_compare import plot_multiple_techs
from matplotlib.ticker import ScalarFormatter

def main():
    result_folder = 'E:\\ipese_new\\osmose_mk\\results\\HCS_base_hps'
    # run_folder_list = ['run_013_moga_HOT_B005_1_5136', 'run_014_moga_HOT_B005_1_5144', 'run_015_moga_HOT_B005_1_5145',
    #               'run_016_moga_HOT_B005_1_5147', 'run_017_moga_HOT_B005_1_5148']
    run_folder_list = ['run_018_moga_HOT_B005_1_5136']
    for run_folder in run_folder_list:
        path_to_rerun_folder = os.path.join('', *[result_folder, run_folder, 'rerun'])

        ## reruns
        plot_icc_of_all_reruns(path_to_rerun_folder)
        reruns_df = get_all_reruns(path_to_rerun_folder)
        plot_perato_reruns(reruns_df, path_to_rerun_folder)

        ## all populations
        path_to_dakota_folder = os.path.join('', *[result_folder, run_folder, 'dakota'])
        plot_perato_all_populations(path_to_dakota_folder, run_folder)
        plot_perato_graphics(path_to_dakota_folder)
    return


def plot_perato_graphics(path_to_dakota_folder):
    path_to_graphics_file = os.path.join(path_to_dakota_folder, 'graphics.dat')
    graphics_df = pd.read_csv(path_to_graphics_file, sep="\s+")
    graphics_df = graphics_df.round(3)
    graphics_df = graphics_df[graphics_df['obj_fn_1'] < 1e7]
    # plot objectives
    plt.figure(figsize=(7, 5))
    ax = plt.subplot()
    x = graphics_df['obj_fn_1']
    y = graphics_df['obj_fn_2']
    T5_max = max(graphics_df['T5'])
    T5_min = min(graphics_df['T5'])
    z = graphics_df['T5']
    ax.scatter(x, y, c=z, vmin=T5_min, vmax=T5_max)
    print(min(x), max(x))
    # ax.set(xlim=(min(x)-5,max(x)+5))
    # ax.set(ylim=(min(y)-1000, max(y)+1000))
    ax.set_ylabel('annualized CAPEX', fontsize=14, color='black', fontweight='normal')
    ax.set_xlabel('electricity [kWh]', fontsize=14, color='black', fontweight='normal')
    ax.set_title('graphics', fontdict={'fontsize': 14, 'fontweight': 'medium'})
    fig1 = plt.gcf()
    fig1.savefig(os.path.join(os.path.dirname(path_to_dakota_folder), 'perato_graphics' + '.png'))
    plt.close(fig1)


def get_all_reruns(path_to_rerun_folder):
    reruns_df = pd.DataFrame()
    runs_list = os.listdir(path_to_rerun_folder)
    for runs in runs_list:
        if 'run' in runs:
            path_to_run_folder = os.path.join(path_to_rerun_folder, runs)
            hps_df = get_hps_df_one_run(path_to_run_folder)
            reruns_df = pd.concat([reruns_df, hps_df], axis=1)
    reruns_df.to_csv(os.path.join(os.path.dirname(path_to_rerun_folder), 'all_reruns.csv'))
    return reruns_df


def plot_perato_reruns(concated_df, path_to_rerun_folder):
    MARKER_DICT = {1: 'X', 2: '+', 3: '*', 4: 'o'}
    cmap = cm.tab20
    total_run_numbers = len(concated_df.columns.levels[0])
    norm = Normalize(vmin=1, vmax=total_run_numbers)
    plot_number = 0
    plt.figure(figsize=(7, 5))
    ax = plt.subplot()
    for run_number in concated_df.columns.levels[0]:
        capex = concated_df[run_number]['Tin']['KPI']['capex']
        opex = concated_df[run_number]['Tin']['KPI']['opex']
        #     number_of_evaporators = concated_df[run_number]['Tin']['Unit_Summary']['#Evap']
        numbers = concated_df[run_number]['Tin']['Unit_Summary']['#Comp']
        anno = (concated_df[run_number]['Tin']['Unit_Summary']['#Cond']) ** 2 * 40
        ax.scatter(opex, capex, color=cmap(norm(plot_number)), label=run_number,
                   marker=MARKER_DICT[numbers], s=anno)
        plot_number += 1
    ncol = 1 if plot_number <= 10 else 2
    # ax.legend(loc='lower left', bbox_to_anchor=(1, 0), ncol=ncol)
    #     ax.set(xlim=(40,70))
    #     ax.set(ylim=(30000, 70000))
    ax.set_title('reruns', fontdict={'fontsize': 14, 'fontweight': 'medium'})
    ax.set_ylabel('annualized CAPEX', fontsize=14, color='black', fontweight='normal')
    ax.set_xlabel('electricity [kWh]', fontsize=14, color='black', fontweight='normal')
    ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
    plt.tight_layout()
    fig1 = plt.gcf()
    fig1.savefig(os.path.join(os.path.dirname(path_to_rerun_folder), 'perato_all_reruns.png'))
    # plt.close(fig1)
    plt.clf()
    return



def plot_icc_of_all_reruns(path_to_rerun_folder):
    ## Plot reruns from dakota ##
    # 2. get paths
    paths = {}
    # runs_to_exclude = ['run_001394', 'run_001780', 'run_001822', 'run_001839',
    #                    'run_001100', 'run_001319', 'run_001713', 'run_001640', 'run_001645', 'run_001675', 'run_001676',
    #                    'run_001678', 'run_001702', 'run_001703']
    for run_folder in os.listdir(path_to_rerun_folder):
        # for run_folder in runs_to_exclude:
        if 'run' in run_folder:
            # if run_folder not in runs_to_exclude:
            folder_layers = [path_to_rerun_folder, run_folder, 's_001\\plots\\icc\\models']
            paths[run_folder] = os.path.join('', *folder_layers)
    # 3. plot
    plot_type = 'icc'
    model_name = 'hp'
    line_type = ['separated', 'base']  # 'base' or 'separated'
    t = 1
    plot_multiple_techs(paths, t, plot_type, line_type, model_name)
    return

def plot_perato_all_populations(path_to_dakota_folder, title):
    # plot all populations
    files = os.listdir(path_to_dakota_folder)
    plt.figure(figsize=(9, 5))
    plot_number = 0

    cmap = cm.viridis
    norm = Normalize(vmin=1, vmax=20)
    plot_number = 0
    ax = plt.subplot()
    for file in files:
        if ('population_' in file and '.dat' in file):
            path_to_last_gen_file = os.path.join(path_to_dakota_folder, file)
            column_names = ['dT_sc', 'dT4', 'dT_dsh', 'dT1', 'T5', 'dT3', 'dT2', 'obj_fn_1', 'obj_fn_2']
            population_df = pd.read_csv(path_to_last_gen_file, sep="\s+", header=None, names=column_names)
            population_df = population_df[population_df['obj_fn_1']<1e7]
            population_df = population_df[population_df['obj_fn_2']<1e5]
            population_df = population_df.round(3)
            # plot individual
            population_name = file.split('.dat')[0]
#             plot_scatter(population_df, name, name)
            #
            number = int(population_name.split('_')[1])
            ax.scatter(population_df['obj_fn_1'],population_df['obj_fn_2'], color=cmap(norm(number)), label=number)
            plot_number += 1
    ncol = 1 if plot_number <= 10 else 2
    # ax.legend(loc='lower left', bbox_to_anchor=(1, 0), ncol=ncol)
#     ax.set(xlim=(40,70))
#     ax.set(ylim=(30000, 70000))
    ax.set_title(title, fontdict={'fontsize': 14, 'fontweight': 'medium'})
    ax.set_ylabel('annualized CAPEX', fontsize=14, color='black', fontweight='normal')
    ax.set_xlabel('electricity [kWh]', fontsize=14, color='black', fontweight='normal')
    plt.tight_layout()
    fig1 = plt.gcf()
    fig1.savefig(os.path.join(os.path.dirname(path_to_dakota_folder), 'perato_all_populations.png'))
    plt.close(fig1)
    return

def get_hps_df_one_run(path_to_rerun_folder):
    # read json
    for file in os.listdir(path_to_rerun_folder):
        if '_out.json' in file:
            path_to_osmose_json_file = os.path.join(path_to_rerun_folder, file)
        if 'params_eval' in file:
            path_to_params_eval_file = os.path.join(path_to_rerun_folder, file)
    # set parameters
    scenario = 0
    cluster = 0

    # get hps configurations
    data = read_json(path_to_osmose_json_file)
    results_dict = data['results']
    evaluated_list = data['evaluated'][scenario][cluster]
    hps_dict = get_hps_dict(results_dict, evaluated_list, scenario)

    # get KPIs
    params_eval = read_json(path_to_params_eval_file)
    hps_dict['KPI'] = {'opex': {'Tin': round(params_eval['obj_fn_1'], 2)},
                       'capex': {'Tin': round(params_eval['obj_fn_2'], 2)}}
    hps_dict['variables'] = {}
    hps_dict['variables']['T5'] = {'Tin': round(params_eval['T5'], 2)}
    hps_dict['variables']['dTsc'] = {'Tin': round(params_eval['dT_sc'], 2)}
    hps_dict['variables']['dTdsh'] = {'Tin': round(params_eval['dT_dsh'], 2)}
    hps_dict['variables']['T4'] = {'Tin': hps_dict['variables']['T5']['Tin'] + round(params_eval['dT4'], 2)}
    hps_dict['variables']['T3'] = {'Tin': hps_dict['variables']['T4']['Tin'] + round(params_eval['dT3'], 2)}
    hps_dict['variables']['T2'] = {'Tin': hps_dict['variables']['T3']['Tin'] + round(params_eval['dT2'], 2)}
    hps_dict['variables']['T1'] = {'Tin': hps_dict['variables']['T2']['Tin'] + round(params_eval['dT1'], 2)}

    # make multi-level df
    hps_df = pd.DataFrame.from_dict({(i, j): hps_dict[i][j]
                                     for i in hps_dict.keys()
                                     for j in hps_dict[i].keys()},
                                    orient='index')
    hps_df = pd.concat([hps_df], axis=1, keys=[params_eval['eval_id']])
    #     print(hps_df)
    return hps_df

def get_hps_dict(results_dict, evaluated_list, scenario):
    # streamQ
    streamQ_dict = results_dict['streamQ'][scenario]
    hps_dict = {'Cond':{},'Evap':{},'Comp':{}}
    for stream_name in streamQ_dict.keys():
        if max(streamQ_dict[stream_name]) > 0.0:
            # get details from evaluated
            if 'hp' in stream_name:
                for stream in evaluated_list['streams']:
                    if stream['name'] == stream_name:
                        Tin = round(stream['Tin_corr'] - 273.15,2)
                        Tout = round(stream['Tout_corr'] - 273.15, 2)
                        if 'Cond' in stream_name:
                            hps_dict['Cond'][stream_name] = {'Tin': Tin, 'Tout': Tout}
                        elif 'Evap' in stream_name:
                            hps_dict['Evap'][stream_name] = {'Tin': Tin, 'Tout': Tout}
                        elif 'Comp' in stream_name:
                            hps_dict['Comp'][stream_name] = {'Tin': Tin, 'Tout': Tout}
                        else:
                            print('couldnt define this stream: ', stream_name)
#                         print (round(stream['Tin_corr'] - 273.15,2), round(stream['Tout_corr'] - 273.15, 2))
    # Units_Mult_t
    Units_Mult_t_dict = results_dict['Units_Mult_t'][0]
    hps_dict['Unit'] = {}
    for unit in Units_Mult_t_dict.keys():
        if (max(Units_Mult_t_dict[unit])> 0.0 and 'hp' in unit):
            hps_dict['Unit'][unit] = {'Tin': max(Units_Mult_t_dict[unit])}
    # Unit summary
    all_units = hps_dict['Unit'].keys()
    hps_dict['Unit_Summary'] = {}
    hps_dict['Unit_Summary']['#Cond'] = {'Tin':len([unit for unit in all_units if 'Cond' in unit])}
    hps_dict['Unit_Summary']['#Evap'] = {'Tin':len([unit for unit in all_units if 'Evap' in unit])}
    hps_dict['Unit_Summary']['#Comp'] = {'Tin':len([unit for unit in all_units if 'Comp' in unit])}
    return hps_dict

def read_json(path_to_json_file):
    with open(path_to_json_file) as f:
        data = json.load(f)
    return data

if __name__ == '__main__':
    main()