"""
Network optimization
"""




import pandas as pd

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Tim Vollrath", "Thuy-An Nguyen", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


class NetworkOptimizationFeatures(object):
    """
    This class just sets up constants of the linear model of the distribution.
    These results are extracted from the work of Florian at the chair.
    Unfortunately his work only worked for this case study and could not be used else where
    See the paper of Fonseca et al. 2015 of the city energy analyst for more info on how that procedure used to work.
    """

    def __init__(self, district_heating_network, district_cooling_network, locator):
        self.network_names = ['']

        for network_name in self.network_names:
            if district_heating_network:
                self.E_pump_DHN_W = pd.read_csv(locator.get_network_energy_pumping_requirements_file("DH", network_name))[
                    'pressure_loss_total_kW'].values * 1000
                self.mass_flow_rate_DHN = self.mass_flow_rate_plant(locator, network_name, "DH")
                self.thermallosses_DHN = pd.read_csv(locator.get_network_total_thermal_loss_file("DH", network_name))[
                    'thermal_loss_total_kW'].values
                self.pipesCosts_DHN_USD = self.pipe_costs(locator, network_name, "DH")

            if district_cooling_network:
                self.E_pump_DCN_W = pd.read_csv(locator.get_network_energy_pumping_requirements_file("DC", network_name))[
                    'pressure_loss_total_kW'].values * 1000
                self.mass_flow_rate_DCN = self.mass_flow_rate_plant(locator, network_name, "DC")
                self.thermallosses_DCN = pd.read_csv(locator.get_network_total_thermal_loss_file("DC", network_name))[
                    'thermal_loss_total_kW'].values
                self.pipesCosts_DCN_USD = self.pipe_costs(locator, network_name, "DC")

    def mass_flow_rate_plant(self, locator, network_name, network_type):
        mass_flow_df = pd.read_csv((locator.get_thermal_network_layout_massflow_nodes_file(network_type, network_name)))
        mass_flow_nodes_df = pd.read_csv((locator.get_thermal_network_node_types_csv_file(network_type, network_name)))
        # identify the node with the plant
        node_id = mass_flow_nodes_df.loc[mass_flow_nodes_df['Type'] == "PLANT", 'Name'].item()
        return mass_flow_df[node_id].values


    def pipe_costs(self, locator, network_name, network_type):
        edges_file = pd.read_csv(locator.get_thermal_network_edge_list_file(network_type, network_name))
        piping_cost_data = pd.read_csv(locator.get_database_components_distribution_thermal_grid('THERMAL_GRID'))
        
        # FIXME: Standardize column name in files
        merge_df = edges_file.rename(columns={'Pipe_DN': 'pipe_DN'}).merge(piping_cost_data, on='pipe_DN')
        merge_df['Inv_USD2015'] = merge_df['Inv_USD2015perm'] * merge_df['length_m']
        pipe_costs = merge_df['Inv_USD2015'].sum()
        return pipe_costs
