from __future__ import division
from __future__ import print_function

import math
import pandas as pd
import plotly.graph_objs as go
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


class PvtMonthlyPlot(cea.plots.solar_technology_potentials.SolarTechnologyPotentialsPlotBase):
    """Implement the pv-electricity-potential plot"""
    name = "PVT Electricity/Thermal Potential"

    def __init__(self, project, parameters, cache):
        super(PvtMonthlyPlot, self).__init__(project, parameters, cache)
        self.input_files = [(self.locator.PVT_totals, [])] + [(self.locator.PVT_results, [building])
                                                              for building in self.buildings]
        self.__data_frame = None
        self.__E_analysis_fields_used = None
        self.__Q_analysis_fields_used = None

    @property
    def data_frame(self):
        """This get's used a couple of times in the calculations, avoid hitting the PlotCache each time"""
        if self.__data_frame is None:
            self.__data_frame = self.PVT_hourly_aggregated_kW
        return self.__data_frame

    @property
    def E_analysis_fields_used(self):
        if self.__E_analysis_fields_used is None:
            self.__E_analysis_fields_used = self.data_frame.columns[
                self.data_frame.columns.str.endswith('_E_kWh')].tolist()
        return self.__E_analysis_fields_used

    @property
    def Q_analysis_fields_used(self):
        if self.__Q_analysis_fields_used is None:
            self.__Q_analysis_fields_used = self.data_frame.columns[
                self.data_frame.columns.str.endswith('_Q_kWh')].tolist()
        return self.__Q_analysis_fields_used

    @property
    def layout(self):
        analysis_range = calc_range(self.data_frame, self.E_analysis_fields_used, self.Q_analysis_fields_used)
        return go.Layout(barmode='stack',
                         yaxis=dict(title='PVT Electricity/Heat production [MWh]', rangemode='tozero',
                                    scaleanchor='y2', range=analysis_range),
                         yaxis2=dict(overlaying='y', anchor='x', range=analysis_range))

    def calc_graph(self):
        # calculate graph
        graph = []
        data_frame = self.data_frame
        monthly_df = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
        monthly_df["month"] = monthly_df.index.strftime("%B")


        E_total = monthly_df[self.E_analysis_fields_used].sum(axis=1)
        Q_total = monthly_df[self.Q_analysis_fields_used].sum(axis=1)

        for field in self.Q_analysis_fields_used:
            y = monthly_df[field]
            total_perc = (y.divide(Q_total) * 100).round(2).values
            total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
            trace1 = go.Bar(x=monthly_df["month"], y=y, yaxis='y2', name=field.split('_kWh', 1)[0], text=total_perc_txt,
                            marker=dict(color=COLOR[field], line=dict(color="rgb(105,105,105)", width=1)),
                            opacity=1, width=0.3, offset=0, legendgroup=field.split('_Q_kWh', 1)[0])
            graph.append(trace1)

        for field in self.E_analysis_fields_used:
            y = monthly_df[field]
            total_perc = (y / E_total * 100).round(2).values
            total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
            trace2 = go.Bar(x=monthly_df["month"], y=y, name=field.split('_kWh', 1)[0], text=total_perc_txt,
                            marker=dict(color=COLOR[field]), width=0.3, offset=-0.35,
                            legendgroup=field.split('_E_kWh', 1)[0])
            graph.append(trace2)
        return graph

    def calc_table(self):
        analysis_fields_used = []
        total_perc = []
        data_frame = self.data_frame
        E_analysis_fields_used = self.E_analysis_fields_used
        Q_analysis_fields_used = self.Q_analysis_fields_used

        # calculation for electricity production
        E_total = (data_frame[E_analysis_fields_used].sum(axis=0) / 1000).round(2).tolist()  # to MW
        # calculate top three potentials
        E_anchors = []
        E_names = []
        monthly_df = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
        monthly_df["month"] = monthly_df.index.strftime("%B")
        monthly_df.set_index("month", inplace=True)

        if sum(E_total) > 0:
            E_total_perc = [str(x) + " (" + str(round(x / sum(E_total) * 100, 1)) + " %)" for x in E_total]
            for field in E_analysis_fields_used:
                E_anchors.append(', '.join(calc_top_three_anchor_loads(monthly_df, field)))
                E_names.append(NAMING[field].split(' ')[6] + ' (' + field.split('_kWh', 1)[0] + ')')
        else:
            E_total_perc = ['0 (0%)'] * len(E_total)
            for field in E_analysis_fields_used:
                E_anchors.append('-')
                E_names.append(NAMING[field].split(' ')[6] + ' (' + field.split('_kWh', 1)[0] + ')')

        analysis_fields_used.extend(E_analysis_fields_used)
        total_perc.extend(E_total_perc)

        # calculation for heat production
        Q_total = (data_frame[Q_analysis_fields_used].sum(axis=0) / 1000).round(2).tolist()  # to MW
        Q_names = []
        Q_anchors = []
        if sum(Q_total) > 0:
            Q_total_perc = [str(x) + " (" + str(round(x / sum(Q_total) * 100, 1)) + " %)" for x in Q_total]
            for field in Q_analysis_fields_used:
                Q_anchors.append(', '.join(calc_top_three_anchor_loads(monthly_df, field)))
                Q_names.append(NAMING[field].split(' ')[6] + ' (' + field.split('_kWh', 1)[0] + ')')
        else:
            Q_total_perc = ['0 (0%)'] * len(Q_total)
            for field in Q_analysis_fields_used:
                Q_anchors.append('-')
                Q_names.append(NAMING[field].split(' ')[6] + ' (' + field.split('_kWh', 1)[0] + ')')

        analysis_fields_used.extend(Q_analysis_fields_used)
        total_perc.extend(Q_total_perc)

        column_names = ['Surfaces', 'Total electricity production [MWh/yr]', 'Months with the highest potentials',
                       'Surfaces ', 'Total heat production [MWh/yr]', 'Months with the highest potentials']
        column_values = [E_names, E_total_perc, E_anchors, Q_names, Q_total_perc, Q_anchors]
        table_df = pd.DataFrame({cn: cv for cn, cv in zip(column_names, column_values)}, columns=column_names)
        return table_df


