"""
Primary energy and CO2 emissions model algorithm for building operation
"""
from __future__ import division

import pandas as pd
from geopandas import GeoDataFrame as gpdf
import os

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def lca_operation(locator, Qww_flag=True, Qhs_flag=True, Qcs_flag=True, Qcdata_flag=True, Qcrefri_flag=True,
                  Eal_flag=True, Eaux_flag=True, Epro_flag=True, Edata_flag=True):
    """
    algorithm to calculate the primary energy and CO2 emissions of buildings
    according to the method used in the integrated model of
    Fonseca et al. 2015.
    Appl. energy. and the performance factors of ecobau.ch

    :param locator: an InputLocator instance set to the scenario to work on
    :type locator: cea.inputlocator.InputLocator
    :param Qww_flag: create a separate file with emissions due to hot water consumption?
    :type Qww_flag: bool
    :param boolean Qhs_flag: create a separate file with emissions due to space heating?
    :type Qhs_flag: bool
    :param Qcs_flag: create a get separate file with emissions due to space cooling?
    :type Qcs_flag: bool
    :param Qcdata_flag: create a separate file with emissions due to servers cooling?
    :type Qcdata_flag: bool
    :param Qcrefri_flag: create a separate file with emissions due to refrigeration?
    :type Qcrefri_flag: bool
    :param Eal_flag: create a separate file with emissions due to appliances and lighting?
    :type Eal_flag: bool
    :param Eaux_flag: create a separate file with emissions due to auxiliary electricity?
    :type Eaux_flag: bool
    :param Epro_flag: create a separate file with emissions due to electricity in industrial processes?
    :type Epro_flag: bool
    :param Edata_flag: create a separate file with emissions due to electricity consumption in data centers?
    :type Edata_flag: bool

    Produces Total_LCA_operation.csv containing the yearly primary energy per building and energy service (i.e. heating,
    hot water, cooling, electricity)

    The following files are also created by this script, depending on which flags were set:

    - Qhs_LCA_operation:.csv
        describes the emissions and primary energy due to space heating
    - Qww_LCA_operation:.csv
        describes the emissions and primary energy due to domestic hot water consumption
    - Qcs_LCA_operation:.csv
        describes the emissions and primary energy due to space cooling
    - Qcdata_LCA_operation:.csv
        describes the emissions and primary energy due to servers cooling
    - Qcrefri_LCA_operation:.csv
        describes the emissions and primary energy due to refrigeration
    - Eal_LCA_operation:.csv
        describes the emissions and primary energy due to appliances and lighting
    - Eaux_LCA_operation:.csv
        describes the emissions and primary energy due to auxiliary electricity
    - Epro_LCA_operation:.csv
        describes the emissions and primary energy due to electricity in industrial processes
    - Edata_LCA_operation:.csv
        describes the emissions and primary energy due to electricity consumption in data centers
    """

    # local files
    demand = pd.read_csv(locator.get_total_demand())
    supply_systems = gpdf.from_file(locator.get_building_supply()).drop('geometry', axis=1)
    data_LCI = locator.get_life_cycle_inventory_supply_systems()
    factors_heating = pd.read_excel(data_LCI, sheetname='heating')
    factors_dhw = pd.read_excel(data_LCI, sheetname='dhw')
    factors_cooling = pd.read_excel(data_LCI, sheetname='cooling')
    factors_electricity = pd.read_excel(data_LCI, sheetname='electricity')

    # local variables
    QC_flag = E_flag = True # minmum output values
    result_folder = locator.get_lca_emissions_results_folder()

    # calculate total_LCA_operation:.csv
    heating = supply_systems.merge(demand,on='Name').merge(factors_heating, left_on='type_hs', right_on='code')
    dhw = supply_systems.merge(demand,on='Name').merge(factors_dhw, left_on='type_dhw', right_on='code')
    cooling = supply_systems.merge(demand,on='Name').merge(factors_cooling, left_on='type_cs', right_on='code')
    electricity = supply_systems.merge(demand,on='Name').merge(factors_electricity, left_on='type_el', right_on='code')

    # for heating services
    heating_services = [[Qhs_flag, 'Qhsf_MWhyr', 'Qhsf', 'Af_m2']]
    for x in heating_services:
        fields_to_plot = ['Name', 'GFA_m2', x[2] + '_ghg_ton', x[2] + '_ghg_kgm2', x[2] + '_nre_pen_GJ', x[2] + '_nre_pen_MJm2']
        heating[fields_to_plot[4]] = heating[x[1]] * heating['PEN'] * 3.6
        heating[fields_to_plot[2]] = heating[x[1]] * heating['CO2'] * 3.6
        heating[fields_to_plot[5]] = heating[x[1]] * heating['PEN'] * 3600/heating['GFA_m2']
        heating[fields_to_plot[3]] =  heating[x[1]] * heating['CO2'] * 3600/heating['GFA_m2']
        if x[0]:
            heating[fields_to_plot].to_csv(os.path.join(result_folder, '%s_LCA_operation.csv' % x[2]), index=False,
                                                        float_format='%.2f')

    # for dhw services
    dhw_services = [[Qww_flag, 'Qwwf_MWhyr', 'Qwwf', 'Af_m2']]
    for x in dhw_services:
        fields_to_plot = ['Name', 'GFA_m2', x[2] + '_ghg_ton', x[2] + '_ghg_kgm2', x[2] + '_nre_pen_GJ', x[2] + '_nre_pen_MJm2']
        dhw[fields_to_plot[4]] = dhw[x[1]] * dhw['PEN'] * 3.6
        dhw[fields_to_plot[2]] = dhw[x[1]] * dhw['CO2'] * 3.6
        dhw[fields_to_plot[5]] = dhw[x[1]] * dhw['PEN'] * 3600 / dhw['GFA_m2']
        dhw[fields_to_plot[3]] = dhw[x[1]] * dhw['CO2'] * 3600 / dhw['GFA_m2']
        if x[0]:
            dhw[fields_to_plot].to_csv(os.path.join(result_folder, x[2] + '_LCA_operation.csv'), index=False,
                                       float_format='%.2f')
    # for cooling services
    cooling_services = [(QC_flag, 'QCf_MWhyr', 'QCf'), (Qcs_flag, 'Qcsf_MWhyr', 'Qcsf'),
                        (Qcdata_flag, 'Qcdataf_MWhyr', 'Qcdataf'), (Qcrefri_flag, 'Qcref_MWhyr', 'Qcref')]
    for x in cooling_services:
        fields_to_plot = ['Name', 'GFA_m2', x[2] + '_ghg_ton', x[2] + '_ghg_kgm2', x[2] + '_nre_pen_GJ', x[2] + '_nre_pen_MJm2']
        cooling[fields_to_plot[4]] = cooling[x[1]] * cooling['PEN'] * 3.6
        cooling[fields_to_plot[2]] = cooling[x[1]] * cooling['CO2'] * 3.6
        cooling[fields_to_plot[5]] = cooling[x[1]] * cooling['PEN'] * 3600/cooling['GFA_m2']
        cooling[fields_to_plot[3]] =  cooling[x[1]] * cooling['CO2'] * 3600/cooling['GFA_m2']
        if x[0]:
            cooling[fields_to_plot].to_csv(os.path.join(result_folder, x[2] + '_LCA_operation.csv'), index=False,
                                           float_format='%.2f')

    # for electrical services
    electrical_services = [(E_flag, 'Ef_MWhyr', 'Ef'), (Eal_flag, 'Ealf_MWhyr', 'Ealf'),
                           (Eaux_flag, 'Eauxf_MWhyr', 'Eauxf'), (Epro_flag, 'Eprof_MWhyr', 'Eprof'),
                           (Edata_flag, 'Edataf_MWhyr', 'Edataf')]
    for x in electrical_services:
        fields_to_plot = ['Name', 'GFA_m2', x[2] + '_ghg_ton', x[2] + '_ghg_kgm2', x[2] + '_nre_pen_GJ', x[2] + '_nre_pen_MJm2']
        electricity[fields_to_plot[4]] = electricity[x[1]] * electricity['PEN'] * 3.6
        electricity[fields_to_plot[2]] = electricity[x[1]] * electricity['CO2'] * 3.6
        electricity[fields_to_plot[5]] = electricity[x[1]] * electricity['PEN'] * 3600/electricity['GFA_m2']
        electricity[fields_to_plot[3]] =  electricity[x[1]] * electricity['CO2'] * 3600/electricity['GFA_m2']
        if x[0]:
            electricity[fields_to_plot].to_csv(result_folder + '\\' + x[2] + '_LCA_operation.csv', index=False,
                                               float_format='%.2f')

    result = heating.merge(dhw, on='Name', suffixes=['_a','_b']).merge(cooling, on='Name',suffixes=['a','_b']).merge(electricity, on='Name')
    result.rename(columns={'GFA_m2_x': 'GFA_m2'}, inplace=True)
    result['O_nre_pen_GJ'] = result['Qhsf_nre_pen_GJ'] + result['Qwwf_nre_pen_GJ'] + result['QCf_nre_pen_GJ'] + result['Ef_nre_pen_GJ']
    result['O_ghg_ton'] = result['Qhsf_ghg_ton'] + result['Qwwf_ghg_ton'] +result['QCf_ghg_ton'] + result['Ef_ghg_ton']
    result['O_nre_pen_MJm2'] = result['Qhsf_nre_pen_MJm2'] + result['Qwwf_nre_pen_MJm2'] + result['QCf_nre_pen_MJm2'] + result['Ef_nre_pen_MJm2']
    result['O_ghg_kgm2'] = result['Qhsf_ghg_kgm2'] + result['Qwwf_ghg_kgm2'] + result['QCf_ghg_kgm2'] + result['Ef_ghg_kgm2']
    fields_to_plot = ['Name', 'GFA_m2', 'O_ghg_ton', 'O_ghg_kgm2', 'O_nre_pen_GJ', 'O_nre_pen_MJm2']
    result[fields_to_plot].to_csv(locator.get_lca_operation(), index=False, float_format='%.2f')


def run_as_script(scenario_path=None):
    import cea.globalvar
    gv = cea.globalvar.GlobalVariables()
    if not scenario_path:
        scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    lca_operation(locator=locator)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder')
    args = parser.parse_args()
    run_as_script(scenario_path=args.scenario)
