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
from cea.utilities.dbf import *
from cea.demand.demand_main import properties_and_schedule, calc_demand_multiprocessing, calc_demand_singleprocessing
from cea.demand import demand_writers

creator.create("FitnessMax", base.Fitness, weights=(-1.0,))
creator.create("Individual", array.array, typecode='b', fitness=creator.FitnessMax)

toolbox = base.Toolbox()

# Attribute generator
toolbox.register("attr_bool", random.randint, 0, 1)

# Structure initializers
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_bool, 100)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)


def objective_function(individual):
    return sum(individual),


toolbox.register("evaluate", objective_function)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
toolbox.register("select", tools.selTournament, tournsize=3)

def create_and_run_one_individual(individual, individual_name, locator_temp):
    temp_properties_path = os.path.join(locator_temp.get_temporary_folder, 'calibration_scenario', 'inputs', 'building-properties')
    shutil.copytree(locator_temp.get_building_properties_folder, temp_properties_path)
    architecture_df = dbf_to_dataframe(os.path.join(temp_properties_path, 'architecture.dbf')).set_index('Name')
    internal_loads_df = dbf_to_dataframe(os.path.join(temp_properties_path, 'internal_loads.dbf')).set_index('Name')
    indoor_comfort_df = dbf_to_dataframe(os.path.join(temp_properties_path, 'indoor_comfort.dbf')).set_index('Name')
    # TODO: edit the dbf's with the individual's variables
    dataframe_to_dbf(architecture_df.reset_index(), os.path.join(temp_properties_path, 'architecture.dbf'))
    dataframe_to_dbf(internal_loads_df.reset_index(), os.path.join(temp_properties_path, 'internal_loads.dbf'))
    dataframe_to_dbf(indoor_comfort_df.reset_index(), os.path.join(temp_properties_path, 'indoor_comfort.dbf'))
    demand_calculation_calibration(locator_temp)
    shutil.copy(locator_temp.get_total_demand, os.path.join(locator.get_calibration_folder, individual_name+'.csv'))

