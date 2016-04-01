"""
===========================
Primary energy and CO2 emissions model algorithm for building operation
===========================
J. Fonseca  script development          26.08.15
D. Thomas   formatting and cleaning     27.08.15
D. Thomas   integration in toolbox      27.08.15

"""
from __future__ import division
import pandas as pd
import arcpy


def lca_operation(path_total_demand, path_properties, path_LCA_operation, path_results):
    """
    algorithm to calculate the primary energy and CO2 emissions of buildings
    according to the method used in the integrated model of
    Fonseca et al. 2015.
    Appl. energy. and the performance factors of ecobau.ch

    Parameters
    ----------
    path_total_demand: string
        path to database of total energy consumption Total.csv
    path_LCA_operation: string
        path to database of emisisions and primary energy factors
        LCA_operation.xls
    path_properties: string
        path to properties file properties.xls
    path_results : string
        path to demand results folder emissions

    Returns
    -------
    LCA_operation:.csv
        csv file of yearly primary energy per building and energy service
        (i.e. heating, hot water, cooling, electricity)
    """

    # local files
    demand = pd.read_csv(path_total_demand, usecols=['Name', 'Qhsf', 'Af', 'Qcsf', 'Qwwf', 'Ef'])
    systems = pd.read_excel(path_properties, sheetname='systems')
    systems_hs = systems[['Name', 'Generation_heating']].copy()
    systems_cs = systems[['Name', 'Generation_cooling']].copy()
    systems_e = systems[['Name', 'Generation_electricity']].copy()
    factors_heating = pd.read_excel(path_LCA_operation, sheetname='heating')
    factors_cooling = pd.read_excel(path_LCA_operation, sheetname='cooling')
    factors_electricity = pd.read_excel(path_LCA_operation, sheetname='electricity')

    # calculate values Qhs_PEN_MJm2, Qww_PEN_MJm2, Qh_PEN_MJm2
    # Qhs_CO2_kgm2, Qww_CO2_kgm2, Qh_CO2_kgm2
    # Qhs_PEN_GJ, Qww_PEN_GJ, Qh_PEN_GJ
    # Qhs_CO2_ton, Qww_CO2_ton, Qh_CO2_ton
    heating = systems_hs.merge(
        demand,
        on='Name').merge(
        factors_heating,
        left_on='Generation_heating',
        right_on='code')
    heating['Qhs_PEN_GJ'] = (heating['Qhsf']*heating['PEN']*3.6)
    heating['Qhs_CO2_ton'] = (heating['Qhsf']*heating['CO2']*3.6)
    heating['Qhs_PEN_MJm2'] = (heating['Qhs_PEN_GJ']*1000)/heating['Af']
    heating['Qhs_CO2_kgm2'] = (heating['Qhs_CO2_ton']*1000)/heating['Af']
    heating['Qww_PEN_GJ'] = (heating['Qwwf']*heating['PEN']*3.6)
    heating['Qww_CO2_ton'] = (heating['Qwwf']*heating['CO2']*3.6)
    heating['Qww_PEN_MJm2'] = (heating['Qww_PEN_GJ']*1000)/heating['Af']
    heating['Qww_CO2_kgm2'] = (heating['Qww_CO2_ton']*1000)/heating['Af']

    cooling = systems_cs.merge(
        demand,
        on='Name').merge(
        factors_cooling,
        left_on='Generation_cooling',
        right_on='code')
    cooling['Qcs_PEN_GJ'] = (cooling['Qcsf']*cooling['PEN']*3.6)
    cooling['Qcs_CO2_ton'] = (cooling['Qcsf']*cooling['CO2']*3.6)
    cooling['Qcs_PEN_MJm2'] = (cooling['Qcs_PEN_GJ']*1000)/cooling['Af']
    cooling['Qcs_CO2_kgm2'] = (cooling['Qcs_CO2_ton']*1000)/cooling['Af']

    electricity = systems_e.merge(
        demand,
        on='Name').merge(
        factors_electricity,
        left_on='Generation_electricity',
        right_on='code')
    electricity['Qe_PEN_GJ'] = (electricity['Ealf']*electricity['PEN']*3.6)
    electricity['Qe_CO2_ton'] = (electricity['Ealf']*electricity['CO2']*3.6)
    electricity['Qe_PEN_MJm2'] = (
        electricity['Qe_PEN_GJ']*1000)/electricity['Af']
    electricity['Qe_CO2_kgm2'] = (
        electricity['Qe_CO2_ton']*1000)/electricity['Af']


    # drop columns and join all results
    columns_to_drop = ['Ealf', 'Qcsf', 'Qhsf', 'Qwwf', 'officialcode', 'code',
                       'COP_low_temp','COP_high_temp','Description','Af','PEN','CO2']
    columns_to_drop2 = ['Ealf', 'Qcsf', 'Qhsf', 'Qwwf', 'officialcode', 'code','Af',
                        'Description','PEN','CO2']
    heating.drop(columns_to_drop, inplace=True, axis=1)
    cooling.drop(columns_to_drop, inplace=True, axis=1)
    electricity.drop(columns_to_drop2, inplace=True, axis=1)
    
    total = heating.merge(cooling,on='Name').merge(electricity,on='Name')
    
    total['PEN_GJ'] = total['Qhs_PEN_GJ'] + total['Qww_PEN_GJ'] + \
        total['Qcs_PEN_GJ'] + total['Qe_PEN_GJ']
        
    total['PCO2_ton'] = total['Qhs_CO2_ton'] + total['Qww_CO2_ton'] + \
        total['Qcs_CO2_ton'] + total['Qe_CO2_ton']
        
    total['PEN_MJm2'] = total['Qhs_PEN_MJm2'] + total['Qww_PEN_MJm2'] + \
        total['Qcs_PEN_MJm2'] + total['Qe_PEN_MJm2']
        
    total['PCO2_kgm2'] = total['Qhs_CO2_kgm2'] + total['Qww_CO2_kgm2'] + \
        total['Qcs_CO2_kgm2'] + total['Qe_CO2_kgm2']

    # save results to disc
    heating.to_csv(
        path_results +
        '\\' +
        'heating_LCA.csv',
        index=False,
        float_format='%.2f')
    cooling.to_csv(
        path_results +
        '\\' +
        'cooling_LCA.csv',
        index=False,
        float_format='%.2f')
    electricity.to_csv(
        path_results +
        '\\' +
        'electricity_LCA.csv',
        index=False,
        float_format='%.2f')
    total[['Name','PEN_GJ','PCO2_ton','PEN_MJm2','PCO2_kgm2']].to_csv(
        path_results +
        '\\' +
        'Total_LCA_operation.csv',
        index=False,
        float_format='%.2f')


def test_lca_operation():
    path_results = r'C:\CEA_FS2015_EXERCISE02\01_Scenario one\103_final output\emissions'  # noqa
    path_LCA_operation = r'C:\CEA_FS2015_EXERCISE02\01_Scenario one\101_input files\LCA data\LCA_operation.xls'  # noqa
    path_properties = r'C:\CEA_FS2015_EXERCISE02\01_Scenario one\102_intermediate output\building properties\properties - Copy.xls'  # noqa
    path_total_demand = r'C:\CEA_FS2015_EXERCISE02\01_Scenario one\103_final output\demand\Total_demand.csv'  # noqa
    lca_operation(
        path_total_demand=path_total_demand,
        path_properties=path_properties,
        path_LCA_operation=path_LCA_operation,
        path_results=path_results)
    print 'done!'

if __name__ == '__main__':
    test_lca_operation()
