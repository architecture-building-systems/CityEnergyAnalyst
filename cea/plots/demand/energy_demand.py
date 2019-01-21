from __future__ import division
from __future__ import print_function

import cea.plots.demand
import plotly.graph_objs as go
from plotly.offline import plot

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

    def __init__(self, project, parameters):
        super(EnergyDemandDistrictPlot, self).__init__(project, parameters)
        self.analysis_fields = ["E_sys_MWhyr",
                                "Qhs_sys_MWhyr", "Qww_sys_MWhyr",
                                "Qcs_sys_MWhyr", 'Qcdata_sys_MWhyr', 'Qcre_sys_MWhyr']
        self.data = self.yearly_loads
        self.layout = go.Layout(barmode='stack',
                                yaxis=dict(title='Energy Demand [MWh/yr]', domain=[0.35, 1]),
                                xaxis=dict(title='Building Name'), showlegend=True)

    def calc_graph(self):
        return self.totals_bar_plot()


def energy_demand_district(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # CALCULATE TABLE
    traces_table = calc_table(analysis_fields, data_frame)

    # PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, title=title, barmode='stack',
                       yaxis=dict(title='Energy Demand [MWh/yr]', domain=[0.35, 1]),
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


def calc_graph(analysis_fields, data_frame):
    # calculate graph
    graph = []
    data_frame['total'] = data_frame[analysis_fields].sum(axis=1)
    data_frame = data_frame.sort_values(by='total', ascending=False)  # this will get the maximum value to the left
    for field in analysis_fields:
        y = data_frame[field]
        name = NAMING[field]
        total_perc = (y / data_frame['total'] * 100).round(2).values
        total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
        trace = go.Bar(x=data_frame["Name"], y=y, name=name, text=total_perc_txt, orientation='v',
                       marker=dict(color=COLOR[field]))
        graph.append(trace)

    return graph


def calc_top_three_anchor_loads(data_frame, field):
    data_frame = data_frame.sort_values(by=field, ascending=False)
    anchor_list = data_frame[:3].Name.values
    return anchor_list


if __name__ == '__main__':
    import cea.config
    import cea.inputlocator

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)

    EnergyDemandDistrictPlot(config, locator, locator.get_zone_building_names()).plot(auto_open=True)
    EnergyDemandDistrictPlot(config, locator, locator.get_zone_building_names()[0:2]).plot(auto_open=True)
    EnergyDemandDistrictPlot(config, locator, [locator.get_zone_building_names()[0]]).plot(auto_open=True)