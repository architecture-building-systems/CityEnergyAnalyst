from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot
import pandas as pd
from cea.plots.variable_naming import LOGO, COLOR, NAMING
import cea.plots.life_cycle

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "2.8"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class PrimaryEnergyPlot(cea.plots.life_cycle.LifeCycleAnalysisPlotBase):
    """Implement the primary-energy plot"""
    name = "Primary energy (non-renewable)"

    @property
    def layout(self):
        return go.Layout(barmode='stack',
                         yaxis=dict(title='Consumption of Fossil Fuels [GJ Oil-eq/yr]'),
                         xaxis=dict(title='Building Name'))

    def calc_graph(self):
        # calculate graph
        analysis_fields = self.analysis_fields_primary_energy
        data_frame = self.data_processed_emissions
        data_frame['total'] = total = data_frame[analysis_fields].sum(axis=1)
        data_frame = data_frame.sort_values(by='total', ascending=False)  # this will get the maximum value to the left
        graph = []
        for field in analysis_fields:
            y = data_frame[field]
            total_perc = (y / total * 100).round(2).values
            total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
            name = NAMING[field]
            trace = go.Bar(x=data_frame.index, y=y, name=name, text=total_perc_txt,
                           marker=dict(color=COLOR[field]))
            graph.append(trace)
        return graph

    def calc_table(self):
        analysis_fields = self.analysis_fields_primary_energy
        data_frame = self.data_processed_emissions
        data_frame['total'] = total = data_frame[analysis_fields].sum(axis=1)
        total = data_frame[analysis_fields].sum().round(2).tolist()
        total_percent = [str('{:20,.2f}'.format(x)) + " (" + str(round(x / sum(total) * 100, 1)) + " %)" for x in total]

        # calculate graph
        anchors = []
        load_names = []
        for field in analysis_fields + ["total"]:
            anchors.append(', '.join(calc_top_three_anchor_loads(data_frame, field)))
        for field in analysis_fields:
            load_names.append(NAMING[field] + ' (' + field + ')')

        column_names = ['Category', 'Consumption for all buildings [GJ Oil-eq/yr]', 'Top 3 most consuming buildings']
        column_values = [load_names + ["TOTAL"], total_percent + [str('{:20,.2f}'.format(sum(total))) + " (100 %)"], anchors]
        table_df = pd.DataFrame({cn: cv for cn, cv in zip(column_names, column_values)}, columns=column_names)
        return table_df



def primary_energy(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # CALCULATE TABLE
    traces_table = calc_table(analysis_fields, data_frame)

    # PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, title=title, barmode='stack',
                       yaxis=dict(title='Consumption of Fossil Fuels [GJ Oil-eq/yr]', domain=[0.35, 1]),
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


def calc_table(analysis_fields, data_frame):
    total = data_frame[analysis_fields].sum().round(2).tolist()
    total_perc = [str('{:20,.2f}'.format(x)) + " (" + str(round(x / sum(total) * 100, 1)) + " %)" for x in total]

    # calculate graph
    anchors = []
    load_names = []
    for field in analysis_fields + ["total"]:
        anchors.append(calc_top_three_anchor_loads(data_frame, field))
    for field in analysis_fields:
        load_names.append(NAMING[field] + ' (' + field + ')')

    table = go.Table(domain=dict(x=[0, 1], y=[0.0, 0.2]),
                     header=dict(values=['Category', 'Consumption for all buildings [GJ Oil-eq/yr]',
                                         'Top 3 most consuming buildings']),
                     cells=dict(values=[load_names + ["TOTAL"],
                                        total_perc + [str('{:20,.2f}'.format(sum(total))) + " (100 %)"], anchors]))

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
    PrimaryEnergyPlot(config.project, {'buildings': None,
                                       'scenario-name': config.scenario_name},
                      cache).plot(auto_open=True)
    PrimaryEnergyPlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                       'scenario-name': config.scenario_name},
                      cache).plot(auto_open=True)
    PrimaryEnergyPlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                       'scenario-name': config.scenario_name},
                      cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
