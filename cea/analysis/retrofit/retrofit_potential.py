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
from cea.utilities import dbf

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


def retrofit_main(locator_baseline, retrofit_scenario_name, keep_partial_matches,
                  retrofit_target_year=None,
                  age_threshold=None,
                  eui_heating_threshold=None,
                  eui_hot_water_threshold=None,
                  eui_cooling_threshold=None,
                  eui_electricity_threshold=None,
                  heating_costs_threshold=None,
                  hot_water_costs_threshold=None,
                  cooling_costs_threshold=None,
                  electricity_costs_threshold=None,
                  heating_losses_threshold=None,
                  hot_water_losses_threshold=None,
                  cooling_losses_threshold=None,
                  emissions_operation_threshold=None):
    selection_names = []  # list to store names of selected buildings to retrofit


    #load databases and select only buildings in geometry
    #geometry
    geometry_df = gdf.from_file(locator_baseline.get_zone_geometry())
    zone_building_names = locator_baseline.get_zone_building_names()
    #age
    age = dbf.dbf_to_dataframe(locator_baseline.get_building_age())
    age = age.loc[age['Name'].isin(zone_building_names)]

    architecture = dbf.dbf_to_dataframe(locator_baseline.get_building_architecture())
    architecture = architecture.loc[architecture['Name'].isin(zone_building_names)]

    comfort = dbf.dbf_to_dataframe(locator_baseline.get_building_comfort())
    comfort = comfort.loc[comfort['Name'].isin(zone_building_names)]

    internal_loads = dbf.dbf_to_dataframe(locator_baseline.get_building_internal())
    internal_loads = internal_loads.loc[internal_loads['Name'].isin(zone_building_names)]

    hvac = dbf.dbf_to_dataframe(locator_baseline.get_building_hvac())
    hvac = hvac.loc[hvac['Name'].isin(zone_building_names)]

    supply = dbf.dbf_to_dataframe(locator_baseline.get_building_supply())
    supply = supply.loc[supply['Name'].isin(zone_building_names)]

    occupancy = dbf.dbf_to_dataframe(locator_baseline.get_building_occupancy())
    occupancy = occupancy.loc[occupancy['Name'].isin(zone_building_names)]


    # CASE 1
    age_crit = [["age", age_threshold]]
    for criteria_name, criteria_threshold in age_crit:
        if criteria_threshold is not None:
            age_difference = retrofit_target_year - criteria_threshold
            selection_names.append(("Crit_" + criteria_name, age_filter_HVAC(age, age_difference)))

    # CASE 2
    eui_crit = [["Qhsf", eui_heating_threshold],
                ["Qwwf", eui_hot_water_threshold],
                ["Qcsf", eui_cooling_threshold],
                ["Ef", eui_electricity_threshold]]
    for criteria_name, criteria_threshold in eui_crit:
        if criteria_threshold is not None:
            demand_totals = pd.read_csv(locator_baseline.get_total_demand())
            selection_names.append(
                ("c_eui_" + criteria_name, eui_filter_HVAC(demand_totals, criteria_name, criteria_threshold)))

    # CASE 3
    op_costs_crit = [["Qhsf", heating_costs_threshold],
                     ["Qwwf", hot_water_costs_threshold],
                     ["Qcsf", cooling_costs_threshold],
                     ["Ef", electricity_costs_threshold]]
    for criteria_name, criteria_threshold in op_costs_crit:
        if criteria_threshold is not None:
            costs_totals = pd.read_csv(locator_baseline.get_costs_operation_file(criteria_name))
            selection_names.append(
                ("c_cost_" + criteria_name, emissions_filter_HVAC(costs_totals, criteria_name + "_cost_m2",
                                                                  criteria_threshold)))

    # CASE 4
    losses_crit = [["Qhsf", "Qhsf_MWhyr", "Qhs_MWhyr", heating_losses_threshold],
                   ["Qwwf", "Qwwf_MWhyr", "Qww_MWhyr", hot_water_losses_threshold],
                   ["Qcsf", "Qcsf_MWhyr", "Qcs_MWhyr", cooling_losses_threshold]]
    for criteria_name, load_with_losses, load_end_use, criteria_threshold in losses_crit:
        if criteria_threshold is not None:
            demand_totals = pd.read_csv(locator_baseline.get_total_demand())
            selection_names.append(("c_loss_" + criteria_name,
                                    losses_filter_HVAC(demand_totals, load_with_losses, load_end_use,
                                                       criteria_threshold)))
    # CASE 5
    LCA_crit = [["ghg", "O_ghg_ton", emissions_operation_threshold]]
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
    retrofit_scenario_path = os.path.join(locator_baseline.get_project_path(), retrofit_scenario_name)
    locator_retrofit = cea.inputlocator.InputLocator(scenario=retrofit_scenario_path)
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
    dbf.dataframe_to_dbf(age.merge(data, on='Name'), locator_retrofit.get_building_age())
    dbf.dataframe_to_dbf(architecture.merge(data, on='Name'), locator_retrofit.get_building_architecture())
    dbf.dataframe_to_dbf(comfort.merge(data, on='Name'), locator_retrofit.get_building_comfort())
    dbf.dataframe_to_dbf(internal_loads.merge(data, on='Name'), locator_retrofit.get_building_internal())
    dbf.dataframe_to_dbf(hvac.merge(data, on='Name'), locator_retrofit.get_building_hvac())
    dbf.dataframe_to_dbf(supply.merge(data, on='Name'), locator_retrofit.get_building_supply())
    dbf.dataframe_to_dbf(occupancy.merge(data, on='Name'), locator_retrofit.get_building_occupancy())
    shutil.copy2(locator_baseline.get_terrain(), locator_retrofit.get_terrain())


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator_baseline = cea.inputlocator.InputLocator(scenario=config.scenario)

    print("Running retrofit-potential for scenario = %s" % config.scenario)
    print('Running retrofit-potential with hot-water-costs-threshold = %s' % config.retrofit_potential.hot_water_costs_threshold)
    print('Running retrofit-potential with age-threshold = %s' % config.retrofit_potential.age_threshold)
    print('Running retrofit-potential with emissions-operation-threshold = %s' % config.retrofit_potential.emissions_operation_threshold)
    print('Running retrofit-potential with eui-electricity-threshold = %s' % config.retrofit_potential.eui_electricity_threshold)
    print('Running retrofit-potential with heating-costs-threshold = %s' % config.retrofit_potential.heating_costs_threshold)
    print('Running retrofit-potential with eui-hot-water-threshold = %s' % config.retrofit_potential.eui_hot_water_threshold)
    print('Running retrofit-potential with electricity-costs-threshold = %s' % config.retrofit_potential.electricity_costs_threshold)
    print('Running retrofit-potential with heating-losses-threshold = %s' % config.retrofit_potential.heating_losses_threshold)
    print('Running retrofit-potential with cooling-losses-threshold = %s' % config.retrofit_potential.cooling_losses_threshold)
    print('Running retrofit-potential with keep-partial-matches = %s' % config.retrofit_potential.keep_partial_matches)
    print('Running retrofit-potential with retrofit-target-year = %s' % config.retrofit_potential.retrofit_target_year)
    print('Running retrofit-potential with eui-cooling-threshold = %s' % config.retrofit_potential.eui_cooling_threshold)
    print('Running retrofit-potential with hot-water-losses-threshold = %s' % config.retrofit_potential.hot_water_losses_threshold)
    print('Running retrofit-potential with eui-heating-threshold = %s' % config.retrofit_potential.eui_heating_threshold)
    print('Running retrofit-potential with cooling-costs-threshold = %s' % config.retrofit_potential.cooling_costs_threshold)
    print('Running retrofit-potential with retrofit-scenario-name = %s' % config.retrofit_potential.retrofit_scenario_name)

    retrofit_main(locator_baseline=locator_baseline,
                  retrofit_scenario_name=config.retrofit_potential.retrofit_scenario_name,
                  keep_partial_matches=config.retrofit_potential.keep_partial_matches,
                  retrofit_target_year=config.retrofit_potential.retrofit_target_year,
                  age_threshold=config.retrofit_potential.age_threshold,
                  eui_heating_threshold=config.retrofit_potential.eui_heating_threshold,
                  eui_hot_water_threshold=config.retrofit_potential.eui_hot_water_threshold,
                  eui_cooling_threshold=config.retrofit_potential.eui_cooling_threshold,
                  eui_electricity_threshold=config.retrofit_potential.eui_electricity_threshold,
                  heating_costs_threshold=config.retrofit_potential.heating_costs_threshold,
                  hot_water_costs_threshold=config.retrofit_potential.hot_water_costs_threshold,
                  cooling_costs_threshold=config.retrofit_potential.cooling_costs_threshold,
                  electricity_costs_threshold=config.retrofit_potential.electricity_costs_threshold,
                  heating_losses_threshold=config.retrofit_potential.heating_losses_threshold,
                  hot_water_losses_threshold=config.retrofit_potential.hot_water_losses_threshold,
                  cooling_losses_threshold=config.retrofit_potential.cooling_losses_threshold,
                  emissions_operation_threshold=config.retrofit_potential.emissions_operation_threshold)


if __name__ == '__main__':
    main(cea.config.Configuration())
