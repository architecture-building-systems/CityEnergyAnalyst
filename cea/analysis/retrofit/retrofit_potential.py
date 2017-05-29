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


def retrofit_main(locator_baseline, age_retrofit, age_criteria, eui_heating_criteria,
                  eui_hotwater_criteria, eui_cooling_criteria, eui_electricity_criteria, emissions_criteria,
                  heating_costs_criteria, hotwater_costs_criteria, cooling_costs_criteria,
                  electricity_costs_criteria, heating_losses_criteria,
                  hotwater_losses_criteria,
                  cooling_losses_criteria):

    selection_names =[] #list to store names of selected buildings to retrofit

    #CASE 1:
    if age_criteria[0]:
        age_difference = age_retrofit - age_criteria[1]
        age_df = dbfreader.dbf2df(locator_baseline.get_building_age())
        selection_names.append(("Crit_age",age_filter_HVAC(age_df, age_difference)))

    #CASE 2.1:
    if eui_heating_criteria[0]:
        demand_totals = pd.read_csv(locator_baseline.get_total_demand())
        selection_names.append(("Crit_eui_Qhsf", eui_filter_HVAC(demand_totals, eui_heating_criteria[1],
                                                          eui_heating_criteria[2])))

    # CASE 2.2:
    if eui_hotwater_criteria[0]:
        demand_totals = pd.read_csv(locator_baseline.get_total_demand())
        selection_names.append(("Crit_eui_Qwwf",eui_filter_HVAC(demand_totals, eui_hotwater_criteria[1],
                                                         eui_hotwater_criteria[2])))

    # CASE 2.3:
    if eui_cooling_criteria[0]:
        demand_totals = pd.read_csv(locator_baseline.get_total_demand())
        selection_names.append(("Crit_eui_Qcsf",eui_filter_HVAC(demand_totals, eui_cooling_criteria[1],
                                                         eui_cooling_criteria[2])))

    # CASE 2.4:
    if eui_electricity_criteria[0]:
        demand_totals = pd.read_csv(locator_baseline.get_total_demand())
        selection_names.append(("Crit_eui_Ef",eui_filter_HVAC(demand_totals, eui_electricity_criteria[1],
                                                         eui_electricity_criteria[2])))

    # CASE 3:
    if emissions_criteria[0]:
        emissions_totals = pd.read_csv(locator_baseline.get_lca_operation())
        selection_names.append(("Crit_ghg_tot",emissions_filter_HVAC(emissions_totals, emissions_criteria[1],
                                                               emissions_criteria[2])))

    #CASE 4.1
    if heating_costs_criteria[0]:
        costs_totals = pd.read_csv(locator_baseline.get_costs_operation_file(heating_costs_criteria[1]))
        selection_names.append(("Crit_cost_Qhsf",emissions_filter_HVAC(costs_totals, heating_costs_criteria[1]+"_cost_m2",
                                                     heating_costs_criteria[2])))

    #CASE 4.2
    if hotwater_costs_criteria[0]:
        costs_totals = pd.read_csv(locator_baseline.get_costs_operation_file(hotwater_costs_criteria[1]))
        selection_names.append(("Crit_cost_Qwwf",emissions_filter_HVAC(costs_totals, hotwater_costs_criteria[1]+"_cost_m2",
                                                     hotwater_costs_criteria[2])))

    #CASE 4.3
    if cooling_costs_criteria[0]:
        costs_totals = pd.read_csv(locator_baseline.get_costs_operation_file(cooling_costs_criteria[1]))
        selection_names.append(("Crit_cost_Qcsf",emissions_filter_HVAC(costs_totals, cooling_costs_criteria[1]+"_cost_m2",
                                                     cooling_costs_criteria[2])))

    #CASE 4.4
    if electricity_costs_criteria[0]:
        costs_totals = pd.read_csv(locator_baseline.get_costs_operation_file(electricity_costs_criteria[1]))
        selection_names.append(("Crit_cost_Ef",emissions_filter_HVAC(costs_totals, electricity_costs_criteria[1]+"_cost_m2",
                                                     electricity_costs_criteria[2])))

    #CASE 5.1
    if heating_losses_criteria:
        demand_totals = pd.read_csv(locator_baseline.get_total_demand())
        selection_names.append(("Crit_loss_Qhsf", losses_filter_HVAC(demand_totals, heating_losses_criteria[1],
                                                                     heating_losses_criteria[2],
                                                                     heating_losses_criteria[3])))
    if hotwater_losses_criteria:
        demand_totals = pd.read_csv(locator_baseline.get_total_demand())
        selection_names.append(("Crit_loss_Qwwf", losses_filter_HVAC(demand_totals, hotwater_losses_criteria[1],
                                                                     hotwater_losses_criteria[2],
                                                                     hotwater_losses_criteria[3])))
    if cooling_losses_criteria:
        demand_totals = pd.read_csv(locator_baseline.get_total_demand())
        selection_names.append(("Crit_loss_Qcsf", losses_filter_HVAC(demand_totals, cooling_losses_criteria[1],
                                                                     cooling_losses_criteria[2],
                                                                     cooling_losses_criteria[3])))

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

    #save results of filer
    data.to_csv(locator_baseline.get_retrofit_filters())


def run_as_script(scenario_path=None):
    gv = cea.globalvar.GlobalVariables()
    if scenario_path is None:
        scenario_path = gv.scenario_reference

    # for the interface it would be good if the default values where calculated as 2 standard deviations of
    #the case study.
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


    locator_baseline = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    retrofit_main(locator_baseline=locator_baseline,age_retrofit=age_retrofit, age_criteria=age_criteria,
                  eui_heating_criteria=eui_heating_criteria, eui_cooling_criteria=eui_cooling_criteria,
                  eui_hotwater_criteria = eui_hotwater_criteria,
                  eui_electricity_criteria=eui_electricity_criteria,
                  emissions_criteria=emissions_operation_criteria,
                  heating_costs_criteria=heating_costs_criteria,
                  hotwater_costs_criteria=hotwater_costs_criteria,
                  cooling_costs_criteria=cooling_costs_criteria,
                  electricity_costs_criteria=electricity_costs_criteria,
                  heating_losses_criteria=heating_losses_criteria,
                  hotwater_losses_criteria=hotwater_losses_criteria,
                  cooling_losses_criteria=cooling_losses_criteria)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder')
    args = parser.parse_args()

    run_as_script(scenario_path=args.scenario)