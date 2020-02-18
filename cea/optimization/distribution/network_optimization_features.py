"""
Network optimization
"""
from __future__ import division
import pandas as pd
import numpy as np
from cea.constants import HOURS_IN_YEAR

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
    This class just sets-ip constants of the linear model of the distribution.
    These results are extracted from the work of Florian at the chair.
    Unfortunately his work only worked for this case study and could not be used else where
    See the paper of Fonseca et al 2015 of the city energy analyst for more info on how that procedure used to work.
    """
    def __init__(self, district_heating_network, district_cooling_network,  locator):
        self.pipesCosts_DHN_USD = 0.0    # USD-2015
        self.pipesCosts_DCN_USD = 0.0     # USD-2015
        self.DeltaP_DHN = np.zeros(HOURS_IN_YEAR)         # Pa
        self.DeltaP_DCN = np.zeros(HOURS_IN_YEAR)        # Pa
        self.thermallosses_DHN = 0.0
        self.thermallosses_DCN = 0.0
        self.network_names = ['']
        self.district_heating_network = district_heating_network
        self.district_cooling_network = district_cooling_network


        for network_name in self.network_names:
            if self.district_heating_network:
                pressure_drop_Pa = pd.read_csv(locator.get_network_total_pressure_drop_file("DH", network_name))
                self.DeltaP_DHN = self.DeltaP_DHN + pressure_drop_Pa['pressure_loss_total_Pa']
            if self.district_cooling_network:
                pressure_drop_Pa = pd.read_csv(locator.get_network_total_pressure_drop_file("DC", network_name))
                self.DeltaP_DCN = self.DeltaP_DCN + pressure_drop_Pa['pressure_loss_total_Pa']

        for network_name in self.network_names:
            if self.district_heating_network:
                thermal_losses_kW = pd.read_csv(locator.get_network_total_thermal_loss_file("DH", network_name))
                self.thermallosses_DHN = self.thermallosses_DHN + thermal_losses_kW['thermal_loss_total_kW']
            if self.district_cooling_network:
                thermal_losses_kW = pd.read_csv(locator.get_network_total_thermal_loss_file("DC", network_name))
                self.thermallosses_DCN = self.thermallosses_DCN + thermal_losses_kW['thermal_loss_total_kW']

        for network_name in self.network_names:
            if self.district_heating_network:
                pipe_cost = self.pipe_costs(locator, network_name, "DH")
                self.pipesCosts_DHN_USD = self.pipesCosts_DHN_USD + pipe_cost
            if self.district_cooling_network:
                pipe_cost = self.pipe_costs(locator, network_name, "DC")
                self.pipesCosts_DCN_USD = self.pipesCosts_DCN_USD + pipe_cost

    def pipe_costs(self, locator, network_name, network_type):
        edges_file = pd.read_csv(locator.get_thermal_network_edge_list_file(network_type, network_name))
        piping_cost_data = pd.read_excel(locator.get_database_distribution_systems(), sheet_name="THERMAL_GRID")
        merge_df = edges_file.merge(piping_cost_data, left_on='Pipe_DN', right_on='Pipe_DN')
        merge_df['Inv_USD2015'] = merge_df['Inv_USD2015perm'] * merge_df['length_m']
        pipe_costs = merge_df['Inv_USD2015'].sum()
        return pipe_costs
