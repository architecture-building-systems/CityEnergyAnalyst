import benchmark_toolbox
reload(benchmark_toolbox)

GraphsBenchmarkTool = benchmark_toolbox.GraphsBenchmarkTool
MobilityTool = benchmark_toolbox.MobilityTool

class BenchmarkToolbox(object):
    def __init__(self):
        self.label = 'City Energy Analyst Benchmark Toolbox'
        self.alias = 'cea=benchmark'
        self.tools = [GraphsBenchmarkTool, MobilityTool]
