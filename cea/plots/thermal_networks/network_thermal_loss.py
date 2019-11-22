"""
Map plots for thermal network losses: Aggregated and peak.

Adapted from code by Lennart Rogenhofer.
"""

from __future__ import division
from __future__ import print_function

from cea.plots.variable_naming import get_color_array
import pandas as pd
import geopandas
import json

from cea.utilities import remap
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system
from cea.utilities.color_fader import color_fader_rgb
import cea.plots.thermal_networks

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Lennart Rogenhofer", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class PeakNetworkThermalLossPlot(cea.plots.thermal_networks.ThermalNetworksMapPlotBase):
    """
    Plot the peak thermal network losses. As with the NetworkLayoutPlot, edge widths are proportional to
    the pipe diameter and node radius' are proportional to the peak building demand.

    Edges (pipes) are colored on a scale to reflect the aggregated pipe heat loss. This information is also added
    to the tooltip.

    Nodes (buildings & plants) are colored on a scale to reflect the average supply temperature. This information
    is also added to the tooltip, as well as the peek building demand.
    """
    name = "Map Network thermal conditions at peak time"

    def __init__(self, project, parameters, cache):
        super(PeakNetworkThermalLossPlot, self).__init__(project, parameters, cache)

    @property
    def edges_df(self):
        edges_df = geopandas.GeoDataFrame.from_file(
            self.locator.get_network_layout_edges_shapefile(self.network_type, self.network_name)).to_crs(
            get_geographic_coordinate_system())
        edges_df["_LineWidth"] = 0.1 * edges_df["Pipe_DN"]
        edges_df["length_m"] = edges_df["length_m"].round(1)

        # color the edges based on aggregated pipe heat loss
        if self.thermal_loss_edges_Wperm is not None: #backward compatibility with detailed thermal network (which does not include this output)
            yearly_thermal_loss = (self.thermal_loss_edges_Wperm.max()).round(2)
            edges_df["Peak Thermal losses [W/m]"] = yearly_thermal_loss.values

        # figure out colors
        q_loss_min = yearly_thermal_loss.min()
        q_loss_max = yearly_thermal_loss.max()
        scaled_q_loss = lambda x: remap(x, q_loss_min, q_loss_max, 0.0, 1.0)

        # matplotlib works on RGB in ranges [0.0, 1.0] - scale the input colors to that, transform and then scale back
        # to web versions ([0, 255])
        min_rgb_mpl = [remap(c, 0.0, 255.0, 0.0, 1.0) for c in get_color_array("white")]
        max_rgb_mpl = [remap(c, 0.0, 255.0, 0.0, 1.0) for c in get_color_array("red")]

        edges_df["_FillColor"] = yearly_thermal_loss.apply(
            lambda q_loss: json.dumps(
                [remap(x, 0.0, 1.0, 0.0, 255.0)
                 for x in color_fader_rgb(min_rgb_mpl, max_rgb_mpl, mix=scaled_q_loss(q_loss))])).values
        return edges_df

    @property
    def nodes_df(self):
        nodes_df = geopandas.GeoDataFrame.from_file(
            self.locator.get_network_layout_nodes_shapefile(self.network_type, self.network_name)).to_crs(
            get_geographic_coordinate_system())

        peak_demands = self.buildings_hourly.apply(pd.Series.max)
        pumping_peak = self.plant_pumping_requirement_kWh.max().round(1)

        if self.mass_flow_kgs_nodes is not None: #backward compatibility with detailed thermal network (which does not include this output)
            Mass_flow_kgs_peak = self.mass_flow_kgs_nodes.max().round(1)
            nodes_df["Peak mass flow rate [kg/s]"] = Mass_flow_kgs_peak.values

        def get_peak_building_demand(row):
            if row["Type"] == "CONSUMER":
                return peak_demands[row["Building"]]
            else:
                return None

        def get_pumping_node(row):
            if row["Type"] == "PLANT":
                return pumping_peak[0]
            else:
                return None

        nodes_df["Peak Thermal Demand [kW]"] = nodes_df.apply(get_peak_building_demand, axis=1)
        nodes_df["Pumping Power [kW]"] = nodes_df.apply(get_pumping_node, axis=1)

        nodes_df["_Radius"] = self.get_radius(nodes_df)

        # Figure out the colors (based on the average supply temperatures)
        min_mass = Mass_flow_kgs_peak.min()
        T_sup_C_max = Mass_flow_kgs_peak.max()
        scale_T_sup_C = lambda x: remap(x, min_mass, T_sup_C_max, 0.0, 1.0)

        # matplotlib works on RGB in ranges [0.0, 1.0] - scale the input colors to that, transform and then scale back
        # to web versions ([0, 255])
        min_rgb_mpl = [remap(c, 0.0, 255.0, 0.0, 1.0) for c in get_color_array("green_lighter")]
        max_rgb_mpl = [remap(c, 0.0, 255.0, 0.0, 1.0) for c in get_color_array("red")]

        nodes_df["_FillColor"] = json.dumps(get_color_array("black"))
        nodes_df["_FillColor"] = Mass_flow_kgs_peak.apply(
            lambda p_loss: json.dumps(
                [remap(x, 0.0, 1.0, 0.0, 255.0)
                 for x in color_fader_rgb(min_rgb_mpl, max_rgb_mpl, mix=scale_T_sup_C(p_loss))])).values
        return nodes_df

    def get_radius(self, nodes_df):
        """Figure out the radius for network nodes based on consumer consumption"""
        scale = 10.0
        demand = self.buildings_hourly.apply(pd.Series.max)
        max_demand = demand.max()

        def radius_from_demand(row):
            if row["Type"] == "CONSUMER":
                building = row["Building"]
                return scale * demand[building] / max_demand
            elif row["Type"] == "PLANT":
                return scale
            else:
                return scale * 0.1
        return nodes_df.apply(radius_from_demand, axis=1)


if __name__ == '__main__':
    import cea.config
    import cea.plots.cache
    import cea.inputlocator

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)
    cache = cea.plots.cache.NullPlotCache()
    PeakNetworkThermalLossPlot(config.project, {'network-type': config.plots.network_type,
                                            'scenario-name': config.scenario_name,
                                            'network-name': config.plots.network_name},
                               cache).plot(auto_open=True)
