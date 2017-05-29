# coding=utf-8
"""Building retrofit potential analysis
"""

from __future__ import division

import multiprocessing as mp
import os

import pandas as pd
import time

import cea.globalvar
import cea.inputlocator
from cea.utilities import dbfreader

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas", "Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def age_filter_HVAC(age_df, delta_min_age):
    return age_df[(age_df.built <= delta_min_age) & (age_df.HVAC <= delta_min_age)].Name.values

def eui_filter_HVAC(demand, load, threshold):
    demand["eui"] = demand[load]/demand["Af_m2"]*1000
    return demand[(demand.eui >= threshold)].Name.values

def emissions_filter_HVAC(emissions, lca, threshold):
    emissions["emi"] = emissions[lca]/emissions["GFA_m2"]*1000
    return emissions[(emissions.emi >= threshold)].Name.values

def losses_filter_HVAC(demand, load_withlosses, load_enduse, threshold):
    def calc_filter(x,y):
        if (x and y) > 0:
            return ((x-y)/y)*100
        else:
            return 0

    demand["losses"] = demand.apply(lambda x: calc_filter(x[load_withlosses], x[load_enduse]), axis=1)
    return demand[(demand.losses >= threshold)].Name.values


def retrofit_main(locator_baseline, age_retrofit, age_crit, eui_crit, LCA_crit, op_costs_crit, losses_crit):


    selection_names =[] #list to store names of selected buildings to retrofit
    #CASE 1
    for criteria in age_crit:
        if criteria[0]:
            age_difference = age_retrofit - criteria[1]
            age_df = dbfreader.dbf2df(locator_baseline.get_building_age())
            selection_names.append(("Crit_age",age_filter_HVAC(age_df, age_difference)))

    #CASE 2
    for criteria in eui_crit:
        if criteria[0]:
            demand_totals = pd.read_csv(locator_baseline.get_total_demand())
            selection_names.append(("Crit_eui_"+criteria[1], eui_filter_HVAC(demand_totals, criteria[1],
                                                                             criteria[2])))

    #CASE 3
    for criteria in op_costs_crit:
        if criteria[0]:
            costs_totals = pd.read_csv(locator_baseline.get_costs_operation_file(criteria[1]))
            selection_names.append(("Crit_cost_"+criteria[1],emissions_filter_HVAC(costs_totals, criteria[1]+"_cost_m2",
                                                                           criteria[2])))

    # CASE 4
    for criteria in losses_crit:
        if criteria[0]:
            demand_totals = pd.read_csv(locator_baseline.get_total_demand())
            selection_names.append(("Crit_loss_"+criteria[1], losses_filter_HVAC(demand_totals, criteria[1],
                                                                         criteria[2],
                                                                         criteria[3])))
    #CASE 5
    for criteria in LCA_crit:
        if criteria[0]:
            emissions_totals = pd.read_csv(locator_baseline.get_lca_operation())
            selection_names.append(("Crit_ghg_tot",emissions_filter_HVAC(emissions_totals, criteria[1],
                                                                         criteria[2])))

    #appending all the resutls
    counter = 0
    for (x,b) in selection_names:
        if counter ==0:
            data = pd.DataFrame({"Name":b})
            data[x] = "TRUE"
        else:
            y = pd.DataFrame({"Name": b})
            y[x] = "TRUE"
            data = data.merge(y, on = "Name", how='outer')
        counter+=1

    # fill with FALSE for those buildings that do not comply the criteria
    data.fillna(value="FALSE", inplace=True)

    # Create a retrofit case with the buildings that
    retrofit_scenario_creator()
    #save results of filer
    data.to_csv(locator_baseline.get_retrofit_filters())

def retrofit_scenario_creator():
    """
    This creates a new retrofit scenario, based on the criteria we have selected as True
    :return:
    """

def run_as_script(scenario_path=None):
    gv = cea.globalvar.GlobalVariables()
    if scenario_path is None:
        scenario_path = gv.scenario_reference

    ## INPUTS
    locator_baseline = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    # for the interface it would be good if the default values where calculated as 2 standard deviations of

    # CRITERIA AGE
    age_retrofit = 2020  #[true or false, threshold]
    age_criteria = [True, 15] #[true or false, threshold]

    #CRITERIA UNERGY USE INTENSITY
    eui_heating_criteria = [True, "Qhsf_MWhyr", 50] #[true or false, load to verify, threshold]
    eui_hotwater_criteria = [True, "Qwwf_MWhyr", 50]  # [true or false, load to verify, threshold]
    eui_cooling_criteria = [True, "Qcsf_MWhyr", 4]  # [true or false, load to verify, threshold]
    eui_electricity_criteria = [False, "Ef_MWhyr", 20]  # [true or false, load to verify, threshold]

    #CRITERIA EMISSIONS
    emissions_operation_criteria = [False, "O_ghg_ton", 30] #[true or false, threshold]

    #CRITERIA COSTS
    heating_costs_criteria = [True, "Qhsf", 2] #[true or false, threshold]
    hotwater_costs_criteria = [True, "Qwwf", 2]  # [true or false, threshold]
    cooling_costs_criteria = [True, "Qcsf", 2]  # [true or false, threshold]
    electricity_costs_criteria = [False, "Ef", 2]  # [true or false, threshold]

    #CASE OF THERMAL LOSSES
    heating_losses_criteria = [True, "Qhsf_MWhyr", "Qhs_MWhyr", 15]  # [true or false, threshold]
    hotwater_losses_criteria = [True, "Qwwf_MWhyr", "Qww_MWhyr", 15]  # [true or false, threshold]
    cooling_losses_criteria = [True, "Qcsf_MWhyr", "Qcs_MWhyr", 15]   # [true or false, threshold]

    ##PROCESS
    age_crit = [age_criteria]
    eui_crit = [eui_heating_criteria, eui_hotwater_criteria, eui_cooling_criteria, eui_electricity_criteria]
    LCA_crit = [emissions_operation_criteria]
    op_costs_crit = [heating_costs_criteria, hotwater_costs_criteria, cooling_costs_criteria, electricity_costs_criteria]
    losses_crit = [heating_losses_criteria, hotwater_losses_criteria, cooling_losses_criteria]
    retrofit_main(locator_baseline=locator_baseline,age_retrofit=age_retrofit, age_crit=age_crit, eui_crit=eui_crit,
                  LCA_crit=LCA_crit,
                  op_costs_crit=op_costs_crit, losses_crit=losses_crit)



if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder')
    args = parser.parse_args()

    run_as_script(scenario_path=args.scenario)