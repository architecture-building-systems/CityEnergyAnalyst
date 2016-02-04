import cea.demand
reload(cea.demand)
import cea.properties
reload(cea.properties)
import cea.emissions
reload(cea.emissions)
import cea.embodied
reload(cea.embodied)
import cea.heatmaps
reload(cea.heatmaps)

DemandTool = cea.demand.DemandTool
PropertiesTool = cea.properties.PropertiesTool
EmissionsTool = cea.emissions.EmissionsTool
EmbodiedEnergyTool = cea.embodied.EmbodiedEnergyTool
HeatmapsTool = cea.heatmaps.HeatmapsTool

class Toolbox(object):
    def __init__(self):
        self.label = 'City Energy Analyst'
        self.alias = 'cea'
        self.tools = [PropertiesTool, DemandTool, EmissionsTool, EmbodiedEnergyTool, HeatmapsTool]
