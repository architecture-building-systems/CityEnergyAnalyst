"""
costs according to supply systems
"""
from __future__ import division

import pandas as pd
from geopandas import GeoDataFrame as gpdf
import cea.globalvar
import cea.inputlocator

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def operation_costs(locator, Qww_flag=True, Qhs_flag=True, Qcs_flag=True, Qcdata_flag=True, Qcrefri_flag=True,
                    Eal_flag=True, Eaux_flag=True, Epro_flag=True, Edata_flag=True):

    # get local files
    ## get demand results for the scenario
    demand = pd.read_csv(locator.get_total_demand())
    ## get the supply systems for each building in the scenario
    supply_systems = gpdf.from_file(locator.get_building_supply()).drop('geometry', axis=1)
    ## get the non-renewable primary energy and greenhouse gas emissions factors for each supply system in the database
    data_LCI = locator.get_life_cycle_inventory_supply_systems()
    factors_heating = pd.read_excel(data_LCI, sheetname='heating')
    factors_dhw = pd.read_excel(data_LCI, sheetname='dhw')
    factors_cooling = pd.read_excel(data_LCI, sheetname='cooling')
    factors_electricity = pd.read_excel(data_LCI, sheetname='electricity')

    # local variables
    QC_flag = E_flag = True # minimum output values

    # calculate the total operational non-renewable primary energy demand and CO2 emissions
    ## create data frame for each type of end use energy containing the type of supply system use, the final energy
    ## demand and the primary energy and emissions factors for each corresponding type of supply system
    heating = supply_systems.merge(demand,on='Name').merge(factors_heating, left_on='type_hs', right_on='code')
    dhw = supply_systems.merge(demand,on='Name').merge(factors_dhw, left_on='type_dhw', right_on='code')
    cooling = supply_systems.merge(demand,on='Name').merge(factors_cooling, left_on='type_cs', right_on='code')
    electricity = supply_systems.merge(demand,on='Name').merge(factors_electricity, left_on='type_el', right_on='code')


    heating_services = [[Qhs_flag, 'Qhsf_MWhyr', 'Qhsf', 'Af_m2']]
    for x in heating_services:
        fields_to_plot = ['Name', 'GFA_m2',
                          x[2] + '_cost', x[2] + '_cost_m2']
        # calculate the total and relative costs
        heating[fields_to_plot[2]] = heating[x[1]] * heating['costs_kWh']* 1000
        heating[fields_to_plot[3]] =  heating[fields_to_plot[2]]/heating['GFA_m2']

        if x[0]:
            # if Qhs_flag is True, create the corresponding csv file
            heating[fields_to_plot].to_csv(locator.get_costs_operation_file(x[2]), index=False, float_format='%.2f')

    ## calculate the operational primary energy and emissions for domestic hot water services
    dhw_services = [[Qww_flag, 'Qwwf_MWhyr', 'Qwwf', 'Af_m2']]
    for x in dhw_services:
        fields_to_plot = ['Name', 'GFA_m2',
                          x[2] + '_cost', x[2] + '_cost_m2']
        # calculate the total and relative costs
        dhw[fields_to_plot[2]] = dhw[x[1]] * dhw['costs_kWh'] * 1000
        dhw[fields_to_plot[3]] = dhw[fields_to_plot[2]] / dhw['GFA_m2']
        if x[0]:
            # if Qww_flag is True, create the corresponding csv file
            dhw[fields_to_plot].to_csv(locator.get_costs_operation_file(x[2]), index=False, float_format='%.2f')

    ## calculate the operational primary energy and emissions for cooling services
    cooling_services = [(QC_flag, 'QCf_MWhyr', 'QCf'), (Qcs_flag, 'Qcsf_MWhyr', 'Qcsf'),
                        (Qcdata_flag, 'Qcdataf_MWhyr', 'Qcdataf'), (Qcrefri_flag, 'Qcref_MWhyr', 'Qcref')]
    for x in cooling_services:
        fields_to_plot = ['Name', 'GFA_m2',
                          x[2] + '_cost', x[2] + '_cost_m2']
        # calculate the total and relative costs
        cooling[fields_to_plot[2]] = cooling[x[1]] * cooling['costs_kWh'] * 1000
        cooling[fields_to_plot[3]] =  cooling[fields_to_plot[2]]/cooling['GFA_m2']
        if x[0]:
            # if QC_flag, Qcs_flag, Qcsdata_flag or Qcrefri_flag is True, create the corresponding csv file
            cooling[fields_to_plot].to_csv(locator.get_costs_operation_file(x[2]), index=False, float_format='%.2f')

    ## calculate the operational primary energy and emissions for electrical services
    electrical_services = [(E_flag, 'Ef_MWhyr', 'Ef'), (Eal_flag, 'Ealf_MWhyr', 'Ealf'),
                           (Eaux_flag, 'Eauxf_MWhyr', 'Eauxf'), (Epro_flag, 'Eprof_MWhyr', 'Eprof'),
                           (Edata_flag, 'Edataf_MWhyr', 'Edataf')]
    for x in electrical_services:
        fields_to_plot = ['Name', 'GFA_m2',
                          x[2] + '_cost', x[2] + '_cost_m2']
        # calculate the total and relative costs
        electricity[fields_to_plot[2]] = electricity[x[1]] * electricity['costs_kWh'] * 1000
        electricity[fields_to_plot[3]] =  electricity[fields_to_plot[2]] /electricity['GFA_m2']
        if x[0]:
            # if E_flag, Eal_flag, Eaux_flag, Epro_flag or Edata_flag is True, create the corresponding csv file
            electricity[fields_to_plot].to_csv(locator.get_costs_operation_file(x[2]), index=False, float_format='%.2f')

    # create a dataframe with the results for each energy service
    result = heating.merge(dhw, on='Name', suffixes=['_a','_b']).merge(cooling, on='Name',suffixes=['a','_b']).merge(electricity, on='Name')
    result.rename(columns={'GFA_m2_x': 'GFA_m2'}, inplace=True)

    # total costs
    # energy service used in the building
    result['O_cost']  =  result['Qhsf_cost']+ result['Qwwf_cost'] + result['QCf_cost'] + result['Ef_cost']
    result['O_cost_m2'] = result['Qhsf_cost_m2'] + result['Qwwf_cost_m2'] + result['QCf_cost_m2'] + result['Ef_cost_m2']

    # export the total operational non-renewable energy demand and emissions for each building
    fields_to_plot = ['Name', 'GFA_m2','O_cost','O_cost_m2']
    result[fields_to_plot].to_csv(locator.get_costs_operation_file("Total"), index=False, float_format='%.2f')


def run_as_script(scenario_path=None):
    if not scenario_path:
        gv = cea.globalvar.GlobalVariables()
        scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    operation_costs(locator=locator)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder')
    args = parser.parse_args()
    run_as_script(scenario_path=args.scenario)