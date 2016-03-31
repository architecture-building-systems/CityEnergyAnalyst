"""
ArcGIS Tool classes for integrating the CEA with ArcGIS.
"""
import os
import arcpy
from cea import globalvar

gv = globalvar.GlobalVariables()

class PropertiesTool(object):
    """
    integrate the properties script with ArcGIS.
    """
    def __init__(self):
        self.label = 'Properties'
        self.description = 'Query building properties from statistical database'
        self.canRunInBackground = False

    def getParameterInfo(self):
        path_buildings = arcpy.Parameter(
            displayName="Buildings file",
            name="path_buildings",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_buildings.filter.list = ['shp']
        path_generation = arcpy.Parameter(
            displayName="Genearation systems file",
            name="path_generation",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_generation.filter.list = ['shp']
        path_results = arcpy.Parameter(
            displayName="path to intermediate results folder",
            name="path_results",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        generate_uses = arcpy.Parameter(
            displayName="Generate the uses",
            name="generate_uses",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        generate_envelope = arcpy.Parameter(
            displayName="Generate the envelope",
            name="generate_envelope",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        generate_systems = arcpy.Parameter(
            displayName="Generate the systems",
            name="generate_systems",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        generate_equipment = arcpy.Parameter(
            displayName="Generate the equipment",
            name="generate_equipment",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        return [path_buildings, path_generation, path_results, generate_uses,
                generate_envelope, generate_systems, generate_equipment]


class DemandTool(object):
    """integrate the demand script with ArcGIS"""
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
        from cea.demand import demand_calculation
        import tempfile
        demand_calculation(path_radiation=parameters[0].valueAsText,
                           path_schedules=os.path.join(
                               os.path.dirname(__file__), 'db', 'Schedules'),
                           path_temporary_folder=tempfile.gettempdir(),
                           path_weather=parameters[1].valueAsText,
                           path_results=parameters[2].valueAsText,
                           path_properties=parameters[3].valueAsText,
                           gv=gv)


class EmbodiedEnergyTool(object):

    def __init__(self):
        self.label = 'Embodied Energy'
        self.description = 'Calculate the Emissions for operation'
        self.canRunInBackground = False

    def getParameterInfo(self):
        yearcalc = arcpy.Parameter(
            displayName="Year to calculate",
            name="yearcalc",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")

        path_properties = arcpy.Parameter(
            displayName="Path to properties file (properties.xls)",
            name="path_properties",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_properties.filter.list = ['xls']

        path_results = arcpy.Parameter(
            displayName="Path to emissions results folder",
            name="path_results",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        retrofit_windows = arcpy.Parameter(
            displayName="retrofit windows",
            name="retrofit_windows",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")

        retrofit_roof = arcpy.Parameter(
            displayName="retrofit roof",
            name="retrofit_roof",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")

        retrofit_walls = arcpy.Parameter(
            displayName="retrofit walls",
            name="retrofit_walls",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")

        retrofit_partitions = arcpy.Parameter(
            displayName="retrofit partitions",
            name="retrofit_partitions",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")

        retrofit_int_floors = arcpy.Parameter(
            displayName="retrofit int floors",
            name="retrofit_int_floors",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")

        retrofit_installations = arcpy.Parameter(
            displayName="retrofit installations",
            name="retrofit_installations",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")

        retrofit_basement_floor = arcpy.Parameter(
            displayName="retrofit basement floor",
            name="retrofit_basement_floor",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")

        return [path_properties,
                path_results,
                yearcalc,
                retrofit_windows,
                retrofit_roof,
                retrofit_walls,
                retrofit_partitions,
                retrofit_int_floors,
                retrofit_installations,
                retrofit_basement_floor]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        path_LCA_embodied_energy = os.path.join(
            os.path.dirname(__file__),
            'db', 'Archetypes', 'Archetypes_embodied_energy.csv')
        path_LCA_embodied_emissions = os.path.join(
            os.path.dirname(__file__),
            'db', 'Archetypes', 'Archetypes_embodied_emissions.csv')

        path_properties = parameters[0]
        path_results = parameters[1]
        yearcalc = parameters[2]
        retrofit_windows = parameters[3]
        retrofit_roof = parameters[4]
        retrofit_walls = parameters[5]
        retrofit_partitions = parameters[6]
        retrofit_int_floors = parameters[7]
        retrofit_installations = parameters[8]
        retrofit_basement_floor = parameters[9]

        from cea.embodied import lca_embodied
        lca_embodied(
            path_LCA_embodied_energy=path_LCA_embodied_energy,
            path_LCA_embodied_emissions=path_LCA_embodied_emissions,
            path_properties=path_properties.valueAsText,
            path_results=path_results.valueAsText,
            yearcalc=int(yearcalc.valueAsText),
            retrofit_windows=bool(retrofit_windows),
            retrofit_roof=bool(retrofit_roof),
            retrofit_walls=bool(retrofit_walls),
            retrofit_partitions=bool(retrofit_partitions),
            retrofit_int_floors=bool(retrofit_int_floors),
            retrofit_installations=bool(retrofit_installations),
            retrofit_basement_floor=bool(retrofit_basement_floor),
            gv=gv)


class EmissionsTool(object):

    def __init__(self):
        self.label = 'Emissions Operation'
        self.description = 'Calculate emissions and primary energy due to building operation'
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
        from cea.emissions import lca_operation
        lca_operation(path_total_demand=parameters[0].valueAsText,
                      path_LCA_operation=parameters[1].valueAsText,
                      path_properties=parameters[2].valueAsText,
                      path_results=parameters[3].valueAsText)


class GraphsDemandTool(object):

    def __init__(self):
        self.label = 'Demand graphs'
        self.description = 'Calculate Graphs of the Demand'
        self.canRunInBackground = False

    def getParameterInfo(self):
        path_buildings = arcpy.Parameter(
            displayName="Buildings file",
            name="path_buildings",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_buildings.filter.list = ['shp']
        path_results_demand = arcpy.Parameter(
            displayName="Demand Folder Path",
            name="path_results_demand",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        path_results = arcpy.Parameter(
            displayName="Graphs Demand Results Folder Path",
            name="path_results",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        return [path_buildings, path_results_demand,
                path_results]

    def execute(self, parameters, messages):
        from cea.graphs import graphs_demand
        graphs_demand(path_buildings=parameters[0].valueAsText,
                    path_results_demand=parameters[1].valueAsText,
                    path_results = parameters[2].valueAsText,
                    analysis_fields = ["Ealf", "Qhsf","Qwwf", "Qcsf"])


class HeatmapsTool(object):

    def __init__(self):
        self.label = 'Heatmaps'
        self.description = 'Create heatmap data layers'
        self.canRunInBackground = False

    def getParameterInfo(self):
        path_data = arcpy.Parameter(
            displayName="File containing the data to read (Total_demand.csv)",
            name="path_data",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_data.filter.list = ['csv']
        analysis_field_variables = arcpy.Parameter(
            displayName="Variables to analyse",
            name="analysis_field_variables",
            datatype="String",
            parameterType="Required",
            multiValue=True,
            direction="Input")
        analysis_field_variables.filter.list = []
        path_buildings = arcpy.Parameter(
            displayName="Buildings file",
            name="path_buildings",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_buildings.filter.list = ['shp']
        path_results = arcpy.Parameter(
            displayName="Results folder",
            name="path_results",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        return [path_data, analysis_field_variables,
                path_buildings, path_results]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        import pandas as pd
        path_data = parameters[0]
        analysis_field_variables = parameters[1]
        csv = pd.read_csv(path_data.valueAsText)
        fields = set(csv.columns.tolist())
        #fields.remove('Name')
        analysis_field_variables.filter.list = list(fields)
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        import tempfile
        from cea.heatmaps import heatmaps
        
        path_data = parameters[0].valueAsText
        value_table = parameters[1].value
        path_buildings = parameters[2].valueAsText
        path_results = parameters[3].valueAsText
        path_variables = os.path.dirname(path_data)
        path_temporary_folder = tempfile.gettempdir()
        file_variable = os.path.basename(path_data)
        analysis_field_variables = [value_table.getvalue(i, 0)
                                    for i in range(value_table.rowcount)]
        heatmaps(
            analysis_field_variables=analysis_field_variables,
            path_variables=path_variables,
            path_buildings=path_buildings,
            path_results=path_results,
            path_temporary_folder=path_temporary_folder,
            file_variable=file_variable)
