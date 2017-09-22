from cea.demand.calibration.latin_sampler import latin_sampler
from cea.demand.demand_main import properties_and_schedule
from cea.demand.calibration.calibration_sampling import apply_sample_parameters
from cea.demand import demand_main
import pickle
import cea
import json
import h5py
import os
import numpy as np
import pandas as pd
from cea.demand.calibration.nn_generator.nn_settings import number_samples, random_variables, target_parameters
from cea.demand.calibration.nn_generator.input_prepare import input_prepare_main

def sampling_main(locator, random_variables, target_parameters, list_building_names, weather_path, gv):

    for i in range(number_samples):
        for building_name in (list_building_names):
            # create list of samples with a LHC sampler and save to disk
            samples, pdf_list = latin_sampler(locator, number_samples, random_variables)
            np.save(locator.get_calibration_samples(building_name), samples)

            # create problem and save to disk as json
            problem = {'variables': random_variables,
                       'building_load': target_parameters, 'probabiltiy_vars': pdf_list}
            pickle.dump(problem, file(locator.get_calibration_problem(building_name), 'w'))

            sample = zip(random_variables, samples[i, :])
            apply_sample_parameters(locator, sample)

        # run cea demand
        demand_main.demand_calculation(locator, weather_path, gv)
        urban_input_matrix, urban_taget_matrix=input_prepare_main(list_building_names, locator, target_parameters, gv)

        nn_inout_path = locator.get_nn_inout_folder()
        file_path_inputs=os.path.join(nn_inout_path,"input%(i)s.csv" % locals())
        data_file_inputs = pd.DataFrame(urban_input_matrix)
        data_file_inputs.to_csv(file_path_inputs)

        file_path_targets = os.path.join(nn_inout_path, "target%(i)s.csv" % locals())
        data_file_targets = pd.DataFrame(urban_taget_matrix)
        data_file_targets.to_csv(file_path_targets)


def run_as_script():
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    weather_path = locator.get_default_weather()
    building_properties, schedules_dict, date = properties_and_schedule(gv, locator)
    list_building_names = building_properties.list_building_names()
    sampling_main(locator, random_variables, target_parameters, list_building_names, weather_path, gv)




if __name__ == '__main__':
    run_as_script()
