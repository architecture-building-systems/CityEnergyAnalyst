# coding=utf-8
"""Building retrofit potential analysis
"""

from __future__ import division

import shutil
import os

import pandas as pd

import cea.globalvar
import cea.inputlocator
from geopandas import GeoDataFrame as gdf
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
    demand["eui"] = demand[load] / demand["Af_m2"] * 1000
    return demand[(demand.eui >= threshold)].Name.values


def emissions_filter_HVAC(emissions, lca, threshold):
    emissions["emi"] = emissions[lca] / emissions["GFA_m2"] * 1000
    return emissions[(emissions.emi >= threshold)].Name.values


def losses_filter_HVAC(demand, load_withlosses, load_enduse, threshold):
    def calc_filter(load_losses, load):
        if (load_losses > 0) and (load > 0):
            return ((load_losses - load) / load) * 100
        else:
            return 0

    demand["losses"] = demand.apply(lambda x: calc_filter(x[load_withlosses], x[load_enduse]), axis=1)
    return demand[(demand.losses >= threshold)].Name.values


def retrofit_main(locator_baseline, name_new_scenario, select_only_all_criteria,
                  age_retrofit,
                  age_criteria,
                  eui_heating_criteria,
                  eui_hotwater_criteria,
                  eui_cooling_criteria,
                  eui_electricity_criteria,
                  heating_costs_criteria,
                  hotwater_costs_criteria,
                  cooling_costs_criteria,
                  electricity_costs_criteria,
                  heating_losses_criteria,
                  hotwater_losses_criteria,
                  cooling_losses_criteria,
                  emissions_operation_criteria):

    selection_names = []  # list to store names of selected buildings to retrofit
    # CASE 1


    age_crit = [["age", age_criteria]]
    for criteria in age_crit:
        if criteria[1][0]:
            age_difference = age_retrofit - criteria[1][1]
            age_df = dbfreader.dbf2df(locator_baseline.get_building_age())
            selection_names.append(("Crit_" + criteria[0], age_filter_HVAC(age_df, age_difference)))

    # CASE 2
    eui_crit = [["Qhsf", "Qhsf_MWhyr", eui_heating_criteria],
                ["Qwwf", "Qwwf_MWhyr", eui_hotwater_criteria],
                ["Qcsf", "Qcsf_MWhyr", eui_cooling_criteria],
                ["Ef", "Ef_MWhyr", eui_electricity_criteria]]
    for criteria in eui_crit:
        if criteria[2][0]:
            demand_totals = pd.read_csv(locator_baseline.get_total_demand())
            selection_names.append(
                ("c_eui_" + criteria[0], eui_filter_HVAC(demand_totals, criteria[1], criteria[2][1])))

    # CASE 3
    op_costs_crit = [["Qhsf", heating_costs_criteria],
                     ["Qwwf", hotwater_costs_criteria],
                     ["Qcsf", cooling_costs_criteria],
                     ["Ef", electricity_costs_criteria]]
    for criteria in op_costs_crit:
        if criteria[1][0]:
            costs_totals = pd.read_csv(locator_baseline.get_costs_operation_file(criteria[0]))
            selection_names.append(
                ("c_cost_" + criteria[0], emissions_filter_HVAC(costs_totals, criteria[0] + "_cost_m2",
                                                                   criteria[1][1])))

    # CASE 4
    losses_crit = [["Qhsf", "Qhsf_MWhyr", "Qhs_MWhyr", heating_losses_criteria],
                    ["Qwwf", "Qwwf_MWhyr", "Qww_MWhyr", hotwater_losses_criteria],
                    ["Qcsf", "Qcsf_MWhyr", "Qcs_MWhyr", cooling_losses_criteria]]
    for criteria in losses_crit:
        if criteria[3][0]:
            demand_totals = pd.read_csv(locator_baseline.get_total_demand())
            selection_names.append(("c_loss_" + criteria[0], losses_filter_HVAC(demand_totals, criteria[1],
                                                                                   criteria[2],
                                                                                   criteria[3][1])))
    # CASE 5
    LCA_crit = [["ghg", "O_ghg_ton", emissions_operation_criteria]]
    for criteria in LCA_crit:
        if criteria[1][0]:
            emissions_totals = pd.read_csv(locator_baseline.get_lca_operation())
            selection_names.append(("c_" + criteria[0], emissions_filter_HVAC(emissions_totals, criteria[1],
                                                                                 criteria[2][1])))

    # appending all the results
    if select_only_all_criteria:
        type_of_join = "inner"
    else:
        type_of_join = "outer"
    counter = 0
    for (criteria, list_true_values) in selection_names:
        if counter == 0:
            data = pd.DataFrame({"Name": list_true_values})
            data[criteria] = "TRUE"
        else:
            y = pd.DataFrame({"Name": list_true_values})
            y[criteria] = "TRUE"
            data = data.merge(y, on="Name", how=type_of_join)
        counter += 1

    # fill with FALSE for those buildings that do not comply the criteria
    data.fillna(value="FALSE", inplace=True)

    # Create a retrofit case with the buildings that pass the criteria
    retrofit_scenario_creator(locator_baseline.scenario_path,
                              os.path.join(locator_baseline.get_project_path(), name_new_scenario),
                              data)


