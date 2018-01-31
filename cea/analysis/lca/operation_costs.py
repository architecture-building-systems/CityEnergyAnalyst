"""
costs according to supply systems
"""
from __future__ import division

import os
import pandas as pd
from geopandas import GeoDataFrame as gpdf
import cea.inputlocator
import cea.config

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def operation_costs(locator, config, plot_Qww=True, plot_Qhs=True, plot_Qcs=True, plot_Qcdata=True, plot_Qcrefri=True,
                    plot_Eal=True, plot_Eaux=True, plot_Epro=True, plot_Edata=True):

    # get local variables
    region = config.region
    variables = config.operation_costs.analysis_fields
    demand = pd.read_csv(locator.get_total_demand())
    supply_systems = gpdf.from_file(locator.get_building_supply()).drop('geometry', axis=1)
    data_LCI = locator.get_life_cycle_inventory_supply_systems(region)
    factors_heating = pd.read_excel(data_LCI, sheetname='heating')
    factors_dhw = pd.read_excel(data_LCI, sheetname='dhw')
    factors_cooling = pd.read_excel(data_LCI, sheetname='cooling')
    factors_electricity = pd.read_excel(data_LCI, sheetname='electricity')

    # local variables
    # calculate the total operational non-renewable primary energy demand and CO2 emissions
    ## create data frame for each type of end use energy containing the type of supply system use, the final energy
    ## demand and the primary energy and emissions factors for each corresponding type of supply system
    heating = supply_systems.merge(demand,on='Name').merge(factors_heating, left_on='type_hs', right_on='code')
    dhw = supply_systems.merge(demand,on='Name').merge(factors_dhw, left_on='type_dhw', right_on='code')
    cooling = supply_systems.merge(demand,on='Name').merge(factors_cooling, left_on='type_cs', right_on='code')
    electricity = supply_systems.merge(demand,on='Name').merge(factors_electricity, left_on='type_el', right_on='code')

    fields_to_plot = []
    heating_services = ['Qhsf']
    for service in heating_services:
        if service in variables:
            fields_to_plot.extend([service+'_cost_yr', service+'_cost_m2yr'])
            # calculate the total and relative costs
            heating[service+'_cost_yr'] = heating[service+'_MWhyr'] * heating['costs_kWh']* 1000
            heating[service+'_cost_m2yr'] =  heating[service+'_cost_yr']/heating['GFA_m2']

    # for cooling services
    dhw_services = ['Qwwf']
    for service in dhw_services:
        if service in variables:
            fields_to_plot.extend([service+'_cost_yr', service+'_cost_m2yr'])
            # calculate the total and relative costs
            dhw[service+'_cost_yr'] = dhw[service+'_MWhyr'] * dhw['costs_kWh']* 1000
            dhw[service+'_cost_m2yr'] =  dhw[service+'_cost_yr']/dhw['GFA_m2']


    ## calculate the operational primary energy and emissions for cooling services
    cooling_services = ['QCf']
    for service in cooling_services:
        if service in variables:
            fields_to_plot.extend([service+'_cost_yr', service+'_cost_m2yr'])
            # calculate the total and relative costs
            cooling[service + '_cost_yr'] = cooling[service + '_MWhyr'] * cooling['costs_kWh'] * 1000
            cooling[service + '_cost_m2yr'] = cooling[service + '_cost_yr'] / cooling['GFA_m2']

    ## calculate the operational primary energy and emissions for electrical services
    electrical_services = ['Ef']
    for service in electrical_services:
        if service in variables:
            fields_to_plot.extend([service+'_cost_yr', service+'_cost_m2yr'])
            # calculate the total and relative costs
            electricity[service + '_cost_yr'] = electricity[service + '_MWhyr'] * electricity['costs_kWh'] * 1000
            electricity[service + '_cost_m2yr'] = electricity[service + '_cost_yr'] / electricity['GFA_m2']

    # create and save results
    result = heating.merge(dhw, on='Name').merge(cooling, on='Name').merge(electricity, on='Name')
    result[['Name']+fields_to_plot].to_csv(locator.get_costs_operation_file(), index=False, float_format='%.2f')


def main(config):
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    print('Running operation-costs with scenario = %s' % config.scenario)

    operation_costs(locator=locator, config=config)

if __name__ == '__main__':
    main(cea.config.Configuration())