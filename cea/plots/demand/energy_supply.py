"""
Implements the Energy Supply pot.
"""
from __future__ import division
from __future__ import print_function

import cea.plots.demand
import cea.plots.demand.energy_demand
import plotly.graph_objs as go

from cea.plots.variable_naming import NAMING, LOGO, COLOR


class EnergySupplyPlot(cea.plots.demand.energy_demand.EnergyDemandDistrictPlot):
    """Implement the energy-supply plot, inherits most of it's functionality from EnergyDemandDistrictPlot"""
    name = "Energy Supply"

    def __init__(self, project, parameters, cache):
        super(EnergySupplyPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["DH_hs_MWhyr", "DH_ww_MWhyr", 'SOLAR_ww_MWhyr', 'SOLAR_hs_MWhyr', "DC_cs_MWhyr",
                                'DC_cdata_MWhyr', 'DC_cre_MWhyr', 'PV_MWhyr', 'GRID_MWhyr', 'NG_hs_MWhyr',
                                'COAL_hs_MWhyr', 'OIL_hs_MWhyr', 'WOOD_hs_MWhyr', 'NG_ww_MWhyr', 'COAL_ww_MWhyr',
                                'OIL_ww_MWhyr', 'WOOD_ww_MWhyr']

    @property
    def layout(self):
        return go.Layout(barmode='stack',
                         yaxis=dict(title='Energy Supply [MWh/yr]'),
                         xaxis=dict(title='Building Name'), showlegend=True)


def main():
    import cea.config
    import cea.inputlocator
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    buildings = config.plots.buildings
    # cache = cea.plots.cache.PlotCache(config.project)
    cache = cea.plots.cache.NullPlotCache()
    EnergySupplyPlot(config.project, {'buildings': None,
                                      'scenario-name': config.scenario_name},
                     cache).plot(auto_open=True)
    EnergySupplyPlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                      'scenario-name': config.scenario_name},
                     cache).plot(auto_open=True)
    EnergySupplyPlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                      'scenario-name': config.scenario_name},
                     cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
