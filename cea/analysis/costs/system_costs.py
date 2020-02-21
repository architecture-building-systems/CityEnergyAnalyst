"""
costs according to supply systems
"""
from __future__ import division

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


def costs_main(locator, config):
    # get local variables
    capital = config.costs.capital
    operational = config.costs.operational

    demand = pd.read_csv(locator.get_total_demand())
    supply_systems = gpdf.from_file(locator.get_building_supply()).drop('geometry', axis=1)
    data_all_in_one_systems = pd.read_excel(locator.get_database_supply_assemblies(), sheet_name=None)
    factors_heating = data_all_in_one_systems['HEATING']
    factors_dhw = data_all_in_one_systems['HOT_WATER']
    factors_cooling = data_all_in_one_systems['COOLING']
    factors_electricity = data_all_in_one_systems['ELECTRICITY']
    factors_resources = pd.read_excel(locator.get_database_feedstocks(), sheet_name=None)

    #get the mean of all values for this
    factors_resources_simple = [(name, values['Opex_var_buy_USD2015perkWh'].mean()) for name, values in factors_resources.items()]
    factors_resources_simple = pd.DataFrame(factors_resources_simple, columns=['code', 'Opex_var_buy_USD2015perkWh'])

    # local variables
    # calculate the total operational non-renewable primary energy demand and CO2 emissions
    ## create data frame for each type of end use energy containing the type of supply system use, the final energy
    ## demand and the primary energy and emissions factors for each corresponding type of supply system
    heating_costs = factors_heating.merge(factors_resources_simple, left_on='feedstock', right_on='code')[
        ['code_x', 'feedstock', 'Opex_var_buy_USD2015perkWh', 'CAPEX_USD2015kW', 'LT_yr', 'O&M_%', 'IR_%']]
    cooling_costs = factors_cooling.merge(factors_resources_simple, left_on='feedstock', right_on='code')[
        ['code_x', 'feedstock', 'Opex_var_buy_USD2015perkWh', 'CAPEX_USD2015kW', 'LT_yr', 'O&M_%', 'IR_%']]
    dhw_costs = factors_dhw.merge(factors_resources_simple, left_on='feedstock', right_on='code')[
        ['code_x', 'feedstock', 'Opex_var_buy_USD2015perkWh', 'CAPEX_USD2015kW', 'LT_yr', 'O&M_%', 'IR_%']]
    electricity_costs = factors_electricity.merge(factors_resources_simple, left_on='feedstock', right_on='code')[
        ['code_x', 'feedstock', 'Opex_var_buy_USD2015perkWh', 'CAPEX_USD2015kW', 'LT_yr', 'O&M_%', 'IR_%']]

    heating = supply_systems.merge(demand, on='Name').merge(heating_costs, left_on='type_hs', right_on='code_x')
    dhw = supply_systems.merge(demand, on='Name').merge(dhw_costs, left_on='type_dhw', right_on='code_x')
    cooling = supply_systems.merge(demand, on='Name').merge(cooling_costs, left_on='type_cs', right_on='code_x')
    electricity = supply_systems.merge(demand, on='Name').merge(electricity_costs, left_on='type_el', right_on='code_x')

    fields_to_plot = []
    heating_services = ['DH_hs', 'OIL_hs', 'NG_hs', 'WOOD_hs', 'COAL_hs', 'SOLAR_hs']
    for service in heating_services:
        try:
            fields_to_plot.extend([service + '_sys_opex_yr', service + '_sys_total_capex_yr', service + '_sys_a_capex_yr',  service + '_sys_opex_m2yr'])
            # calculate the total and relative costs
            heating[service + '_sys_total_capex_yr'] = heating[service + '0_kW'] * heating['CAPEX_USD2015kW']
            heating[service + '_sys_a_capex_yr'] = calc_inv_costs_annualized(heating[service + '_sys_total_capex_yr'], heating['IR_%']/100, heating['LT_yr'])
            heating[service + '_sys_opex_yr'] = heating[service + '_MWhyr'] * heating['Opex_var_buy_USD2015perkWh'] * 1000 + heating[service + '_sys_total_capex_yr'] * heating['O&M_%']/100
            heating[service + '_sys_opex_m2yr'] = heating[service + '_sys_opex_yr'] / heating['Aocc_m2']
        except KeyError:
            print(heating)
            print(list(heating.columns))
            raise

    # for cooling services
    dhw_services = ['DH_ww', 'OIL_ww', 'NG_ww', 'WOOD_ww', 'COAL_ww', 'SOLAR_ww']
    for service in dhw_services:
        fields_to_plot.extend([service + '_sys_opex_yr', service + '_sys_total_capex_yr', service + '_sys_a_capex_yr', service + '_sys_opex_m2yr'])
        # calculate the total and relative costs
        # calculate the total and relative costs
        dhw[service + '_sys_total_capex_yr'] = dhw[service + '0_kW'] * dhw['CAPEX_USD2015kW']
        dhw[service + '_sys_a_capex_yr'] =  calc_inv_costs_annualized(dhw[service + '_sys_total_capex_yr'], dhw['IR_%']/100, dhw['LT_yr'])
        dhw[service + '_sys_opex_yr'] = dhw[service + '_MWhyr'] * dhw['Opex_var_buy_USD2015perkWh'] * 1000 + dhw[service + '_sys_total_capex_yr'] * dhw['O&M_%']/100
        dhw[service + '_sys_opex_m2yr'] = dhw[service + '_sys_opex_yr'] / dhw['Aocc_m2']

    ## calculate the operational primary energy and emissions for cooling services
    cooling_services = ['DC_cs', 'DC_cdata', 'DC_cre']
    for service in cooling_services:
        fields_to_plot.extend([service + '_sys_opex_yr', service + '_sys_total_capex_yr', service + '_sys_a_capex_yr', service + '_sys_opex_m2yr'])
        # change price to that of local electricity mix
        # calculate the total and relative costs
        cooling[service + '_sys_total_capex_yr'] = cooling[service + '0_kW'] * cooling['CAPEX_USD2015kW']
        cooling[service + '_sys_a_capex_yr'] = calc_inv_costs_annualized(cooling[service + '_sys_total_capex_yr'], cooling['IR_%']/100, cooling['LT_yr'])
        cooling[service + '_sys_opex_yr'] = cooling[service + '_MWhyr'] * cooling['Opex_var_buy_USD2015perkWh'] * 1000 + cooling[service + '_sys_total_capex_yr'] * cooling['O&M_%']/100
        cooling[service + '_sys_opex_m2yr'] = cooling[service + '_sys_opex_yr'] / cooling['Aocc_m2']

    ## calculate the operational primary energy and emissions for electrical services
    electrical_services = ['GRID', 'PV']
    for service in electrical_services:
        fields_to_plot.extend([service + '_sys_opex_yr', service + '_sys_total_capex_yr', service+ '_sys_a_capex_yr', service + '_sys_opex_m2yr'])
        # calculate the total and relative costs
        electricity[service + '_sys_total_capex_yr'] = electricity[service + '0_kW'] * electricity['CAPEX_USD2015kW']
        electricity[service + '_sys_a_capex_yr'] = calc_inv_costs_annualized(electricity[service + '_sys_total_capex_yr'], electricity['IR_%']/100, electricity['LT_yr']/100)
        electricity[service + '_sys_opex_yr'] = electricity[service + '_MWhyr'] * electricity['Opex_var_buy_USD2015perkWh'] * 1000 + electricity[service + '_sys_total_capex_yr'] * electricity['O&M_%']/100
        electricity[service + '_sys_opex_m2yr'] = electricity[service + '_sys_opex_yr'] / electricity['Aocc_m2']

    # plot also NFA area and costs
    fields_to_plot.extend(['Aocc_m2'])

    # embodied emissions
    if capital:
        fields_to_plot.extend(['Capex_a_sys_disconnected_USD',
                             'Capex_a_sys_connected_USD',
                             'Capex_total_sys_connected_USD',
                             'Capex_total_sys_disconnected_USD',
                               'Capex_total_sys_USD', 'TAC_sys_USD'
                               ])
    # operation emissions
    if operational:
        fields_to_plot.extend(['Opex_a_sys_connected_USD',
                             'Opex_a_sys_disconnected_USD',
                             'Opex_a_sys_USD'])

    # create and save results
    result = heating.merge(dhw, on='Name', suffixes=('', '_dhw'))
    result = result.merge(cooling, on='Name', suffixes=('', '_cooling'))
    result = result.merge(electricity, on='Name', suffixes=('', '_ electricity'))

    # add totals:
    result['Opex_a_sys_connected_USD'] = result['GRID_sys_opex_yr'] + \
                                         result['DH_hs_sys_opex_yr'] + \
                                         result['DH_ww_sys_opex_yr'] + \
                                         result['DC_cdata_sys_opex_yr'] + \
                                         result['DC_cs_sys_opex_yr'] + \
                                         result['DC_cre_sys_opex_yr']

    result['Opex_a_sys_disconnected_USD'] = result['OIL_hs_sys_opex_yr'] + \
                                            result['NG_hs_sys_opex_yr'] + \
                                            result['WOOD_hs_sys_opex_yr'] + \
                                            result['COAL_hs_sys_opex_yr'] + \
                                            result['SOLAR_hs_sys_opex_yr'] + \
                                            result['PV_sys_opex_yr'] + \
                                            result['OIL_ww_sys_opex_yr'] + \
                                            result['NG_ww_sys_opex_yr'] + \
                                            result['WOOD_ww_sys_opex_yr'] + \
                                            result['COAL_ww_sys_opex_yr'] + \
                                            result['SOLAR_ww_sys_opex_yr']

    result['Capex_a_sys_connected_USD'] =  result['GRID_sys_a_capex_yr'] + \
                                         result['DH_hs_sys_a_capex_yr'] + \
                                         result['DH_ww_sys_a_capex_yr'] + \
                                         result['DC_cdata_sys_a_capex_yr'] + \
                                         result['DC_cs_sys_a_capex_yr'] + \
                                         result['DC_cre_sys_a_capex_yr']

    result['Capex_a_sys_disconnected_USD'] =  result['OIL_hs_sys_a_capex_yr'] + \
                                            result['NG_hs_sys_a_capex_yr'] + \
                                            result['WOOD_hs_sys_a_capex_yr'] + \
                                            result['COAL_hs_sys_a_capex_yr'] + \
                                            result['SOLAR_hs_sys_a_capex_yr'] + \
                                            result['PV_sys_a_capex_yr'] + \
                                            result['OIL_ww_sys_a_capex_yr'] + \
                                            result['NG_ww_sys_a_capex_yr'] + \
                                            result['WOOD_ww_sys_a_capex_yr'] + \
                                            result['COAL_ww_sys_a_capex_yr'] + \
                                            result['SOLAR_ww_sys_a_capex_yr']

    result['Capex_total_sys_connected_USD'] =  result['GRID_sys_total_capex_yr'] + \
                                         result['DH_hs_sys_total_capex_yr'] + \
                                         result['DH_ww_sys_total_capex_yr'] + \
                                         result['DC_cdata_sys_total_capex_yr'] + \
                                         result['DC_cs_sys_total_capex_yr'] + \
                                         result['DC_cre_sys_total_capex_yr']

    result['Capex_total_sys_disconnected_USD'] =  result['OIL_hs_sys_total_capex_yr'] + \
                                            result['NG_hs_sys_total_capex_yr'] + \
                                            result['WOOD_hs_sys_total_capex_yr'] + \
                                            result['COAL_hs_sys_total_capex_yr'] + \
                                            result['SOLAR_hs_sys_total_capex_yr'] + \
                                            result['PV_sys_total_capex_yr'] + \
                                            result['OIL_ww_sys_total_capex_yr'] + \
                                            result['NG_ww_sys_total_capex_yr'] + \
                                            result['WOOD_ww_sys_total_capex_yr'] + \
                                            result['COAL_ww_sys_total_capex_yr'] + \
                                            result['SOLAR_ww_sys_total_capex_yr']

    result['Capex_total_sys_USD'] = result['Capex_total_sys_disconnected_USD'] + result['Capex_total_sys_connected_USD']
    result['TAC_sys_USD'] = result['Capex_a_sys_disconnected_USD'] + result['Capex_a_sys_connected_USD']
    result['Opex_a_sys_USD'] = result['Opex_a_sys_disconnected_USD'] + result['Opex_a_sys_connected_USD']

    result[['Name'] + fields_to_plot].to_csv(
        locator.get_costs_operation_file(), index=False, float_format='%.2f')


def calc_inv_costs_annualized(InvC, Inv_IR, Inv_LT):
    return InvC * (Inv_IR) * (1 + Inv_IR) ** Inv_LT / ((1 + Inv_IR) ** Inv_LT - 1)

def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    print('Running system-costs with scenario = %s' % config.scenario)

    costs_main(locator=locator,config=config)


if __name__ == '__main__':
    main(cea.config.Configuration())
