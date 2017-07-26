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


def eui_filter_HVAC(demand, variable_name, threshold, column_suffix='_MWhyr'):
    demand["eui"] = demand[variable_name + column_suffix] / demand["Af_m2"] * 1000
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


def retrofit_main(locator_baseline, name_new_scenario, keep_partial_matches,
                  age_retrofit=None,
                  age_criteria=None,
                  eui_heating_criteria=None,
                  eui_hotwater_criteria=None,
                  eui_cooling_criteria=None,
                  eui_electricity_criteria=None,
                  heating_costs_criteria=None,
                  hotwater_costs_criteria=None,
                  cooling_costs_criteria=None,
                  electricity_costs_criteria=None,
                  heating_losses_criteria=None,
                  hotwater_losses_criteria=None,
                  cooling_losses_criteria=None,
                  emissions_operation_criteria=None):
    selection_names = []  # list to store names of selected buildings to retrofit


    #load databases and select only buildings in geometry
    #geometry
    geometry_df = gdf.from_file(locator_baseline.get_zone_geometry())
    names = geometry_df['Name'].values
    #age
    age = dbfreader.dbf_to_dataframe(locator_baseline.get_building_age())
    age = age.loc[age['Name'].isin(names)]

    architecture = dbfreader.dbf_to_dataframe(locator_baseline.get_building_architecture())
    architecture = architecture.loc[architecture['Name'].isin(names)]

    comfort = dbfreader.dbf_to_dataframe(locator_baseline.get_building_comfort())
    comfort = comfort.loc[comfort['Name'].isin(names)]

    internal_loads = dbfreader.dbf_to_dataframe(locator_baseline.get_building_internal())
    internal_loads = internal_loads.loc[internal_loads['Name'].isin(names)]

    hvac = dbfreader.dbf_to_dataframe(locator_baseline.get_building_hvac())
    hvac = hvac.loc[hvac['Name'].isin(names)]

    supply = dbfreader.dbf_to_dataframe(locator_baseline.get_building_supply())
    supply = supply.loc[supply['Name'].isin(names)]

    occupancy = dbfreader.dbf_to_dataframe(locator_baseline.get_building_occupancy())
    occupancy = occupancy.loc[occupancy['Name'].isin(names)]


    # CASE 1
    age_crit = [["age", age_criteria]]
    for criteria_name, criteria_threshold in age_crit:
        if criteria_threshold is not None:
            age_difference = age_retrofit - criteria_threshold
            selection_names.append(("Crit_" + criteria_name, age_filter_HVAC(age, age_difference)))

    # CASE 2
    eui_crit = [["Qhsf", eui_heating_criteria],
                ["Qwwf", eui_hotwater_criteria],
                ["Qcsf", eui_cooling_criteria],
                ["Ef", eui_electricity_criteria]]
    for criteria_name, criteria_threshold in eui_crit:
        if criteria_threshold is not None:
            demand_totals = pd.read_csv(locator_baseline.get_total_demand())
            selection_names.append(
                ("c_eui_" + criteria_name, eui_filter_HVAC(demand_totals, criteria_name, criteria_threshold)))

    # CASE 3
    op_costs_crit = [["Qhsf", heating_costs_criteria],
                     ["Qwwf", hotwater_costs_criteria],
                     ["Qcsf", cooling_costs_criteria],
                     ["Ef", electricity_costs_criteria]]
    for criteria_name, criteria_threshold in op_costs_crit:
        if criteria_threshold is not None:
            costs_totals = pd.read_csv(locator_baseline.get_costs_operation_file(criteria_name))
            selection_names.append(
                ("c_cost_" + criteria_name, emissions_filter_HVAC(costs_totals, criteria_name + "_cost_m2",
                                                                  criteria_threshold)))

    # CASE 4
    losses_crit = [["Qhsf", "Qhsf_MWhyr", "Qhs_MWhyr", heating_losses_criteria],
                   ["Qwwf", "Qwwf_MWhyr", "Qww_MWhyr", hotwater_losses_criteria],
                   ["Qcsf", "Qcsf_MWhyr", "Qcs_MWhyr", cooling_losses_criteria]]
    for criteria_name, load_with_losses, load_end_use, criteria_threshold in losses_crit:
        if criteria_threshold is not None:
            demand_totals = pd.read_csv(locator_baseline.get_total_demand())
            selection_names.append(("c_loss_" + criteria_name,
                                    losses_filter_HVAC(demand_totals, load_with_losses, load_end_use,
                                                       criteria_threshold)))
    # CASE 5
    LCA_crit = [["ghg", "O_ghg_ton", emissions_operation_criteria]]
    for criteria_name, lca_name, criteria_threshold in LCA_crit:
        if criteria_threshold is not None:
            emissions_totals = pd.read_csv(locator_baseline.get_lca_operation())
            selection_names.append(
                ("c_" + criteria_name, emissions_filter_HVAC(emissions_totals, lca_name, criteria_threshold)))

    # appending all the results
    if keep_partial_matches:
        type_of_join = "outer"
    else:
        type_of_join = "inner"
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

    data.fillna(value="FALSE", inplace=True)
    if data.empty and (keep_partial_matches==False):
        raise ValueError("There is not a single building matching all selected criteria,"
                         "try to keep those buildings that partially match the criteria")

    # Create a retrofit case with the buildings that pass the criteria
    retrofit_scenario_path = os.path.join(locator_baseline.get_project_path(), name_new_scenario)
    locator_retrofit = cea.inputlocator.InputLocator(scenario_path=retrofit_scenario_path)
    retrofit_scenario_creator(locator_baseline, locator_retrofit, geometry_df, age, architecture, internal_loads, comfort, hvac,
                              supply, occupancy, data, type_of_join)

