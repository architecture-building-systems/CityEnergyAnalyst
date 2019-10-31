from __future__ import division
import numpy as np
import time
import pandas as pd
import os
import subprocess
import csv
import cea.osmose.settings as settings

import cea.osmose.extract_demand_outputs as extract_demand_outputs
import cea.osmose.plot_osmose_result as plot_results
import cea.osmose.compare_el_usages as compare_el
import cea.osmose.post_process_osmose_results as post_processing

# import from settings # TODO: add to config
TECHS = settings.TECHS
specified_buildings = settings.specified_buildings
timesteps = settings.timesteps
osmose_project_path = settings.osmose_project_path
osmose_project_data_path = settings.osmose_project_data_path
ampl_lic_path = settings.ampl_lic_path
result_destination = settings.result_destination
new_calculation = settings.new_calculation
season = settings.season
cases = settings.cases


def main(case):
    # make folder to save results
    path_to_case_folder = os.path.join(result_destination, case)
    make_directory(path_to_case_folder, new_calculation)

    if type(timesteps) is int:
        # extract demand outputs
        building_names, \
        Tamb, \
        timesteps_calc, \
        periods = extract_demand_outputs.extract_cea_outputs_to_osmose_main(case, timesteps, season,
                                                                            specified_buildings)
        ## start ampl license
        start_ampl_license(ampl_lic_path, "start")
        ## run osmose
        time_print = timesteps
        run_osmose_for_building_cases(Tamb, building_names, case, path_to_case_folder, periods, timesteps_calc, time_print)
    elif type(timesteps) is list:
        ## start ampl license
        start_ampl_license(ampl_lic_path, "start")
        for time in timesteps:
            time_print = time
            # extract demand outputs
            building_names, \
            Tamb, \
            timesteps_calc, \
            periods = extract_demand_outputs.extract_cea_outputs_to_osmose_main(case, [time], season,
                                                                                specified_buildings)
            ## run osmose
            run_osmose_for_building_cases(Tamb, building_names, case, path_to_case_folder, periods, timesteps_calc, time_print)

    return np.nan



def run_osmose_for_building_cases(Tamb, building_names, case, path_to_case_folder, periods, timesteps_calc, time_print):
    write_osmose_general_inputs(path_to_case_folder, periods, timesteps_calc)
    for building in building_names:
        print building, ' in ', case
        write_osmose_building_inputs(Tamb, building)
        for tech in TECHS:
            osmose_one_run(building, case, periods, tech, time_print)

        # # plot results
        # building_timestep_tag = building + "_" + str(periods) + "_" + str(timesteps_calc)
        # building_result_path = os.path.join(path_to_case_folder, building_timestep_tag)
        # # building_result_path = os.path.join(building_result_path, 'base')
        # # file_name = 'outputs.csv'
        # # post_processing.main(building, TECHS, file_name, building_result_path)

        # # building_result_path = os.path.join(building_result_path, "reduced")
        # plot_results.main(building, TECHS, building_result_path)
        # compare_el.main(building, building_result_path, case)
        # # start_ampl_license(ampl_lic_path, "stop")


def osmose_one_run(building, case, periods, tech, time_print):
    # run osmose
    t = time.localtime()
    print time.strftime("%H:%M", t)
    t0 = time.clock()
    result_path, run_folder = exec_osmose(tech, osmose_project_path)
    # rename the files to keep track
    case_short = case.split('_')[4]
    old_name = run_folder
    if os.path.exists(os.path.join(result_path, old_name)):
        if type(timesteps) is int:
            new_name = old_name + '_' + case_short + '_' + building + '_' + str(periods) + '_' + str(time_print)
        elif type(timesteps) is list:
            new_name = old_name + '_' + case_short + '_' + building + '_' + str(periods) + '_' + str(time_print)
        else:
            print('check timesteps')

        ##Remove .jpg
        # model_folder = [result_path, run_folder, 's_001\\plots\\icc\\models']
        # path_to_model_folder = os.path.join('', *model_folder)
        # files = os.listdir(path_to_model_folder)
        # [os.remove(os.path.join(path_to_model_folder, file)) for file in files if '.jpg' in file]

        ##Rename
        os.rename(os.path.join(result_path, run_folder), os.path.join(result_path, new_name))
    time_elapsed = time.clock() - t0
    print round(time_elapsed, 0), ' s for running: ', tech, '\n'
    return


def write_osmose_building_inputs(Tamb, building):
    write_value_to_csv(building, osmose_project_data_path, "building_name.csv")  # osmose input
    write_value_to_csv(Tamb, osmose_project_data_path, "Tamb.csv")


def write_osmose_general_inputs(path_to_case_folder, periods, timesteps_calc):
    write_string_to_txt(path_to_case_folder, osmose_project_data_path, "path_to_case_folder.txt")  # osmose input
    write_value_to_csv(timesteps_calc, osmose_project_data_path, "timesteps.csv")  # osmose input
    write_value_to_csv(periods, osmose_project_data_path, "periods.csv")  # osmose input


def make_directory(dirName, new_calculation=True):
    if not os.path.exists(dirName):
        os.mkdir(dirName)
        print"Directory ", dirName, " Created "
    elif new_calculation == True:
        raise ValueError("Directory ", dirName,
                         " already exists, please clean up the files and restart the calculation.")
    else:
        print"Directory ", dirName, " already exists"
    return np.nan


def write_value_to_csv(timesteps, osmose_project_path, filename):
    csvData = [[timesteps, "N/A"], []]
    file_path = os.path.join(osmose_project_path, filename)
    with open(file_path, 'w') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerows(csvData)
    csvFile.close()
    return np.nan


def write_string_to_txt(content, osmose_project_path, filename):
    file_path = os.path.join(osmose_project_path, filename)
    with open(file_path, "w") as text_file:
        text_file.write(content)
    return np.nan


def start_ampl_license(ampl_lic_path, action):
    command = os.path.join(ampl_lic_path, "ampl_lic.exe " + action)
    p_ampllic = subprocess.Popen(command, cwd=ampl_lic_path)
    ampllic_out, ampllic_err = p_ampllic.communicate()
    if ampllic_out is not None:
        print ampllic_out.decode('utf-8')
    if ampllic_err is not None:
        ampllic_err.decode('utf-8')
    return np.nan


def exec_osmose(tech, osmose_project_path):
    frontend_file = tech + "_frontend.lua"
    frontend_path = osmose_project_path + "\\" + frontend_file
    project_path = os.path.dirname(osmose_project_path)

    p = subprocess.Popen(["lua", (frontend_path)], cwd=project_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    print "running: ", frontend_file
    output, err = p.communicate()

    # if err.decode('utf-8') is not '':
    #     print(err.decode('utf-8'))
    #     if err.decode('utf-8').startswith('WARNING:'):
    #         print 'warning ', err
    #     if err.decode('utf-8').startswith('pandoc: Could not find image'):
    #         print 'warning ', err

    # print(output.decode('utf-8'))

    # print OutMsg
    result_path = os.path.dirname(osmose_project_path) + "\\results\\" + tech
    run_folder = os.listdir(result_path)[len(os.listdir(result_path)) - 1]
    print tech, run_folder
    OutMsg_path = os.path.join(result_path, run_folder) + settings.osmose_outMsg_path
    f = open(OutMsg_path, "r")
    keywords = ['integer infeasible', 'mipgap']
    for line_count, line_text in enumerate(f):
        for keyword in keywords:
            if keyword in line_text:
                print line_text

    return result_path, run_folder


if __name__ == '__main__':
    for case in cases:
        main(case)
    # stop ampl license
    start_ampl_license(ampl_lic_path, "stop")
