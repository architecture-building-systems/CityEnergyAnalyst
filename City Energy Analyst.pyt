import cea.toolbox

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

reload(cea.toolbox)

DemandTool = cea.toolbox.DemandTool
PropertiesTool = cea.toolbox.PropertiesTool
EmissionsTool = cea.toolbox.EmissionsTool
EmbodiedEnergyTool = cea.toolbox.EmbodiedEnergyTool
HeatmapsTool = cea.toolbox.HeatmapsTool
GraphsDemandTool = cea.toolbox.GraphsDemandTool
RadiationTool = cea.toolbox.RadiationTool
ScenarioPlotsTool = cea.toolbox.ScenarioPlotsTool

class Toolbox(object):
    def __init__(self):
        self.label = 'City Energy Analyst'
        self.alias = 'cea'
        self.tools = [PropertiesTool, DemandTool, EmissionsTool, EmbodiedEnergyTool, HeatmapsTool, GraphsDemandTool,
                      RadiationTool, ScenarioPlotsTool]