def pvt_district_monthly(data_frame, analysis_fields, title, output_path):
    E_analysis_fields_used = data_frame.columns[data_frame.columns.isin(analysis_fields[0:5])].tolist()
    Q_analysis_fields_used = data_frame.columns[data_frame.columns.isin(analysis_fields[5:10])].tolist()

    range = calc_range(data_frame, E_analysis_fields_used, Q_analysis_fields_used)
    # CALCULATE GRAPH
    traces_graphs = calc_graph(E_analysis_fields_used, Q_analysis_fields_used, data_frame)

    # CALCULATE TABLE
    traces_table = calc_table(E_analysis_fields_used, Q_analysis_fields_used, data_frame)

    # PLOT GRAPH
    traces_graphs.append(traces_table)
    layout = go.Layout(images=LOGO, title=title, barmode='stack',
                       yaxis=dict(title='PVT Electricity/Heat production [MWh]', domain=[0.35, 1], rangemode='tozero',
                                  scaleanchor='y2', range=range),
                       yaxis2=dict(overlaying='y', anchor='x', domain=[0.35, 1], range=range))

    fig = go.Figure(data=traces_graphs, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graphs, 'layout': layout}


def calc_range(data_frame, E_analysis_fields_used, Q_analysis_fields_used):
    monthly_df = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
    monthly_df["month"] = monthly_df.index.strftime("%B")
    E_total = monthly_df[E_analysis_fields_used].sum(axis=1)
    Q_total = monthly_df[Q_analysis_fields_used].sum(axis=1)
    y_axis_max = math.ceil(max(E_total.max(), Q_total.max()))
    y_asix_min = min(0, min(Q_total.min(), E_total.min()))
    return [y_asix_min, y_axis_max]


