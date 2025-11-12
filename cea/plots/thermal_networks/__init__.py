



import json
import os

import geopandas
import numpy as np
import pandas as pd

import cea.plots.cache
from cea.constants import HOURS_IN_YEAR
from cea.plots.base import PlotBase
from cea.plots.variable_naming import get_color_array
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

"""
Implements py:class:`cea.plots.ThermalNetworksPlotBase` as a base class for all plots in the category 
"thermal-networks" and also set's the label for that category.
"""

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# identifies this package as a plots category and sets the label name for the category
label = 'Thermal networks'


class ThermalNetworksPlotBase(PlotBase):
    """Implements properties / methods used by all plots in this category"""
    category_name = "thermal-networks"

    # default parameters for plots in this category - override if your plot differs
    expected_parameters = {
        'scenario-name': 'general:scenario-name',
        'network-type': 'plots:network-type',
        'network-name': 'plots:network-name',
    }

    def __init__(self, project, parameters, cache):
        super(ThermalNetworksPlotBase, self).__init__(project, parameters, cache)
        self.category_path = os.path.join('special', self.category_name)
        self.network_name = parameters['network-name'] if parameters['network-name'] else ''
        self.network_type = parameters['network-type']

    @property
    def title(self):
        """Override the version in PlotBase"""
        if not self.network_name:  # different plot titles if a network name is specified, here without network name
            return '{name} for {network_type}'.format(name=self.name, network_type=self.network_type)
        else:
            # plot title including network name
            return '{name} for {network_type} in {network_name}'.format(name=self.name, network_type=self.network_type,
                                                                        network_name=self.network_name)

    @property
    def output_path(self):
        file_name = '{network_type}_{network_name}_{name}'.format(network_type=self.network_type,
                                                                  network_name=self.network_name, name=self.id())
        return self.locator.get_timeseries_plots_file(file_name, self.category_path)

    @property
    @cea.plots.cache.cached
    def buildings_hourly(self):
        thermal_demand_df = pd.read_csv(self.locator.get_thermal_demand_csv_file(self.network_type, self.network_name))
        thermal_demand_df.set_index(self.date)
        thermal_demand_df = thermal_demand_df / 1000
        return thermal_demand_df

    @property
    @cea.plots.cache.cached
    def hourly_loads(self):
        hourly_loads = pd.DataFrame(self.buildings_hourly.sum(axis=1))
        if self.network_type == 'DH':
            hourly_loads.columns = ['Q_dem_heat']
        else:
            hourly_loads.columns = ['Q_dem_cool']
        return hourly_loads

    @property
    @cea.plots.cache.cached
    def date(self):
        """Read in the date information from demand results of the first building in the zone"""
        buildings = self.locator.get_zone_building_names()
        df_date = pd.read_csv(self.locator.get_demand_results_file(buildings[0]))
        return df_date["DATE"]

    @property
    @cea.plots.cache.cached
    def plant_pumping_requirement_kWh(self):
        hourly_pressure_loss = pd.read_csv(
            self.locator.get_network_energy_pumping_requirements_file(self.network_type, self.network_name))
        hourly_pressure_loss = hourly_pressure_loss['pressure_loss_total_kW']
        return pd.DataFrame(hourly_pressure_loss)

    @property
    @cea.plots.cache.cached
    def total_thermal_losses_kWh(self):
        hourly_thermal_loss = pd.read_csv(
            self.locator.get_network_total_thermal_loss_file(self.network_type, self.network_name))
        hourly_thermal_loss = hourly_thermal_loss['thermal_loss_total_kW']
        return pd.DataFrame(hourly_thermal_loss)

    def _calculate_relative_loss(self, absolute_loss):
        """
                Calculate relative heat or pressure loss:
                1. Sum up all plant heat produced in each time step
                2. Divide absolute losses by that value
                """
        # read plant heat supply
        plant_heat_supply = pd.read_csv(self.locator.get_thermal_network_plant_heat_requirement_file(self.network_type,
                                                                                                     self.network_name))
        plant_heat_supply = abs(plant_heat_supply)  # make sure values are positive
        if len(plant_heat_supply.columns.values) > 1:  # sum of all plants
            plant_heat_supply = plant_heat_supply.sum(axis=1)
        plant_heat_supply[plant_heat_supply == 0] = np.nan
        # necessary to avoid errors from shape mismatch
        plant_heat_supply = np.reshape(plant_heat_supply.values, (HOURS_IN_YEAR, 1))
        relative_loss = absolute_loss.values / plant_heat_supply * 100  # calculate relative value in %
        relative_loss = np.nan_to_num(relative_loss)  # remove nan or inf values to avoid runtime error
        # if relative losses are more than 100% temperature requirements are not met. All produced heat is lost.
        relative_loss[relative_loss > 100] = 100
        # don't show 0 values
        relative_loss[relative_loss == 0] = np.nan
        return relative_loss

    @property
    @cea.plots.cache.cached
    def hourly_heat_loss(self):
        hourly_heat_loss = pd.read_csv(
            self.locator.get_network_thermal_loss_edges_file(self.network_type, self.network_name))
        hourly_heat_loss = abs(hourly_heat_loss).sum(axis=1)  # aggregate heat losses of all edges
        return pd.DataFrame(hourly_heat_loss)

    @property
    @cea.plots.cache.cached
    def P_loss_kWh(self):
        return pd.read_csv(self.locator.get_thermal_network_pressure_losses_edges_file(self.network_type,
                                                                                       self.network_name))

    @property
    @cea.plots.cache.cached
    def linear_pressure_loss_Paperm(self):
        return pd.read_csv(self.locator.get_network_linear_pressure_drop_edges(self.network_type,
                                                                               self.network_name))

    @property
    @cea.plots.cache.cached
    def pressure_at_nodes_Pa(self):
        return pd.read_csv(self.locator.get_network_pressure_at_nodes(self.network_type,
                                                                      self.network_name))

    @property
    @cea.plots.cache.cached
    def mass_flow_kgs_pipes(self):
        return pd.read_csv(self.locator.get_thermal_network_layout_massflow_edges_file(self.network_type,
                                                                                       self.network_name))

    @property
    @cea.plots.cache.cached
    def velocity_mps_pipes(self):
        try:
            return pd.read_csv(self.locator.get_thermal_network_velocity_edges_file(self.network_type,
                                                                                       self.network_name))
        except Exception:
            #backward compatibility with detailed network simulation (which does not produce this data)
            return None

    @property
    @cea.plots.cache.cached
    def mass_flow_kgs_nodes(self):
        try:
            return pd.read_csv(self.locator.get_thermal_network_layout_massflow_nodes_file(self.network_type,
                                                                                       self.network_name))
        except Exception:
        # backward compatibility with detailed network simulation (which does not produce this data)
            return None

    @property
    @cea.plots.cache.cached
    def thermal_loss_edges_kWh(self):
        return pd.read_csv(self.locator.get_network_thermal_loss_edges_file(self.network_type,
                                                                            self.network_name))  # edge loss

    @property
    @cea.plots.cache.cached
    def thermal_loss_edges_Wperm(self):
        try:
            return pd.read_csv(self.locator.get_network_linear_thermal_loss_edges_file(self.network_type,
                                                                                       self.network_name))  # edge loss
        except Exception:
            # backward compatibility with detailed network simulation (which does not produce this data)
            return None

    @property
    def network_pipe_length(self):
        df = pd.read_csv(self.locator.get_thermal_network_edge_list_file(self.network_type, self.network_name))
        total_pipe_length = df['length_m'].sum()
        return total_pipe_length

    @property
    @cea.plots.cache.cached
    def temperature_supply_nodes_C(self):
        """Node supply temperatures"""
        supply_df = pd.read_csv(
            self.locator.get_network_temperature_supply_nodes_file(self.network_type, self.network_name))
        supply_df -= 273.15  # convert from Kelvin to C
        return supply_df

    @property
    @cea.plots.cache.cached
    def temperature_return_nodes_C(self):
        """Node return temperatures"""
        return_df = pd.read_csv(
            self.locator.get_network_temperature_return_nodes_file(self.network_type, self.network_name))
        return_df -= 273.15  # convert from Kelvin to C
        return return_df

    @property
    @cea.plots.cache.cached
    def temperature_supply_return_plant_C(self):
        """Node supply temperatures"""
        supply_df = pd.read_csv(
            self.locator.get_network_temperature_plant(self.network_type, self.network_name))
        return supply_df


