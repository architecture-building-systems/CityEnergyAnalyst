from __future__ import division
from __future__ import print_function

import cea.config
import cea.plots.optimization
import plotly.graph_objs as go

from cea.plots.variable_naming import NAMING, COLOR

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class CentralizedCostsPerGenerationUnitPlot(cea.plots.optimization.OptimizationOverviewPlotBase):
    """Implements the "CAPEX vs. OPEX district cooling network for every optimal supply system scenario in
    generation  X" plot"""

    name = "Centralized costs per generation unit"

    def __init__(self, project, parameters, cache):
        super(CentralizedCostsPerGenerationUnitPlot, self).__init__(project, parameters, cache)
        self.layout = go.Layout(title=self.title, barmode='relative',
                       yaxis=dict(title='Cost [USD$(2015)/year]', domain=[0.0, 1.0]))

        self.analysis_fields_cost_cooling_centralized = ["Capex_a_ACH_USD",
                                                         "Capex_a_CCGT_USD",
                                                         "Capex_a_CT_USD",
                                                         "Capex_a_Tank_USD",
                                                         "Capex_a_VCC_USD",
                                                         "Capex_a_VCC_backup_USD",
                                                         "Capex_a_pump_USD",
                                                         "Capex_a_PV_USD",
                                                         "Network_costs_USD",
                                                         "Substation_costs_USD",
                                                         "Opex_var_ACH_USD",
                                                         "Opex_var_CCGT_USD",
                                                         "Opex_var_CT_USD",
                                                         "Opex_var_Lake_USD",
                                                         "Opex_var_VCC_USD",
                                                         "Opex_var_VCC_backup_USD",
                                                         "Opex_var_pumps_USD",
                                                         "Opex_var_PV_USD",
                                                         "Electricitycosts_for_appliances_USD",
                                                         "Electricitycosts_for_hotwater_USD"]
        self.analysis_fields_cost_heating_centralized = ["Capex_a_SC_USD",
                                                         "Capex_a_PVT_USD",
                                                         "Capex_a_furnace_USD",
                                                         "Capex_a_Boiler_Total_USD",
                                                         "Capex_a_CHP_USD",
                                                         "Capex_a_Lake_USD",
                                                         "Capex_a_Sewage_USD",
                                                         "Capex_a_pump_USD",
                                                         "Opex_HP_Sewage_USD",
                                                         "Opex_HP_Lake_USD",
                                                         "Opex_GHP_USD",
                                                         "Opex_CHP_Total_USD",
                                                         "Opex_Furnace_Total_USD",
                                                         "Opex_Boiler_Total_USD",
                                                         "Electricity_Costs_USD"]
        self.analysis_fields = (self.analysis_fields_cost_heating_centralized if self.network_type == 'DH'
                                else self.analysis_fields_cost_cooling_centralized)
        self.input_files = [(self.locator.get_total_demand, []),
                            (self.locator.get_preprocessing_costs, []),
                            (self.locator.get_optimization_checkpoint, [self.generation])]

    @property
    def title(self):
        return "CAPEX vs. OPEX district {network} network for every optimal supply system scenario in generation  {generation}".format(
            generation=self.generation,
            network=('heating' if self.network_type == 'DH' else 'cooling'))

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file(
            'gen{generation}_centralized_costs_per_generation_unit'.format(generation=self.generation),
            self.category_name)

    def calc_graph(self):
        data = self.preprocessing_final_generation_data_cost_centralized()
        graph = []
        for field in self.analysis_fields:
            y = data[field].values
            flag_for_unused_technologies = all(v == 0 for v in y)
            if not flag_for_unused_technologies:
                trace = go.Bar(x=data.index, y=y, name=NAMING[field], marker=dict(color=COLOR[field]))
                graph.append(trace)
        return graph


if __name__ == '__main__':
    config = cea.config.Configuration()

    parameters = {
        k: config.get(v) for k, v in CentralizedCostsPerGenerationUnitPlot.expected_parameters.items()
    }
    plot = CentralizedCostsPerGenerationUnitPlot(config.project, parameters=parameters)
    print('plot:', plot.name, '/', plot.id(), '/', plot.title)

    # plot the plot!
    plot.plot()