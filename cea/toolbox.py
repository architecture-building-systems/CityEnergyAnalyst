"""
ArcGIS Tool classes for integrating the CEA with ArcGIS.
"""
import os
import arcpy
from cea import globalvar
import inputlocator
reload(inputlocator)

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
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        prop_thermal_flag = arcpy.Parameter(
            displayName="Generate thermal properties of the building envelope",
            name="prop_thermal_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        prop_thermal_flag.value = True
        prop_architecture_flag = arcpy.Parameter(
            displayName="Generate construction and architecture properties",
            name="prop_architecture_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        prop_architecture_flag.value = True
        prop_HVAC_flag = arcpy.Parameter(
            displayName="Generate HVAC systems properties",
            name="prop_HVAC_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        prop_HVAC_flag.value = True
        return [scenario_path, prop_thermal_flag, prop_architecture_flag, prop_HVAC_flag]

    def execute(self, parameters, messages):
        from cea.properties import properties

        scenario_path = parameters[0].valueAsText
        locator = inputlocator.InputLocator(scenario_path)

        prop_thermal_flag = parameters[1]
        prop_architecture_flag = parameters[2]
        prop_HVAC_flag = parameters[3]
        properties(locator=locator,
                   prop_thermal_flag=prop_thermal_flag.value,
                   prop_architecture_flag=prop_architecture_flag.value,
                   prop_hvac_flag=prop_HVAC_flag.value, gv=gv)


class DemandTool(object):
    """integrate the demand script with ArcGIS"""
    def __init__(self):
        self.label = 'Demand'
        self.description = 'Calculate the Demand'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        return [scenario_path]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        import cea.demand
        reload(cea.demand)

        scenario_path = parameters[0].valueAsText
        locator = inputlocator.InputLocator(scenario_path)

        cea.demand.demand_calculation(locator=locator, gv=gv)


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

        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        return [yearcalc, scenario_path]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        from cea.embodied import lca_embodied

        yearcalc = int(parameters[0].valueAsText)
        scenario_path = parameters[1].valueAsText

        locator = inputlocator.InputLocator(scenario_path=scenario_path)
        lca_embodied(yearcalc=yearcalc, locator=locator, gv=gv)



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
