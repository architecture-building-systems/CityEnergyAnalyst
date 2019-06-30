#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# In[2]:

def main():
    # get all file paths
    hcs_folder_name = 'icc_ER0'
    tech = 'HCS_ER0'
    main_folder_path = 'C:\\Users\\Shanshan\\Documents\\WP1_results_0629\\icc\\' + hcs_folder_name

    line_types = ['separated', 'base']  # 'base' or 'separated'
    parts_of_data = ['all']
    icc_type = 'process'  # 'process', 'chiller'

    # choose times to plot
    t_start = 73
    t_end = t_start + 24
    # hours = [73]
    hours = np.arange(t_start, t_end, 1)
    # hours = [8,9,10]
    # print(hours)
    # hours = [7]
    hourly_exergy_list = []
    hourly_exergy_req_list = []
    hourly_exergy_pro_list = []
    hourly_exergy = {}
    hourly_heating_exergy = {}



    all_folders_in_path = os.listdir(main_folder_path)
    for folder in all_folders_in_path:
        folder_path = os.path.join('', *[main_folder_path, folder, 'scenario_1\\plots'])
        print(folder_path)
        for t in hours:
            data_df, x_heat, y_carnot = get_data_df(folder_path, line_types, parts_of_data, icc_type, tech, t)
            if not data_df.empty:
                plot_icc(x_heat, y_carnot, tech, line_types, parts_of_data, data_df, folder_path, t)

    return


# build a new set of lines to calculate area
def get_all_lines(data, line_type, icc_type):
    # reset index
    data.reset_index(inplace=True)
    data.drop(columns=['index'], inplace=True)

    lines_ascend = {}
    lines_descend = {}
    index_ascend, index_descend = 0, 0
    points = []

    if line_type == 'separated':
        ascending_rule = True
        if icc_type == 'chiller':
            ascending_rule = False
    elif line_type == 'base':
        ascending_rule = False
    else:
        raise ValueError('The lint_type is wrong: ', line_type)

    data.heat = round(data.heat, 4)

    for index in data.index:
        if index == 0:
            points = [index]
        else:
            value_1 = data.heat.iloc[index - 1]
            value_2 = data.heat.iloc[index]
            diff = value_2 - value_1
            if ascending_rule:
                if (index < (len(data.index) - 1) and diff >= 0.0):
                    # print('add in points ascending:', index, data.loc[index]['heat'])
                    points.append(index)
                elif (index < (len(data.index) - 1) and np.isclose(diff, 0.0)):
                    points.append(index)
                else:
                    print('add in line ascending:', index, data.loc[index]['heat'])
                    lines_ascend[index_ascend] = points
                    print('number of ascending lines: ', index_ascend + 1)
                    index_ascend = index_ascend + 1
                    points = [index - 1, index]
                    ascending_rule = not ascending_rule
            elif not ascending_rule:
                if (index < (len(data.index) - 1) and diff <= 0):
                    # print('add in points decending:', index, data.loc[index]['heat'])
                    points.append(index)
                elif (index < (len(data.index) - 1) and np.isclose(diff, 0.0)):
                    points.append(index)
                else:
                    print('add in line decending:', index, data.loc[index]['heat'])
                    lines_descend[index_descend] = points
                    print('number of descending lines: ', index_descend + 1)
                    index_descend = index_descend + 1
                    points = [index - 1, index]
                    ascending_rule = not ascending_rule
    return lines_ascend, lines_descend



def get_data_df(folder_path, line_types, parts_of_data, icc_type, tech, t):

    x_heat, y_carnot = {}, {}
    for line_type in line_types:
        for part_of_data in parts_of_data:
            x_heat[line_type + '_' + part_of_data] = {}
            y_carnot[line_type + '_' + part_of_data] = {}

    for line_type in line_types:
        file_name = 'carnot_' + line_type + '_s_selection_p1_t' + str(t) + '_' + tech + '_c1_DefaultHeatCascade.txt'
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            data_df = pd.read_csv(file_path, delimiter='\s+', header=None, names=['heat', 'carnot'])
            for part_of_data in parts_of_data:
                if part_of_data == 'cooling':
                    print('cooling')
                    data_cooling = data_df[data_df.carnot <= 0]
                    x_heat[line_type + '_' + part_of_data][t] = data_cooling.heat
                    y_carnot[line_type + '_' + part_of_data][t] = data_cooling.carnot
                elif part_of_data == 'heating':
                    data_heating = data_df[data_df.carnot >= 0]
                    x_heat[line_type + '_' + part_of_data][t] = data_heating.heat
                    y_carnot[line_type + '_' + part_of_data][t] = data_heating.carnot
                else:
                    x_heat[line_type + '_' + part_of_data][t] = data_df.heat
                    y_carnot[line_type + '_' + part_of_data][t] = data_df.carnot
        else:
            data_df = pd.DataFrame()
            print 'cannot find file: ', file_path
    return data_df, x_heat, y_carnot




def plot_icc(x_heat, y_carnot, tech, line_types, parts_of_data, data_df, folder_path, t):
    plt.rcParams["figure.figsize"] = (6, 6)
    plt.rcParams.update({'figure.autolayout': True})
    # fig, (ax1,ax2) = plt.subplots(2,1)
    fig, ax1 = plt.subplots(1, 1)
    COLOR_TABLE = {'base': '#C96A50', 'separated': '#3E9AA3'}
    for line_type in line_types:
        for part_of_data in parts_of_data:
            ax1.plot(x_heat[line_type + '_' + part_of_data][t], y_carnot[line_type + '_' + part_of_data][t], label=t,
                     color=COLOR_TABLE[line_type])
            # plt.legend(loc='best') #,bbox_to_anchor=(1.1,1.05)
            # Set x axis label.
            ax1.set_xlabel("Heat Load [kW]", fontsize=20)
            # Set y axis label.
            ax1.set_ylabel("Carnot factor", fontsize=20)
            ax1.set_ylim([-0.08, 0.08])
            ax1.set_xlim([-10, data_df.heat.max() + 10])
            ax1.tick_params(axis='both', which='major', labelsize=16)
            title = tech
            ax1.set_title(title, fontsize=20)

        ax1.fill_between(x_heat[line_types[1] + '_' + part_of_data][t], 0,
                         y_carnot[line_types[1] + '_' + part_of_data][t], color=COLOR_TABLE[line_types[1]], alpha=0.5)

    fig.savefig(os.path.join(folder_path, str(t) + '_hourly_carnot_' + line_type + '_' + part_of_data + '.png'))
    return


# In[9]:




# In[ ]:

if __name__ == '__main__':
    main()


