from cea.demand.calibration.nn_generator.nn_settings import random_variables, target_parameters
from cea.demand.calibration.nn_generator.nn_trainer import nn_input_collector

import cea.inputlocator
import cea.globalvar
import cea.config
from cea.demand.demand_main import properties_and_schedule
from cea.demand.metamodel.nn_generator.nn_trainer_resume import neural_trainer_resume, nn_model_collector


def run_nn_resume_single(locator, random_variables, target_parameters, list_building_names, weather_path, gv):

    urban_input_matrix, urban_taget_matrix = nn_input_collector(locator)
    model, scalerT, scalerX = nn_model_collector(locator)
    neural_trainer_resume(urban_input_matrix, urban_taget_matrix, model, scalerX, scalerT, locator)

def main(config):
    gv = cea.globalvar.GlobalVariables()
    locator = cea.inputlocator.InputLocator(scenario_path=config.scenario)
    weather_path = config.weather()
    building_properties, schedules_dict, date = properties_and_schedule(gv, locator)
    list_building_names = building_properties.list_building_names()
    run_nn_resume_single(locator, random_variables, target_parameters, list_building_names, weather_path, gv)

if __name__ == '__main__':
    main(cea.config.Configuration())