class ThermalNetworksMapPlotBase(ThermalNetworksPlotBase):
    """
    Some of the plots in the Thermal Networks category display their data on a map (using deck.gl)

    This works by using the Jinja2 templating engine to create a html <div/> containing all the javascript
    necessary to show the plot. The template used is ``network_plot.html``.
    """

    def __init__(self, project, parameters, cache):
        super(ThermalNetworksMapPlotBase, self).__init__(project, parameters, cache)
        self.network_args = [self.network_type, self.network_name]

        self.colors = {
            "zone": get_color_array("grey_light"),
            "district": get_color_array("white"),
            "edges": get_color_array("blue") if self.network_type == "DC" else get_color_array("red"),
            "building": get_color_array("orange"),
            "plant": get_color_array("purple")
        }

        self.color_by_type = {
            "NONE": self.colors["edges"],
            "PLANT": self.colors["plant"],
            "CONSUMER": self.colors["building"]
        }

        self.input_files = [(self.locator.get_zone_geometry, []),
                            (self.locator.get_thermal_demand_csv_file, self.network_args),
                            (self.locator.get_thermal_network_edge_list_file, self.network_args),
                            (self.locator.get_network_thermal_loss_edges_file, self.network_args),
                            (self.locator.get_thermal_network_node_types_csv_file, self.network_args)]

    @property
    def edges_df(self):
        """
        This property is expected to return a GeoDataFrame containing the edges of the network to display
        including the data.

        Any columns included will be shown in the Tooltip of the map, except for those starting with an underscore.

        There are some special columns that must be added here, that are used for visualization purposes:

        - _LineWidth: The line width to use for the edges. This can be a computed property based on edge data


        :return:
        :rtype: geopandas.GeoDataFrame
        """
        raise NotImplementedError("Please implement edges_df in subclass")

    @property
    def nodes_df(self):
        """
        This property is expected to return a GeoDataFrame containing the nodes of the network to display including
        the data.

        Any columns included will be shown in the Tooltip of the map, except for those starting with an underscore.

        There are some special columns that must be added here, that are used for visualization purposes:

        - _Radius: The radius of the node. This can be a computed property based on node data.
        - _FillColor: The color ([R, G, B]) to use for the line, serialized as JSON. This can be a computed property
                      based on node data.

        :return:
        :rtype: geopandas.GeoDataFrame
        """
        raise NotImplementedError("Please implement nodes_df in subclass")

    def _plot_div_producer(self):
        """
        Since this plot doesn't use plotly to plot, we override _plot_div_producer to return a string containing
        the html div to use for this plot. The template ``network_plot.html`` expects some parameters:

        - hash: this is used to make the html id's in the plot unique
        - edges: a GeoJson serialization of the networks edges and data
        - nodes: a GeoJson serialization of the networks nodes and data,
        - colors: a JSON dictionary of [R, G, B] arrays for the colors to use
        - zone: a GeoJson serialization of the zone's buildings
        - district: a GeoJson serialization of the distrct's buildings

        :return: a str containing a full html ``<div/>`` that includes the js code to display the map.
        """

        import os
        import hashlib
        import random
        from jinja2 import Template

        zone_df = geopandas.GeoDataFrame.from_file(self.locator.get_zone_geometry()).to_crs(
            get_geographic_coordinate_system())
        zone_df["_FillColor"] = json.dumps(self.colors["zone"])
        zone = zone_df.to_json(show_bbox=True)

        district_df = geopandas.GeoDataFrame.from_file(self.locator.get_surroundings_geometry()).to_crs(
            get_geographic_coordinate_system())
        district_df["_FillColor"] = json.dumps(self.colors["district"])
        district = district_df.to_json(show_bbox=True)

        edges = self.edges_df.to_json(show_bbox=True)
        nodes = self.nodes_df.to_json(show_bbox=True)

        hash = hashlib.md5((str(random.random()) + edges + nodes).encode("utf-8")).hexdigest()
        template = os.path.join(os.path.dirname(__file__), "network_plot.html")
        div = Template(open(template).read()).render(hash=hash, edges=edges, nodes=nodes,
                                                     zone=zone, district=district)
        return div
