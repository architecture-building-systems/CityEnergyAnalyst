"""
District Cooling System Class:
defines all properties of a district cooling system regard both its structure and its operation:
STRUCTURE
- Connectivity vector (identifying connections to networks and stand-alone buildings)
- List of the networks (network objects) found in the DCS
OPERATION
- Demands of the individual subsystems (networks and stand-alone buildings)
- Distributed energy potentials (allocated to each of the subsystems)
MIX (STRUCTURE & OPERATION)
- List of supply systems (supplySystem objects)
PERFORMANCE
- Total annualised cost
- Total annualised heat release
- Total annualised system energy demand
- Total annualised greenhouse gas emissions
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2022, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"

import numpy as np
import pandas as pd

from cea.optimization_new.network import Network
from cea.optimization_new.energyFlow import EnergyFlow
from cea.optimization_new.supplySystem import SupplySystem


class DistrictEnergySystem(object):
    max_nbr_networks = 0
    building_ids = []

    def __init__(self, connectivity):
        self._identifier = 'xxx'
        self.connectivity = connectivity
        self.stand_alone_buildings = []
        self.networks = []
        self.subsystem_demands = {}
        self.distributed_potentials = {}
        self.supply_systems = {}
        self.total_annualised_cost = 'xxx'
        self.total_annualised_heat_release = 'xxx'
        self.total_annualised_system_energy = 'xxx'
        self.total_annualised_GHG = 'xxx'

    @property
    def identifier(self):

        return self._identifier

    @identifier.setter
    def identifier(self, new_identifier):
        if isinstance(new_identifier, str):
            self._identifier = new_identifier
        else:
            print("Please set a valid identifier.")

    def generate_networks(self):
        """
        Generate networks according to the connectivity-vector. Generate list of stand-alone buildings and a list
        of networks (Network-objects).

        :return self.networks: thermal networks placed in the domain
        :rtype self.networks: list of <cea.optimization_new.network>-Network objects
        """
        network_ids = np.unique(np.array(self.connectivity))
        for network_id in network_ids:
            if network_id == 0:
                buildings_are_disconnected = list(self.connectivity == network_id)
                self.stand_alone_buildings = [building_id for [building_id, is_disconnected]
                                              in zip(DistrictEnergySystem.building_ids, buildings_are_disconnected)
                                              if is_disconnected]
            else:
                buildings_are_connected_to_network = list(self.connectivity == network_id)
                connected_buildings = [building_id for [building_id, is_connected]
                                       in zip(DistrictEnergySystem.building_ids, buildings_are_connected_to_network)
                                       if is_connected]
                full_network_identifier = 'N' + str(1000 + network_id)
                network = Network(full_network_identifier, connected_buildings)
                network.run_steiner_tree_optimisation()
                network.calculate_operational_conditions()
                self.networks.append(network)
        return self.networks

    def aggregate_demand(self, domain_buildings):
        """
        Calculate aggregated thermal energy demand profiles of the district energy system's subsystems, i.e. thermal
        networks. This includes the connected building's thermal energy demand and network losses.

        :param domain_buildings: all buildings in domain
        :type domain_buildings: list of <cea.optimization_new.building>-Building objects
        :return self.subsystem_demands: aggregated demand profiles of subsystems
        :rtype self.subsystem_demands: dict of pd.Series (keys are network.identifiers)
        """
        building_energy_carriers = np.array([building.demand_flow.energy_carrier.code for building in domain_buildings])
        required_energy_carriers = np.unique(building_energy_carriers)
        if len(required_energy_carriers) != 1:
            raise ValueError(f"The building energy demands require {len(required_energy_carriers)} different energy "
                             f"carriers to be produced. "
                             f"The optimisation algorithm can not handle more than one at the moment.")
        else:
            energy_carrier = required_energy_carriers[0]

        network_ids = [network.identifier for network in self.networks]
        self.subsystem_demands = dict([(network_id,
                                        EnergyFlow('primary', 'consumer', energy_carrier,
                                                   pd.Series(0.0, index=np.arange(EnergyFlow.time_frame)))
                                        )
                                       for network_id in network_ids])

        for network in self.networks:
            building_demand_flows = [building.demand_flow for building in domain_buildings
                                     if building.identifier in network.connected_buildings]
            aggregated_demand = EnergyFlow.aggregate(building_demand_flows)[0]
            aggregated_demand.profile += network.network_losses
            self.subsystem_demands[network.identifier] = aggregated_demand

        return self.subsystem_demands

    def distribute_potentials(self, domain_energy_potentials):
        """
        Distribute the total domain's energy potentials depending on the buildings within each of networks (for
        building-scale potentials) or on the share of the domain's total demand each network makes out (for domain-scale
        potentials).
        """
        network_demand_shares = None
        network_identifiers = [network.identifier for network in self.networks]
        self.distributed_potentials = {network_id: {} for network_id in network_identifiers}

        for energy_potential in domain_energy_potentials:
            main_energy_carrier = energy_potential.main_potential.energy_carrier.code
            # distribute building-scale energy potentials
            if energy_potential.scale == 'Building':
                for network in self.networks:
                    main_network_pot_profile = sum([energy_potential.main_building_profiles[building]
                                                    for building in network.connected_buildings])
                    if main_energy_carrier in self.distributed_potentials[network.identifier].keys():
                        self.distributed_potentials[network.identifier][main_energy_carrier] += main_network_pot_profile
                    else:
                        main_network_pot_flow = EnergyFlow('source', 'secondary',
                                                           main_energy_carrier, main_network_pot_profile)
                        self.distributed_potentials[network.identifier][main_energy_carrier] = main_network_pot_flow

                    if energy_potential.auxiliary_potential.energy_carrier:
                        aux_energy_carrier = energy_potential.auxiliary_potential.energy_carrier.code
                        aux_network_pot_profile = sum([energy_potential.auxiliary_building_profiles[building]
                                                       for building in network.connected_buildings])
                        if aux_energy_carrier in self.distributed_potentials[network.identifier].keys():
                            self.distributed_potentials[network.identifier][aux_energy_carrier] += \
                            aux_network_pot_profile
                        else:
                            aux_network_pot_flow = EnergyFlow('source', 'secondary',
                                                              aux_energy_carrier, aux_network_pot_profile)
                            self.distributed_potentials[network.identifier][aux_energy_carrier] = aux_network_pot_flow
            # distribute domain-scale energy potentials
            if energy_potential.scale == 'Domain':
                if not network_demand_shares:
                    network_yearly_demands = {network: self.subsystem_demands[network].profile.sum()
                                              for network in network_identifiers}
                    network_demands_sum = sum([network_yearly_demands[network] for network in network_identifiers])
                    network_demand_shares = {network: network_yearly_demands[network]/network_demands_sum
                                             for network in network_identifiers}

                for network_id in network_identifiers:
                    main_network_pot_profile = energy_potential.main_potential.profile * \
                                               network_demand_shares[network_id]
                    if main_energy_carrier in self.distributed_potentials[network_id].keys():
                        self.distributed_potentials[network_id][main_energy_carrier] += main_network_pot_profile
                    else:
                        main_network_pot_flow = EnergyFlow('source', 'secondary',
                                                           main_energy_carrier, main_network_pot_profile)
                        self.distributed_potentials[network_id][main_energy_carrier] = main_network_pot_flow

                    if energy_potential.auxiliary_potential.energy_carrier:
                        aux_energy_carrier = energy_potential.auxiliary_potential.energy_carrier.code
                        aux_network_pot_profile = energy_potential.auxiliary_potential.profile\
                                                  * network_demand_shares[network_id]
                        if aux_energy_carrier in self.distributed_potentials[network_id].keys():
                            self.distributed_potentials[network_id][aux_energy_carrier] += aux_network_pot_profile
                        else:
                            aux_network_pot_flow = EnergyFlow('source', 'secondary',
                                                              aux_energy_carrier, aux_network_pot_profile)
                            self.distributed_potentials[network_id][aux_energy_carrier] = aux_network_pot_flow

        return self.distributed_potentials

    def generate_supply_systems(self):
        """
        Build and calculate operation for supply systems of each of the subsystems of the district energy system:

        :return self.supply_systems: supply systems of all subsystems
        :rtype self.supply_systems: list of <cea.optimization_new.supplySystem>-SupplySystem objects
        """
        for network in self.networks:
            supply_system = SupplySystem(demand_energy_flow=self.subsystem_demands[network.identifier],
                                         available_potentials=self.distributed_potentials[network.identifier])
            supply_system.build_system_structure()
            supply_system.optimize_subsystem()
            self.supply_systems[network.identifier] = supply_system
        return self.supply_systems

    @staticmethod
    def initialize_class_variables(domain):
        """ Define a maximum number of networks and store domain building identifiers in class variables. """
        DistrictEnergySystem.max_nbr_networks = domain.config.optimization_new.maximum_number_of_networks
        DistrictEnergySystem.building_ids = [building.identifier for building in domain.buildings]
