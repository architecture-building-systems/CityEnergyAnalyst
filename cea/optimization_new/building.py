"""
This Building Class defines a building in the domain analysed by the optimisation script.

The buildings described using the Building Class bundle all properties relevant for the optimisation, including:
- The building's unique identifier (i.e. 'name' from the input editor)
- The building's location
- The demand profile of the building
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2022, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"

import pandas as pd

from cea.optimization_new.component import Component
from cea.optimization_new.supplySystem import SupplySystem
from cea.optimization_new.containerclasses.energyFlow import EnergyFlow
from cea.optimization_new.containerclasses.supplySystemStructure import SupplySystemStructure


class Building(object):
    _base_supply_systems = pd.DataFrame()
    _supply_system_database = pd.DataFrame()

    def __init__(self, identifier: str, demands_file_path):
        self.identifier = identifier
        self.demands_file_path = demands_file_path
        self.stand_alone_supply_system = SupplySystem()
        self.crs = None
        self._demand_flow = EnergyFlow()
        self._footprint = None
        self._location = None
        self._initial_connectivity_state = 'stand_alone'
        self._stand_alone_supply_system_code = None
        self._stand_alone_supply_system_composition = {'primary': [], 'secondary': [], 'tertiary': []}

    @property
    def demand_flow(self):

        return self._demand_flow

    @demand_flow.setter
    def demand_flow(self, new_demand_flow):
        if isinstance(new_demand_flow, EnergyFlow):
            self._demand_flow = new_demand_flow
        else:
            raise ValueError("Please, make sure you're assigning a valid demand profile. "
                             "Try assigning demand profiles using the load_demand_profile method.")

    @property
    def footprint(self):

        return self._footprint

    @footprint.setter
    def footprint(self, new_footprint):
        if new_footprint.geom_type == 'Polygon':
            self._footprint = new_footprint
        else:
            raise ValueError("Please only assign a polygon to the building footprint. "
                             "Try using the load_building_location method for assigning building footprints.")

    @property
    def location(self):

        return self._location

    @location.setter
    def location(self, new_location):
        if new_location.geom_type == 'Point':
            self._location = new_location
        else:
            raise ValueError("Please only assign a point to the building location. "
                             "Try using the load_building_location method for assigning building locations.")

    @property
    def initial_connectivity_state(self):
        return self._initial_connectivity_state

    @initial_connectivity_state.setter
    def initial_connectivity_state(self, new_base_connectivity):
        if new_base_connectivity in ['stand_alone', 'network'] \
                or (new_base_connectivity.startswith('N') and new_base_connectivity[1:].isdigit()):
            self._initial_connectivity_state = new_base_connectivity
        else:
            raise ValueError("Please only assign 'stand_alone' or 'network_i' to the base connectivity of the building.")

    def load_demand_profile(self, energy_system_type='DH'):
        """
        Load the buildings relevant demand profile, i.e. 'QC_sys_kWh' for the district heating optimisation &
        'QC_sys_kWh' for the district cooling optimisation)
        """
        demand_dataframe = pd.read_csv(self.demands_file_path)

        if energy_system_type == 'DC':
            self.demand_flow = EnergyFlow('primary', 'consumer', 'T10W', demand_dataframe['QC_sys_kWh'])
        elif energy_system_type == 'DH':
            self.demand_flow = EnergyFlow('primary', 'consumer', 'T30W', demand_dataframe['QH_sys_kWh'])
        else:
            print('Please indicate a valid energy system type.')

        return self.demand_flow

    def load_building_location(self, domain_shp_file):
        """
        Load building's location from the domain's shape file (in the project's projected WGS84 coordinate
        reference system).
        """
        if self.location is None:
            self.crs = domain_shp_file.crs
            self.footprint = domain_shp_file[domain_shp_file.name == self.identifier].geometry.iloc[0]
            self.location = self.footprint.representative_point()
        else:
            pass

        return self.location

    def load_base_supply_system(self, locator, energy_system_type='DH'):
        """
        Load the building's base supply system and determine what the supply system composition for the given system
        looks like (using SUPPLY_NEW.xlsx-database). The base supply system is given in the 'supply_systems.dbf'-file.
        """

        # load the building supply systems file as a class variable
        if Building._base_supply_systems.empty:
            building_supply_systems_file = locator.get_building_supply()
            Building._base_supply_systems = pd.read_csv(building_supply_systems_file)

        # fetch the base supply system for the building according to the building supply systems file
        base_supply_system_info = Building._base_supply_systems[Building._base_supply_systems['name'] == self.identifier]
        if base_supply_system_info.empty:
            raise ValueError(f"Please make sure supply systems file specifies a base-case supply system for all "
                             f"buildings. No information could be found on building '{self.identifier}'.")
        elif energy_system_type == 'DH':
            self._stand_alone_supply_system_code = base_supply_system_info['supply_type_hs'].values[0]
        elif energy_system_type == 'DC':
            self._stand_alone_supply_system_code = base_supply_system_info['supply_type_cs'].values[0]
        else:
            raise ValueError(f"'{energy_system_type}' is not a valid energy system type. The relevant base supply "
                             f"system for building '{self.identifier}' could therefore not be assigned.")

        # load the 'assemblies'-supply systems database as a class variable
        if Building._supply_system_database.empty:
            if energy_system_type == 'DH':
                Building._supply_system_database = pd.read_csv(locator.get_database_assemblies_supply_heating())
            elif energy_system_type == 'DC':
                Building._supply_system_database = pd.read_csv(locator.get_database_assemblies_supply_cooling())
            else:
                raise ValueError(f"'{energy_system_type}' is not a valid energy system type. No appropriate "
                                 f"'assemblies'-supply system database could therefore be loaded.")

        # fetch the supply system composition for the building or it's associated district energy system
        self.fetch_supply_system_composition()

        return

    def fetch_supply_system_composition(self):
        """
        Identify if the building is connected to a district heating or cooling network or has a stand-alone system.
        Depending on the case, fetch the system composition (primary, secondary & tertiary components) for the building
        or complete the system composition for the district energy system the building is connected to.

        To establish a default stand-alone supply system in the event of a building's disconnection from a district
        energy system, it's assumed that the supply system composition of the respective networks is directly applied to
        the building's stand-alone supply system.
        """
        # register if the building is connected to a district heating or cooling network or has a stand-alone system
        system_details = Building._supply_system_database[Building._supply_system_database['code']
                                                          == self._stand_alone_supply_system_code]
        energy_system_scale = system_details['scale'].values[0].replace(" ", "").lower()

        if energy_system_scale in ['', '-', 'building']:
            self.initial_connectivity_state = 'stand_alone'
        elif energy_system_scale == 'district':
            self.initial_connectivity_state = 'network'

        # fetch the system composition (primary, secondary & tertiary components)
        # ... for the stand-alone supply system
        for category in ['primary', 'secondary', 'tertiary']:
            category_components = system_details[category + '_components'].values[0].replace(" ", "")

            if category_components == '-':
                self._stand_alone_supply_system_composition[category] = []
            else:
                self._stand_alone_supply_system_composition[category] = category_components.split(',')

        # ... or for the network supply system
        if self.initial_connectivity_state == 'network':

            if system_details['code'].values[0] not in SupplySystemStructure.initial_network_supply_systems.keys():
                network_id = f'N{len(SupplySystemStructure.initial_network_supply_systems) + 1001}'
                SupplySystemStructure.initial_network_supply_systems[system_details['code'].values[0]] = network_id
                SupplySystemStructure.initial_network_supply_systems_composition[network_id] = {'primary': [],
                                                                                                'secondary': [],
                                                                                                'tertiary': []}

                for category in ['primary', 'secondary', 'tertiary']:
                    category_components = system_details[category + '_components'].values[0].replace(" ", "")

                    if category_components == '-':
                        SupplySystemStructure.initial_network_supply_systems_composition[network_id][category] = []
                    else:
                        SupplySystemStructure.initial_network_supply_systems_composition[network_id][category] = \
                            category_components.split(',')

            else:
                network_id = SupplySystemStructure.initial_network_supply_systems[system_details['code'].values[0]]

            self.initial_connectivity_state = network_id

        return

    def check_demand_energy_carrier(self):
        """
        Check if the energy carrier of the building's demand profile is compatible with the energy carrier of the
        building's allocated supply system, if it's not, correct the demand profile to match the supply system's
        energy carrier.
        """
        if Component.code_to_class_mapping is None:
            raise ValueError("Please make sure the Component-class has been initialised properly before checking the "
                             "building's demand energy carrier.")

        primary_component_classes = [Component.code_to_class_mapping[component_code]
                                     for component_code in self._stand_alone_supply_system_composition['primary']]
        instantiated_components = [component_class(code, 'primary', self.demand_flow.profile.max())
                                   for component_class, code
                                   in zip(primary_component_classes,
                                          self._stand_alone_supply_system_composition['primary'])]
        main_energy_carriers = [component.main_energy_carrier for component in instantiated_components]

        if len(set(main_energy_carriers)) > 1:
            raise ValueError(f"The primary components of the building {self.identifier}'s supply system are not "
                             f"compatible with one another. Please correct your system choice in the INPUT "
                             f"EDITOR accordingly.")
        elif len(set(main_energy_carriers)) == 0:
            raise ValueError("Network type mismatch: 'DH' (district heating) cannot be used for cooling loads, "
                           "and 'DC' (district cooling) cannot be used for heating loads. "
                           "Please verify that the network-type matches the building's demand.")
        else:
            self.demand_flow.energy_carrier = main_energy_carriers[0]

        return

    def calculate_supply_system(self, available_potentials):
        """
        Create a SupplySystem-object for the building's base supply system and calculate how it would need to be
        operated to meet the building's demand.
        """
        # determine the required system capacity
        max_supply_flow = self.demand_flow.isolate_peak()
        user_component_selection = self._stand_alone_supply_system_composition

        # use the SupplySystemStructure methods to dimension each of the system's components
        system_structure = SupplySystemStructure(max_supply_flow, available_potentials, user_component_selection,
                                                 self.identifier)
        system_structure.build()

        # create a SupplySystem-instance and operate the system to meet the yearly demand profile.
        self.stand_alone_supply_system = SupplySystem(system_structure,
                                                      system_structure.capacity_indicators,
                                                      self.demand_flow)
        self.stand_alone_supply_system.evaluate()

        return self.stand_alone_supply_system

    @staticmethod
    def distribute_building_potentials(domain_energy_potentials, domain_buildings):
        """
        Attribute the respective building-scale energy potentials to each of the buildings in the domain.

        :param domain_energy_potentials: renewable energy potentials available in the domain
        :type domain_energy_potentials: list of
                <cea.optimization_new.containerclasses.energysystems.energyPotential.EnergyPotential>-class objects
        :param domain_buildings: all buildings in the domain
        :type domain_energy_potentials: list of <cea.optimization_new.building.Building>-class objects
        """
        # identify which energy potentials are building-scale potentials (e.g. PV).
        building_scale_energy_potentials = [energy_potential for energy_potential in domain_energy_potentials
                                            if energy_potential.scale == 'Building']
        building_energy_potentials = {building.identifier: {} for building in domain_buildings}

        # group the potentials by energy carriers and sum them up if necessary
        for potential in building_scale_energy_potentials:
            for building, profile in potential.main_building_profiles.items():
                if potential.main_potential.energy_carrier.code in building_energy_potentials[building].keys():
                    building_energy_potentials[building][potential.main_potential.energy_carrier.code] += \
                        EnergyFlow('source', 'secondary',
                                    potential.main_potential.energy_carrier.code, profile)
                else:
                    building_energy_potentials[building][potential.main_potential.energy_carrier.code] = \
                        EnergyFlow('source', 'secondary',
                                    potential.main_potential.energy_carrier.code, profile)
            for building, profile in potential.auxiliary_building_profiles.items():
                if potential.auxiliary_potential.energy_carrier.code in building_energy_potentials[building].keys():
                    building_energy_potentials[building][potential.auxiliary_potential.energy_carrier.code] += \
                        EnergyFlow('source', 'secondary',
                                    potential.main_potential.energy_carrier.code, profile)
                else:
                    building_energy_potentials[building][potential.auxiliary_potential.energy_carrier.code] = \
                        EnergyFlow('source', 'secondary',
                                    potential.main_potential.energy_carrier.code, profile)

        return building_energy_potentials