def retrofit_scenario_creator(src, dst, data, symlinks=False, ignore=None):
    """
    This creates a new retrofit scenario, based on the criteria we have selected as True
    :return:
    """

    # Create new folder and trow error if already existing
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks, ignore)

    # Get locator
    locator_new_scenario = cea.inputlocator.InputLocator(scenario_path=dst)

    # Import properties buildings and export just selected buildings + criteria

    geometry = gdf.from_file(locator_new_scenario.get_building_geometry())
    geometry.merge(data, on='Name').to_file(locator_new_scenario.get_building_geometry())

    age = dbfreader.dbf2df(locator_new_scenario.get_building_age())
    dbfreader.df2dbf(age.merge(data, on='Name'), locator_new_scenario.get_building_age())

    architecture = dbfreader.dbf2df(locator_new_scenario.get_building_architecture())
    dbfreader.df2dbf(architecture.merge(data, on='Name'), locator_new_scenario.get_building_architecture())

    comfort = dbfreader.dbf2df(locator_new_scenario.get_building_comfort())
    dbfreader.df2dbf(comfort.merge(data, on='Name'), locator_new_scenario.get_building_comfort())

    internal_loads = dbfreader.dbf2df(locator_new_scenario.get_building_internal())
    dbfreader.df2dbf(internal_loads.merge(data, on='Name'), locator_new_scenario.get_building_internal())

    hvac = dbfreader.dbf2df(locator_new_scenario.get_building_hvac())
    dbfreader.df2dbf(hvac.merge(data, on='Name'), locator_new_scenario.get_building_hvac())

    supply = dbfreader.dbf2df(locator_new_scenario.get_building_supply())
    dbfreader.df2dbf(supply.merge(data, on='Name'), locator_new_scenario.get_building_supply())

    occupancy = dbfreader.dbf2df(locator_new_scenario.get_building_occupancy())
    dbfreader.df2dbf(occupancy.merge(data, on='Name'), locator_new_scenario.get_building_occupancy())


def run_as_script(scenario_path=None):
    gv = cea.globalvar.GlobalVariables()
    if scenario_path is None:
        scenario_path = gv.scenario_reference

    # INPUTS
    locator_baseline = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    # for the interface it would be good if the default values where calculated as 2 standard deviations of

    # FLAGS
    select_only_all_criteria = False  # keep only buildings that attain all the criteria simultaneously?

    # CRITERIA AGE
    name_new_scenario = "retrofit_HVAC"
    age_retrofit = 2020  # [true or false, threshold]
    age_criteria = [True, 15]  # [true or false, threshold]

    # CRITERIA ENERGY USE INTENSITY
    eui_heating_criteria = [True, 50]  # [true or false, load to verify, threshold]
    eui_hotwater_criteria = [True, 50]  # [true or false, load to verify, threshold]
    eui_cooling_criteria = [True, 4]  # [true or false, load to verify, threshold]
    eui_electricity_criteria = [True, 20]  # [true or false, load to verify, threshold]

    # CRITERIA EMISSIONS
    emissions_operation_criteria = [True, 30]  # [true or false, threshold]

    # CRITERIA COSTS
    heating_costs_criteria = [True, 2]  # [true or false, threshold]
    hotwater_costs_criteria = [True, 2]  # [true or false, threshold]
    cooling_costs_criteria = [True, 2]  # [true or false, threshold]
    electricity_costs_criteria = [True, 2]  # [true or false, threshold]

    # CASE OF THERMAL LOSSES
    heating_losses_criteria = [True, 15]  # [true or false, threshold]
    hotwater_losses_criteria = [True, 15]  # [true or false, threshold]
    cooling_losses_criteria = [True, 15]  # [true or false, threshold]

    # PROCESS
    retrofit_main(locator_baseline=locator_baseline, select_only_all_criteria=select_only_all_criteria,
                  name_new_scenario=name_new_scenario,
                  age_retrofit=age_retrofit,
                  age_criteria=age_criteria,
                  eui_heating_criteria=eui_heating_criteria,
                  eui_hotwater_criteria=eui_hotwater_criteria,
                  eui_cooling_criteria=eui_cooling_criteria,
                  eui_electricity_criteria=eui_electricity_criteria,
                  heating_costs_criteria=heating_costs_criteria,
                  hotwater_costs_criteria=hotwater_costs_criteria,
                  cooling_costs_criteria=cooling_costs_criteria,
                  electricity_costs_criteria=electricity_costs_criteria,
                  heating_losses_criteria=heating_losses_criteria,
                  hotwater_losses_criteria=hotwater_losses_criteria,
                  cooling_losses_criteria=cooling_losses_criteria,
                  emissions_operation_criteria=emissions_operation_criteria)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder')
    args = parser.parse_args()

    run_as_script(scenario_path=args.scenario)
