"""
ArcGIS Tool classes for integrating the CEA with ArcGIS.
"""
import os
import arcpy
from cea import globalvar
import inputlocator
reload(inputlocator)


def add_message(msg, **kwargs):
    """Log to arcpy.AddMessage() instead of print to STDOUT"""
    arcpy.AddMessage(msg % kwargs)

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
        gv = globalvar.GlobalVariables()
        gv.log = add_message
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
        gv = globalvar.GlobalVariables()
        gv.log = add_message
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
        gv = globalvar.GlobalVariables()
        gv.log = add_message
        locator = inputlocator.InputLocator(scenario_path=scenario_path)
        lca_embodied(yearcalc=yearcalc, locator=locator, gv=gv)



class EmissionsTool(object):

    def __init__(self):
        self.label = 'Emissions Operation'
        self.description = 'Calculate emissions and primary energy due to building operation'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        Qww_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to hot water consumption.",
            name="Qww_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Qww_flag.value = True
        Qhs_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to space heating.",
            name="Qhs_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Qhs_flag.value = True
        Qcs_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to space cooling.",
            name="Qcs_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Qcs_flag.value = True
        Qcdata_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to servers cooling.",
            name="Qcdata_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Qcdata_flag.value = True
        Qcrefri_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to refrigeration.",
            name="Qcrefri_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Qcrefri_flag.value = True
        Eal_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to appliances and lighting.",
            name="Eal_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Eal_flag.value = True
        Eaux_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to auxiliary electricity.",
            name="Eaux_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Eaux_flag.value = True
        Epro_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to electricity in industrial processes.",
            name="Epro_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Epro_flag.value = True
        Edata_flag = arcpy.Parameter(
            displayName="Create a separate file with emissions due to electricity consumption in data centers.",
            name="Edata_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        Edata_flag.value = True

        return [scenario_path, Qww_flag, Qhs_flag, Qcs_flag, Qcdata_flag, Qcrefri_flag, Eal_flag, Eaux_flag, Epro_flag,
                Edata_flag]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        from cea.emissions import lca_operation
        import inputlocator
        scenario_path = parameters[0].valueAsText
        locator = inputlocator.InputLocator(scenario_path)
        Qww_flag = parameters[1].value
        Qhs_flag = parameters[2].value
        Qcs_flag = parameters[3].value
        Qcdata_flag = parameters[4].value
        Qcrefri_flag = parameters[5].value
        Eal_flag = parameters[6].value
        Eaux_flag = parameters[7].value
        Epro_flag = parameters[8].value
        Edata_flag = parameters[9].value
        lca_operation(locator=locator, Qww_flag=Qww_flag, Qhs_flag=Qhs_flag, Qcs_flag=Qcs_flag, Qcdata_flag=Qcdata_flag,
                      Qcrefri_flag=Qcrefri_flag, Eal_flag=Eal_flag, Eaux_flag=Eaux_flag, Epro_flag=Epro_flag,
                      Edata_flag=Edata_flag)


class GraphsDemandTool(object):

    def __init__(self):
        self.label = 'Demand graphs'
        self.description = 'Calculate Graphs of the Demand'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        analysis_fields = arcpy.Parameter(
            displayName="Variables to analyse",
            name="analysis_fields",
            datatype="String",
            parameterType="Required",
            multiValue=True,
            direction="Input")
        analysis_fields.filter.list = []
        return [scenario_path, analysis_fields]

    def updateParameters(self, parameters):
        import pandas as pd
        scenario_path = parameters[0].valueAsText
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return
        analysis_fields = parameters[1]
        locator = inputlocator.InputLocator(scenario_path)
        df_total_demand = pd.read_csv(locator.get_total_demand())
        first_building = df_total_demand['Name'][0]
        df_building = pd.read_csv(locator.get_demand_results_file(first_building))
        fields = set(df_building.columns.tolist())
        fields.remove('DATE')
        fields.remove('Name')
        analysis_fields.filter.list = list(fields)
        return

    def execute(self, parameters, messages):
        import cea.graphs
        reload(cea.graphs)
        scenario_path = parameters[0].valueAsText
        locator = inputlocator.InputLocator(scenario_path)
        analysis_fields = parameters[1].valueAsText.split(';')[:4]  # max 4 fields for analysis
        gv = globalvar.GlobalVariables()
        gv.log = add_message
        cea.graphs.graphs_demand(locator=locator, analysis_fields=analysis_fields, gv=gv)


class HeatmapsTool(object):

    def __init__(self):
        self.label = 'Heatmaps'
        self.description = 'Create heatmap data layers'
        self.canRunInBackground = False

    def getParameterInfo(self):
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        path_variables = arcpy.Parameter(
            displayName="Choose the file to analyse",
            name="path_variables",
            datatype="String",
            parameterType="Required",
            direction="Input")
        path_variables.filter.list = []
        analysis_fields = arcpy.Parameter(
            displayName="Variables to analyse",
            name="analysis_fields",
            datatype="String",
            parameterType="Required",
            multiValue=True,
            direction="Input")
        analysis_fields.filter.list = []
        analysis_fields.parameterDependencies = ['path_variables']

        return [scenario_path, path_variables, analysis_fields]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        # scenario_path
        scenario_path = parameters[0].valueAsText
        if not os.path.exists(scenario_path):
            parameters[0].setErrorMessage('Scenario folder not found: %s' % scenario_path)
            return
        # path_variables
        locator = inputlocator.InputLocator(scenario_path)
        file_names = [os.path.basename(locator.get_total_demand())]
        file_names.extend([f for f in os.listdir(locator.get_lca_emissions_results_folder()) if f.endswith('.csv')])
        path_variables = parameters[1]
        if not path_variables.value or path_variables.value not in file_names:
            path_variables.filter.list = file_names
            path_variables.value = file_names[0]
        # analysis_fields
        analysis_fields = parameters[2]
        if path_variables.value == file_names[0]:
            file_to_analyze = locator.get_total_demand()
        else:
            file_to_analyze = os.path.join(locator.get_lca_emissions_results_folder(), path_variables.value)
        import pandas as pd
        df = pd.read_csv(file_to_analyze)
        fields = df.columns.tolist()
        fields.remove('Name')
        analysis_fields.filter.list = list(fields)
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        scenario_path = parameters[0].valueAsText
        file_to_analyze = parameters[1].valueAsText
        analysis_fields = parameters[2].valueAsText.split(';')

        locator = inputlocator.InputLocator(scenario_path)
        if file_to_analyze == os.path.basename(locator.get_total_demand()):
            file_to_analyze = locator.get_total_demand()
            path_results = locator.get_heatmaps_demand_folder()
        else:
            file_to_analyze = os.path.join(locator.get_lca_emissions_results_folder(), file_to_analyze)
            path_results = locator.get_heatmaps_emission_folder()
        import cea.heatmaps
        reload(cea.heatmaps)
        cea.heatmaps.heatmaps(locator=locator, analysis_fields=analysis_fields,
                 path_results=path_results, file_to_analyze=file_to_analyze)
        return

