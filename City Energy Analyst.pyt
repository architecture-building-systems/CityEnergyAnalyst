import cea
import cea.GUI
import cea.GUI.toolbox

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

reload(cea)
reload(cea.GUI)
reload(cea.GUI.toolbox)

DemandTool = cea.GUI.toolbox.DemandTool
PropertiesTool = cea.GUI.toolbox.PropertiesTool
EmissionsTool = cea.GUI.toolbox.EmissionsTool
EmbodiedEnergyTool = cea.GUI.toolbox.EmbodiedEnergyTool
HeatmapsTool = cea.GUI.toolbox.HeatmapsTool
GraphsDemandTool = cea.GUI.toolbox.GraphsDemandTool
RadiationTool = cea.GUI.toolbox.RadiationTool
ScenarioPlotsTool = cea.GUI.toolbox.ScenarioPlotsTool
GraphsBenchmarkTool = cea.GUI.toolbox.GraphsBenchmarkTool
MobilityTool = cea.GUI.toolbox.MobilityTool

class Toolbox(object):
    def __init__(self):
        self.label = 'City Energy Analyst'
        self.alias = 'cea'
        self.tools = [PropertiesTool, DemandTool, EmissionsTool, EmbodiedEnergyTool, HeatmapsTool, GraphsDemandTool,
                      RadiationTool, ScenarioPlotsTool, GraphsBenchmarkTool, MobilityTool]
