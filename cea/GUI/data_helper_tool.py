import cea
from cea.GUI.toolbox import add_message

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

class DataHelperTool(object):
    """
    integrate the cea/demand/preprocessing/properties.py script with ArcGIS.
    """

    def __init__(self):
        self.label = 'Data helper'
        self.description = 'Query characteristics of buildings and systems from statistical data'
        self.canRunInBackground = False

    def getParameterInfo(self):
        import arcpy
        scenario_path = arcpy.Parameter(
            displayName="Path to the scenario",
            name="scenario_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        prop_architecture_flag = arcpy.Parameter(
            displayName="Generate architectural properties",
            name="prop_architecture_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        prop_architecture_flag.value = True
        prop_HVAC_flag = arcpy.Parameter(
            displayName="Generate technical systems properties",
            name="prop_HVAC_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        prop_HVAC_flag.value = True
        prop_comfort_flag = arcpy.Parameter(
            displayName="Generate comfort properties",
            name="prop_comfort_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        prop_comfort_flag.value = True
        prop_internal_loads_flag = arcpy.Parameter(
            displayName="Generate internal loads properties",
            name="prop_internal_loads_flag",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        prop_internal_loads_flag.value = True
        return [scenario_path, prop_architecture_flag, prop_HVAC_flag, prop_comfort_flag,
                prop_internal_loads_flag]

    def execute(self, parameters, messages):
        from cea.demand.preprocessing.properties import properties

        scenario_path = parameters[0].valueAsText
        locator = cea.inputlocator.InputLocator(scenario_path)
        prop_architecture_flag = parameters[1]
        prop_HVAC_flag = parameters[2]
        prop_comfort_flag = parameters[3]
        prop_internal_loads_flag = parameters[4]
        gv = cea.globalvar.GlobalVariables()
        gv.log = add_message
        properties(locator=locator,
                   prop_architecture_flag=prop_architecture_flag.value, prop_hvac_flag=prop_HVAC_flag.value,
                   prop_comfort_flag=prop_comfort_flag.value, prop_internal_loads_flag=prop_internal_loads_flag.value
                   )