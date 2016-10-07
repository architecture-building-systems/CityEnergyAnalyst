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

import os

from cea import inputlocator
from cea.demand import demand_main

from SALib.analyze import morris
from SALib.sample.morris import sample as sampler
from geopandas import GeoDataFrame as gpdf
import pandas as pd
import numpy as np


# main
def screening_main(locator, weather_path, gv, output_parameters):

    # Define the model inputs
    variables = pd.read_excel(locator.get_uncertainty_db(), "THERMAL")
    num_vars = variables.name.count() #integer with number of variables
    names = variables.name.values # [,,] with names of each variable
    bounds = []
    for var in range(num_vars):
        limits = [variables.loc[var,'min'],variables.loc[var,'max']]
        bounds.append(limits)

    #define the problem
    problem = {'num_vars': num_vars,'names': names, 'bounds': bounds}
    #create samples (combinations of variables)
    samples = sampler(problem, N=1000, num_levels=4, grid_jump=2)

    print len(samples)
    #call the CEA for building demand and store the results of every sample in a vector
    simulations = np.empty([samples.shape[0]])
    for i, sample in enumerate(samples):
        simulations[i] = screening_cea(sample, names, output_parameters, locator, weather_path, gv)

    #do morris analysis
    for simulation in simulations:
        morris_results = morris.analyze(problem, samples, simulation, conf_level=0.95, print_to_console = True,
                            num_levels= 4, grid_jump = 2)
        #Si is adict with the keys "S1", "S2", "ST", "S1_conf", "S2_conf", and "ST_conf".
        #The _conf keys store the corresponding confidence intervals,

        for x in morris_results['ST']:
            variables['ST'] = x

    return variables #returns dict ranked

# function to call cea
def screening_cea(sample, names, output_parameters, locator, weather_path, gv):

    #put the sample in inputs of the CEA
    shifter(locator, sample, names)

    # totals of all buildings for the screening and selection of screening parameters
    totals = demand_main.demand_calculation(locator, weather_path, gv)[output_parameters]

    totals_output_parameters = np.empty([totals.shape[0]])
    for i, x in enumerate(totals):
        totals_output_parameters[i] = totals[x]

    return totals_output_parameters

#function to change input parameters in CEA
def shifter(locator, sample, names):
    print sample
    thermal = gpdf.from_file(locator.get_building_thermal())
    for i, j in zip(names,sample):
        thermal[i] = j
    thermal.to_file(locator.get_building_thermal())

def run_as_script():
    import cea.globalvar as gv
    import cea.inputlocator as inputlocator
    gv = gv.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = inputlocator.InputLocator(scenario_path=scenario_path)
    weather_path = locator.get_default_weather()
    output_parameters = ['Qhf_MWhyr', 'Qcf_MWhyr', 'Ef_MWhyr']
    screening_main(locator, weather_path, gv, output_parameters)

if __name__ == '__main__':
    run_as_script()