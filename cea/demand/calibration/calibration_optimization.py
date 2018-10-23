import multiprocessing as mp
import os
import array
import random
import numpy
import shutil
import time
import pandas as pd
from cea.utilities import epwreader
from deap import algorithms
from deap import base
from deap import creator
from deap import tools
import cea.inputlocator
import cea.globalvar
from cea.utilities.dbf import *
from cea.demand.demand_main import demand_calculation
from cea.demand import demand_writers
from cea.demand.calibration.bayesian_calibrator.calibration_sampling import calc_cv_rmse

creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
creator.create("Individual", array.array, typecode='b', fitness=creator.FitnessMin)

toolbox = base.Toolbox()

# Attribute generator
toolbox.register("attr_bool", random.randint, 0, 1)

# Structure initializers
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_bool, 100)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)


def objective_function(individual):
    return sum(individual),

def objective_function(individual_number, individual, generation, simulation, measured):
    """
    Objective function is used to calculate the error corresponding to the individual
    :param individual: Input individual
    :type individual: list
    :return: returns costs, CO2, primary energy and the master_to_slave_vars
    """
    print ('cea optimization progress: individual ' + str(individual_number) + ' and generation '+ str(generation) + '/' + str(config.optimization.ngen))

    # calculate RMSE for all 100 buildings and take maximum - minimize (total RMSE and maximum RMSE)
    cv_rmse, rmse = calc_cv_rmse(simulation, measured)

    # TODO: add evaluation function?

    return cv_rmse, rmse, master_to_slave_vars, valid_individual

def create_individual(lower_bound, upper_bound, buildings):

    # initiate the individual
    individual = [0] * len(lower_bound) * int(buildings)

    for building in range(buildings):
        # type_leak
        individual[building * len(lower_bound) + 0] = random.randint(1, 6)

        # type_win
        individual[building * len(lower_bound) + 1] = random.randint(1, 7)

        # type_roof
        individual[building * len(lower_bound) + 2] = random.sample({1, 2, 4, 7}, 1)[0]

        # type_wall
        individual[building * len(lower_bound) + 3] = random.sample({1, 2, 3, 4, 6}, 1)[0]

        # type_cons
        individual[building * len(lower_bound) + 4] = random.randint(1, 3)

        # Ea_Wm2
        individual[building * len(lower_bound) + 5] = round(0.8 + random.randint(0, 4) * (0.1), 1)

        # El_Wm2
        individual[building * len(lower_bound) + 6] = round(0.8 + random.randint(0, 4) * (0.1), 1)

        # Epro_Wm2
        individual[building * len(lower_bound) + 7] = round(0.8 + random.randint(0, 4) * (0.1), 1)

        # Vww_lpd
        individual[building * len(lower_bound) + 8] = round(0.8 + random.randint(0, 4) * (0.1), 1)

        # Qcpro_Wm2
        individual[building * len(lower_bound) + 9] = round(0.8 + random.randint(0, 4) * (0.1), 1)


    return individual

lower_bound = [1, 1, 1, 1, 1, 0.8, 0.8, 0.8, 0.8, 0.8]  # corresponding to type_leak, type_win, type_roof, type_wall, type_cons, Ea_Wm2, El_Wm2, Epro_Wm2, Vww_lpd, Qcpro_Wm2
upper_bound = [6, 7, 7, 6, 3, 1.2, 1.2, 1.2, 1.2, 1.2]

toolbox.register("generate", create_individual, lower_bound, upper_bound)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.generate)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("evaluate", objective_function)
toolbox.register("evaluate", objective_function)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
toolbox.register("select", tools.selTournament, tournsize=3)

