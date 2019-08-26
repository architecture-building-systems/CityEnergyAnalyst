from __future__ import division
from __future__ import print_function

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


class SolarCollectorEvacuatedTubeMonthlyPlot(cea.plots.solar_technology_potentials.SolarTechnologyPotentialsPlotBase):
    """Monthly plots for evacuated tubes (flat plates work exactly the same but on different data,
    see :py:class:`SolarCollectorFlatPlateMonthlyPlot`)"""

    name = "Evacuated Tube SC Thermal Potential"

    def __init__(self, project, parameters, cache):
        super(SolarCollectorEvacuatedTubeMonthlyPlot, self).__init__(project, parameters, cache)

    @property
    def data_frame(self):
        return self.SC_ET_hourly_aggregated_kW

    @property
    def analysis_fields(self):
        return [f.replace('SC_', 'SC_ET_') for f in self.sc_analysis_fields]

    @property
    def input_files(self):
        return [(self.locator.SC_totals, ['ET'])] + [(self.locator.SC_results, [building, 'ET'])
                                                     for building in self.buildings]

    @property
    def layout(self):
        return go.Layout(barmode='stack', yaxis=dict(title='SC Heat Production [MWh]',
                                                                       ))

    def calc_graph(self):
        # calculate graph
        data_frame = self.data_frame
        analysis_fields = self.analysis_fields

        graph = []
        monthly_df = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
        monthly_df["month"] = monthly_df.index.strftime("%B")
        # analysis_fields_used = monthly_df.columns[monthly_df.columns.isin(analysis_fields)].tolist()
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
        data_frame = self.data_frame
        analysis_fields = self.analysis_fields
        total = (data_frame[analysis_fields].sum(axis=0) / 1000).round(2).tolist()  # to MW
        # calculate top three potentials
        anchors = []
        load_names = []
        monthly_df = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
        monthly_df["month"] = monthly_df.index.strftime("%B")
        monthly_df.set_index("month", inplace=True)
        if sum(total) > 0:
            total_percent = [str(x) + " (" + str(round(x / sum(total) * 100, 1)) + " %)" for x in total]
            for field in analysis_fields:
                anchors.append(', '.join(calc_top_three_anchor_loads(monthly_df, field)))
                load_names.append(NAMING[field] + ' (' + field.split('_kWh', 1)[0] + ')')
        else:
            total_percent = ['0 (0%)'] * len(total)
            for field in analysis_fields:
                anchors.append('-')
                load_names.append(NAMING[field] + ' (' + field.split('_kWh', 1)[0] + ')')

        column_names = ['Surface', 'Total [MWh/yr]', 'Months with the highest potentials']
        column_values = [load_names, total_percent, anchors]
        table_df = pd.DataFrame({cn: cv for cn, cv in zip(column_names, column_values)}, columns=column_names)
        return table_df


class SolarCollectorFlatPlateMonthlyPlot(SolarCollectorEvacuatedTubeMonthlyPlot):
    name = "Flat Plate SC Thermal Potential"

    @property
    def data_frame(self):
        return self.SC_FP_hourly_aggregated_kW

    @property
    def analysis_fields(self):
        return [f.replace('SC_', 'SC_FP_') for f in self.sc_analysis_fields]

    @property
    def input_files(self):
        return [(self.locator.SC_totals, ['FP'])] + [(self.locator.SC_results, [building, 'FP'])
                                                     for building in self.buildings]



def sc_district_monthly(data_frame, analysis_fields, title, output_path):
    analysis_fields_used = data_frame.columns[data_frame.columns.isin(analysis_fields)].tolist()

    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields_used, data_frame)

    # CALCULATE TABLE
    traces_table = calc_table(analysis_fields_used, data_frame)

    # PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, title=title, barmode='stack', yaxis=dict(title='SC Heat Production [MWh]',
                                                                             domain=[0.35, 1]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(analysis_fields, data_frame):
    # calculate graph
    graph = []
    monthly_df = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
    monthly_df["month"] = monthly_df.index.strftime("%B")
    # analysis_fields_used = monthly_df.columns[monthly_df.columns.isin(analysis_fields)].tolist()
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
    # calculate top three potentials
    anchors = []
    load_names = []
    monthly_df = (data_frame.set_index("DATE").resample("M").sum() / 1000).round(2)  # to MW
    monthly_df["month"] = monthly_df.index.strftime("%B")
    monthly_df.set_index("month", inplace=True)
    if sum(total) > 0:
        total_perc = [str(x) + " (" + str(round(x / sum(total) * 100, 1)) + " %)" for x in total]
        for field in analysis_fields:
            anchors.append(calc_top_three_anchor_loads(monthly_df, field))
            load_names.append(NAMING[field] + ' (' + field.split('_kWh', 1)[0] + ')')
    else:
        total_perc = ['0 (0%)'] * len(total)
        for field in analysis_fields:
            anchors.append('-')
            load_names.append(NAMING[field] + ' (' + field.split('_kWh', 1)[0] + ')')

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

    # panel_type=ET
    weather_path = locator.get_weather_file()
    SolarCollectorEvacuatedTubeMonthlyPlot(config.project, {'buildings': None,
                                                            'scenario-name': config.scenario_name,
                                                            'weather': weather_path},
                                           cache).plot(auto_open=True)
    SolarCollectorEvacuatedTubeMonthlyPlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                                            'scenario-name': config.scenario_name,
                                                            'weather': weather_path},
                                           cache).plot(auto_open=True)
    SolarCollectorEvacuatedTubeMonthlyPlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                                            'scenario-name': config.scenario_name,
                                                            'weather': weather_path},
                                           cache).plot(auto_open=True)

    # panel_type=FP
    SolarCollectorFlatPlateMonthlyPlot(config.project, {'buildings': None,
                                                        'scenario-name': config.scenario_name,
                                                        'weather': weather_path},
                                       cache).plot(auto_open=True)
    SolarCollectorFlatPlateMonthlyPlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                                        'scenario-name': config.scenario_name,
                                                        'weather': weather_path},
                                       cache).plot(auto_open=True)
    SolarCollectorFlatPlateMonthlyPlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                                        'scenario-name': config.scenario_name,
                                                        'weather': weather_path},
                                       cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
