import json
import requests
import os
import pandas as pd


def post_process_osmose_out_json(path_to_run_folder, remove_json):
    # read json file
    data = read_osmose_out_json(path_to_run_folder, remove_json)
    if data:
        scenario = 0

        # get electricity consumption of each unit
        timesteps = len(data['evaluated'][scenario])
        get_unit_electricity_from_json(data, path_to_run_folder, scenario, timesteps)

        # get streams
        get_streams_Q_T_from_json(data, path_to_run_folder, scenario, timesteps)
    return


def get_unit_electricity_from_json(data, path_to_run_folder, scenario, timesteps):
    electricity_dict = data['results']['Units_demand'][scenario]['Electricity']
    new_el_dict = {}
    for key in electricity_dict.keys():
        unit_el_list = electricity_dict[key]
        if len(unit_el_list) < timesteps:
            unit_el_list = unit_el_list.extend([0] * (timesteps - len(unit_el_list)))
        new_el_dict[key] = unit_el_list
    electricity_df = pd.DataFrame(new_el_dict).T
    electricity_df.to_csv(os.path.join(path_to_run_folder, 'unit_electricity.csv'))


def get_streams_Q_T_from_json(data, path_to_run_folder, scenario, timesteps):
    streamQ_dict = data['results']['streamQ'][scenario]
    evaluated_dict = data['evaluated'][scenario]
    # initialize streams_t_dict
    streams_t_dict = {}
    for time in range(timesteps):
        streams_t_dict[time] = {}
    for stream_name in streamQ_dict.keys():
        for stream in evaluated_dict[time]['streams']:
            if stream['name'] == stream_name:
                for time in range(timesteps):
                    Q = streamQ_dict[stream_name][time]
                    if Q > 0.0:
                        streams_t_dict[time][stream_name] = {}
                        streams_t_dict[time][stream_name]['Tin'] = round(stream['Tin_corr'] - 273.15, 2)  #FIXME: BUGGY
                        streams_t_dict[time][stream_name]['Tout'] = round(stream['Tout_corr'] - 273.15, 2)
                        streams_t_dict[time][stream_name]['Q'] = Q
                        if streams_t_dict[time][stream_name]['Tin'] > streams_t_dict[time][stream_name]['Tout']:
                            stream_type = 'hot'
                        else:
                            stream_type = 'cold'
                        streams_t_dict[time][stream_name]['type'] = stream_type
    excel_writer = pd.ExcelWriter(os.path.join(path_to_run_folder, 'streams_T.xlsx'), engine='xlsxwriter')
    for time in streams_t_dict.keys():
        df = pd.DataFrame(streams_t_dict[time]).T.sort_values(by=['Tin', 'Tout'])
        df.to_excel(excel_writer, sheet_name=str(time))
    excel_writer.save()


def read_osmose_out_json(path_to_run_folder, remove_json):
    # get paths
    for item in os.listdir(path_to_run_folder):
        if 'json' in item:
            path_to_osmose_json_file = os.path.join(path_to_run_folder, item)
            # read json
            with open(path_to_osmose_json_file) as f:
                data = json.load(f)
                if remove_json:
                    f.close()
                    os.remove(path_to_osmose_json_file)
    if not data:
        print('json not stored, please enable option.storejson = True')
        data = False
    return data


if __name__ == '__main__':
    # get file paths
    # results_folder_path = 'E:\\ipese_new\\osmose_mk\\results\\'
    results_folder_path = 'E:\\OSMOSE_projects\\HCS_mk\\results\\'
    scenario_folder = 'HCS_base_coil_hps'
    run_folder = 'run_009_onerun'
    remove_json = False
    path_to_run_folder = os.path.join('', *[results_folder_path, scenario_folder, run_folder])
    post_process_osmose_out_json(path_to_run_folder, remove_json)