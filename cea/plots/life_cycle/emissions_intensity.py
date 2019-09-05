from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot
import cea.plots.life_cycle
from cea.plots.variable_naming import LOGO, COLOR, NAMING

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "2.8"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class EmissionsIntensityPlot(cea.plots.life_cycle.LifeCycleAnalysisPlotBase):
    """Implements the Green House Gas Emissions Intensity plot"""
    name = "Green House Gas Emissions intensity"

    @property
    def layout(self):
        return go.Layout(barmode='stack',
                         yaxis=dict(title='Green House Gas Emissions per GFA [kg CO2-eq/m2.yr]'),
                         xaxis=dict(title='Building Name'))

    def calc_graph(self):
        # calculate graph
        graph = []
        analysis_fields = self.analysis_fields_emissions_m2
        data_frame = self.data_processed_emissions
        data_frame['total'] = total = data_frame[analysis_fields].sum(axis=1)
        data_frame = data_frame.sort_values(by='total', ascending=False)  # this will get the maximum value to the left
        for field in analysis_fields:
            y = data_frame[field]
            total_perc = (y / total * 100).round(2).values
            total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
            name = NAMING[field]
            trace = go.Bar(x=data_frame.index, y=y, name=name, text=total_perc_txt,
                           marker=dict(color=COLOR[field]))
            graph.append(trace)

        return graph


def emissions_intensity(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    layout = go.Layout(images=LOGO, title=title, barmode='stack',
                       yaxis=dict(title='Green House Gas Emissions per Gross Flor Area [kg CO2-eq/m2.yr]'),
                       xaxis=dict(title='Building Name'))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(analysis_fields, data_frame):
    # calculate graph
    graph = []
    data_frame['total'] = total = data_frame[analysis_fields].sum(axis=1)
    data_frame = data_frame.sort_values(by='total', ascending=False)  # this will get the maximum value to the left
    for field in analysis_fields:
        y = data_frame[field]
        total_perc = (y / total * 100).round(2).values
        total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
        name = NAMING[field]
        trace = go.Bar(x=data_frame.index, y=y, name=name, text=total_perc_txt,
                       marker=dict(color=COLOR[field]))
        graph.append(trace)

    return graph


def main():
    """Test this plot"""
    import cea.config
    import cea.inputlocator
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    cache = cea.plots.cache.PlotCache(config.project)
    # cache = cea.plots.cache.NullPlotCache()
    EmissionsIntensityPlot(config.project, {'buildings': None,
                                            'scenario-name': config.scenario_name},
                           cache).plot(auto_open=True)
    EmissionsIntensityPlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                            'scenario-name': config.scenario_name},
                           cache).plot(auto_open=True)
    EmissionsIntensityPlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                            'scenario-name': config.scenario_name},
                           cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
