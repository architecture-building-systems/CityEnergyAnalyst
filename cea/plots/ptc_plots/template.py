



import plotly.graph_objs as go
from cea.plots.variable_naming import COLOR, NAMING
import cea.config
import cea.inputlocator
import cea.plots.cache

# Part VII. Import the folder where your new plots are located
# example
# import cea.plots.schedules

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# Part VIII. Define the name of the class of your plot and also point to the superclasse (MyCategoryPlotBase is for the template)
class PTCPlot(cea.plots.ptc_plots.PTC_PlotBase):

    # Part IX. Define the name of the plot. This will come in the Dashboard
    # Example:
    name = "PTC Output Total"

    # Part X. Define the files and variables that this plot will use. If they are the same as the superclass (those in __init__) then let it be like this
    #otherwise you are overwriting them.
    # Example:
    def __init__(self, project, parameters, cache):
        super(PTCPlot, self).__init__(project, parameters, cache)


    # Part XI. Define how would you like that the axe titles of the plots be defined.
    # Exmaple:
    def calc_titles(self):
        if self.normalization == "PTC area":
            titley = 'Thermal output [kW/m2] collector'
        elif self.normalization == "PVT roof area":
            titley = 'Thermal output [kW/m2] roof'
        else:
            titley = 'Thermal output [kW]'
        return titley

    # Part XII. Tell the ploting engine what plot you will be needing (Check Plotly.com for options).
    # Exmaple:
    @property
    def layout(self):
        return go.Layout(barmode='relative', yaxis=dict(title=self.calc_titles()), showlegend=True)

    # Part XIII. Tell the ploting engine how the main titel to exist.
    # Example:
    @property
    def title(self):
        """Override the version in PlotBase"""
        if self.normalization == "none":
            return "%s for District (%s)" % (self.name, self.timeframe)
        else:
            return "%s for District normalized to %s (%s)" % (self.name, self.normalization, self.timeframe)

    # Part XIV. Tell the ploting engine how to make the graph
    # Example:
    def calc_graph(self):
        data = self.schedule_data_aggregated()
        traces = []
        analysis_fields = self.remove_unused_fields(data, self.schedule_analysis_fields)
        for field in analysis_fields:
            y = data[field].values
            name = NAMING[field]
            trace = go.Bar(x=data.index, y=y, name=name, marker=dict(color=COLOR[field]))
            traces.append(trace)
        return traces

    # Part XV. Test the plot by runninng this.
    # Do not forget to change the default.config file to include the Parameters, in case you have new ones.
    # Example:
def main():
    """Test this plot"""

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    cache = cea.plots.cache.NullPlotCache()
    PTCPlot(config.project, {
                                        'scenario-name': config.scenario_name,
                                        'timeframe': config.plots.timeframe,
                                        'normalization': config.plots.normalization},
                       cache).plot(auto_open=True)



if __name__ == '__main__':
    main()
