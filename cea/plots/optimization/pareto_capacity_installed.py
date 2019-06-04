from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot
import cea.plots.optimization
from cea.plots.variable_naming import LOGO, COLOR, NAMING

__author__ = "Bhargava Srepathi"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Bhargava Srepathi", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class ParetoCapacityInstalledPlot(cea.plots.optimization.OptimizationOverviewPlotBase):
    """Show a pareto curve installed capacity for a generation"""
    name = "Capacity installed in a generation"

    def __init__(self, project, parameters, cache):
        super(ParetoCapacityInstalledPlot, self).__init__(project, parameters, cache)
        self.analysis_fields_individual_heating = ['Base_boiler_BG_capacity_W', 'Base_boiler_NG_capacity_W',
                                                   'CHP_BG_capacity_W',
                                                   'CHP_NG_capacity_W', 'Furnace_dry_capacity_W',
                                                   'Furnace_wet_capacity_W',
                                                   'GHP_capacity_W', 'HP_Lake_capacity_W', 'HP_Sewage_capacity_W',
                                                   'PVT_capacity_W', 'PV_capacity_W', 'Peak_boiler_BG_capacity_W',
                                                   'Peak_boiler_NG_capacity_W', 'SC_ET_capacity_W', 'SC_FP_capacity_W',
                                                   'Disconnected_Boiler_BG_capacity_W',
                                                   'Disconnected_Boiler_NG_capacity_W',
                                                   'Disconnected_FC_capacity_W',
                                                   'Disconnected_GHP_capacity_W']
        self.analysis_fields_individual_cooling = ['Lake_kW', 'VCC_LT_kW', 'VCC_HT_kW', 'single_effect_ACH_LT_kW',
                                                   'single_effect_ACH_HT_kW', 'DX_kW', 'CHP_CCGT_thermal_kW',
                                                   'Storage_thermal_kW']
        self.analysis_fields = (self.analysis_fields_individual_heating if self.network_type == 'DH'
                                else self.analysis_fields_individual_cooling)
        self.input_files = [(self.locator.get_optimization_all_individuals, [])]

    @property
    def layout(self):
        return go.Layout(title=self.title, barmode='stack', yaxis=dict(title='Power Capacity [kW]', domain=[.35, 1]),
                         xaxis=dict(title='Point in the Pareto Curve'))

    @property
    def title(self):
        return 'Capacity installed in generation {generation}'.format(
            generation=self.parameters['generation'])

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file(
            'gen{generation}_centralized_and_decentralized_capacities_installed'.format(generation=self.generation),
            self.category_name)

    def calc_graph(self):
        # CALCULATE GRAPH FOR CONNECTED BUILDINGS
        graph = []
        data = self.preprocessing_capacities_data()
        analysis_fields = self.remove_unused_fields(data, self.analysis_fields)
        data['total'] = data[analysis_fields].sum(axis=1)
        data['Name'] = data.index.values
        data = data.sort_values(by='total', ascending=False)  # this will get the maximum value to the left
        for field in analysis_fields:
            y = data[field]
            flag_for_unused_technologies = all(v == 0 for v in y)
            if not flag_for_unused_technologies:
                name = NAMING[field]
                total_perc = (y / data['total'] * 100).round(2).values
                total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
                trace = go.Bar(x=data['Name'], y=y, text=total_perc_txt, name=name,
                               marker=dict(color=COLOR[field]))
                graph.append(trace)

        # FIXME: CALCULATE GRAPH FOR DISCONNECTED BUILDINGS
        return graph


def pareto_capacity_installed(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # CALCULATE TABLE
    traces_table = calc_table(analysis_fields, data_frame)

    # PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, title=title, barmode='stack',
                       yaxis=dict(title='Power Capacity [kW]', domain=[.35, 1]),
                       xaxis=dict(title='Point in the Pareto Curve'))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_table(analysis_fields, data_frame):
    # analysis of renewable energy share
    data_frame['load base unit'] = calc_top_three_technologies(analysis_fields, data_frame, analysis_fields)

    table = go.Table(domain=dict(x=[0, 1], y=[0, 0.2]),
                     header=dict(values=['Individual ID', 'Building connectivity [%]', 'Load Base Unit']),
                     cells=dict(values=[data_frame.index, data_frame['Buildings Connected Share'].values,
                                        data_frame['load base unit'].values]))
    return table


def calc_graph(analysis_fields, data):
    # CALCULATE GRAPH FOR CONNECTED BUILDINGS
    graph = []
    data['total'] = data[analysis_fields].sum(axis=1)
    data['Name'] = data.index.values
    data = data.sort_values(by='total', ascending=False)  # this will get the maximum value to the left
    for field in analysis_fields:
        y = data[field]
        flag_for_unused_technologies = all(v == 0 for v in y)
        if not flag_for_unused_technologies:
            name = NAMING[field]
            total_perc = (y / data['total'] * 100).round(2).values
            total_perc_txt = ["(" + str(x) + " %)" for x in total_perc]
            trace = go.Bar(x=data['Name'], y=y, text=total_perc_txt, name=name,
                           marker=dict(color=COLOR[field]))
            graph.append(trace)

    # CALCULATE GRAPH FOR DISCONNECTED BUILDINGS

    return graph


def calc_building_connected_share(network_string):
    share = round(sum([int(x) for x in network_string]) / len(network_string) * 100, 0)
    return share


def calc_renewable_share(all_fields, renewable_sources_fields, dataframe):
    nominator = dataframe[renewable_sources_fields].sum(axis=1)
    denominator = dataframe[all_fields].sum(axis=1)
    share = (nominator / denominator * 100).round(2)
    return share


def calc_top_three_technologies(analysis_fields, data_frame, fields):
    top_values = []
    data = data_frame[analysis_fields]
    for individual in data.index:
        top_values.extend(data.ix[individual].sort_values(ascending=False)[:1].index.values)

    # change name
    top_values = [x.split('_capacity', 1)[0] for x in top_values]

    return top_values


if __name__ == '__main__':
    config = cea.config.Configuration()

    parameters = {
        k: config.get(v) for k, v in ParetoCapacityInstalledPlot.expected_parameters.items()
    }
    plot = ParetoCapacityInstalledPlot(config.project, parameters=parameters)
    print('plot:', plot.name, '/', plot.id(), '/', plot.title)

    # plot the plot!
    plot.plot()
