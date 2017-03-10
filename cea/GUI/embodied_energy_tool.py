from cea.interfaces.arcgis.CityEnergyAnalyst import add_message

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class EmbodiedEnergyTool(object):
    def __init__(self):
        self.label = 'Embodied Energy'
        self.description = 'Calculate the Emissions for operation'
        self.canRunInBackground = False

    def getParameterInfo(self):
        import arcpy
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
        import cea.analysis.embodied
        reload(cea.analysis.embodied)

        yearcalc = int(parameters[0].valueAsText)
        scenario_path = parameters[1].valueAsText
        gv = cea.globalvar.GlobalVariables()
        gv.log = add_message
        locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
        cea.analysis.embodied.lca_embodied(year_to_calculate=yearcalc, locator=locator, gv=gv)