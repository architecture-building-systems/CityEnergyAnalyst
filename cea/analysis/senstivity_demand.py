# -*- coding: utf-8 -*-
"""
===========================
Sensitivity of demand_main.py

This script uses the morris algorithm (morris 1991)(campologo 2011) and Sobol Algorithm Sltalli 20110
to screen the most sensitive variables of a selection of parameters of the CEA.
Th morris method serves to basic screening o finput variables and it is base on OAT
The Sobol method serves for a complete sensitivity analysis of input vatiables. It is based on variance methods.

===========================

"""
from __future__ import division

from cea.demand import demand_main

import multiprocessing as mp
from SALib.analyze import sobol, morris
from SALib.sample.saltelli import sample as sampler_sobol
from SALib.sample.morris import sample as sampler_morris
import pandas as pd
import numpy as np
import time

# main
def sensitivity_main(locator, weather_path, gv, output_parameters, groups_var, num_samples, method):
    t0 = time.clock()

    #Model constants
    gv.multiprocessing = False # false to deactivate the multiprocessing in the demand algorithm
                               # multiprocessing will be activated in this algorithm.
    gv.resol = 'monthly'
    gv.output_type = 'sensitivity'

    #Define the model inputs
    for group in groups_var:
        variables = pd.read_excel(locator.get_uncertainty_db(), group)

    num_vars = variables.name.count() #integer with number of variables
    names = variables.name.values # [,,] with names of each variable
    bounds = []
    for var in range(num_vars):
        limits = [variables.loc[var,'min'],variables.loc[var,'max']]
        bounds.append(limits)

    #define the problem
    problem = {'num_vars': num_vars,'names': names, 'bounds': bounds, 'groups': None}

    #create samples (combinations of variables)
    if method is 'sobol':
        second_order = False
        samples = sampler_sobol(problem, N=num_samples, calc_second_order=second_order)
    else:
        grid = 2
        levels = 4
        optimal_trajects = int(0.04*num_samples)
        samples = sampler_morris(problem, N=num_samples, grid_jump=grid, num_levels=levels,
                                 optimal_trajectories=optimal_trajects, local_optimization=True)

    #call the CEA for building demand and store the results of every sample in a vector
    gv.log("Running %i samples" % len(samples))
    simulations = screening_cea_multiprocessing(samples, names, output_parameters, locator, weather_path, gv)

    #do morris analysis and output to excel
    buildings_num = simulations[0].shape[0]
    writer = pd.ExcelWriter(locator.get_sensitivity_output(method, num_samples))
    for parameter in output_parameters:
        results_1 = []
        results_2 = []
        results_3 = []
        for building in range(buildings_num):
            simulations_parameter = np.array([x.loc[building, parameter] for x in simulations])
            if method is 'sobol':
                sobol_result = sobol.analyze(problem, simulations_parameter, calc_second_order=second_order)
                results_1.append(sobol_result['S1'])
                results_2.append(sobol_result['ST'])
                results_3.append(sobol_result['ST_conf'])
            else:
                morris_result = morris.analyze(problem, samples, simulations_parameter, grid_jump=grid, num_levels=levels)
                results_1.append(morris_result['mu_star'])
                results_2.append(morris_result['sigma'])
                results_3.append(morris_result['mu_star_conf'])
        pd.DataFrame(results_1, columns = problem['names']).to_excel(writer,parameter+'S1')
        pd.DataFrame(results_2, columns=problem['names']).to_excel(writer, parameter+'ST')
        pd.DataFrame(results_3, columns=problem['names']).to_excel(writer, parameter + 'conf')

    writer.save()
    gv.log('Sensitivity Sobol method done - time elapsed: %(time_elapsed).2f seconds', time_elapsed=time.clock() - t0)

# function to call cea
def screening_cea_multiprocessing(samples, names, output_parameters, locator, weather_path, gv):
    pool = mp.Pool()
    gv.log("Using %i CPU's" % mp.cpu_count())
    joblist = [pool.apply_async(screening_cea, [counter, sample,  names, output_parameters, locator, weather_path, gv])
               for sample, counter in zip(samples, range(len(samples)))]
    results = [job.get() for job in joblist]
    # return in order
    results = sorted(results, key=lambda tup: tup[0])
    results = [x[1] for x in results]
    return results

def screening_cea(counter, sample,  var_names, output_parameters, locator, weather_path, gv):

    #create a dict with the new input vatiables form the sample and pass in gv
    gv.samples = dict(zip(var_names, sample))
    result = None
    while result is None:  # trick to avoid that arcgis stops calculating the days and tries again.
       try:
           result = demand_main.demand_calculation(locator, weather_path, gv)[output_parameters]
       except Exception, e:
           print e, result
           pass
    gv.log('Sample No. %s finished' %(counter+1))
    return (counter,result)

def run_as_script():
    import cea.globalvar as gv
    import cea.inputlocator as inputlocator
    gv = gv.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    weather_path = locator.get_default_weather()
    output_parameters = ['QHf_MWhyr', 'QCf_MWhyr', 'Ef_MWhyr', 'Total_MWhyr']
    method = 'sobol'
    groups_var =  ['THERMAL']
    num_samples = 1000 #generally 1000 or until it converges
    sensitivity_main(locator, weather_path, gv, output_parameters, groups_var, num_samples, method)

if __name__ == '__main__':
    run_as_script()