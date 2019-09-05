from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
import pandas as pd
from plotly.offline import plot
import cea.plots.solar_technology_potentials
from cea.plots.variable_naming import LOGO, COLOR, NAMING

__author__ = "Shanshan Hsieh"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class PhotovoltaicMonthlyPlot(cea.plots.solar_technology_potentials.SolarTechnologyPotentialsPlotBase):
    """Implement the pv-electricity-potential plot"""
    name = "PV Electricity Potential"

    def __init__(self, project, parameters, cache):
        super(PhotovoltaicMonthlyPlot, self).__init__(project, parameters, cache)
        self.input_files = [(self.locator.PV_totals, [])] + [(self.locator.PV_results, [building])
                                                             for building in self.buildings]

    @property
    def layout(self):
        return go.Layout(barmode='stack', yaxis=dict(title='PV Electricity [MWh]'))

    def calc_graph(self):
        graph = []
        data_frame = self.PV_hourly_aggregated_kW
        analysis_fields = self.pv_analysis_fields
        monthly_df = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
        monthly_df["month"] = monthly_df.index.strftime("%B")
        total = monthly_df[analysis_fields].sum(axis=1)
        for field in analysis_fields:
            y = monthly_df[field]
            total_percent = (y.divide(total) * 100).round(2).values
            total_percent_txt = ["(" + str(x) + " %)" for x in total_percent]
            trace = go.Bar(x=monthly_df["month"], y=y, name=field.split('_kWh', 1)[0], text=total_percent_txt,
                           marker=dict(color=COLOR[field]))
            graph.append(trace)
        return graph

    def calc_table(self):
        data_frame = self.PV_hourly_aggregated_kW
        analysis_fields = self.pv_analysis_fields
        total = (data_frame[analysis_fields].sum(axis=0) / 1000).round(2).tolist()  # to MW
        anchors = []
        load_names = []
        monthly_df = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
        monthly_df["month"] = monthly_df.index.strftime("%B")
        monthly_df.set_index("month", inplace=True)
        if sum(total) > 0:
            total_percent = [str(x) + " (" + str(round(x / sum(total) * 100, 1)) + " %)" for x in total]
            # calculate graph
            for field in analysis_fields:
                load_names.append(NAMING[field] + ' (' + field.split('_kWh', 1)[0] + ')')
                anchors.append(', '.join(calc_top_three_anchor_loads(monthly_df, field)))
        else:
            total_percent = ['0 (0%)'] * len(total)
            for field in analysis_fields:
                load_names.append(NAMING[field] + ' (' + field.split('_kWh', 1)[0] + ')')
                anchors.append('-')

        column_names = ['Surface', 'Total [MWh/yr]', 'Months with the highest potentials']
        column_values = [load_names, total_percent, anchors]
        table_df = pd.DataFrame({cn: cv for cn, cv in zip(column_names, column_values)}, columns=column_names)
        return table_df


def pv_district_monthly(data_frame, analysis_fields, title, output_path):
    analysis_fields_used = data_frame.columns[data_frame.columns.isin(analysis_fields)].tolist()

    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields_used, data_frame)

    # CALCULATE TABLE
    traces_table = calc_table(analysis_fields_used, data_frame)

    # PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, title=title, barmode='stack', yaxis=dict(title='PV Electricity [MWh]',
                                                                             domain=[0.35, 1]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(analysis_fields, data_frame):
    # calculate graph
    graph = []
    monthly_df = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
    monthly_df["month"] = monthly_df.index.strftime("%B")
    total = monthly_df[analysis_fields].sum(axis=1)
    for field in analysis_fields:
        y = monthly_df[field]
        total_perc = (y.divide(total) * 100).round(2).values
        total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
        trace = go.Bar(x=monthly_df["month"], y=y, name=field.split('_kWh', 1)[0], text=total_perc_txt,
                       marker=dict(color=COLOR[field]))
        graph.append(trace)

    return graph


def calc_table(analysis_fields, data_frame):
    total = (data_frame[analysis_fields].sum(axis=0) / 1000).round(2).tolist()  # to MW
    anchors = []
    load_names = []
    monthly_df = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
    monthly_df["month"] = monthly_df.index.strftime("%B")
    monthly_df.set_index("month", inplace=True)
    if sum(total) > 0:
        total_perc = [str(x) + " (" + str(round(x / sum(total) * 100, 1)) + " %)" for x in total]
        # calculate graph
        for field in analysis_fields:
            load_names.append(NAMING[field] + ' (' + field.split('_kWh', 1)[0] + ')')
            anchors.append(calc_top_three_anchor_loads(monthly_df, field))
    else:
        total_perc = ['0 (0%)'] * len(total)
        for field in analysis_fields:
            load_names.append(NAMING[field] + ' (' + field.split('_kWh', 1)[0] + ')')
            anchors.append('-')

    table = go.Table(domain=dict(x=[0, 1], y=[0.0, 0.2]),
                     header=dict(values=['Surface', 'Total [MWh/yr]', 'Months with the highest potentials']),
                     cells=dict(values=[load_names, total_perc, anchors]))

    return table


def calc_top_three_anchor_loads(data_frame, field):
    data_frame = data_frame.sort_values(by=field, ascending=False)
    anchor_list = data_frame[:3].index.values
    return anchor_list


def main():
    """Test this plot"""
    import cea.config
    import cea.inputlocator
    import cea.plots.cache
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    cache = cea.plots.cache.PlotCache(config.project)
    # cache = cea.plots.cache.NullPlotCache()
    weather_path = locator.get_weather_file()
    PhotovoltaicMonthlyPlot(config.project, {'buildings': None,
                                             'scenario-name': config.scenario_name,
                                             'weather': weather_path},
                            cache).plot(auto_open=True)
    PhotovoltaicMonthlyPlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                             'scenario-name': config.scenario_name,
                                             'weather': weather_path},
                            cache).plot(auto_open=True)
    PhotovoltaicMonthlyPlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                             'scenario-name': config.scenario_name,
                                             'weather': weather_path},
                            cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
