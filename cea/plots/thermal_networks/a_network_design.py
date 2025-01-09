"""
Map plots for network pressure losses: Aggregated and peak.

Adapted from code by Lennart Rogenhofer.
"""





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


class NetworkLayoutOperationPeak(cea.plots.thermal_networks.ThermalNetworksMapPlotBase):
    """
    Plot condensing all the properties of the network of interest at peak time.
    """
    name = "Network Layout at Nominal Operating Conditions"

    def __init__(self, project, parameters, cache):
        super(NetworkLayoutOperationPeak, self).__init__(project, parameters, cache)

    @property
    def edges_df(self):
        edges_df = geopandas.GeoDataFrame.from_file(
            self.locator.get_network_layout_edges_shapefile(self.network_type, self.network_name)).to_crs(
            get_geographic_coordinate_system())
        edges_df["_LineWidth"] = 0.1 * edges_df["pipe_DN"]
        edges_df["length_m"] = edges_df["length_m"].round(1)

        # color the edges based on aggregated pipe heat loss
        P_loss_kPaperm_peak = (self.linear_pressure_loss_Paperm.max() / 1000).round(1) #to kPa/m
        Mass_flow_kgs_peak = self.mass_flow_kgs_pipes.max().round(1) #in kgs
        edges_df["Peak pressure loss [kPa/m]"] = P_loss_kPaperm_peak.values
        edges_df["Peak mass flow rate [kg/s]"] = Mass_flow_kgs_peak.values

        if self.velocity_mps_pipes is not None:  # backward compatibility with detailed thermal network (which does not include this output)
            velocity_ms_peak = self.velocity_mps_pipes.max().round(1)  # in kgs
            edges_df["Peak velocity [m/s]"] = velocity_ms_peak.values

        # color the edges based on aggregated pipe heat loss
        if self.thermal_loss_edges_Wperm is not None:  # backward compatibility with detailed thermal network (which does not include this output)
            yearly_thermal_loss = (self.thermal_loss_edges_Wperm.max()).round(2)
            edges_df["Peak Thermal losses [W/m]"] = yearly_thermal_loss.values

        # figure out colors
        p_loss_min = edges_df.pipe_DN.min()
        p = edges_df.pipe_DN.max()
        min_rgb_mpl = [remap(c, 0.0, 255.0, 0.0, 1.0) for c in get_color_array("white")]
        max_rgb_mpl = [remap(c, 0.0, 255.0, 0.0, 1.0) for c in get_color_array("red")]

        edges_df["_FillColor"] = edges_df.pipe_DN.apply(
            lambda p_loss: json.dumps(
                [remap(x, 0.0, 1.0, 0.0, 255.0)
                 for x in color_fader_rgb(min_rgb_mpl, max_rgb_mpl,
                                          mix=remap(p_loss, p_loss_min, p, 1.0, 1.0))])).values
        return edges_df

    @property
    def nodes_df(self):
        nodes_df = geopandas.GeoDataFrame.from_file(
            self.locator.get_network_layout_nodes_shapefile(self.network_type, self.network_name)).to_crs(
            get_geographic_coordinate_system())

        P_loss_kPa_peak = (self.pressure_at_nodes_Pa.max() / 1000).round(1) #to kPa
        nodes_df["Peak pressure [kPa]"] = P_loss_kPa_peak.values

        #temperature at all nodes
        temperature_supply = self.temperature_supply_nodes_C.round(1)
        temperature_return = self.temperature_return_nodes_C.round(1)
        index_max = self.buildings_hourly.idxmax(axis=0)
        delta_T = (temperature_supply - temperature_return).round(1)

        #temperature at the plant
        index_max_T_plant = self.buildings_hourly.sum(axis=1).idxmax(axis=0)
        temperature_supply_plant = self.temperature_supply_return_plant_C['temperature_supply_K'] - 273
        temperature_return_plant = self.temperature_supply_return_plant_C['temperature_return_K'] - 273
        T_supply_peak = round(temperature_supply_plant[index_max_T_plant],1)
        delta_T_peak = round((temperature_supply_plant - temperature_return_plant)[index_max_T_plant],1)

        #energy generation at the plant
        annual_loads = self.hourly_loads.values
        Q_loss_kWh = self.total_thermal_losses_kWh.values
        Peak_load_MWh = round((annual_loads + Q_loss_kWh).max()/1000,1)

        if self.mass_flow_kgs_nodes is not None: #backward compatibility with detailed thermal network (which does not include this output)
            Mass_flow_kgs_peak = self.mass_flow_kgs_nodes.max().round(1)
            nodes_df["Peak mass flow rate [kg/s]"] = Mass_flow_kgs_peak.values

        peak_demands = self.buildings_hourly.apply(pd.Series.max)
        pumping_peak = self.plant_pumping_requirement_kWh.max().round(1)

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

        def get_T_plant_node(row):
            if row["Type"] == "PLANT":
                return T_supply_peak
            else:
                return None

        def get_Peak_plant_node(row):
            if row["Type"] == "PLANT":
                return Peak_load_MWh
            else:
                return None

        def get_DT_plant_node(row):
            if row["Type"] == "PLANT":
                return delta_T_peak
            else:
                return None

        def get_peak_supply_temp(row):
            if row["Building"] in index_max.index.values:
                return temperature_supply[row['Name']][index_max[row["Building"]]]
            else:
                return None

        def get_peak_delta_temp(row):
            if row["Building"] in index_max.index.values:
                return delta_T[row['Name']][index_max[row["Building"]]]
            else:
                return None


        nodes_df["Peak Supply Temperature [C]"] = nodes_df.apply(get_peak_supply_temp, axis=1)
        nodes_df["Peak delta Temperature [C]"] = nodes_df.apply(get_peak_delta_temp, axis=1)
        nodes_df["Peak Thermal Demand [kW]"] = nodes_df.apply(get_peak_building_demand, axis=1)
        nodes_df["Pumping Power [kW]"] = nodes_df.apply(get_pumping_node, axis=1)
        nodes_df["Supply Temperature [C]"] = nodes_df.apply(get_T_plant_node, axis=1)
        nodes_df["Delta Temperature [C]"] = nodes_df.apply(get_DT_plant_node, axis=1)
        nodes_df["Peak Thermal Generation [MW]"] = nodes_df.apply(get_Peak_plant_node, axis=1)

        nodes_df["_Radius"] = self.get_radius(nodes_df)

        # Figure out the colors (based on the average supply temperatures)
        P_loss_min = nodes_df["Peak Thermal Demand [kW]"].min()
        P_loss_max = nodes_df["Peak Thermal Demand [kW]"].max()

        # matplotlib works on RGB in ranges [0.0, 1.0] - scale the input colors to that, transform and then scale back
        # to web versions ([0, 255])
        min_rgb_mpl = [remap(c, 0.0, 255.0, 0.0, 1.0) for c in get_color_array("white")]
        max_rgb_mpl = [remap(c, 0.0, 255.0, 0.0, 1.0) for c in get_color_array("red")]

        nodes_df["Peak Thermal Demand [kW]"] = nodes_df["Peak Thermal Demand [kW]"].fillna(0.0)
        nodes_df["_FillColor"] = json.dumps(get_color_array("black"))
        nodes_df["_FillColor"] = nodes_df["Peak Thermal Demand [kW]"].apply(
            lambda p_loss: json.dumps(
                [remap(x, 0.0, 1.0, 0.0, 255.0)
                 for x in color_fader_rgb(min_rgb_mpl, max_rgb_mpl,
                                          mix=remap(p_loss, P_loss_min, P_loss_max, 0.0, 1.0))])).values

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

    NetworkLayoutOperationPeak(config.project, {'network-type': config.plots.network_type,
                                            'scenario-name': config.scenario_name,
                                            'network-name': config.plots.network_name},
                               cache).plot(auto_open=True)
