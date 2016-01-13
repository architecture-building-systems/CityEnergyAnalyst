import prototype.demand
reload(prototype.demand)
import prototype.properties
reload(prototype.properties)
import prototype.emissions
reload(prototype.emissions)
import prototype.embodied
reload(prototype.embodied)
import prototype.heatmaps
reload(prototype.heatmaps)

DemandTool = prototype.demand.DemandTool
PropertiesTool = prototype.properties.PropertiesTool
EmissionsTool = prototype.emissions.EmissionsTool
EmbodiedEnergyTool = prototype.embodied.EmbodiedEnergyTool
HeatmapsTool = prototype.heatmaps.HeatmapsTool

class Toolbox(object):
    def __init__(self):
        self.label = 'City Energy Analyst'
        self.alias = 'cea'
        self.tools = [PropertiesTool, DemandTool, EmissionsTool, EmbodiedEnergyTool, HeatmapsTool]
