



import plotly.graph_objs as go
import cea.plots.demand
from cea.plots.variable_naming import COLOR, NAMING


class EnergySupplyIntensityPlot(cea.plots.demand.DemandPlotBase):
    name = "Energy Final Use Intensity"

    def __init__(self, project, parameters, cache):
        super(EnergySupplyIntensityPlot, self).__init__(project, parameters, cache)
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
                         yaxis=dict(title='Energy Use Intensity [kWh/m2.yr]'), showlegend=True)


    def calc_graph(self):
        analysis_fields = self.remove_unused_fields(self.data, self.analysis_fields)
        if len(self.buildings) == 1:
            assert len(self.data) == 1, 'Expected DataFrame with only one row'
            building_data = self.data.iloc[0]
            traces = []
            area = building_data["GFA_m2"]
            x = ["Absolute [MWh/yr]", "Relative [kWh/m2.yr]"]
            for field in analysis_fields:
                name = NAMING[field]
                y = [building_data[field], building_data[field] / area * 1000]
                trace = go.Bar(x=x, y=y, name=name, marker=dict(color=COLOR[field]))
                traces.append(trace)
            return traces
        else:
            traces = []
            dataframe = self.data
            for field in analysis_fields:
                dataframe[field] = dataframe[field] * 1000 / dataframe["GFA_m2"]  # in kWh/m2y
            dataframe['total'] = dataframe[analysis_fields].sum(axis=1)
            dataframe.sort_values(by='total', ascending=False, inplace=True)
            dataframe.reset_index(inplace=True, drop=True)
            for field in analysis_fields:
                y = dataframe[field]
                name = NAMING[field]
                total_percent = (y / dataframe['total'] * 100).round(2).values
                total_percent_txt = ["(%.2f %%)" % x for x in total_percent]
                trace = go.Bar(x=dataframe["name"], y=y, name=name, text=total_percent_txt, marker=dict(color=COLOR[field]))
                traces.append(trace)
            return traces


def main():
    import cea.config
    import cea.inputlocator
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    # cache = cea.plots.cache.PlotCache(config.project)
    cache = cea.plots.cache.NullPlotCache()

    EnergySupplyIntensityPlot(config.project, {'buildings': None,
                                               'scenario-name': config.scenario_name},
                              cache).plot(auto_open=True)
    EnergySupplyIntensityPlot(config.project, {'buildings': locator.get_zone_building_names()[0:2],
                                               'scenario-name': config.scenario_name},
                              cache).plot(auto_open=True)
    EnergySupplyIntensityPlot(config.project, {'buildings': [locator.get_zone_building_names()[0]],
                                               'scenario-name': config.scenario_name},
                              cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
