"""
Implements the Energy Supply pot.
"""




import cea.plots.demand.energy_end_use
import plotly.graph_objs as go



class EnergySupplyPlot(cea.plots.demand.energy_end_use.EnergyDemandDistrictPlot):
    """Implement the energy-supply plot, inherits most of it's functionality from EnergyDemandDistrictPlot"""
    name = "Energy Final Use"

    def __init__(self, project, parameters, cache):
        super(EnergySupplyPlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["DH_hs_MWhyr", "DH_ww_MWhyr", 'SOLAR_ww_MWhyr', 'SOLAR_hs_MWhyr', "DC_cs_MWhyr",
                                'DC_cdata_MWhyr', 'DC_cre_MWhyr', 'PV_MWhyr', 'NG_hs_MWhyr',
                                'COAL_hs_MWhyr', 'OIL_hs_MWhyr', 'WOOD_hs_MWhyr', 'NG_ww_MWhyr', 'COAL_ww_MWhyr',
                                'OIL_ww_MWhyr', 'WOOD_ww_MWhyr',
                                'GRID_a_MWhyr',
                                'GRID_l_MWhyr',
                                'GRID_v_MWhyr',
                                'GRID_ve_MWhyr',
                                'GRID_cs_MWhyr',
                                'GRID_aux_MWhyr',
                                'GRID_data_MWhyr',
                                'GRID_pro_MWhyr',
                                'GRID_ww_MWhyr',
                                'GRID_hs_MWhyr',
                                'GRID_cdata_MWhyr',
                                'GRID_cre_MWhyr'
                                ]

    @property
    def layout(self):
        return go.Layout(barmode='stack',
                         yaxis=dict(title='Energy Demand [MWh/yr]'),
                         xaxis=dict(title='Building Name'), showlegend=True)


def main():
    import cea.config
    import cea.inputlocator
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    # buildings = config.plots.buildings
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
