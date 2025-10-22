"""
Show a Pareto curve plot for individuals in a given generation.
"""




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


class RequirementsCurveDistrictElectricityPlot(cea.plots.supply_system.SupplySystemPlotBase):
    """Show a pareto curve for a single generation"""
    name = "Requirements curve electricity"
    expected_parameters = {
        'system': 'plots-supply-system:system',
        'timeframe': 'plots:timeframe',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(RequirementsCurveDistrictElectricityPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = [
            # due to energy generation units
            "E_HP_SC_FP_req_W",
            "E_HP_SC_ET_req_W",
            "E_HP_PVT_req_W",
            "E_HP_Server_req_W",
            "E_HP_Sew_req_W",
            "E_HP_Lake_req_W",
            "E_GHP_req_W",
            "E_BaseBoiler_req_W",
            "E_PeakBoiler_req_W",
            "E_BackupBoiler_req_W",

            "E_BaseVCC_WS_req_W",
            "E_PeakVCC_WS_req_W",
            "E_BaseVCC_AS_req_W",
            "E_PeakVCC_AS_req_W",
            "E_BackupVCC_AS_req_W",

            # Due to heating and cooling networks
            "E_DHN_req_W",
            "E_DCN_req_W",

            # Due to Seasonal storage
            "E_Storage_charging_req_W",
            "E_Storage_discharging_req_W",

            # Due to building demands and decentralized generation
            'Eal_req_W',
            'Edata_req_W',
            'Epro_req_W',
            'Eaux_req_W',
            # system requirements (by decentralized units)
            'E_hs_ww_req_district_scale_W',
            'E_cs_cre_cdata_req_district_scale_W',
            'E_hs_ww_req_building_scale_W',
            'E_cs_cre_cdata_req_building_scale_W'

        ]
        self.analysis_field_demand = ['E_electricalnetwork_sys_req_W']
        self.input_files = [(self.locator.get_optimization_slave_electricity_requirements_data,
                             [self.individual, self.generation])]

    @property
    def title(self):
        return "Requirements curve electrical for %s (%s)" % (self.system, self.timeframe)

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file(
            '{system}_electricity_requirements'.format(system=self.system), self.category_name)

    @property
    def layout(self):
        return dict(barmode='relative', yaxis=dict(title='Energy Demand [MWh]'))

    def calc_graph(self):
        # main data about technologies
        data = self.process_individual_requirements_curve_electricity()
        graph = []
        analysis_fields = self.remove_unused_fields(data, self.analysis_fields)
        for field in analysis_fields:
            y = (data[field].values) / 1E6  # into MWh
            trace = go.Bar(x=data.index, y=y, name=NAMING[field],
                           marker=dict(color=COLOR[field]))
            graph.append(trace)

        # data about demand
        for field in self.analysis_field_demand:
            y = (data[field].values) / 1E6  # into MWh
            trace = go.Scattergl(x=data.index, y=y, name=NAMING[field],
                               line=dict(width=1, color=COLOR[field]))

            graph.append(trace)

        return graph


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    RequirementsCurveDistrictElectricityPlot(config.project,
                                             {'scenario-name': config.scenario_name,
                                              'system': config.plots_supply_system.system,
                                              'timeframe': config.plots.timeframe},
                                             cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
