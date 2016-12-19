import cea.GUI.benchmark_graphs_tool
import cea.GUI.demand_graphs_tool
import cea.GUI.demand_tool
import cea.GUI.embodied_energy_tool
import cea.GUI.emissions_tool
import cea.GUI.heatmaps_tool
import cea.GUI.mobility_tool
import cea.GUI.radiation_tool
import cea.GUI.data_helper_tool
import cea.GUI.scenario_plots_tool
import cea.GUI.toolbox

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

reload(cea.GUI.toolbox)
reload(cea.GUI.radiation_tool)
reload(cea.GUI.data_helper_tool)
reload(cea.GUI.demand_tool)
reload(cea.GUI.embodied_energy_tool)
reload(cea.GUI.emissions_tool)
reload(cea.GUI.demand_graphs_tool)
reload(cea.GUI.heatmaps_tool)
reload(cea.GUI.scenario_plots_tool)
reload(cea.GUI.benchmark_graphs_tool)


DemandTool = cea.GUI.demand_tool.DemandTool
DataHelperTool = cea.GUI.data_helper_tool.DataHelperTool
EmissionsTool = cea.GUI.emissions_tool.EmissionsTool
EmbodiedEnergyTool = cea.GUI.embodied_energy_tool.EmbodiedEnergyTool
HeatmapsTool = cea.GUI.heatmaps_tool.HeatmapsTool
DemandGraphsTool = cea.GUI.demand_graphs_tool.DemandGraphsTool
RadiationTool = cea.GUI.radiation_tool.RadiationTool
ScenarioPlotsTool = cea.GUI.scenario_plots_tool.ScenarioPlotsTool
BenchmarkGraphsTool = cea.GUI.benchmark_graphs_tool.BenchmarkGraphsTool
MobilityTool = cea.GUI.mobility_tool.MobilityTool

class Toolbox(object):
    def __init__(self):
        self.label = 'City Energy Analyst'
        self.alias = 'cea'
        self.tools = [DataHelperTool, DemandTool, EmissionsTool, EmbodiedEnergyTool, HeatmapsTool, DemandGraphsTool,
                      RadiationTool, ScenarioPlotsTool, BenchmarkGraphsTool, MobilityTool]
