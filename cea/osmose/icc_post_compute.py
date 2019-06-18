import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def main(building_name, function, line_types, parts_of_data, hours):
    hourly_exergy_list = []
    hourly_exergy = {}

    x_heat, y_carnot = {}, {}
    for line_type in line_types:
        for part_of_data in parts_of_data:
            x_heat[line_type + '_' + part_of_data] = {}
            y_carnot[line_type + '_' + part_of_data] = {}

    for t in hours:
        for line_type in line_types:
            file_name = 'carnot_' + line_type + '_s_selection_p1_t' + str(t) + '_' + tech + '_c1_DefaultHeatCascade.txt'
            #     file_name = 'carnot_base_s_selection_p1_t'+str(t)+'_'+tech+'_c1_DefaultHeatCascade.txt'
            #     file_name = 'carnot_separated_s_selection_p1_t'+str(t)+'_'+tech+'_c1_DefaultHeatCascade.txt'
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                data_df = pd.read_csv(file_path, delimiter='\s+', header=None, names=['heat', 'carnot'])
                for part_of_data in parts_of_data:
                    if part_of_data == 'cooling':
                        print('cooling')
                        data_cooling = data_df[data_df.carnot <= 0]
                        x_heat[line_type + '_' + part_of_data][t] = data_cooling.heat
                        y_carnot[line_type + '_' + part_of_data][t] = data_cooling.carnot
                        hourly_exergy = get_exergy_total_exergy(data_cooling, part_of_data, line_type, hourly_exergy)

                    elif part_of_data == 'heating':
                        data_heating = data_df[data_df.carnot >= 0]
                        x_heat[line_type + '_' + part_of_data][t] = data_heating.heat
                        y_carnot[line_type + '_' + part_of_data][t] = data_heating.carnot
                        hourly_exergy = get_exergy_total_exergy(data_heating, part_of_data, line_type, hourly_exergy)
                    else:
                        print('all')

                        # get area directly
                    area = np.trapz(data_df.carnot, data_df.heat)
                    # print ('area from np.trapz:' ,area)
                    hourly_exergy_list.append(area)

    COLOR_TABLE = {'base': '#C96A50', 'separated': '#3E9AA3'}
    for line_type in line_types:
        for part_of_data in parts_of_data:
            for t in hours:
                plt.plot(x_heat[line_type + '_' + part_of_data][t], y_carnot[line_type + '_' + part_of_data][t],
                         label=t,
                         color=COLOR_TABLE[line_type])
            # plt.legend(loc='best') #,bbox_to_anchor=(1.1,1.05)
            # Set x axis label.
            plt.xlabel("Heat Load [kW]", fontsize=12)
            # Set y axis label.
            plt.ylabel("Carnot factor", fontsize=12)
            plt.ylim([-0.08, 0.08])
            plt.xlim([0, 1250])
            title = tech
            plt.title(title)
            plt.savefig(os.path.join(folder_path, '0_hourly_carnot_' + line_type + '_' + part_of_data + '.png'))
    # print (hourly_exergy_list, hourly_exergy_req_list, hourly_exergy_pro_list)
    # print (np.add(hourly_exergy_req_list,hourly_exergy_pro_list))

    print ('hourly trapz area: ', hourly_exergy_list)
    total_exergy_kWh = sum(hourly_exergy_list)


    # save file
    hourly_exergy_df = pd.DataFrame.from_dict(hourly_exergy)
    total_df = pd.DataFrame(hourly_exergy_df.sum()).T
    hourly_exergy_df = hourly_exergy_df.append(total_df).reset_index().drop(columns='index')
    hourly_exergy_df.to_csv(os.path.join(folder_path, '0_hourly_exergy.csv'))
    return np.nan


# build a new set of lines to calculate area
def get_all_lines(data, line_type):
    # reset index
    data.reset_index(inplace=True)
    data.drop(columns=['index'], inplace=True)

    lines_ascend = {}
    lines_descend = {}
    index_ascend, index_descend = 0, 0
    points = []

    if line_type == 'separated':
        ascending_rule = True
    elif line_type == 'base':
        ascending_rule = False
    else:
        raise ValueError('The line_type is wrong: ', line_type)

    # round to 4 decimal
    data.heat = data.heat.round(4)

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
                    # print('add in line ascending:', index, data.loc[index]['heat'])
                    lines_ascend[index_ascend] = points
                    # print('number of ascending lines: ', index_ascend + 1)
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
                    # print('add in line decending:', index, data.loc[index]['heat'])
                    lines_descend[index_descend] = points
                    # print('number of descending lines: ', index_descend + 1)
                    index_descend = index_descend + 1
                    points = [index - 1, index]
                    ascending_rule = not ascending_rule
    return lines_ascend, lines_descend




def get_exergy(df, dict_of_points):
    areas = []
    for key in dict_of_points.keys():
        index_min = min(dict_of_points[key])
        index_max = max(dict_of_points[key])
        carnot = df.carnot[index_min:index_max + 1]
        heat = df.heat[index_min:index_max + 1]
        area = np.trapz(carnot, heat)
        areas.append(area)
    return sum(areas)





def get_exergy_total_exergy(data, part_of_data, line_type, hourly_exergy):
    print('calculating total exergy for: ', part_of_data, line_type)
    ## get line to the lowest heat to calculate exergy supplied/requirement
    name = 'hourly_' + part_of_data + '_' + line_type
    min_heat = data.heat.min()
    print('lowest enthalpy: ', min_heat)
    if part_of_data == 'cooling':
        min_heat_index = max(data[data.heat == min_heat].index)
        print(' index with lowest enthalpy: ', min_heat_index)
        data_min_heat = data.loc[0:min_heat_index]
        lines_ascend, lines_descend = get_all_lines(data_min_heat, line_type)
        print(' ', lines_ascend, 'ok if empty')
        # write to dict
        if name in hourly_exergy.keys():
            hourly_exergy[name].append(get_exergy(data, lines_descend))
        else:
            hourly_exergy[name] = [get_exergy(data, lines_descend)]
    elif part_of_data == 'heating':
        min_heat_index = min(data[data.heat == min_heat].index)
        print(' index with lowest enthalpy: ', min_heat_index)
        data_min_heat = data.loc[min_heat_index:]
        lines_ascend, lines_descend = get_all_lines(data_min_heat, line_type)
        print(' ', lines_descend, 'ok if empty')
        # write to dict
        if name in hourly_exergy.keys():
            hourly_exergy[name].append(get_exergy(data, lines_ascend))
        else:
            hourly_exergy[name] = [get_exergy(data, lines_ascend)]
    return hourly_exergy




if __name__ == '__main__':
    # get all file paths
    hcs_folder_name = 'HCS_windows'
    tech = 'HCS_coil'
    # run_name = 'run_034'
    case_short = 'HOT'
    building_name = 'B001'
    timesteps = 24

    run_name = case_short + '_' + building_name + '_' + str(timesteps)

    folder_path = os.path.join('', *['C:\\OSMOSE_projects', hcs_folder_name, 'results', tech, run_name,
                                     'scenario_1\\plots'])

    line_types = ['base', 'separated']  # 'base' or 'separated'
    parts_of_data = ['heating', 'cooling']

    # choose times to plot
    hours = np.arange(1, 25, 1)
    # hours = [10]
    # print(hours)
    # hours = [7]
    main(building_name, case_short, line_types, parts_of_data, hours)