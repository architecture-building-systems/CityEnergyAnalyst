import cea.GUI.toolbox as toolbox

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

reload(cea.GUI.toolbox)

DemandTool = toolbox.DemandTool
PropertiesTool = toolbox.PropertiesTool
EmissionsTool = toolbox.EmissionsTool
EmbodiedEnergyTool = toolbox.EmbodiedEnergyTool
HeatmapsTool = toolbox.HeatmapsTool
GraphsDemandTool = toolbox.GraphsDemandTool
RadiationTool = toolbox.RadiationTool
ScenarioPlotsTool = toolbox.ScenarioPlotsTool
GraphsBenchmarkTool = toolbox.GraphsBenchmarkTool
MobilityTool = toolbox.MobilityTool

class Toolbox(object):
    def __init__(self):
        self.label = 'City Energy Analyst'
        self.alias = 'cea'
        self.tools = [PropertiesTool, DemandTool, EmissionsTool, EmbodiedEnergyTool, HeatmapsTool, GraphsDemandTool,
                      RadiationTool, ScenarioPlotsTool, GraphsBenchmarkTool, MobilityTool]
