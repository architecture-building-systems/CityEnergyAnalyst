"""
===========================
Run multiple scenarios
===========================
File history and credits:
J. Fonseca  script development and cleaning          10.18.15

"""
from __future__ import division

import os
import tempfile

import arcpy
import embodied
import pandas as pd

import cea.globalvar
import cea.preprocessing.properties
from cea import demand
from cea.analysis import emissions
from cea.plots import heatmaps

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


reload(cea.globalvar)
reload(heatmaps)
reload(embodied)
reload(cea.preprocessing.properties)
reload(emissions)
reload(demand)

gv = cea.globalvar.GlobalVariables()

class MultipleTool(object):

    def __init__(self):
        self.label = 'Multi_scenarios_tool'
        self.description = 'Run_multiple_scenarios'
        self.canRunInBackground = False

    def getParameterInfo(self):
        path_list_scenarios = arcpy.Parameter(
            displayName="list_scenarios",
            name="path_list_scenarios",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_list_scenarios.filter.list = ['xls']
        return [path_list_scenarios]
                
    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return
    
    def updateMessages(self, parameters):
        return
    
    def execute(self, parameters, messages):
        multiple_scenarios(path_list_scenarios=parameters[0].valueAsText,
                            path_LCA_embodied_energy = os.path.join(os.path.dirname(__file__), 'databases', 'Archetypes', 'Archetypes_embodied_energy.csv'),
                            path_LCA_embodied_emissions = os.path.join(os.path.dirname(__file__), 'databases', 'Archetypes', 'Archetypes_embodied_emissions.csv'),
                            path_archetypes = os.path.join(os.path.dirname(__file__),'databases', 'Archetypes', 'Archetypes_HVAC_properties.csv'),
                            path_schedules=os.path.join(os.path.dirname(__file__), 'databases', 'Schedules'),
                            path_temporary_folder = tempfile.gettempdir(),
                            gv=gv)
                    
def multiple_scenarios(path_list_scenarios, path_LCA_embodied_energy, path_LCA_embodied_emissions, path_archetypes, path_schedules, path_temporary_folder, gv):
    """
    Algorithm to calculate multiple scenarios at the time

    Parameters
    ----------
    To do

    Returns
    -------
    To do
    """
    paths_of_scenarios = pd.read_excel(path_list_scenarios, sheetname='scenarios')
    number_scenarios = paths_of_scenarios.path_scenario.count()
    
    for x in range(number_scenarios):
        
        if paths_of_scenarios.run_properties[x] == 1:
            path_buildings = paths_of_scenarios.path_scenario[x]+'\\'+r'101_input files\feature classes'+'\\'+'buildings.shp'  # noqa
            path_generation = paths_of_scenarios.path_scenario[x]+'\\'+r'101_input files\feature classes'+'\\'+'generation.shp'  # noqa
            path_results = paths_of_scenarios.path_scenario[x]+'\\'+r'102_intermediate output\building properties'  # noqa
            generate_uses = True
            generate_envelope = True
            generate_systems = True
            generate_equipment = True
            cea.preprocessing.properties.properties(path_archetypes, path_buildings, path_generation, path_results, generate_uses,
                                                    generate_envelope, generate_systems, generate_equipment,
                                                    gv)
            message = 'Properties scenario ' + str(x) + ' completed'
            arcpy.AddMessage(message)
            
        if paths_of_scenarios.run_demand[x] == 1:
            path_radiation = paths_of_scenarios.path_scenario[x]+'\\'+r'102_intermediate output\radiation data'+'\\'+paths_of_scenarios.file_name_radiation[x]  # noqa
            path_weather = paths_of_scenarios.path_scenario[x]+'\\'+r'101_input files\weather data'+'\\'+paths_of_scenarios.file_name_weather[x]  # noqa
            path_results = paths_of_scenarios.path_scenario[x]+'\\'+r'103_final output\demand'  # noqa
            path_properties = paths_of_scenarios.path_scenario[x]+'\\'+r'102_intermediate output\building properties\properties.xls'  # noqa
            path_temporary_folder = tempfile.gettempdir()
            demand.analytical(path_radiation, path_schedules, path_temporary_folder, path_weather,
                              path_results, path_properties, gv)

            message = 'Demand scenario ' + str(x) + ' completed'
            arcpy.AddMessage(message)
            
        if paths_of_scenarios.run_emissions[x] == 1:
            path_results = paths_of_scenarios.path_scenario[x]+'\\'+r'103_final output\emissions'  # noqa
            path_LCA_operation = paths_of_scenarios.path_scenario[x]+'\\'+r'101_input files\LCA data\LCA_operation.xls'  # noqa
            path_properties = paths_of_scenarios.path_scenario[x]+'\\'+r'102_intermediate output\building properties\properties.xls'  # noqa
            path_total_demand = paths_of_scenarios.path_scenario[x]+'\\'+r'103_final output\demand\Total_demand.csv'  # noqa
            emissions.lca_operation(
                path_total_demand,
                path_properties,
                path_LCA_operation,
                path_results)     

            message = 'emissions operation scenario ' + str(x) + ' completed'
            arcpy.AddMessage(message)
            
        if paths_of_scenarios.run_embodied[x] == 1:
            path_results = paths_of_scenarios.path_scenario[x]+'\\'+r'103_final output\emissions'  # noqa
            path_properties = paths_of_scenarios.path_scenario[x]+'\\'+r'102_intermediate output\building properties\properties.xls'  # noqa
            yearcalc = paths_of_scenarios.year_calc[x]
            retrofit_windows = True
            retrofit_roof = True
            retrofit_walls = True
            retrofit_partitions = True
            retrofit_int_floors = True
            retrofit_installations = True
            retrofit_basement_floor = True
            embodied.lca_embodied(
                path_LCA_embodied_energy,
                path_LCA_embodied_emissions,
                path_properties,
                path_results,
                yearcalc,
                retrofit_windows,
                retrofit_roof,
                retrofit_walls,
                retrofit_partitions,
                retrofit_int_floors,
                retrofit_installations,
                retrofit_basement_floor,
                gv)            

            message = 'gray emissions scenario ' + str(x) + ' completed'
            arcpy.AddMessage(message)
            
        if paths_of_scenarios.run_heatmaps[x] == 1:  
            analysis_field_variables = ["QHf", "QCf", "Ef"]  # noqa
            path_buildings = paths_of_scenarios.path_scenario[x]+'\\'+r'101_input files\feature classes'+'\\'+'buildings.shp'  # noqa
            path_variables = paths_of_scenarios.path_scenario[x]+'\\'+r'103_final output\demand'  # noqa
            path_results = paths_of_scenarios.path_scenario[x]+'\\'+r'103_final output\heatmaps'  # noqa
            file_variable = 'Total_demand.csv'
            heatmaps.heatmaps(
                analysis_field_variables,
                path_variables,
                path_buildings,
                path_results,
                path_temporary_folder,
                file_variable)              
    print 'finished'
                   
def test_multiple_scenarios():
    path_list_scenarios = r'C:\CEA_FS2015_EXERCISE02\list_scenarios.xls'
    path_LCA_embodied_energy = os.path.join(os.path.dirname(__file__), 'databases', 'Archetypes', 'Archetypes_embodied_energy.csv')  # noqa
    path_LCA_embodied_emissions = os.path.join(os.path.dirname(__file__), 'databases', 'Archetypes', 'Archetypes_embodied_emissions.csv')  # noqa
    path_archetypes = os.path.join(os.path.dirname(__file__),'databases', 'Archetypes', 'Archetypes_HVAC_properties.csv')
    path_schedules = os.path.join(os.path.dirname(__file__), 'databases', 'Schedules') #noqa
    path_temporary_folder = tempfile.gettempdir()
    multiple_scenarios(path_list_scenarios, path_LCA_embodied_energy, path_LCA_embodied_emissions, path_archetypes, path_schedules, path_temporary_folder, gv)

if __name__ == '__main__':
    test_multiple_scenarios()