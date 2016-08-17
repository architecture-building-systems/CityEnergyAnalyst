import sandbox.mmosteiro.toolbox as toolbox
reload(toolbox)

GraphsBenchmarkTool = toolbox.GraphsBenchmarkTool
MobilityTool = toolbox.MobilityTool


class BenchmarkToolbox(object):
    def __init__(self):
        self.label = 'City Energy Analyst Benchmark Toolbox'
        self.alias = 'cea=benchmark'
        self.tools = [GraphsBenchmarkTool, MobilityTool]
