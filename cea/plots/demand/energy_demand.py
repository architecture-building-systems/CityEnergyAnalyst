from __future__ import division
from __future__ import print_function

import cea.plots.demand
import cea.plots.cache
import plotly.graph_objs as go
from plotly.offline import plot
import pandas as pd

from cea.plots.variable_naming import NAMING, LOGO, COLOR

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class EnergyDemandDistrictPlot(cea.plots.demand.DemandPlotBase):
    """Implement the energy-use plot"""
    name = "Energy Demand"

    def __init__(self, project, parameters, cache):
        super(EnergyDemandDistrictPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["E_sys_MWhyr",
                                "Qhs_sys_MWhyr", "Qww_sys_MWhyr",
                                "Qcs_sys_MWhyr", 'Qcdata_sys_MWhyr', 'Qcre_sys_MWhyr']

    @property
    def layout(self):
        return go.Layout(barmode='stack',
                         yaxis=dict(title='Energy Demand [MWh/yr]'),
                         xaxis=dict(title='Building Name'), showlegend=True)

    def calc_graph(self):
        graph = []
        analysis_fields = self.remove_unused_fields(self.data, self.analysis_fields)
        dataframe = self.data
        dataframe['total'] = dataframe[analysis_fields].sum(axis=1)
        dataframe.sort_values(by='total', ascending=False, inplace=True)
        dataframe.reset_index(inplace=True, drop=True)
        for field in analysis_fields:
            y = dataframe[field]
            name = NAMING[field]
            total_percent = (y / dataframe['total'] * 100).round(2).values
            total_percent_txt = ["(%.2f %%)" % x for x in total_percent]
            trace = go.Bar(x=dataframe["Name"], y=y, name=name, text=total_percent_txt, orientation='v',
                           marker=dict(color=COLOR[field]))
            graph.append(trace)

        return graph

    def calc_table(self):
        data_frame = self.data
        analysis_fields = self.remove_unused_fields(self.data, self.analysis_fields)
        median = data_frame[analysis_fields].median().round(2).tolist()
        total = data_frame[analysis_fields].sum().round(2).tolist()
        total_perc = [str(x) + " (" + str(round(x / sum(total) * 100, 1)) + " %)" for x in total]
        # calculate graph
        anchors = []
        load_names = []
        for field in analysis_fields:
            anchors.append(', '.join(calc_top_three_anchor_loads(data_frame, field)))
            load_names.append(NAMING[field] + ' (' + field.split('_', 1)[0] + ')')

        column_names = ['Load Name', 'Total [MWh/yr]', 'Median [MWh/yr]', 'Top 3 Consumers']
        table_df = pd.DataFrame({'Load Name': load_names + ["Total"],
                                 'Total [MWh/yr]': total_perc + [str(sum(total)) + " (" + str(100) + " %)"],
                                 'Median [MWh/yr]': median + ["-"],
                                 'Top 3 Consumers': anchors + ['-']}, columns=column_names)
        return table_df


def energy_demand_district(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # CALCULATE TABLE
    traces_table = calc_table(analysis_fields, data_frame)

    # PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, title=title, barmode='stack',
                       yaxis=dict(title='Energy [MWh/yr]', domain=[0.35, 1]),
                       xaxis=dict(title='Building Name'), showlegend=True)
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_table(analysis_fields, data_frame):
    median = data_frame[analysis_fields].median().round(2).tolist()
    total = data_frame[analysis_fields].sum().round(2).tolist()
    total_perc = [str(x) + " (" + str(round(x / sum(total) * 100, 1)) + " %)" for x in total]
    # calculate graph
    anchors = []
    load_names = []
    for field in analysis_fields:
        anchors.append(calc_top_three_anchor_loads(data_frame, field))
        load_names.append(NAMING[field] + ' (' + field.split('_', 1)[0] + ')')

    table = go.Table(domain=dict(x=[0, 1.0], y=[0, 0.2]),
                     header=dict(values=['Load Name', 'Total [MWh/yr]', 'Median [MWh/yr]', 'Top 3 Consumers']),
                     cells=dict(values=[load_names, total_perc, median, anchors]))

    return table


def calc_graph(analysis_fields, data):
    graph = []
    data['total'] = data[analysis_fields].sum(axis=1)
    data = data.sort_values(by='total', ascending=False)
    for field in analysis_fields:
        y = data[field]
        name = NAMING[field]
        total_percent = (y / data['total'] * 100).round(2).values
        total_percent_txt = ["(%.2f %%)" % x for x in total_percent]
        trace = go.Bar(x=data["Name"], y=y, name=name, text=total_percent_txt, orientation='v',
                       marker=dict(color=COLOR[field]))
        graph.append(trace)

    return graph


def calc_top_three_anchor_loads(data_frame, field):
    data_frame = data_frame.sort_values(by=field, ascending=False)
    anchor_list = data_frame[:3].Name.values
    return anchor_list


def main():
    import cea.config
    import cea.inputlocator
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    # cache = cea.plots.cache.PlotCache(config.project)
    cache = cea.plots.cache.NullPlotCache()
    EnergyDemandDistrictPlot(config.project, {'buildings': None,
                                              'scenario-name': config.scenario_name},
                             cache).plot(auto_open=True)
    EnergyDemandDistrictPlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                              'scenario-name': config.scenario_name},
                             cache).plot(auto_open=True)
    EnergyDemandDistrictPlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                              'scenario-name': config.scenario_name},
                             cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
