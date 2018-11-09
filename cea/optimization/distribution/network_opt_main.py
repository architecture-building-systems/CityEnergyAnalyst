"""
Network optimization
"""
from __future__ import division
import pandas as pd
import numpy as np

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Tim Vollrath", "Thuy-An Nguyen", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

class network_opt_main(object):
    """
    This class just sets-ip constants of the linear model of the distribution.
    These results are extracted form the work of Florian at the chair.
    Unfortunately his work only worked for this case study and could not be used else where
    See the paper of Fonseca et al 2015 of the city energy analyst for more info on how that procedure used to work.
    """
    def __init__(self, config, locator):
        self.pipesCosts_DHN_USD = 0     # USD-2015
        self.pipesCosts_DCN_USD = 0     # USD-2015
        self.DeltaP_DHN = np.zeros(8760)         # Pa
        self.DeltaP_DCN = np.zeros(8760)        # Pa
        self.thermallosses_DHN = 0
        self.thermallosses_DCN = 0

        network_names = config.thermal_network.network_names

        if len(network_names) == 0:
            network_names = ['']

        for network_name in network_names:
            pressure_drop_Pa = pd.read_csv(locator.get_optimization_network_layout_pressure_drop_file(config.thermal_network.network_type, network_name))
            if config.thermal_network.network_type == 'DH':
                for i in range(8760):
                    self.DeltaP_DHN[i] = self.DeltaP_DHN[i] + pressure_drop_Pa['pressure_loss_total_Pa'][i]
            if config.thermal_network.network_type == 'DC':
                for i in range(8760):
                    self.DeltaP_DCN[i] = self.DeltaP_DCN[i] + pressure_drop_Pa['pressure_loss_total_Pa'][i]

        for network_name in network_names:
            thermal_loss_sum = 0
            thermal_losses_kW = pd.read_csv(locator.get_optimization_network_layout_qloss_system_file(config.thermal_network.network_type, network_name))
            for column_name in thermal_losses_kW.columns:
                thermal_loss_sum = thermal_loss_sum + (thermal_losses_kW[column_name].sum())*1000
            if config.thermal_network.network_type == 'DH':
                self.thermallosses_DHN = self.thermallosses_DHN + thermal_loss_sum
            if config.thermal_network.network_type == 'DC':
                self.thermallosses_DCN = self.thermallosses_DCN + thermal_loss_sum

        for network_name in network_names:
            pipe_cost = 0
            edges_file = pd.read_csv(locator.get_optimization_network_edge_list_file(config.thermal_network.network_type, network_name))
            internal_diameter = (edges_file['D_int_m'].values) * 1000
            pipe_length = edges_file['pipe length'].values

            for i in range(len(internal_diameter)):
                piping_cost_data = pd.read_excel(locator.get_supply_systems(config.region), sheetname="Piping")
                piping_cost_data = piping_cost_data[
                    (piping_cost_data['Diameter_min'] <= internal_diameter[i]) & (
                                piping_cost_data['Diameter_max'] > internal_diameter[i])]
                pipe_cost = pipe_cost + (piping_cost_data.iloc[0]['Investment']) * pipe_length[i]

            if config.thermal_network.network_type == 'DH':
                self.pipesCosts_DHN_USD = self.pipesCosts_DHN_USD + pipe_cost
            if config.thermal_network.network_type == 'DC':
                self.pipesCosts_DCN_USD = self.pipesCosts_DCN_USD + pipe_cost
