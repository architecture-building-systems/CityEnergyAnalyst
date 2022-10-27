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


class DistrictCoolingSystem(object):
    def __init__(self):
        self._identifier = 'xxx'
        self.connectivity = 'xxx'
        self.networks = 'xxx'
        self.subsystem_demands = 'xxx'
        self.distributed_potentials = 'xxx'
        self.supply_systems = 'xxx'
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

    def generate_networks(self,):

        return self.networks

    def aggregate_demand(self):

        return self.subsystem_demands

    def distribute_potentials(self):

        return self.distributed_potentials

    def generate_supply_systems(self):

        return self.supply_systems
