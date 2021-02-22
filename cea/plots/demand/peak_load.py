



import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import LOGO, COLOR, NAMING
import cea.plots.demand

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "2.8"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class PeakLoadCurvePlot(cea.plots.demand.DemandPlotBase):
    name = "Peak Demand"

    def __init__(self, project, parameters, cache):
        super(PeakLoadCurvePlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["E_sys0_kW",
                                "Qhs_sys0_kW", "Qww_sys0_kW",
                                "Qcs_sys0_kW", 'Qcdata_sys0_kW', 'Qcre_sys0_kW']

    @property
    def layout(self):
        return go.Layout(barmode='stack', yaxis=dict(title='Peak Demand [kW]'), showlegend=True,
                         xaxis=dict(title='Building Name'))

    def calc_graph(self):
        analysis_fields = self.remove_unused_fields(self.data, self.analysis_fields)
        if len(self.buildings) == 1:
            assert len(self.data) == 1, 'Expected DataFrame with only one row'
            building_data = self.data.iloc[0]
            traces = []
            area = building_data["GFA_m2"]
            x = ["Absolute [kW]", "Relative [W/m2]"]
            for field in analysis_fields:
                name = NAMING[field]
                y = [building_data[field], building_data[field] / area * 1000]
                trace = go.Bar(x=x, y=y, name=name, marker=dict(color=COLOR[field]))
                traces.append(trace)
            return traces
        else:
            traces = []
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
                traces.append(trace)
            return traces


def diversity_factor(data_frame_timeseries, data_frame_totals, analysis_fields, title, output_path):
    traces = []
    x = ["Aggregated [MW] ", "System [MW]"]
    for field in analysis_fields:
        y1 = data_frame_totals[field + '0_kW'].sum() / 1000
        y2 = data_frame_timeseries[field + '_kWh'].max() / 1000
        y = [y1, y2]
        trace = go.Bar(x=x, y=y, name=field.split('0', 1)[0])
        traces.append(trace)

    layout = go.Layout(title=title, barmode='stack', yaxis=dict(title='Peak Load [MW]'))
    fig = go.Figure(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)


def main():
    import cea.config
    import cea.inputlocator
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    # cache = cea.plots.cache.PlotCache(config.project)
    cache = cea.plots.cache.NullPlotCache()

    PeakLoadCurvePlot(config.project, {'buildings': None,
                                       'scenario-name': config.scenario_name},
                      cache).plot(auto_open=True)
    PeakLoadCurvePlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                       'scenario-name': config.scenario_name},
                      cache).plot(auto_open=True)
    PeakLoadCurvePlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                       'scenario-name': config.scenario_name},
                      cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
