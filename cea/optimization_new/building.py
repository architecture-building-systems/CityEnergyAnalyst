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
from cea.optimization_new.energyFlow import EnergyFlow


class Building(object):

    def __init__(self, identifier, demands_file_path):
        self.identifier = identifier
        self.demands_file_path = demands_file_path
        self._demand_flow = EnergyFlow()
        self._footprint = None
        self._location = None

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

        demand_dataframe = pd.read_csv(self.demands_file_path)

        if energy_system_type == 'DC':
            self.demand_flow = EnergyFlow('primary', 'consumer', 'T10C', demand_dataframe['QC_sys_kWh'])
        elif energy_system_type == 'DH':
            self.demand_flow = EnergyFlow('primary', 'consumer', 'T60C', demand_dataframe['QH_sys_kWh'])
        else:
            print('Please indicate a valid energy system type.')

        return self.demand_flow

    def load_building_location(self, domain_shp_file):

        if self.location is None:
            self.footprint = domain_shp_file[domain_shp_file.Name == self.identifier].geometry.iloc[0]
            self.location = self.footprint.representative_point()
        else:
            pass

        return self.location
