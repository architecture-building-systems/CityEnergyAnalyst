"""
Subsystem Class:
defines all properties as supply system of a single network or stand-alone building in the DCS, including:
STRUCTURE
- types of installed components
- capacities of components
OPERATION
- energy inputs, outputs and losses during operation
PERFORMANCE
- cost of components and energy carriers
- system energy demand (i.e. power inputs to the supply system)
- heat rejection of the system (losses + exhausts)
- greenhouse gas emissions of the system
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2022, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"


class SupplySystem(object):

    def __init__(self, demand_profile=None):
        if demand_profile is None:
            self.demand_profile = []
        else:
            self.demand_profile = demand_profile
        self.maximum_demand = 'xxx'
        self.capacity_indicators = 'xxx'
        self.primary_components = 'xxx'
        self.secondary_components = 'xxx'
        self.tertiary_components = 'xxx'
        self.component_energy_inputs = 'xxx'
        self.component_energy_outputs = 'xxx'
        self.component_energy_losses = 'xxx'
        self.cost = 'xxx'
        self.system_energy_demand = 'xxx'
        self.heat_rejection = 'xxx'
        self.greenhouse_gas_emissions = 'xxx'

    def calculate_maximum_demand(self,):

        return self.maximum_demand

    def optimize_subsystem(self):

        return self.capacity_indicators

    def create_components(self):

        return self.primary_components, self.secondary_components, self.tertiary_components

    def perform_water_filling_principle(self):

        return self.component_energy_inputs, self.component_energy_outputs

    def calculate_power_generation(self):

        return self.component_energy_inputs, self.component_energy_outputs, self.component_energy_losses

    def calculate_cost(self):

        return self.cost

    def calculate_system_energy_demand(self):

        return self.system_energy_demand

    def calculate_heat_rejection(self):

        return self.heat_rejection

    def calculate_greenhouse_gas_emissions(self):

        return self.greenhouse_gas_emissions

