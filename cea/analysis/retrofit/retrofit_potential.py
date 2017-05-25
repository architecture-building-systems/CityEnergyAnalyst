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

def eui_filter_HVAC(demand, load, threshold, ):
    demand["eui"] = demand[load]/demand["Af_m2"]*1000
    return demand[(demand.eui >= threshold)].Name.values

def emissions_filter_HVAC(emissions, lca, threshold, ):
    emissions["emi"] = emissions[lca]/emissions["GFA_m2"]*1000
    return emissions[(emissions.emi >= threshold)].Name.values

def retrofit_main(locator_baseline, age_retrofit, age_criteria, eui_heating_criteria,
                  eui_hotwater_criteria, eui_cooling_criteria, emissions_criteria,
                  heating_cooling_costs_criteria):

    selection_names =[] #list to store names of selected buildings to retrofit

    #CASE 1:
    if age_criteria[0]:
        age_difference = age_retrofit - age_criteria[1]
        age_df = dbfreader.dbf2df(locator_baseline.get_building_age())
        selection_names.extend(age_filter_HVAC(age_df, age_difference))

    #CASE 2.1:
    if eui_heating_criteria[0]:
        demand_totals = pd.read_csv(locator_baseline.get_total_demand())
        selection_names.extend(eui_filter_HVAC(demand_totals, eui_heating_criteria[1], eui_heating_criteria[2]))

    # CASE 2.2:
    if eui_hotwater_criteria[0]:
        demand_totals = pd.read_csv(locator_baseline.get_total_demand())
        selection_names.extend(eui_filter_HVAC(demand_totals, eui_hotwater_criteria[1], eui_hotwater_criteria[2]))

    # CASE 2.2:
    if eui_cooling_criteria[0]:
        demand_totals = pd.read_csv(locator_baseline.get_total_demand())
        selection_names.extend(eui_filter_HVAC(demand_totals, eui_cooling_criteria[1], eui_cooling_criteria[2]))

    # CASE 3:
    if emissions_criteria[0]:
        emissions_totals = pd.read_csv(locator_baseline.get_lca_operation())
        selection_names.extend(eui_filter_HVAC(emissions_totals, emissions_criteria[1], emissions_criteria[2]))

    if heating_cooling_costs_criteria[0]:

    print selection_names

def run_as_script(scenario_path=None):
    gv = cea.globalvar.GlobalVariables()
    if scenario_path is None:
        scenario_path = gv.scenario_reference

    age_retrofit = 2020  #[true or false, threshold]
    age_criteria = [True, 15] #[true or false, threshold]
    eui_heating_criteria = [True, "Qhsf_MWhyr", 220] #[true or false, load to verify, threshold]
    eui_hotwater_criteria = [True, "Qwwf_MWhyr", 40]  # [true or false, load to verify, threshold]
    eui_cooling_criteria = [True, "Qcsf_MWhyr", 100]  # [true or false, load to verify, threshold]
    emissions_operation_criteria = [True, "O_ghg_ton", 30] #[true or false, threshold]
    heating_cooling_costs_criteria = [True, 0.2] #[true or false, threshold]
    locator_baseline = cea.inputlocator.InputLocator(scenario_path=scenario_path)

    retrofit_main(locator_baseline=locator_baseline,age_retrofit=age_retrofit, age_criteria=age_criteria,
                  eui_heating_criteria=eui_heating_criteria, eui_cooling_criteria=eui_cooling_criteria,
                  eui_hotwater_criteria = eui_hotwater_criteria,
                  emissions_criteria=emissions_operation_criteria,
                  heating_cooling_costs_criteria=heating_cooling_costs_criteria,
                  )

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder')
    args = parser.parse_args()

    run_as_script(scenario_path=args.scenario)