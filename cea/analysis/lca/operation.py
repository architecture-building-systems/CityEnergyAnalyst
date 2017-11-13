"""
Non-renewable primary energy and CO2 emissions model algorithm for building operation

J. Fonseca  script development          26.08.15
D. Thomas   formatting and cleaning     27.08.15
D. Thomas   integration in toolbox      27.08.15
J. Fonseca  script redevelopment        19.04.16
"""
from __future__ import division

import pandas as pd
from geopandas import GeoDataFrame as gpdf
import os
import cea.globalvar
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


def lca_operation(locator, config, Qww_flag=True, Qhs_flag=True, Qcs_flag=True, Qcdata_flag=True, Qcrefri_flag=True,
                  Eal_flag=True, Eaux_flag=True, Epro_flag=True, Edata_flag=True):
    """
    Algorithm to calculate the primary energy and CO2 emissions of buildings according to the method used in the
    integrated model of [Fonseca-Schlueter-2015]_ and the performance factors of [ecobau.ch].

    :param locator: an InputLocator instance set to the scenario to work on
    :type locator: InputLocator
    :param Qww_flag: create a separate file with emissions due to hot water consumption?
    :type Qww_flag: boolean
    :param Qhs_flag: create a separate file with emissions due to space heating?
    :type Qhs_flag: boolean
    :param Qcs_flag: create a get separate file with emissions due to space cooling?
    :type Qcs_flag: boolean
    :param Qcdata_flag: create a separate file with emissions due to servers cooling?
    :type Qcdata_flag: boolean
    :param Qcrefri_flag: create a separate file with emissions due to refrigeration?
    :type Qcrefri_flag: boolean
    :param Eal_flag: create a separate file with emissions due to appliances and lighting?
    :type Eal_flag: boolean
    :param Eaux_flag: create a separate file with emissions due to auxiliary electricity?
    :type Eaux_flag: boolean
    :param Epro_flag: create a separate file with emissions due to electricity in industrial processes?
    :type Epro_flag: boolean
    :param Edata_flag: create a separate file with emissions due to electricity consumption in data centers?
    :type Edata_flag: boolean

    The following file is created by this script:

    - total_LCA_operation: .csv
        csv file of yearly non-renewable primary energy demand and CO2 emissions per building for all energy
        services (i.e. heating, hot water, cooling, electricity) both total and per square meter

    Depending on which flags were set, the following files can also be created by this script:

    - Qhs_LCA_operation: .csv
        describes the emissions and primary energy due to space heating
    - Qww_LCA_operation: .csv
        describes the emissions and primary energy due to domestic hot water consumption
    - Qcs_LCA_operation: .csv
        describes the emissions and primary energy due to space cooling
    - Qcdata_LCA_operation: .csv
        describes the emissions and primary energy due to servers cooling
    - Qcrefri_LCA_operation: .csv
        describes the emissions and primary energy due to refrigeration
    - Eal_LCA_operation: .csv
        describes the emissions and primary energy due to appliances and lighting
    - Eaux_LCA_operation: .csv
        describes the emissions and primary energy due to auxiliary electricity
    - Epro_LCA_operation: .csv
        describes the emissions and primary energy due to electricity in industrial processes
    - Edata_LCA_operation: .csv
        describes the emissions and primary energy due to electricity consumption in data centers

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
    data_LCI = locator.get_life_cycle_inventory_supply_systems(config.region)
    factors_heating = pd.read_excel(data_LCI, sheetname='heating')
    factors_dhw = pd.read_excel(data_LCI, sheetname='dhw')
    factors_cooling = pd.read_excel(data_LCI, sheetname='cooling')
    factors_electricity = pd.read_excel(data_LCI, sheetname='electricity')

    # local variables
    QC_flag = E_flag = True  # minimum output values
    result_folder = locator.get_lca_emissions_results_folder()

    # calculate the total operational non-renewable primary energy demand and CO2 emissions
    ## create data frame for each type of end use energy containing the type of supply system use, the final energy
    ## demand and the primary energy and emissions factors for each corresponding type of supply system
    heating = supply_systems.merge(demand, on='Name').merge(factors_heating, left_on='type_hs', right_on='code')
    dhw = supply_systems.merge(demand, on='Name').merge(factors_dhw, left_on='type_dhw', right_on='code')
    cooling = supply_systems.merge(demand, on='Name').merge(factors_cooling, left_on='type_cs', right_on='code')
    electricity = supply_systems.merge(demand, on='Name').merge(factors_electricity, left_on='type_el', right_on='code')

    ## calculate the operational primary energy and emissions for heating services
    heating_services = [[Qhs_flag, 'Qhsf_MWhyr', 'Qhsf', 'Af_m2']]
    for x in heating_services:
        fields_to_plot = ['Name', 'GFA_m2', x[2] + '_ghg_ton', x[2] + '_ghg_kgm2', x[2] + '_nre_pen_GJ',
                          x[2] + '_nre_pen_MJm2']
        # calculate the total (GJ) and specific (MJ/m2) operational non-renewable primary energy demand (O_nre_pen_)
        heating[fields_to_plot[4]] = heating[x[1]] * heating['PEN'] * 3.6
        heating[fields_to_plot[5]] = (heating[x[1]] * heating['PEN'] * 3600) / heating['GFA_m2']
        # calculate the total (t CO2-eq) and specific (kg CO2-eq/m2) operational greenhouse gas emissions (O_ghg_)
        heating[fields_to_plot[2]] = heating[x[1]] * heating['CO2'] * 3.6
        heating[fields_to_plot[3]] = (heating[x[1]] * heating['CO2'] * 3600) / heating['GFA_m2']
        if x[0]:
            # if Qhs_flag is True, create the corresponding csv file
            heating[fields_to_plot].to_csv(os.path.join(result_folder, '%s_LCA_operation.csv' % x[2]), index=False,
                                           float_format='%.2f')

    ## calculate the operational primary energy and emissions for domestic hot water services
    dhw_services = [[Qww_flag, 'Qwwf_MWhyr', 'Qwwf', 'Af_m2']]
    for x in dhw_services:
        fields_to_plot = ['Name', 'GFA_m2', x[2] + '_ghg_ton', x[2] + '_ghg_kgm2', x[2] + '_nre_pen_GJ',
                          x[2] + '_nre_pen_MJm2']
        # calculate the total (GJ) and specific (MJ/m2) operational non-renewable primary energy demand (O_nre_pen_)
        dhw[fields_to_plot[4]] = dhw[x[1]] * dhw['PEN'] * 3.6
        dhw[fields_to_plot[5]] = (dhw[x[1]] * dhw['PEN'] * 3600) / dhw['GFA_m2']
        # calculate the total (t CO2-eq) and specific (kg CO2-eq/m2) operational greenhouse gas emissions (O_ghg_)
        dhw[fields_to_plot[2]] = dhw[x[1]] * dhw['CO2'] * 3.6
        dhw[fields_to_plot[3]] = (dhw[x[1]] * dhw['CO2'] * 3600) / dhw['GFA_m2']
        if x[0]:
            # if Qww_flag is True, create the corresponding csv file
            dhw[fields_to_plot].to_csv(os.path.join(result_folder, x[2] + '_LCA_operation.csv'), index=False,
                                       float_format='%.2f')
    ## calculate the operational primary energy and emissions for cooling services
    cooling_services = [(QC_flag, 'QCf_MWhyr', 'QCf'), (Qcs_flag, 'Qcsf_MWhyr', 'Qcsf'),
                        (Qcdata_flag, 'Qcdataf_MWhyr', 'Qcdataf'), (Qcrefri_flag, 'Qcref_MWhyr', 'Qcref')]
    for x in cooling_services:
        fields_to_plot = ['Name', 'GFA_m2', x[2] + '_ghg_ton', x[2] + '_ghg_kgm2', x[2] + '_nre_pen_GJ',
                          x[2] + '_nre_pen_MJm2']
        # calculate the total (GJ) and specific (MJ/m2) operational non-renewable primary energy demand (O_nre_pen_)
        cooling[fields_to_plot[4]] = cooling[x[1]] * cooling['PEN'] * 3.6
        cooling[fields_to_plot[5]] = (cooling[x[1]] * cooling['PEN'] * 3600) / cooling['GFA_m2']
        # calculate the total (t CO2-eq) and specific (kg CO2-eq/m2) operational greenhouse gas emissions (O_ghg_)
        cooling[fields_to_plot[2]] = cooling[x[1]] * cooling['CO2'] * 3.6
        cooling[fields_to_plot[3]] = (cooling[x[1]] * cooling['CO2'] * 3600) / cooling['GFA_m2']
        if x[0]:
            # if QC_flag, Qcs_flag, Qcsdata_flag or Qcrefri_flag is True, create the corresponding csv file
            cooling[fields_to_plot].to_csv(os.path.join(result_folder, x[2] + '_LCA_operation.csv'), index=False,
                                           float_format='%.2f')

    ## calculate the operational primary energy and emissions for electrical services
    electrical_services = [(E_flag, 'Ef_MWhyr', 'Ef'), (Eal_flag, 'Ealf_MWhyr', 'Ealf'),
                           (Eaux_flag, 'Eauxf_MWhyr', 'Eauxf'), (Epro_flag, 'Eprof_MWhyr', 'Eprof'),
                           (Edata_flag, 'Edataf_MWhyr', 'Edataf')]
    for x in electrical_services:
        fields_to_plot = ['Name', 'GFA_m2', x[2] + '_ghg_ton', x[2] + '_ghg_kgm2', x[2] + '_nre_pen_GJ',
                          x[2] + '_nre_pen_MJm2']
        # calculate the total (GJ) and specific (MJ/m2) operational non-renewable primary energy demand (O_nre_pen_)
        electricity[fields_to_plot[4]] = electricity[x[1]] * electricity['PEN'] * 3.6
        electricity[fields_to_plot[5]] = electricity[x[1]] * electricity['PEN'] * 3600 / electricity['GFA_m2']
        # calculate the total (t CO2-eq) and specific (kg CO2-eq/m2) operational greenhouse gas emissions (O_ghg_)
        electricity[fields_to_plot[2]] = electricity[x[1]] * electricity['CO2'] * 3.6
        electricity[fields_to_plot[3]] = (electricity[x[1]] * electricity['CO2'] * 3600) / electricity['GFA_m2']
        if x[0]:
            # if E_flag, Eal_flag, Eaux_flag, Epro_flag or Edata_flag is True, create the corresponding csv file
            electricity[fields_to_plot].to_csv(result_folder + '\\' + x[2] + '_LCA_operation.csv', index=False,
                                               float_format='%.2f')

    # create a dataframe with the results for each energy service
    result = heating.merge(dhw, on='Name', suffixes=['_a', '_b']).merge(cooling, on='Name', suffixes=['a', '_b']).merge(
        electricity, on='Name')
    result.rename(columns={'GFA_m2_x': 'GFA_m2'}, inplace=True)

    # calculate the total operational non-renewable primary energy demand and emissions as a sum of the results for each
    # energy service used in the building
    result['O_nre_pen_GJ'] = result['Qhsf_nre_pen_GJ'] + result['Qwwf_nre_pen_GJ'] + result['QCf_nre_pen_GJ'] + result[
        'Ef_nre_pen_GJ']
    result['O_ghg_ton'] = result['Qhsf_ghg_ton'] + result['Qwwf_ghg_ton'] + result['QCf_ghg_ton'] + result['Ef_ghg_ton']
    result['O_nre_pen_MJm2'] = result['Qhsf_nre_pen_MJm2'] + result['Qwwf_nre_pen_MJm2'] + result['QCf_nre_pen_MJm2'] + \
                               result['Ef_nre_pen_MJm2']
    result['O_ghg_kgm2'] = result['Qhsf_ghg_kgm2'] + result['Qwwf_ghg_kgm2'] + result['QCf_ghg_kgm2'] + result[
        'Ef_ghg_kgm2']

    # export the total operational non-renewable energy demand and emissions for each building
    fields_to_plot = ['Name', 'GFA_m2', 'O_ghg_ton', 'O_ghg_kgm2', 'O_nre_pen_GJ', 'O_nre_pen_MJm2']
    result[fields_to_plot].to_csv(locator.get_lca_operation(), index=False, float_format='%.2f')


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    print('Running emissions with scenario = %s' % config.scenario)
    print('Running emissions with emissions-variables = %s' % config.emissions.emissions_variables)

    Qww_flag = 'Qww' in config.emissions.emissions_variables
    Qhs_flag = 'Qhs' in config.emissions.emissions_variables
    Qcs_flag = 'Qcs' in config.emissions.emissions_variables
    Qcdata_flag = 'Qcdata' in config.emissions.emissions_variables
    Qcrefri_flag = 'Qcrefri' in config.emissions.emissions_variables
    Eal_flag = 'Eal' in config.emissions.emissions_variables
    Eaux_flag = 'Eaux' in config.emissions.emissions_variables
    Epro_flag = 'Epro' in config.emissions.emissions_variables
    Edata_flag = 'Edata' in config.emissions.emissions_variables

    lca_operation(locator=locator, config=config, Qww_flag=Qww_flag, Qhs_flag=Qhs_flag, Qcs_flag=Qcs_flag, Qcdata_flag=Qcdata_flag,
                  Qcrefri_flag=Qcrefri_flag, Eal_flag=Eal_flag, Eaux_flag=Eaux_flag, Epro_flag=Epro_flag,
                  Edata_flag=Edata_flag)


if __name__ == '__main__':
    main(cea.config.Configuration())
