




import pandas as pd

def save_results(locator,
                 date_array,
                 individual_number,
                 generation_number,
                 buildings_district_scale_costs,
                 buildings_district_scale_emissions,
                 buildings_district_scale_heat,
                 buildings_district_scale_sed,
                 buildings_building_scale_costs,
                 buildings_building_scale_emissions,
                 buildings_building_scale_heat,
                 buildings_building_scale_sed,
                 heating_dispatch,
                 cooling_dispatch,
                 electricity_dispatch,
                 electricity_requirements,
                 performance_totals_dict,
                 building_connectivity_dict,
                 district_heating_capacity_installed_dict,
                 district_cooling_capacity_installed_dict,
                 district_electricity_capacity_installed_dict,
                 buildings_building_scale_heating_capacities,
                 buildings_building_scale_cooling_capacities
                 ):
    locator.ensure_parent_folder_exists(locator.get_optimization_slave_generation_results_folder(generation_number))

    # SAVE INDIVIDUAL DISTRICT HEATING INSTALLED CAPACITIES
    pd.DataFrame(district_heating_capacity_installed_dict, index=[0]).to_csv(
        locator.get_optimization_district_scale_heating_capacity(individual_number,
                                                                 generation_number),
        index=False, float_format='%.3f')
    pd.DataFrame(district_cooling_capacity_installed_dict, index=[0]).to_csv(
        locator.get_optimization_district_scale_cooling_capacity(individual_number,
                                                                 generation_number),
        index=False, float_format='%.3f')
    pd.DataFrame(district_electricity_capacity_installed_dict, index=[0]).to_csv(
        locator.get_optimization_district_scale_electricity_capacity(individual_number,
                                                                     generation_number),
        index=False, float_format='%.3f')

    buildings_building_scale_heating_capacities.to_csv(
        locator.get_optimization_building_scale_heating_capacity(individual_number,
                                                                 generation_number),
        index=False, float_format='%.3f')

    buildings_building_scale_cooling_capacities.to_csv(
        locator.get_optimization_building_scale_cooling_capacity(individual_number,
                                                                 generation_number),
        index=False, float_format='%.3f')

    # SAVE BUILDING CONNECTIVITY
    pd.DataFrame(building_connectivity_dict).to_csv(
        locator.get_optimization_slave_building_connectivity(individual_number,
                                                             generation_number),
        index=False, float_format='%.3f')

    # SAVE PERFORMANCE RELATED FILES
    # export all including performance heating and performance cooling since we changed them
    performance_building_scale_dict = dict(buildings_building_scale_costs, **buildings_building_scale_emissions,
                                           **buildings_building_scale_heat, **buildings_building_scale_sed)
    pd.DataFrame(performance_building_scale_dict, index=[0]).to_csv(
        locator.get_optimization_slave_building_scale_performance(individual_number,
                                                                  generation_number),
        index=False, float_format='%.3f')

    performance_district_scale_dict = dict(buildings_district_scale_costs, **buildings_district_scale_emissions,
                                           **buildings_district_scale_heat, **buildings_district_scale_sed)
    pd.DataFrame(performance_district_scale_dict, index=[0]).to_csv(
        locator.get_optimization_slave_district_scale_performance(individual_number,
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