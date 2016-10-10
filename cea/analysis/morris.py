# -*- coding: utf-8 -*-
"""
===========================
Variable-screening

This script uses the morris algorithm (morris 1991)(campologo 2011)
to screen the most sensitive variables of a selection of parameters of the CEA.
The method allows to rank each one of this parameters and select the top
most sensitive. This script is used as part of the calibration of the CEA to
measured data.
===========================

"""
from __future__ import division

from cea.demand import demand_main

import multiprocessing as mp
from SALib.analyze import morris
from SALib.sample.morris import sample as sampler
import pandas as pd
import numpy as np

# main
def screening_main(locator, weather_path, gv, output_parameters):

    #Model constants
    gv.multiprocessing = False # default false
    population = 1 #generally 1000
    confidence = 0.95 # generally 0.95
    grid = 2   # generally 2
    levels = 4 # generally 4

    #Define the model inputs
    variables = pd.read_excel(locator.get_uncertainty_db(), "THERMAL")
    num_vars = variables.name.count() #integer with number of variables
    names = variables.name.values # [,,] with names of each variable
    bounds = []
    for var in range(num_vars):
        limits = [variables.loc[var,'min'],variables.loc[var,'max']]
        bounds.append(limits)

    #define the problem
    problem = {'num_vars': num_vars,'names': names, 'bounds': bounds, 'groups': None}

    #create samples (combinations of variables)
    samples = sampler(problem, N=population, num_levels=levels, grid_jump=grid)
    print len(samples), samples

    #call the CEA for building demand and store the results of every sample in a vector
    simulations = screening_cea_multiprocessing(samples, names, output_parameters, locator, weather_path, gv)
    print simulations

    #do morris analysis
    buildings_num = simulations[0].shape[0]
    parameter_results = []
    for parameter in output_parameters:
        morris_results = []
        for building in range(buildings_num):
            simulations_parameter = np.array([x.loc[building, parameter] for x in simulations])
            morris_results.append(morris.analyze(problem, samples, simulations_parameter, conf_level=confidence,
                                            num_levels=levels, grid_jump=grid))

        parameter_results.append(pd.DataFrame(morris_results))
    print parameter_results

    return  #returns dict ranked

# function to call cea
def screening_cea_multiprocessing(samples, names, output_parameters, locator, weather_path, gv):

    out_q = mp.Queue()
    jobs = [mp.Process(target=screening_cea, args=(out_q, sample, names, output_parameters, locator, weather_path,
                                            gv)) for sample in samples]
    for job in jobs: job.start()
    for job in jobs: job.join()

    results = [out_q.get() for job in jobs]
    return results


def screening_cea(out_q, sample,  var_names, output_parameters, locator, weather_path, gv):

    #create a dict with the new input vatiables form the sample and pass in gv
    gv.samples = dict(zip(var_names, sample))
    print gv.samples
    #demadn calculation and return the total file
    totals_output_parameters = demand_main.demand_calculation(locator, weather_path, gv)[output_parameters]

    return out_q.put(totals_output_parameters)

def run_as_script():
    import cea.globalvar as gv
    import cea.inputlocator as inputlocator
    gv = gv.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    weather_path = locator.get_default_weather()
    output_parameters = ['QHf_MWhyr', 'QCf_MWhyr', 'Ef_MWhyr', 'Ef0_kW', 'QHf0_kW', 'QCf0_kW']
    screening_main(locator, weather_path, gv, output_parameters)

if __name__ == '__main__':
    run_as_script()