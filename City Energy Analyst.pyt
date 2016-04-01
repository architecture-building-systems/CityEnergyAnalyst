import cea.toolbox
reload(cea.toolbox)

DemandTool = cea.toolbox.DemandTool
PropertiesTool = cea.toolbox.PropertiesTool
EmissionsTool = cea.toolbox.EmissionsTool
EmbodiedEnergyTool = cea.toolbox.EmbodiedEnergyTool
HeatmapsTool = cea.toolbox.HeatmapsTool
GraphsDemandTool = cea.toolbox.GraphsDemandTool

class Toolbox(object):
    def __init__(self):
        self.label = 'City Energy Analyst'
        self.alias = 'cea'
        self.tools = [PropertiesTool, DemandTool, EmissionsTool, EmbodiedEnergyTool, HeatmapsTool, GraphsDemandTool]
