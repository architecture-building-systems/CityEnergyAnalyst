"""
===========================
Analytical energy demand model algorithm
===========================
File history and credits:
J. Fonseca  script development          24.08.15
D. Thomas   formatting and cleaning
D. Thomas   integration in toolbox
A. Elesawy  first steps with GitHub
"""
from __future__ import division
import pandas as pd
import numpy as np
import functions as f
import globalvar
reload(globalvar)
import arcpy
import tempfile
import os

gv = globalvar.GlobalVariables()
reload(f)


class DemandTool(object):

    def __init__(self):
        self.label = 'Demand'
        self.description = 'Calculate the Demand'
        self.canRunInBackground = False

    def getParameterInfo(self):
        path_radiation = arcpy.Parameter(
            displayName="Radiation Path",
            name="path_radiation",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_radiation.filter.list = ['csv']
        path_weather = arcpy.Parameter(
            displayName="Weather Data File Path",
            name="path_weather",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_weather.filter.list = ['csv']
        path_results = arcpy.Parameter(
            displayName="Demand Results Folder Path",
            name="path_results",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        path_properties = arcpy.Parameter(
            displayName="Properties File Path",
            name="path_properties",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_properties.filter.list = ['xls']
        return [path_radiation, path_weather,
                path_results, path_properties]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        analytical(path_radiation=parameters[0].valueAsText,
                   path_schedules=os.path.join(
                       os.path.dirname(__file__), 'db', 'Schedules'),
                   path_temporary_folder = tempfile.gettempdir(),
                   path_weather=parameters[1].valueAsText,
                   path_results=parameters[2].valueAsText,
                   path_properties=parameters[3].valueAsText,
                   gv=gv)


def analytical(path_radiation, path_schedules, path_temporary_folder, path_weather,
               path_results, path_properties, gv):
    """
    Algorithm to calculate the hourly demand of energy services in buildings
    using the integrated model of Fonseca et al. 2015. Appl. energy.

    Parameters
    ----------
    path_radiation:
        path to solar radiation file in vertical surfaces
        RadiationYearFinal.csv
    path_schedules: string
        path to folder containing occupancy profile schedules
    path_weather : string
        path to weather data file weather_design_hour.csv
    path_results : string
        path to demand results folder demand
    path_properties: string
        path to properties file properties.xls

    Returns
    -------
    single_demand: .csv
        csv file for every building with hourly demand data
    total_demand: .csv
        csv file of yearly demand data per buidling.
    """

    # local variables
    WeatherData = pd.read_csv(path_weather, usecols=['te', 'RH'])
    list_uses = gv.list_uses
    radiation_file = pd.read_csv(path_radiation)
    systems_temp = pd.read_excel(path_properties, sheetname='systems_temp')
    systems = pd.read_excel(path_properties, sheetname='systems')
    envelope = pd.read_excel(path_properties, sheetname='envelope')
    uses = pd.read_excel(path_properties, sheetname='uses')
    general = pd.read_excel(path_properties, sheetname='general')

    # weather conditions
    T_ext = np.array(WeatherData.te)
    RH_ext = np.array(WeatherData.RH)
    T_ext_max = T_ext.max()
    T_ext_min = T_ext.min()

    # obtain scehdules per building
    rows = len(list_uses)
    Profiles = list(range(rows))
    for row in range(rows):
        Profiles[row] = pd.read_csv(path_schedules + '\\' + 'Occupancy_' +
                                    list_uses[row] + '.csv', nrows=8760)

    # calculate file with all properties @ daren:
    all_properties = f.get_all_properties(uses,
                                          envelope,
                                          general,
                                          systems,
                                          systems_temp,
                                          radiation_file,
                                          gv)

    # calculate clean file of radiation - @ daren: this is a A BOTTLE NECK
    Solar = f.CalcIncidentRadiation(all_properties, radiation_file)

    # compute demand and save in disc
    buildings = all_properties.Name.count()
    list_buildings =  range(buildings) #buildings
    for building in list_buildings:
        total = f.CalcThermalLoads(
            building,
            all_properties.ix[building],
            Solar.ix[building],
            path_results,
            Profiles,
            list_uses,
            T_ext,
            T_ext_max,
            RH_ext,
            T_ext_min,path_temporary_folder,
            gv,
            0,
            0)
        message = 'Building No. ' + str(building+1) + ' completed out of ' + str(buildings)
        arcpy.AddMessage(message)

    #
    counter = 0
    for x in list_buildings:
        name = all_properties.Name[x]
        if counter ==0:
            df = pd.read_csv(path_temporary_folder+'\\'+name+'T'+'.csv')
            counter +=1
        else:
            df2 = pd.read_csv(path_temporary_folder+'\\'+name+'T'+'.csv')
            df = df.append(df2,ignore_index=True)
    df.to_csv(
        os.path.join(
            path_results,
            'Total_demand.csv'),
        index=False,
        float_format='%.2f')

    print 'finished'


def test_demand():
    path_radiation = r'C:\CEA_FS2015_EXERCISE02\01_Scenario one\102_intermediate output\radiation data\Radiation2000-2009.csv'  # noqa
    path_schedules = os.path.join(os.path.dirname(__file__), 'db', 'Schedules')
    path_weather = r'C:\CEA_FS2015_EXERCISE02\01_Scenario one\101_input files\weather data\weather_2000-2009_hour.csv'  # noqa
    path_results = r'C:\CEA_FS2015_EXERCISE02\01_Scenario one\103_final output\demand'  # noqa
    path_properties = r'C:\CEA_FS2015_EXERCISE02\01_Scenario one\102_intermediate output\building properties\properties.xls'  # noqa
    path_temporary_folder = tempfile.gettempdir()
    analytical(path_radiation, path_schedules, path_temporary_folder, path_weather,
               path_results, path_properties, gv)

if __name__ == '__main__':
    test_demand()