def calc_graph(E_analysis_fields_used, Q_analysis_fields_used, data_frame):
    # calculate graph
    graph = []
    monthly_df = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
    monthly_df["month"] = monthly_df.index.strftime("%B")
    E_total = monthly_df[E_analysis_fields_used].sum(axis=1)
    Q_total = monthly_df[Q_analysis_fields_used].sum(axis=1)

    for field in Q_analysis_fields_used:
        y = monthly_df[field]
        total_perc = (y.divide(Q_total) * 100).round(2).values
        total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
        trace1 = go.Bar(x=monthly_df["month"], y=y, yaxis='y2', name=field.split('_kWh', 1)[0], text=total_perc_txt,
                        marker=dict(color=COLOR[field], line=dict(color="rgb(105,105,105)", width=1)),
                        opacity=1, width=0.3, offset=0, legendgroup=field.split('_Q_kWh', 1)[0])
        graph.append(trace1)

    for field in E_analysis_fields_used:
        y = monthly_df[field]
        total_perc = (y / E_total * 100).round(2).values
        total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
        trace2 = go.Bar(x=monthly_df["month"], y=y, name=field.split('_kWh', 1)[0], text=total_perc_txt,
                        marker=dict(color=COLOR[field]), width=0.3, offset=-0.35,
                        legendgroup=field.split('_E_kWh', 1)[0])
        graph.append(trace2)

    return graph


def calc_table(E_analysis_fields_used, Q_analysis_fields_used, data_frame):
    analysis_fields_used = []
    total_perc = []

    # calculation for electricity production
    E_total = (data_frame[E_analysis_fields_used].sum(axis=0) / 1000).round(2).tolist()  # to MW
    # calculate top three potentials
    E_anchors = []
    E_names = []
    monthly_df = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
    monthly_df["month"] = monthly_df.index.strftime("%B")
    monthly_df.set_index("month", inplace=True)

    if sum(E_total) > 0:
        E_total_perc = [str(x) + " (" + str(round(x / sum(E_total) * 100, 1)) + " %)" for x in E_total]
        for field in E_analysis_fields_used:
            E_anchors.append(calc_top_three_anchor_loads(monthly_df, field))
            E_names.append(NAMING[field].split(' ')[6] + ' (' + field.split('_kWh', 1)[0] + ')')
    else:
        E_total_perc = ['0 (0%)'] * len(E_total)
        for field in E_analysis_fields_used:
            E_anchors.append('-')
            E_names.append(NAMING[field].split(' ')[6] + ' (' + field.split('_kWh', 1)[0] + ')')

    analysis_fields_used.extend(E_analysis_fields_used)
    total_perc.extend(E_total_perc)

    # calculation for heat production
    Q_total = (data_frame[Q_analysis_fields_used].sum(axis=0) / 1000).round(2).tolist()  # to MW
    Q_names = []
    Q_anchors = []
    if sum(Q_total) > 0:
        Q_total_perc = [str(x) + " (" + str(round(x / sum(Q_total) * 100, 1)) + " %)" for x in Q_total]
        for field in Q_analysis_fields_used:
            Q_anchors.append(calc_top_three_anchor_loads(monthly_df, field))
            Q_names.append(NAMING[field].split(' ')[6] + ' (' + field.split('_kWh', 1)[0] + ')')
    else:
        Q_total_perc = ['0 (0%)'] * len(Q_total)
        for field in Q_analysis_fields_used:
            Q_anchors.append('-')
            Q_names.append(NAMING[field].split(' ')[6] + ' (' + field.split('_kWh', 1)[0] + ')')

    analysis_fields_used.extend(Q_analysis_fields_used)
    total_perc.extend(Q_total_perc)

    table = go.Table(domain=dict(x=[0, 1], y=[0.0, 0.2]),
                     header=dict(values=['Surfaces', 'Total electricity production [MWh/yr]',
                                         'Months with the highest potentials', 'Surfaces',
                                         'Total heat production [MWh/yr]', 'Months with the highest potentials']),
                     cells=dict(values=[E_names, E_total_perc, E_anchors, Q_names, Q_total_perc, Q_anchors]))
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
    PvtMonthlyPlot(config.project, {'buildings': None,
                                    'scenario-name': config.scenario_name,
                                    'weather': weather_path},
                   cache).plot(auto_open=True)
    PvtMonthlyPlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                    'scenario-name': config.scenario_name,
                                    'weather': weather_path},
                   cache).plot(auto_open=True)
    PvtMonthlyPlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                    'scenario-name': config.scenario_name,
                                    'weather': weather_path},
                   cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
