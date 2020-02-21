
from __future__ import division
from __future__ import print_function

import pandas as pd

def save_results(locator,
                 date_array,
                 individual_number,
                 generation_number,
                 buildings_connected_costs,
                 buildings_connected_emissions,
                 buildings_disconnected_costs,
                 buildings_disconnected_emissions,
                 heating_dispatch,
                 cooling_dispatch,
                 electricity_dispatch,
                 electricity_requirements,
                 performance_totals_dict,
                 building_connectivity_dict,
                 district_heating_capacity_installed_dict,
                 district_cooling_capacity_installed_dict,
                 district_electricity_capacity_installed_dict,
                 buildings_disconnected_heating_capacities,
                 buildings_disconnected_cooling_capacities
                 ):
    # SAVE INDIVIDUAL DISTRICT HEATING INSTALLED CAPACITIES
    pd.DataFrame(district_heating_capacity_installed_dict, index=[0]).to_csv(
        locator.get_optimization_connected_heating_capacity(individual_number,
                                                            generation_number),
        index=False, float_format='%.3f')
    pd.DataFrame(district_cooling_capacity_installed_dict, index=[0]).to_csv(
        locator.get_optimization_connected_cooling_capacity(individual_number,
                                                            generation_number),
        index=False, float_format='%.3f')
    pd.DataFrame(district_electricity_capacity_installed_dict, index=[0]).to_csv(
        locator.get_optimization_connected_electricity_capacity(individual_number,
                                                                generation_number),
        index=False, float_format='%.3f')

    buildings_disconnected_heating_capacities.to_csv(
        locator.get_optimization_disconnected_heating_capacity(individual_number,
                                                               generation_number),
        index=False, float_format='%.3f')

    buildings_disconnected_cooling_capacities.to_csv(
        locator.get_optimization_disconnected_cooling_capacity(individual_number,
                                                               generation_number),
        index=False, float_format='%.3f')

    # SAVE BUILDING CONNECTIVITY
    pd.DataFrame(building_connectivity_dict).to_csv(
        locator.get_optimization_slave_building_connectivity(individual_number,
                                                             generation_number),
        index=False, float_format='%.3f')

    # SAVE PERFORMANCE RELATED FILES
    # export all including performance heating and performance cooling since we changed them
    performance_disconnected_dict = dict(buildings_disconnected_costs, **buildings_disconnected_emissions)
    pd.DataFrame(performance_disconnected_dict, index=[0]).to_csv(
        locator.get_optimization_slave_disconnected_performance(individual_number,
                                                                generation_number),
        index=False, float_format='%.3f')

    performance_connected_dict = dict(buildings_connected_costs, **buildings_connected_emissions)
    pd.DataFrame(performance_connected_dict, index=[0]).to_csv(
        locator.get_optimization_slave_connected_performance(individual_number,
                                                             generation_number),
        index=False, float_format='%.3f')

    pd.DataFrame(performance_totals_dict, index=[0]).to_csv(
        locator.get_optimization_slave_total_performance(individual_number,
                                                         generation_number),
        index=False, float_format='%.3f')

    # add date and plot
    electricity_dispatch['DATE'] = date_array
    cooling_dispatch['DATE'] = date_array
    heating_dispatch['DATE'] = date_array
    electricity_requirements['DATE'] = date_array

    pd.DataFrame(electricity_requirements).to_csv(
        locator.get_optimization_slave_electricity_requirements_data(individual_number,
                                                                     generation_number), index=False,
        float_format='%.3f')

    pd.DataFrame(electricity_dispatch).to_csv(
        locator.get_optimization_slave_electricity_activation_pattern(individual_number,
                                                                      generation_number),
        index=False, float_format='%.3f')

    pd.DataFrame(cooling_dispatch).to_csv(locator.get_optimization_slave_cooling_activation_pattern(individual_number,
                                                                                                    generation_number),
                                          index=False, float_format='%.3f')

    pd.DataFrame(heating_dispatch).to_csv(locator.get_optimization_slave_heating_activation_pattern(individual_number,
                                                                                                    generation_number),
                                          index=False, float_format='%.3f')