def retrofit_scenario_creator(locator_baseline, locator_retrofit, geometry_df, age, architecture, internal_loads, comfort, hvac,
                              supply, occupancy, data, keep_partial_matches):
    """
    This creates a new retrofit scenario, based on the criteria we have selected as True
    :return:
    """

    #confirm that the builings selected are part of the zone

    new_geometry = geometry_df.merge(data, on='Name')
    if new_geometry.empty and keep_partial_matches:
        raise ValueError("The keep partial matches flag is on, Still, there is not a single building matching any of "
                         "the criteria, please try other criteria / thresholds instead")


    new_geometry.to_file(locator_retrofit.get_zone_geometry(), driver='ESRI Shapefile')
    district = gdf.from_file(locator_baseline.get_district_geometry())
    district.to_file(locator_retrofit.get_district_geometry())
    dbfreader.dataframe_to_dbf(age.merge(data, on='Name'), locator_retrofit.get_building_age())
    dbfreader.dataframe_to_dbf(architecture.merge(data, on='Name'), locator_retrofit.get_building_architecture())
    dbfreader.dataframe_to_dbf(comfort.merge(data, on='Name'), locator_retrofit.get_building_comfort())
    dbfreader.dataframe_to_dbf(internal_loads.merge(data, on='Name'), locator_retrofit.get_building_internal())
    dbfreader.dataframe_to_dbf(hvac.merge(data, on='Name'), locator_retrofit.get_building_hvac())
    dbfreader.dataframe_to_dbf(supply.merge(data, on='Name'), locator_retrofit.get_building_supply())
    dbfreader.dataframe_to_dbf(occupancy.merge(data, on='Name'), locator_retrofit.get_building_occupancy())
    shutil.copy2(locator_baseline.get_terrain(), locator_retrofit.get_terrain())


def run_as_script(scenario_path=None):
    gv = cea.globalvar.GlobalVariables()
    if scenario_path is None:
        scenario_path = gv.scenario_reference

    # INPUTS
    locator_baseline = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    # for the interface it would be good if the default values where calculated as 2 standard deviations of

    # FLAGS
    keep_partial_matches = True # keep buildings that attained one or more of the criteria

    # CRITERIA AGE
    name_new_scenario = "retrofit_HVAC"
    age_retrofit = 2020  # [true or false, threshold]
    age_criteria = 15  # [years] threshold age of HVAC (built / retrofitted)

    # CRITERIA ENERGY USE INTENSITY
    eui_heating_criteria = 150  # load to verify, threshold
    eui_hotwater_criteria = 50  # load to verify
    eui_cooling_criteria = 4  # load to verify, threshold
    eui_electricity_criteria = 20  # load to verify, threshold
    #
    # # CRITERIA EMISSIONS
    emissions_operation_criteria = 30  # threshold
    #
    # # CRITERIA COSTS
    heating_costs_criteria = 2  # threshold
    hotwater_costs_criteria = 2  # threshold
    cooling_costs_criteria = 2  # threshold
    electricity_costs_criteria = 2  # threshold
    #
    # # CASE OF THERMAL LOSSES
    heating_losses_criteria = 15  # threshold
    hotwater_losses_criteria = 15  # threshold
    cooling_losses_criteria = 15  # threshold

    # PROCESS
    retrofit_main(locator_baseline=locator_baseline, name_new_scenario=name_new_scenario,
                  keep_partial_matches=keep_partial_matches,
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
