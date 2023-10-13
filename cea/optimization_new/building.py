"""
This Building Class defines a building in the domain analysed by the optimisation script.

The buildings described using the Building Class bundle all properties relevant for the optimisation, including:
- The building's unique identifier (i.e. 'Name' from the input editor)
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
from cea.utilities import dbf
from cea.optimization_new.supplySystem import SupplySystem
from cea.optimization_new.containerclasses.energyFlow import EnergyFlow
from cea.optimization_new.containerclasses.supplySystemStructure import SupplySystemStructure


class Building(object):
    _base_supply_systems = pd.DataFrame()
    _supply_system_database = pd.DataFrame()

    def __init__(self, identifier, demands_file_path):
        self.identifier = identifier
        self.demands_file_path = demands_file_path
        self.stand_alone_supply_system = SupplySystem()
        self.crs = None
        self._demand_flow = EnergyFlow()
        self._footprint = None
        self._location = None
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

    def load_demand_profile(self, energy_system_type='DH'):
        """
        Load the buildings relevant demand profile, i.e. 'QC_sys_kWh' for the district heating optimisation &
        'QC_sys_kWh' for the district cooling optimisation)
        """
        demand_dataframe = pd.read_csv(self.demands_file_path)

        if energy_system_type == 'DC':
            self.demand_flow = EnergyFlow('primary', 'consumer', 'T10W', demand_dataframe['QC_sys_kWh'])
        elif energy_system_type == 'DH':
            self.demand_flow = EnergyFlow('primary', 'consumer', 'T60W', demand_dataframe['QH_sys_kWh'])
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
            self.footprint = domain_shp_file[domain_shp_file.Name == self.identifier].geometry.iloc[0]
            self.location = self.footprint.representative_point()
        else:
            pass

        return self.location

    def load_base_supply_system(self, file_locator, energy_system_type='DH'):
        """
        Load the building's base supply system and determine what the supply system composition for the given system
        looks like (using SUPPLY_NEW.xlsx-database). The base supply system is given in the 'supply_systems.dbf'-file.
        """

        # load the building supply systems file as a class variable
        if Building._base_supply_systems.empty:
            building_supply_systems_file = file_locator.get_building_supply()
            Building._base_supply_systems = dbf.dbf_to_dataframe(building_supply_systems_file)

        # fetch the base supply system for the building according to the building supply systems file
        base_supply_system_info = Building._base_supply_systems[Building._base_supply_systems['Name'] == self.identifier]
        if base_supply_system_info.empty:
            raise ValueError(f"Please make sure supply systems file specifies a base-case supply system for all "
                             f"buildings. No information could be found on building '{self.identifier}'.")
        elif energy_system_type == 'DH':
            self._stand_alone_supply_system_code = base_supply_system_info['type_hs'].values[0]
        elif energy_system_type == 'DC':
            self._stand_alone_supply_system_code = base_supply_system_info['type_cs'].values[0]
        else:
            raise ValueError(f"'{energy_system_type}' is not a valid energy system type. The relevant base supply "
                             f"system for building '{self.identifier}' could therefore not be assigned.")

        # load the 'assemblies'-supply systems database as a class variable
        if Building._supply_system_database.empty:
            supply_systems_database_file = pd.ExcelFile(file_locator.get_database_supply_assemblies_new())
            if energy_system_type == 'DH':
                Building._supply_system_database = pd.read_excel(supply_systems_database_file, 'HEATING')
            elif energy_system_type == 'DC':
                Building._supply_system_database = pd.read_excel(supply_systems_database_file, 'COOLING')
            else:
                raise ValueError(f"'{energy_system_type}' is not a valid energy system type. No appropriate "
                                 f"'assemblies'-supply system database could therefore be loaded.")

        # fetch the system composition (primary, secondary & tertiary components) for the building
        system_details = Building._supply_system_database[Building._supply_system_database['code']
                                                          == self._stand_alone_supply_system_code]
        for category in ['primary', 'secondary', 'tertiary']:
            category_components = system_details[category + '_components'].values[0].replace(" ", "")
            if category_components == '-':
                self._stand_alone_supply_system_composition[category] = []
            else:
                self._stand_alone_supply_system_composition[category] = category_components.split(',')
        return

    def calculate_supply_system(self, available_potentials):
        """
        Create a SupplySystem-object for the building's base supply system and calculate how it would need to be
        operated to meet the building's demand.
        """
        # determine the required system capacity
        max_supply_flow = self.demand_flow.profile.max()
        user_component_selection = self._stand_alone_supply_system_composition

        # use the SupplySystemStructure methods to dimension each of the system's components
        system_structure = SupplySystemStructure(max_supply_flow, available_potentials, user_component_selection)
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
