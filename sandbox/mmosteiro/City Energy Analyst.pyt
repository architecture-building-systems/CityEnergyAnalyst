import cea.toolbox
reload(cea.toolbox)

DemandTool = cea.toolbox.DemandTool
PropertiesTool = cea.toolbox.PropertiesTool
EmissionsTool = cea.toolbox.EmissionsTool
EmbodiedEnergyTool = cea.toolbox.EmbodiedEnergyTool
MobilityTool = cea.toolbox.MobilityTool
HeatmapsTool = cea.toolbox.HeatmapsTool
GraphsDemandTool = cea.toolbox.GraphsDemandTool
GraphsBenchmarkTool = cea.toolbox.GraphsBenchmarkTool
RadiationTool = cea.toolbox.RadiationTool

class Toolbox(object):
    def __init__(self):
        self.label = 'City Energy Analyst'
        self.alias = 'cea'
        self.tools = [PropertiesTool, DemandTool, EmissionsTool, EmbodiedEnergyTool, MobilityTool, HeatmapsTool,
                      GraphsDemandTool, GraphsBenchmarkTool, RadiationTool]
