"""
===========================
Primary energy and CO2 emissions model algorithm for buidling operation
===========================
J. Fonseca  script development          26.08.15
D. Thomas   formatting and cleaning     27.08.15
D. Thomas   integration in toolbox      27.08.15

"""
from __future__ import division
import pandas as pd
import arcpy


class EmissionsTool(object):

    def __init__(self):
        self.label = 'Emissions'
        self.description = 'Calculate the Emissions for operation'
        self.canRunInBackground = False

    def getParameterInfo(self):
        path_total_demand = arcpy.Parameter(
            displayName="Energy demand (Total_demand.csv)",
            name="path_total_demand",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_total_demand.filter.list = ['csv']
        path_LCA_operation = arcpy.Parameter(
            displayName="LCA operation data (LCA_operation.xls)",
            name="path_LCA_operation",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_LCA_operation.filter.list = ['xls']
        path_properties = arcpy.Parameter(
            displayName="Properties File Path (properties.xls)",
            name="path_properties",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_properties.filter.list = ['xls']
        path_results = arcpy.Parameter(
            displayName="Results folder",
            name="path_results",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        return [path_total_demand, path_LCA_operation,
                path_properties, path_results]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        lca_operation(path_total_demand=parameters[0].valueAsText,
                      path_LCA_operation=parameters[1].valueAsText,
                      path_properties=parameters[2].valueAsText,
                      path_results=parameters[3].valueAsText)


def lca_operation(
        path_total_demand,
        path_LCA_operation,
        path_properties,
        path_results):
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
    demand = pd.read_csv(
        path_total_demand,
        usecols={
            'Name',
            'Qhsf',
            'Af',
            'Qcsf',
            'Qwwf',
            'Ealf'})
    systems = pd.read_excel(path_properties, sheetname='systems')
    systems_hs = systems[['Name', 'Generation_heating']].copy()
    systems_ww = systems[['Name', 'Generation_hotwater']].copy()
    systems_cs = systems[['Name', 'Generation_cooling']].copy()
    systems_e = systems[['Name', 'Generation_electricity']].copy()
    factors_heating = pd.read_excel(path_LCA_operation, sheetname='heating')
    factors_cooling = pd.read_excel(path_LCA_operation, sheetname='cooling')
    factors_electricity = pd.read_excel(
        path_LCA_operation,
        sheetname='electricity')

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

    heating2 = systems_ww.merge(
        demand,
        on='Name').merge(
        factors_heating,
        left_on='Generation_hotwater',
        right_on='code')
    heating['Qww_PEN_GJ'] = (heating2['Qwwf']*heating2['PEN']*3.6)
    heating['Qww_CO2_ton'] = (heating2['Qwwf']*heating2['CO2']*3.6)
    heating['Qww_PEN_MJm2'] = (heating['Qww_PEN_GJ']*1000)/heating2['Af']
    heating['Qww_CO2_kgm2'] = (heating['Qww_CO2_ton']*1000)/heating2['Af']

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

    Total = heating[['Name']].copy()
    Total['PEN_GJ'] = heating['Qhs_PEN_GJ'] + heating['Qww_PEN_GJ'] + \
        cooling['Qcs_PEN_GJ'] + electricity['Qe_PEN_GJ']
    Total['CO2_ton'] = heating['Qhs_CO2_ton'] + heating['Qww_CO2_ton'] + \
        cooling['Qcs_CO2_ton'] + electricity['Qe_CO2_ton']
    Total['PEN_MJm2'] = heating['Qhs_PEN_MJm2'] + heating['Qww_PEN_MJm2'] + \
        cooling['Qcs_PEN_MJm2'] + electricity['Qe_PEN_MJm2']
    Total['CO2_kgm2'] = heating['Qhs_CO2_kgm2'] + heating['Qww_CO2_kgm2'] + \
        cooling['Qcs_CO2_kgm2'] + electricity['Qe_CO2_kgm2']

    # save results to disc
    columns_to_drop = {'Ealf', 'Qcsf', 'Qhsf', 'Qwwf', 'officialcode', 'code'}
    heating.drop(columns_to_drop, inplace=True, axis=1)
    cooling.drop(columns_to_drop, inplace=True, axis=1)
    electricity.drop(columns_to_drop, inplace=True, axis=1)
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
    Total.to_csv(
        path_results +
        '\\' +
        'Total_LCA_operation.csv',
        index=False,
        float_format='%.2f')


def test_lca_operation():
    path_results = r'C:\CEA_FS2015_EXERCISE01\01_Scenario one\103_final output\emissions'  # noqa
    path_LCA_operation = r'C:\CEA_FS2015_EXERCISE01\01_Scenario one\101_input files\LCA data\LCA_operation.xls'  # noqa
    path_properties = r'C:\CEA_FS2015_EXERCISE01\01_Scenario one\102_intermediate output\building properties\properties.xls'  # noqa
    path_total_demand = r'C:\CEA_FS2015_EXERCISE01\01_Scenario one\103_final output\demand\Total_demand.csv'  # noqa
    lca_operation(
        path_LCA_operation,
        path_properties,
        path_total_demand,
        path_results)
    print 'done!'

if __name__ == '__main__':
    test_lca_operation()
