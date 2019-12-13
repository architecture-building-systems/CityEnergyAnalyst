from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot
import pandas as pd
import cea.plots.solar_potential
from cea.plots.variable_naming import LOGO, COLOR

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class SolarRadiationPlot(cea.plots.solar_potential.SolarPotentialPlotBase):
    """Implement the solar-radiation-per-building plot"""
    name = "Solar radiation per building"

    @property
    def layout(self):
        return go.Layout(title=self.title, barmode='stack',
                         yaxis=dict(title='Solar radiation [MWh/yr]'),
                         xaxis=dict(title='Building'))

    def calc_graph(self):
        # calculate graph
        graph = []
        data_frame = self.input_data_not_aggregated_MW
        data_frame['total'] = data_frame[self.analysis_fields].sum(axis=1)
        data_frame = data_frame.sort_values(by='total', ascending=False)  # this will get the maximum value to the left
        for field in self.analysis_fields:
            y = data_frame[field]
            total_perc = (y / data_frame['total'] * 100).round(2).values
            total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
            trace = go.Bar(x=data_frame["Name"], y=y, name=field, text=total_perc_txt,
                           marker=dict(color=COLOR[field]))
            graph.append(trace)

        return graph

    def calc_table(self):
        analysis_fields = self.analysis_fields
        data_frame = self.input_data_not_aggregated_MW
        median = data_frame[analysis_fields].median().round(2).tolist()
        total = data_frame[analysis_fields].sum().round(2).tolist()
        total_perc = [str(x) + " (" + str(round(x / sum(total) * 100, 1)) + " %)" for x in total]

        # calculate graph
        anchors = []
        for field in analysis_fields:
            anchors.append(', '.join(calc_top_three_anchor_loads(data_frame, field)))
        column_names = ['Surface', 'Total [MWh/yr]', 'Median [MWh/yr]', 'Top 3 most irradiated']
        column_values = [analysis_fields, total_perc, median, anchors]
        table_df = pd.DataFrame({cn: cv for cn, cv in zip(column_names, column_values)}, columns=column_names)
        return table_df

def solar_radiation_district(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph, x_axis = calc_graph(analysis_fields, data_frame)

    # CALCULATE TABLE
    traces_table = calc_table(analysis_fields, data_frame)

    # PLOT GRAPH
    traces_graph.append(traces_table)

    # CREATE BUTTON
    layout = go.Layout(images=LOGO, title=title, barmode='stack',
                       yaxis=dict(title='Solar radiation [MWh/yr]', domain=[0.35, 1]),
                       xaxis=dict(title='Building'))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(analysis_fields, data_frame):
    # calculate graph
    graph = []
    data_frame['total'] = data_frame[analysis_fields].sum(axis=1)
    data_frame = data_frame.sort_values(by='total', ascending=False)  # this will get the maximum value to the left
    for field in analysis_fields:
        y = data_frame[field]
        total_perc = (y / data_frame['total'] * 100).round(2).values
        total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
        trace = go.Bar(x=data_frame["Name"], y=y, name=field, text=total_perc_txt,
                       marker=dict(color=COLOR[field]))
        graph.append(trace)

    return graph, data_frame.index,


def calc_table(analysis_fields, data_frame):
    median = data_frame[analysis_fields].median().round(2).tolist()
    total = data_frame[analysis_fields].sum().round(2).tolist()
    total_perc = [str(x) + " (" + str(round(x / sum(total) * 100, 1)) + " %)" for x in total]

    # calculate graph
    anchors = []
    for field in analysis_fields:
        anchors.append(calc_top_three_anchor_loads(data_frame, field))
    table = go.Table(domain=dict(x=[0, 1], y=[0.0, 0.2]),
                     header=dict(values=['Surface', 'Total [MWh/yr]', 'Median [MWh/yr]', 'Top 3 most irradiated']),
                     cells=dict(values=[analysis_fields, total_perc, median, anchors]))

    return table


def calc_top_three_anchor_loads(data_frame, field):
    data_frame = data_frame.sort_values(by=field, ascending=False)
    anchor_list = data_frame[:3].index.values
    return anchor_list


def main():
    """Test this plot"""
    import cea.config
    import cea.inputlocator
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    cache = cea.plots.cache.PlotCache(config.project)
    # cache = cea.plots.cache.NullPlotCache()
    weather_path = locator.get_weather_file()
    SolarRadiationPlot(config.project, {'buildings': None,
                                        'scenario-name': config.scenario_name,
                                        'weather': weather_path},
                       cache).plot(auto_open=True)
    SolarRadiationPlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                        'scenario-name': config.scenario_name,
                                        'weather': weather_path},
                       cache).plot(auto_open=True)
    SolarRadiationPlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                        'scenario-name': config.scenario_name,
                                        'weather': weather_path},
                       cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
