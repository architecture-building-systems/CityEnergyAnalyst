"""
Map plots for network pressure losses: Aggregated and peak.

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


class AggregatedNetworkPressureLossPlot(cea.plots.thermal_networks.ThermalNetworksMapPlotBase):
    """
    Plot the aggregated thermal network losses. As with the NetworkLayoutPlot, edge widths are proportional to
    the pipe diameter and node radius' are proportional to the peak building demand.

    Edges (pipes) are colored on a scale to reflect the aggregated pipe heat loss. This information is also added
    to the tooltip.

    Nodes (buildings & plants) are colored on a scale to reflect the average supply temperature. This information
    is also added to the tooltip, as well as the peek building demand.
    """
    name = "Aggregated Network Pressure Loss"

    def __init__(self, project, parameters, cache):
        super(AggregatedNetworkPressureLossPlot, self).__init__(project, parameters, cache)

    @property
    def edges_df(self):
        edges_df = geopandas.GeoDataFrame.from_file(
            self.locator.get_network_layout_edges_shapefile(self.network_type, self.network_name)).to_crs(
            get_geographic_coordinate_system())
        edges_df["_LineWidth"] = 0.1 * edges_df["Pipe_DN"]

        # color the edges based on aggregated pipe pressure loss
        P_loss_kWh_aggregated = self.P_loss_kWh.sum().round(2)
        edges_df["Aggregated Pumping Energy Pipes [kWh]"] = P_loss_kWh_aggregated.values

        # figure out colors
        p_loss_min = P_loss_kWh_aggregated.min()
        p_loss_max = P_loss_kWh_aggregated.max()
        scale_p_loss = lambda x: remap(x, p_loss_min, p_loss_max, 0.0, 1.0)

        # matplotlib works on RGB in ranges [0.0, 1.0] - scale the input colors to that, transform and then scale back
        # to web versions ([0, 255])
        min_rgb_mpl = [remap(c, 0.0, 255.0, 0.0, 1.0) for c in get_color_array("white")]
        max_rgb_mpl = [remap(c, 0.0, 255.0, 0.0, 1.0) for c in get_color_array("red")]

        edges_df["_FillColor"] = P_loss_kWh_aggregated.apply(
            lambda p_loss: json.dumps(
                [remap(x, 0.0, 1.0, 0.0, 255.0)
                 for x in color_fader_rgb(min_rgb_mpl, max_rgb_mpl, mix=scale_p_loss(p_loss))])).values
        return edges_df

    @property
    def nodes_df(self):
        nodes_df = geopandas.GeoDataFrame.from_file(
            self.locator.get_network_layout_nodes_shapefile(self.network_type, self.network_name)).to_crs(
            get_geographic_coordinate_system())
        P_loss_substation_kWh = self.P_loss_substation_kWh.sum().round(2)
        nodes_df["Aggregated Pumping Energy Buildings [kWh]"] = P_loss_substation_kWh

        peak_demands = self.buildings_hourly.apply(pd.Series.max)

        def get_peak_building_demand(row):
            if row["Type"] == "CONSUMER":
                return peak_demands[row["Building"]]
            else:
                return None

        nodes_df["Peak Building Demand [kW]"] = nodes_df.apply(get_peak_building_demand, axis=1)

        nodes_df["_Radius"] = self.get_radius(nodes_df)

        # Figure out the colors (based on the average supply temperatures)
        P_loss_min = P_loss_substation_kWh.min()
        P_loss_max = P_loss_substation_kWh.max()
        scale_p_loss = lambda x: remap(x, P_loss_min, P_loss_max, 0.0, 1.0)

        # matplotlib works on RGB in ranges [0.0, 1.0] - scale the input colors to that, transform and then scale back
        # to web versions ([0, 255])
        min_rgb_mpl = [remap(c, 0.0, 255.0, 0.0, 1.0) for c in get_color_array("green_lighter")]
        max_rgb_mpl = [remap(c, 0.0, 255.0, 0.0, 1.0) for c in get_color_array("red")]

        nodes_df["_FillColor"] = json.dumps(get_color_array("black"))
        for building in P_loss_substation_kWh.index:
            nodes_df.loc[nodes_df["Building"] == building,
                         "Aggregated Pumping Energy Buildings [kWh]"] = P_loss_substation_kWh[building]
            nodes_df.loc[nodes_df["Building"] == building, "_FillColor"] = json.dumps(
                [remap(c, 0.0, 1.0, 0.0, 255.0)
                 for c in color_fader_rgb(min_rgb_mpl, max_rgb_mpl,
                                          mix=scale_p_loss(P_loss_substation_kWh[building]))])

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


class PeakNetworkPressureLossPlot(cea.plots.thermal_networks.ThermalNetworksMapPlotBase):
    """
    Plot the peak thermal network losses. As with the NetworkLayoutPlot, edge widths are proportional to
    the pipe diameter and node radius' are proportional to the peak building demand.

    Edges (pipes) are colored on a scale to reflect the aggregated pipe heat loss. This information is also added
    to the tooltip.

    Nodes (buildings & plants) are colored on a scale to reflect the average supply temperature. This information
    is also added to the tooltip, as well as the peek building demand.
    """
    name = "Peak Network Pressure Loss"

    def __init__(self, project, parameters, cache):
        super(PeakNetworkPressureLossPlot, self).__init__(project, parameters, cache)

    @property
    def edges_df(self):
        edges_df = geopandas.GeoDataFrame.from_file(
            self.locator.get_network_layout_edges_shapefile(self.network_type, self.network_name)).to_crs(
            get_geographic_coordinate_system())
        edges_df["_LineWidth"] = 0.1 * edges_df["Pipe_DN"]

        # color the edges based on aggregated pipe heat loss
        P_loss_kWh_peak = self.P_loss_kWh.max().round(2)
        edges_df["Peak Pumping Energy Pipes [kWh]"] = P_loss_kWh_peak.values

        # figure out colors
        p_loss_min = P_loss_kWh_peak.min()
        p = P_loss_kWh_peak.max()
        scale_p_loss = lambda x: remap(x, p_loss_min, p, 0.0, 1.0)

        # matplotlib works on RGB in ranges [0.0, 1.0] - scale the input colors to that, transform and then scale back
        # to web versions ([0, 255])
        min_rgb_mpl = [remap(c, 0.0, 255.0, 0.0, 1.0) for c in get_color_array("white")]
        max_rgb_mpl = [remap(c, 0.0, 255.0, 0.0, 1.0) for c in get_color_array("red")]

        edges_df["_FillColor"] = P_loss_kWh_peak.apply(
            lambda p_loss: json.dumps(
                [remap(x, 0.0, 1.0, 0.0, 255.0)
                 for x in color_fader_rgb(min_rgb_mpl, max_rgb_mpl, mix=scale_p_loss(p_loss))])).values
        return edges_df

    @property
    def nodes_df(self):
        nodes_df = geopandas.GeoDataFrame.from_file(
            self.locator.get_network_layout_nodes_shapefile(self.network_type, self.network_name)).to_crs(
            get_geographic_coordinate_system())
        P_loss_substation_peak = self.P_loss_substation_kWh.max().round(2)
        nodes_df["Peak Pumping Energy Buildings [kWh]"] = P_loss_substation_peak

        peak_demands = self.buildings_hourly.apply(pd.Series.max)

        def get_peak_building_demand(row):
            if row["Type"] == "CONSUMER":
                return peak_demands[row["Building"]]
            else:
                return None

        nodes_df["Peak Building Demand [kW]"] = nodes_df.apply(get_peak_building_demand, axis=1)

        nodes_df["_Radius"] = self.get_radius(nodes_df)

        # Figure out the colors (based on the average supply temperatures)
        P_loss_min = P_loss_substation_peak.min()
        P_loss_max = P_loss_substation_peak.max()
        scale_p_loss = lambda x: remap(x, P_loss_min, P_loss_max, 0.0, 1.0)

        # matplotlib works on RGB in ranges [0.0, 1.0] - scale the input colors to that, transform and then scale back
        # to web versions ([0, 255])
        min_rgb_mpl = [remap(c, 0.0, 255.0, 0.0, 1.0) for c in get_color_array("green_lighter")]
        max_rgb_mpl = [remap(c, 0.0, 255.0, 0.0, 1.0) for c in get_color_array("red")]

        nodes_df["_FillColor"] = json.dumps(get_color_array("black"))
        for building in P_loss_substation_peak.index:
            nodes_df.loc[nodes_df["Building"] == building,
                         "Aggregated Pumping Energy Buildings [kWh]"] = P_loss_substation_peak[building]
            nodes_df.loc[nodes_df["Building"] == building, "_FillColor"] = json.dumps(
                [remap(c, 0.0, 1.0, 0.0, 255.0)
                 for c in color_fader_rgb(min_rgb_mpl, max_rgb_mpl,
                                          mix=scale_p_loss(P_loss_substation_peak[building]))])

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

    AggregatedNetworkPressureLossPlot(config.project, {'network-type': config.plots.network_type,
                                                  'scenario-name': config.scenario_name,
                                                  'network-name': config.plots.network_name},
                                 cache).plot(auto_open=True)

    PeakNetworkPressureLossPlot(config.project, {'network-type': config.plots.network_type,
                                            'scenario-name': config.scenario_name,
                                            'network-name': config.plots.network_name},
                           cache).plot(auto_open=True)
