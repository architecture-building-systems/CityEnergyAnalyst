



import plotly.graph_objs as go
import pandas as pd

from cea.plots.variable_naming import NAMING, COLOR
import cea.plots.lifecycle

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class AnnualCostsPlot(cea.plots.lifecycle.LifecyclePlotBase):
    """Implement the "CAPEX vs. OPEX of a building system"""
    name = "Annualized costs per Building"
    expected_parameters = {
        'buildings': 'plots:buildings',
        'scenario-name': 'general:scenario-name',
        'normalization': 'plots-lifecycle:normalization',
    }

    def __init__(self, project, parameters, cache):
        super(AnnualCostsPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["Capex_a_sys_district_scale_USD",
                                "Capex_a_sys_building_scale_USD",
                                "Opex_a_sys_district_scale_USD",
                                "Opex_a_sys_building_scale_USD",
                                'Capex_a_sys_city_scale_USD',
                                'Opex_a_sys_city_scale_USD']
        self.normalization = self.parameters['normalization']
        self.titley = self.calc_titles()
        self.input_files = [(self.locator.get_demand_results_file, [building]) for building in self.buildings]
        self.data_clean = None

    def calc_titles(self):
        if self.normalization == "gross floor area":
            titley = 'Annualized cost [USD$(2015)/m2.yr]'
        elif self.normalization == "net floor area":
            titley = 'Annualized cost [USD$(2015)/m2.yr]'
        elif self.normalization == "air conditioned floor area":
            titley = 'Annualized cost [USD$(2015)/m2.yr]'
        elif self.normalization == "building occupancy":
            titley = 'Annualized cost [USD$(2015)/p.yr]'
        else:
            titley = 'Annualized cost [USD$(2015)/yr]'
        return titley

    @property
    def title(self):
        """Override the version in PlotBase"""
        if set(self.buildings) != set(self.locator.get_zone_building_names()):
            if len(self.buildings) == 1:
                return "%s for Building %s " % (self.name, self.buildings[0])
            else:
                return "%s for Selected Buildings" % (self.name)
        return "%s for District" % (self.name)

    @property
    def layout(self):
        return go.Layout(barmode='relative', yaxis=dict(title=self.titley))

    @cea.plots.cache.cached
    def data_building_costs(self):
        data_building_costs = pd.read_csv(self.locator.get_costs_operation_file()).set_index('Name')
        if len(self.buildings) == 1:
            data_raw_df = pd.DataFrame(data_building_costs.loc[self.buildings]).T
        else:
            data_raw_df = pd.DataFrame(data_building_costs.loc[self.buildings])
        data_normalized = self.normalize_data_individual_costs(data_raw_df, self.buildings, self.analysis_fields)
        return data_normalized.fillna(0)

    def calc_graph(self):
        data = self.data_building_costs()
        print(data.columns)
        graph = []
        for field in self.analysis_fields:
            y = data[field].values
            trace = go.Bar(x=data.index, y=y, name=NAMING[field],
                           marker=dict(color=COLOR[field]))
            graph.append(trace)

        return graph


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    import cea.inputlocator
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    cache = cea.plots.cache.NullPlotCache()
    AnnualCostsPlot(config.project,
                    {'buildings': locator.get_zone_building_names(),
                     'scenario-name': config.scenario_name,
                     'normalization': config.plots_lifecycle.normalization},
                    cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