def demand_calculation_calibration(locator, gv, config):
    """
    Algorithm to calculate the hourly demand of energy services in buildings
    using the integrated model of [Fonseca2015]_.

    Produces a demand file per building and a total demand file for the whole zone of interest:
      - a csv file for every building with hourly demand data.
      - ``Total_demand.csv``, csv file of yearly demand data per building.


    :param locator: An InputLocator to locate input files
    :type locator: cea.inputlocator.InputLocator

    :param weather_path: A path to the EnergyPlus weather data file (.epw)
    :type weather_path: str

    :param gv: global variables
    :type gv: cea.globalvar.GlobalVariables

    :param use_dynamic_infiltration_calculation: Set this to ``True`` if the (slower) dynamic infiltration
        calculation method (:py:func:`cea.demand.ventilation_air_flows_detailed.calc_air_flows`) should be used instead
        of the standard.
    :type use_dynamic_infiltration_calculation: bool

    :param multiprocessing: Set this to ``True`` if the :py:mod:`multiprocessing` module should be used to speed up
        calculations by making use of multiple cores.
    :type multiprocessing: bool

    :returns: None
    :rtype: NoneType

    .. [Fonseca2015] Fonseca, Jimeno A., and Arno Schlueter. “Integrated Model for Characterization of
        Spatiotemporal Building Energy Consumption Patterns in Neighborhoods and City Districts.”
        Applied Energy 142 (2015): 247–265.
    """

    # INITIALIZE TIMER
    t0 = time.clock()

    # LOCAL VARIABLES
    multiprocessing = config.multiprocessing
    region = config.region
    list_building_names = config.calibration_optimization.buildings
    loads_output = config.calibration_optimization.loads
    resolution_output = 'monthly'
    use_dynamic_infiltration = config.demand.use_dynamic_infiltration_calculation
    use_daysim_radiation = config.demand.use_daysim_radiation
    use_stochastic_occupancy = config.demand.use_stochastic_occupancy
    massflows_output = config.demand.massflows_output
    temperatures_output = config.demand.temperatures_output
    format_output = config.demand.format_output
    override_variables = config.demand.override_variables
    weather_data = epwreader.epw_reader(config.weather)[['year', 'drybulb_C', 'wetbulb_C',
                                                         'relhum_percent', 'windspd_ms', 'skytemp_C']]
    year = weather_data['year'][0]

    # CALCULATE OBJECT WITH PROPERTIES OF ALL BUILDINGS
    building_properties, schedules_dict, date = properties_and_schedule(gv, locator, region, year, use_daysim_radiation,
                                                                        override_variables)

    # SPECIFY NUMBER OF BUILDINGS TO SIMULATE
    if not list_building_names:
        list_building_names = building_properties.list_building_names()
        print('Running demand calculation for all buildings in the zone')
    else:
        print('Running demand calculation for the next buildings=%s' % list_building_names)

    # DEMAND CALCULATION
    if multiprocessing and mp.cpu_count() > 1:
        calc_demand_multiprocessing(building_properties, date, gv, locator, list_building_names,
                                    schedules_dict, weather_data, use_dynamic_infiltration, use_stochastic_occupancy,
                                    resolution_output, loads_output, massflows_output, temperatures_output,
                                    format_output, config, region)
    else:
        calc_demand_singleprocessing(building_properties, date, gv, locator, list_building_names, schedules_dict,
                                     weather_data, use_dynamic_infiltration, use_stochastic_occupancy,
                                     resolution_output, loads_output, massflows_output, temperatures_output,
                                     format_output, region)

    # WRITE TOTAL YEARLY VALUES
    writer_totals = demand_writers.YearlyDemandWriter(loads_output, massflows_output, temperatures_output)
    totals, time_series = writer_totals.write_to_csv(list_building_names, locator)

    time_elapsed = time.clock() - t0
    print('done - time elapsed: %d.2f seconds' % time_elapsed)


def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    temp_scenario_path = os.path.join(locator.get_temporary_folder(), 'calibration_scenario')
    shutil.copytree(locator.get_project_path, temp_scenario_path)
    locator_temp = cea.inputlocator.InputLocator(scenario=temp_scenario_path)
    building_names = config.calibration_optimization.buildings
    building_loads = config.calibration_optimization.loads
    materials = config.calibration_optimization.materials
    internal_loads = config.calibration_optimization.internal_loads
    indoor_comfort = config.calibration_optimization.indoor_comfort
    building_metering = os.path.join(locator.get_demand_measured_folder, 'Yearly_demand_metering.csv')
    material_choices = {'type_cons': list(pd.read_excel(locator.get_envelope_systems, 'CONSTRUCTION')['code']),
                        'type_leak': list(pd.read_excel(locator.get_envelope_systems, 'LEAKAGE')['code']),
                        'type_win': list(pd.read_excel(locator.get_envelope_systems, 'WINDOW')['code']),
                        'type_roof': list(pd.read_excel(locator.get_envelope_systems, 'ROOF')['code']),
                        'type_wall': list(pd.read_excel(locator.get_envelope_systems, 'WALL')['code']),
                        'type_shade': list(pd.read_excel(locator.get_envelope_systems, 'SHADING')['code'])}
    # TODO: I am just choosing these three values as the only options for now, but ideally these should depend on the distribution of the uncertainties
    uncertainty_distributions = locator.get_uncertainty_db(config.region)
    internal_loads_choices = pd.read_excel(uncertainty_distributions, 'INTERNAL_LOADS')[['name', 'min', 'mu', 'max']].set_index('name')
    indoor_comfort_choices = pd.read_excel(uncertainty_distributions, 'INDOOR_COMFORT')[['name', 'min', 'mu', 'max']].set_index('name')

    random.seed(64)

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
