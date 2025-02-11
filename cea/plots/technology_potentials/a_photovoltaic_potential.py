import pandas as pd
import plotly.graph_objs as go

import cea.plots.technology_potentials
from cea.plots.variable_naming import COLOR, NAMING

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class PVPotentialPlot(cea.plots.technology_potentials.SolarTechnologyPotentialsPlotBase):
    """Implement the pv-electricity-potential plot"""

    name = "Photovoltaic Potential"

    expected_parameters = {
        # 'buildings': 'plots:buildings',
        'scenario-name': 'general:scenario-name',
        'timeframe': 'plots:timeframe',
        'normalization': 'plots:normalization',
        'type-pvpanel': 'solar:type-pvpanel'
    }

    def __init__(self, project, parameters, cache):
        super(PVPotentialPlot, self).__init__(project, parameters, cache)
        self.normalization = self.parameters['normalization']
        self.panel_type = self.parameters['type-pvpanel']
        # self.input_files = [(self.locator.PV_totals, [self.panel_type])] + [(self.locator.PV_results, [building])
        #                                                                     for building in self.buildings]
        self.input_files = [(self.locator.get_total_demand, []), (self.locator.PV_totals, [self.panel_type])]

        self.buildings = self.locator.get_zone_building_names()

    def calc_titles(self):
        if self.normalization == "gross floor area":
            titley = 'PV Electricity [kWh/m2]'
        elif self.normalization == "net floor area":
            titley = 'PV Electricity [kWh/m2]'
        elif self.normalization == "air conditioned floor area":
            titley = 'PV Electricity [kWh/m2]'
        elif self.normalization == "surface area":
            titley = 'PV Electricity [kWh/m2]'
        elif self.normalization == "building occupancy":
            titley = 'PV Electricity [kWh/p]'
        else:
            titley = 'PV Electricity [MWh]'
        return titley

    @property
    def layout(self):
        return go.Layout(barmode='relative', yaxis=dict(title=self.calc_titles()), showlegend=True)

    @property
    def title(self):
        """Override the version in PlotBase"""
        # if set(self.buildings) != set(self.locator.get_zone_building_names()):
        #     if len(self.buildings) == 1:
        #         if self.normalization == "none":
        #             return "%s for Building %s (%s)" % (self.name, self.buildings[0], self.timeframe)
        #         else:
        #             return "%s for Building %s normalized to %s (%s)" % (
        #                 self.name, self.buildings[0], self.normalization, self.timeframe)
        #     else:
        #         if self.normalization == "none":
        #             return "%s for Selected Buildings (%s)" % (self.name, self.timeframe)
        #         else:
        #             return "%s for Selected Buildings normalized to %s (%s)" % (
        #                 self.name, self.normalization, self.timeframe)
        # else:

        if self.normalization == "none":
            return "%s for District (%s)" % (self.name, self.timeframe)
        else:
            return "%s for District normalized to %s (%s)" % (self.name, self.normalization, self.timeframe)

    # FOR PV PANELS
    @cea.plots.cache.cached
    def PV_hourly_aggregated_kW(self):
        data = pd.read_csv(self.locator.PV_totals(self.panel_type)).set_index('Date')
        data_normalized = self.normalize_data(data, self.buildings, self.pv_analysis_fields,
                                              self.pv_analysis_fields_area)
        PV_hourly_aggregated_kW = self.resample_time_data(data_normalized)

        return PV_hourly_aggregated_kW

    def calc_graph(self):
        data = self.PV_hourly_aggregated_kW()
        traces = []
        analysis_fields = self.remove_unused_fields(data, self.pv_analysis_fields)
        for field in analysis_fields:
            if self.normalization != "none":
                y = data[field].values  # in kW
            else:
                y = data[field].values / 1E3  # to MW

            name = NAMING[field]
            trace = go.Bar(x=data.index, y=y, name=name, marker=dict(color=COLOR[field]))
            traces.append(trace)
        return traces


def main():
    """Test this plot"""
    import cea.config
    import cea.inputlocator
    import cea.plots.cache
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    cache = cea.plots.cache.NullPlotCache()
    PVPotentialPlot(config.project, {'buildings': None,
                                     'scenario-name': config.scenario_name,
                                     'timeframe': config.plots.timeframe,
                                     'normalization': config.plots.normalization},
                    cache).plot(auto_open=True)
    PVPotentialPlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                     'scenario-name': config.scenario_name,
                                     'timeframe': config.plots.timeframe,
                                     'normalization': config.plots.normalization},
                    cache).plot(auto_open=True)
    PVPotentialPlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                     'scenario-name': config.scenario_name,
                                     'timeframe': config.plots.timeframe,
                                     'normalization': config.plots.normalization},
                    cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
