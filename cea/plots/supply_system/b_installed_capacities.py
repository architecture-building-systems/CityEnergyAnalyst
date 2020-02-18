"""
Show a Pareto curve plot for individuals in a given generation.
"""
from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go

import cea.plots.supply_system
from cea.plots.variable_naming import NAMING, COLOR

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class InstalledCapacities(cea.plots.supply_system.SupplySystemPlotBase):
    """Show a pareto curve for a single generation"""
    name = "Installed Capacities"
    expected_parameters = {
        'system': 'plots-supply-system:system',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(InstalledCapacities, self).__init__(project, parameters, cache)
        self.analysis_fields_connected_heating = ['Capacity_BackupBoiler_NG_heat_connected_W',
                                                  'Capacity_PeakBoiler_NG_heat_connected_W',
                                                  'Capacity_BaseBoiler_NG_heat_connected_W',
                                                  'Capacity_CHP_DB_heat_connected_W',
                                                  'Capacity_CHP_NG_heat_connected_W',
                                                  'Capacity_CHP_WB_heat_connected_W',
                                                  'Capacity_HP_DS_heat_connected_W',
                                                  'Capacity_HP_GS_heat_connected_W',
                                                  'Capacity_HP_SS_heat_connected_W',
                                                  'Capacity_HP_WS_heat_connected_W',
                                                  'Capacity_SC_ET_heat_connected_W',
                                                  'Capacity_SC_FP_heat_connected_W',
                                                  'Capacity_PVT_heat_connected_W',
                                                  'Capacity_SeasonalStorage_WS_heat_connected_W']

        self.analysis_fields_connected_cooling = ["Capacity_TrigenCCGT_heat_NG_connected_W",
                                                  "Capacity_TrigenACH_cool_NG_connected_W",
                                                  "Capacity_BaseVCC_WS_cool_connected_W",
                                                  "Capacity_PeakVCC_WS_cool_connected_W",
                                                  "Capacity_BaseVCC_AS_cool_connected_W",
                                                  "Capacity_PeakVCC_AS_cool_connected_W",
                                                  "Capacity_BackupVCC_AS_cool_connected_W",
                                                  "Capacity_DailyStorage_WS_cool_connected_W"]

        self.analysis_fields_connected_electricity = ['Capacity_PV_el_connected_W',
                                                      'Capacity_PVT_el_connected_W',
                                                      'Capacity_CHP_WB_el_connected_W',
                                                      'Capacity_CHP_NG_el_connected_W',
                                                      'Capacity_CHP_DB_el_connected_W',
                                                      "Capacity_TrigenCCGT_el_NG_connected_W",
                                                      'Capacity_GRID_el_connected_W',
                                                      ]
        self.analysis_fields_disconnected_heating = ['Capacity_BaseBoiler_NG_heat_disconnected_W',
                                                     'Capacity_FC_NG_heat_disconnected_W',
                                                     'Capacity_GS_HP_heat_disconnected_W']
        self.analysis_fields_disconnected_cooling = ['Capacity_DX_AS_cool_disconnected_W',
                                                     'Capacity_BaseVCC_AS_cool_disconnected_W',
                                                     'Capacity_VCCHT_AS_cool_disconnected_W',
                                                     'Capacity_ACH_SC_FP_cool_disconnected_W',
                                                     'Capaticy_ACH_SC_ET_cool_disconnected_W',
                                                     'Capacity_ACHHT_FP_cool_disconnected_W']
        self.input_files = [(self.locator.get_optimization_slave_electricity_requirements_data,
                             [self.individual, self.generation])]

    @property
    def title(self):
        return "Installed Capacities for %s" % (self.system)

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file(
            '{system}_install_capacities'.format(system=self.system), self.category_name)

    @property
    def layout(self):
        return go.Layout(barmode='stack',  # annotations=annotations,
                         yaxis=dict(title='Installed Capacity [kW]', domain=[0, 1]),
                         xaxis=dict(domain=[0.0, 0.2]),
                         yaxis2=dict(anchor='x2', domain=[0, 1]),
                         xaxis2=dict(domain=[0.25, 1.0]))

    def calc_graph(self):
        # GET BARCHART OF CONNECTED BUILDINGS
        # get data
        data_connected = self.process_connected_capacities_kW()
        data_disconnected = self.process_disconnected_capacities_kW()

        # organize fiels according to heating, cooling and electricity
        analysis_fields_connected_heating = self.analysis_fields_connected_heating
        analysis_fields_connected_cooling = self.analysis_fields_connected_cooling
        analysis_fields_connected_electricity = self.analysis_fields_connected_electricity
        analysis_fields_disconnected_heating = self.analysis_fields_disconnected_heating
        analysis_fields_disconnected_cooling = self.analysis_fields_disconnected_cooling
        fields = analysis_fields_connected_heating + analysis_fields_connected_cooling + analysis_fields_connected_electricity
        analysis_fields_connected = self.remove_unused_fields(data_connected, fields)
        fields = analysis_fields_disconnected_heating + analysis_fields_disconnected_cooling
        analysis_fields_disconnected = self.remove_unused_fields(data_disconnected, fields)

        # iterate and create plots
        graph = []
        total_connected = data_connected[analysis_fields_connected].sum(axis=1)[0]
        for field in analysis_fields_connected:
            x = ['Technology for connected buildings']
            y = data_connected[field]
            total_perc = (y[0] / total_connected * 100).round(2)
            total_perc_txt = [str(round(y[0])) + " kW (" + str(total_perc) + " %)"]
            trace = go.Bar(x=x,
                           y=y,
                           name=field,
                           text=total_perc_txt,
                           marker=dict(color=COLOR[field]))
            graph.append(trace)

        data_disconnected['total'] = data_disconnected[analysis_fields_disconnected].sum(axis=1)
        for field in analysis_fields_disconnected:
            x = data_disconnected.index
            y = data_disconnected[field].values
            total_perc = (y / data_disconnected['total'] * 100).round(2).values
            total_perc_txt = [str(round(value, 1)) + " kW (" + str(perc) + " %)" for perc, value in zip(total_perc, y)]
            trace = go.Bar(x=x,
                           y=y,
                           name=NAMING[field],
                           text=total_perc_txt,
                           marker=dict(color=COLOR[field]),
                           xaxis='x2',
                           yaxis='y2',
                           showlegend=True)
            graph.append(trace)

        return graph


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    InstalledCapacities(config.project,
                        {'scenario-name': config.scenario_name,
                         'system': config.plots_supply_system.system,},
                        cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
