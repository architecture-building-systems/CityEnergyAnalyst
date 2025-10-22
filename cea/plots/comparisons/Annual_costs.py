



import plotly.graph_objs as go

import cea.plots.comparisons
from cea.plots.variable_naming import NAMING, COLOR

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class ComparisonsAnnualCostsPlot(cea.plots.comparisons.ComparisonsPlotBase):
    """Implement the "CAPEX vs. OPEX of centralized system in generation X" plot"""
    name = "Annualized costs"

    def __init__(self, project, parameters, cache):
        super(ComparisonsAnnualCostsPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["Capex_a_sys_district_scale_USD",
                                "Capex_a_sys_building_scale_USD",
                                "Opex_a_sys_district_scale_USD",
                                "Opex_a_sys_building_scale_USD",
                                'Capex_a_sys_city_scale_USD',
                                'Opex_a_sys_city_scale_USD']
        self.normalization = self.parameters['normalization']
        self.input_files = [(x[4].get_optimization_slave_total_performance, [x[3], x[2]]) if x[2] != "today" else
                            (x[4].get_costs_operation_file, []) for x in self.scenarios_and_systems]
        self.titley = self.calc_titles()
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
        if self.normalization != "none":
            return "Annual Costs per Scenario normalized to {normalized}".format(normalized=self.normalization)
        else:
            return "Annual Costs per Scenario"

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file('scenarios_annualized_costs')

    @property
    def layout(self):
        return go.Layout(barmode='relative',
                         yaxis=dict(title=self.titley))

    def calc_graph(self):
        data = self.preprocessing_annual_costs_scenarios()
        graph = []
        for field in self.analysis_fields:
            y = data[field].values
            flag_for_unused_technologies = all(v == 0 for v in y)
            if not flag_for_unused_technologies:
                trace = go.Bar(x=data['scenario_name'], y=y, name=NAMING[field],
                               marker=dict(color=COLOR[field]))
                graph.append(trace)

        return graph


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    ComparisonsAnnualCostsPlot(config.project,
                               {'scenarios-and-systems': config.plots_comparisons.scenarios_and_systems,
                                'normalization': config.plots.normalization},
                                cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
