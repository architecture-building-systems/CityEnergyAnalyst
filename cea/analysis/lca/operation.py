"""
Non-renewable primary energy and GHG_kgCO2MJ emissions model algorithm for building operation
"""
from __future__ import division

import os

import pandas as pd
from geopandas import GeoDataFrame as gpdf

import cea.config
import cea.inputlocator

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def lca_operation(locator):
    """
    Algorithm to calculate the primary energy and GHG_kgCO2MJ emissions of buildings according to the method used in the
    integrated model of [Fonseca-Schlueter-2015]_ and the performance factors of [ecobau.ch].

    :param locator: an InputLocator instance set to the scenario to work on
    :type locator: InputLocator


    The following file is created by this script:

    - total_LCA_operation: .csv
        csv file of yearly non-renewable primary energy demand and GHG_kgCO2MJ emissions per building for all energy
        services (i.e. heating, hot water, cooling, electricity) both total and per square meter

    :returns: This function does not return anything
    :rtype: NoneType

    .. [Fonseca-Schlueter-2015] J. Fonseca & A. Schlueter (2015) "Integrated model for characterization of
        spatiotemporal building energy consumption patterns in neighborhoods and city districts". Applied Energy 142.
    """

    # get local files
    ## get demand results for the scenario
    demand = pd.read_csv(locator.get_total_demand())
    ## get the supply systems for each building in the scenario
    supply_systems = gpdf.from_file(locator.get_building_supply()).drop('geometry', axis=1)
    ## get the non-renewable primary energy and greenhouse gas emissions factors for each supply system in the database
    data_all_in_one_systems = pd.read_excel(locator.get_database_supply_assemblies(), sheet_name=None)
    factors_heating = data_all_in_one_systems['HEATING']
    factors_dhw = data_all_in_one_systems['HOT_WATER']
    factors_cooling = data_all_in_one_systems['COOLING']
    factors_electricity = data_all_in_one_systems['ELECTRICITY']
    factors_resources = pd.read_excel(locator.get_database_feedstocks(),sheet_name =None)

    # get the mean of all values for this
    factors_resources_simple = [(name, values['GHG_kgCO2MJ'].mean()) for name, values in factors_resources.items()]
    factors_resources_simple = pd.DataFrame(factors_resources_simple, columns=['code', 'GHG_kgCO2MJ']).append(
        # append NONE choice with zero values
        {'code': 'NONE'}, ignore_index=True).fillna(0)

    # local variables
    Qhs_flag = Qww_flag = Qcs_flag = E_flag = True
    # calculate the total operational non-renewable primary energy demand and GHG_kgCO2MJ emissions
    ## create data frame for each type of end use energy containing the type of supply system use, the final energy
    ## demand and the primary energy and emissions factors for each corresponding type of supply system

    heating_factors = factors_heating.merge(factors_resources_simple, left_on='feedstock', right_on='code')[
        ['code_x', 'feedstock','GHG_kgCO2MJ']]
    cooling_factors = factors_cooling.merge(factors_resources_simple, left_on='feedstock', right_on='code')[
        ['code_x', 'feedstock', 'GHG_kgCO2MJ']]
    dhw_factors = factors_dhw.merge(factors_resources_simple, left_on='feedstock', right_on='code')[
        ['code_x', 'feedstock', 'GHG_kgCO2MJ']]
    electricity_factors = factors_electricity.merge(factors_resources_simple, left_on='feedstock', right_on='code')[
        ['code_x', 'feedstock', 'GHG_kgCO2MJ']]

    heating = supply_systems.merge(demand, on='Name').merge(heating_factors, left_on='type_hs', right_on='code_x')
    dhw = supply_systems.merge(demand, on='Name').merge(dhw_factors, left_on='type_dhw', right_on='code_x')
    cooling = supply_systems.merge(demand, on='Name').merge(cooling_factors, left_on='type_cs', right_on='code_x')
    electricity = supply_systems.merge(demand, on='Name').merge(electricity_factors, left_on='type_el',
                                                                right_on='code_x')

    ## calculate the operational primary energy and emissions for heating services
    heating_services = [(Qhs_flag, 'DH_hs_MWhyr', 'DH_hs', 'Af_m2'),
                        (Qhs_flag, 'SOLAR_hs_MWhyr', 'SOLAR_hs', 'Af_m2'),
                        (Qhs_flag, 'NG_hs_MWhyr', 'NG_hs', 'Af_m2'),
                        (Qhs_flag, 'COAL_hs_MWhyr', 'COAL_hs', 'Af_m2'),
                        (Qhs_flag, 'OIL_hs_MWhyr', 'OIL_hs', 'Af_m2'),
                        (Qhs_flag, 'WOOD_hs_MWhyr', 'WOOD_hs', 'Af_m2')]
    for x in heating_services:
        fields_to_plot = ['Name', 'GFA_m2', x[2] + '_ghg_ton', x[2] + '_ghg_kgm2']
        # calculate the total (t GHG_kgCO2MJ-eq) and specific (kg GHG_kgCO2MJ-eq/m2) operational greenhouse gas emissions (O_ghg_)
        heating[fields_to_plot[2]] = heating[x[1]] * heating['GHG_kgCO2MJ'] * 3.6
        heating[fields_to_plot[3]] = (heating[x[1]] * heating['GHG_kgCO2MJ'] * 3600) / heating['GFA_m2']

    ## calculate the operational primary energy and emissions for domestic hot water services
    dhw_services = [(Qww_flag, 'DH_ww_MWhyr', 'DH_ww'),
                    (Qww_flag, 'SOLAR_ww_MWhyr', 'SOLAR_ww'),
                    (Qww_flag, 'NG_ww_MWhyr', 'NG_ww'),
                    (Qww_flag, 'COAL_ww_MWhyr', 'COAL_ww'),
                    (Qww_flag, 'OIL_ww_MWhyr', 'OIL_ww'),
                    (Qww_flag, 'WOOD_ww_MWhyr', 'WOOD_ww')]

    for x in dhw_services:
        fields_to_plot = ['Name', 'GFA_m2', x[2] + '_ghg_ton', x[2] + '_ghg_kgm2']
        # calculate the total (t GHG_kgCO2MJ-eq) and specific (kg GHG_kgCO2MJ-eq/m2) operational greenhouse gas emissions (O_ghg_)
        dhw[fields_to_plot[2]] = dhw[x[1]] * dhw['GHG_kgCO2MJ'] * 3.6
        dhw[fields_to_plot[3]] = (dhw[x[1]] * dhw['GHG_kgCO2MJ'] * 3600) / dhw['GFA_m2']

    ## calculate the operational primary energy and emissions for cooling services
    cooling_services = [(Qcs_flag, 'DC_cs_MWhyr', 'DC_cs'),
                        (Qcs_flag, 'DC_cdata_MWhyr', 'DC_cdata'),
                        (Qcs_flag, 'DC_cre_MWhyr', 'DC_cre')]
    for x in cooling_services:
        fields_to_plot = ['Name', 'GFA_m2', x[2] + '_ghg_ton', x[2] + '_ghg_kgm2']
        # calculate the total (t GHG_kgCO2MJ-eq) and specific (kg GHG_kgCO2MJ-eq/m2) operational greenhouse gas emissions (O_ghg_)
        cooling[fields_to_plot[2]] = cooling[x[1]] * cooling['GHG_kgCO2MJ'] * 3.6
        cooling[fields_to_plot[3]] = (cooling[x[1]] * cooling['GHG_kgCO2MJ'] * 3600) / cooling['GFA_m2']

    ## calculate the operational primary energy and emissions for electrical services
    electrical_services = [(E_flag, 'GRID_MWhyr', 'GRID'),
                           (E_flag, 'PV_MWhyr', 'PV')]
    for x in electrical_services:
        fields_to_plot = ['Name', 'GFA_m2', x[2] + '_ghg_ton', x[2] + '_ghg_kgm2']
        # calculate the total (t GHG_kgCO2MJ-eq) and specific (kg GHG_kgCO2MJ-eq/m2) operational greenhouse gas emissions (O_ghg_)
        electricity[fields_to_plot[2]] = electricity[x[1]] * electricity['GHG_kgCO2MJ'] * 3.6
        electricity[fields_to_plot[3]] = (electricity[x[1]] * electricity['GHG_kgCO2MJ'] * 3600) / electricity['GFA_m2']

    # create a dataframe with the results for each energy service
    result = heating.merge(dhw, on='Name', suffixes=['_a', '_b']).merge(cooling, on='Name', suffixes=['a', '_b']).merge(
        electricity, on='Name')
    result.rename(columns={'GFA_m2_x': 'GFA_m2'}, inplace=True)

    # calculate the total operational non-renewable primary energy demand and emissions as a sum of the results for each
    # energy service used in the building
    result['GHG_sys_kgCO2m2'] = 0.0
    result['GHG_sys_tonCO2'] = 0.0
    all_services = electrical_services + cooling_services + heating_services + dhw_services
    for service in all_services:
        fields_to_plot += [service[2] + '_ghg_ton', service[2] + '_ghg_kgm2']
        result['GHG_sys_tonCO2'] += result[service[2] + '_ghg_ton']
        result['GHG_sys_kgCO2m2'] += result[service[2] + '_ghg_kgm2']

    # export the total operational non-renewable energy demand and emissions for each building
    fields_to_plot += ['Name', 'GFA_m2', 'GHG_sys_tonCO2', 'GHG_sys_kgCO2m2']
    result[fields_to_plot].to_csv(locator.get_lca_operation(), index=False, float_format='%.2f')


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    print('Running emissions with scenario = %s' % config.scenario)

    lca_operation(locator=locator)


if __name__ == '__main__':
    main(cea.config.Configuration())