def create_and_run_one_individual(individual, individual_name, locator, config_temp, list_buildings, materials, internal_loads, indoor_comfort):
    '''
    For a given individual, this function should first copy the reference case into a temp directory, then edit the
    corresponding input files with the given individual's input parameters, then run the demand.

    :param individual:
    :param individual_name:
    :param locator_temp:
    :return:
    '''


    # individual = [1, 1, 1, 0.3, 1, ...]
    # At the moment, this function doesn't do anything because the individual is not yet defined (I'm not sure  what
    # type of data, etc. it will be in). Once this is clear to me, I can add the part where the input dbf files are
    # edited.

    # get temp scenario building properties path (this step is actually not necessary)
    locator_temp = cea.inputlocator.InputLocator(config_temp.scenario)
    # temp_properties_path = os.path.join(locator_temp.get_building_properties_folder)
    # get dbf files that need to be edited
    architecture_df = dbf_to_dataframe(locator.get_building_architecture()).set_index('Name')
    internal_loads_df = dbf_to_dataframe(locator.get_building_internal()).set_index('Name')
    indoor_comfort_df = dbf_to_dataframe(locator.get_building_comfort()).set_index('Name')
    # edit dbf files based on individual data
    len_variables = len(materials) + len(internal_loads) + len(indoor_comfort)
    for i in range(len(list_buildings)):
        for j in range(len(materials)):
            architecture_df.loc[list_buildings[i], materials[j]] = 'T'+individual[i * len_variables + j]
        j += 1
        for k in range(len(internal_loads)):
            internal_loads_df.loc[list_buildings[i], internal_loads[k]] *= individual[i * len_variables + j + k]
        k += 1
        for l in range(len(indoor_comfort)):
            indoor_comfort_df.loc[list_buildings[i], indoor_comfort[l]] *= individual[i * len_variables + j + k + l]
    # export edited dbf files
    dataframe_to_dbf(architecture_df.reset_index(), locator_temp.get_building_architecture())
    dataframe_to_dbf(internal_loads_df.reset_index(), locator_temp.get_building_internal())
    dataframe_to_dbf(indoor_comfort_df.reset_index(), locator_temp.get_building_comfort())
    # calculate demand
    demand_calculation(locator=locator_temp, gv=cea.globalvar.GlobalVariables(), config=config_temp)
    # copy results from the given individual to the actual scenario
    shutil.copy(locator_temp.get_total_demand(), os.path.join(locator.get_calibration_folder(), individual_name+'.csv'))

def create_temp_config_instance(config, locator):
    '''
    for each individual, the input files should be edited with the corresponding values and then passed to the
    demand calculation. but we don't want to edit the actual case study, so instead we create a temp folder for the
    temporary scenarios that need to be created.

    :param config:
    :return temp_config:
    '''

    temp_config = cea.config.Configuration()
    temp_config.scenario = os.path.join(locator.get_temporary_folder(), 'calibration_scenario')
    # # get names of buildings to be calibrated
    # building_names = config.calibration_optimization.buildings
    temp_config.demand.buildings = config.calibration_optimization.buildings
    # # get variables based on which the parameters should be calibrated (e.g. Ef_Wm2)
    # building_loads = config.calibration_optimization.loads
    temp_config.demand.loads = config.calibration_optimization.loads_output
    # set demand calculation to monthly - TODO: would it make sense to use this method for hourly calibration too?
    temp_config.demand.resolution_output = 'monthly'

    shutil.copytree(config.scenario, temp_config.scenario)

    return temp_config


def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    # TODO: create one temp folder per processor for multiprocessing?
    temp_config = create_temp_config_instance(config, locator)
    # get materials that need to be assigned (e.g. walls)
    materials = config.calibration_optimization.materials
    # get internal loads that need to be calibrated (e.g. Ea_Wm2)
    internal_loads = config.calibration_optimization.internal_loads
    # get indoor comfort properties that need to be calibrated (e.g. ve_lps)
    indoor_comfort = config.calibration_optimization.indoor_comfort
    # list variables to be calibrated
    list_variables = materials + internal_loads + indoor_comfort
    # get measured data
    building_metering = os.path.join(locator.get_demand_measured_folder, 'Yearly_demand_metering.csv')
    # get possible values the parameters to be calibrated may take, namely:
    ## type of material (e.g. type_win = 'T1')
    material_choices = {'type_cons': list(pd.read_excel(locator.get_envelope_systems, 'CONSTRUCTION')['code']),
                        'type_leak': list(pd.read_excel(locator.get_envelope_systems, 'LEAKAGE')['code']),
                        'type_win': list(pd.read_excel(locator.get_envelope_systems, 'WINDOW')['code']),
                        'type_roof': list(pd.read_excel(locator.get_envelope_systems, 'ROOF')['code']),
                        'type_wall': list(pd.read_excel(locator.get_envelope_systems, 'WALL')['code']),
                        'type_shade': list(pd.read_excel(locator.get_envelope_systems, 'SHADING')['code'])}
    ## indoor comfort and internal load variable distributions
    # TODO: choosing these three values for now, but ideally these should depend on the uncertainty distribution
    uncertainty_distributions = locator.get_uncertainty_db(config.region)
    internal_loads_choices = pd.read_excel(uncertainty_distributions, 'INTERNAL_LOADS')[['name', 'min', 'mu', 'max']].set_index('name')
    indoor_comfort_choices = pd.read_excel(uncertainty_distributions, 'INDOOR_COMFORT')[['name', 'min', 'mu', 'max']].set_index('name')
    # get measured data for comparison
    demand_metering = locator.get_yearly_demand_measured_file().set_index('Name')

    random.seed(64)
    create_individual(lower_bound, upper_bound, 2)

    pop = toolbox.population(n=300)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)

    pop, log = algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2, ngen=40,
                                   stats=stats, halloffame=hof, verbose=True)

    return pop, log, hof


if __name__ == "__main__":
    main(cea.config.Configuration())
