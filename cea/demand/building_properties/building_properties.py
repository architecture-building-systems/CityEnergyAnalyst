"""
Classes of building properties
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from cea.demand.building_properties.building_comfort import BuildingComfort
from cea.demand.building_properties.building_internal_loads import BuildingInternalLoads
from cea.demand.building_properties.building_properties_row import BuildingPropertiesRow
from cea.demand.building_properties.building_supply_systems import BuildingSupplySystems
from cea.demand.building_properties.building_rc_model import BuildingRCModel
from cea.demand.building_properties.building_geometry import BuildingGeometry
from cea.demand.building_properties.building_envelope import BuildingEnvelope
from cea.demand.building_properties.building_hvac import BuildingHVAC
from cea.demand.building_properties.building_typology import BuildingTypology
from cea.demand.building_properties.building_solar import BuildingSolar

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle", "Jimeno A. Fonseca", "Daren Thomas", "Jack Hawthorne", "Reynold Mok"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"



class BuildingProperties:
    """
    Groups building properties used for the calc-thermal-loads functions. Stores the full DataFrame for each of the
    building properties and provides methods for indexing them by name.

    G. Happle   BuildingPropsThermalLoads   27.05.2016
    """

    def __init__(self, locator, weather_data, building_names=None):
        """
        Read building properties from input shape files and construct a new BuildingProperties object.

        :param locator: an InputLocator for locating the input files
        :type locator: cea.inputlocator.InputLocator

        :param List[str] building_names: list of buildings to read properties

        :returns: BuildingProperties
        :rtype: BuildingProperties
        """

        if building_names is None:
            building_names = locator.get_zone_building_names()

        self.building_names = building_names
        print("read input files")
        
        self.geometry = BuildingGeometry(locator, building_names)
        prop_geometry = self.geometry._prop_geometry

        self.envelope = BuildingEnvelope(locator, building_names)
        prop_envelope = self.envelope._prop_envelope

        self.hvac = BuildingHVAC(locator, building_names)
        prop_hvac = self.hvac._prop_hvac

        self.typology = BuildingTypology(locator, building_names)
        prop_typology = self.typology._prop_typology

        self.comfort = BuildingComfort(locator, building_names)
        prop_comfort = self.comfort._prop_comfort

        self.internal_loads = BuildingInternalLoads(locator, building_names)
        prop_internal_loads = self.internal_loads._prop_internal_loads

        self.supply_systems = BuildingSupplySystems(locator, building_names)
        prop_supply_systems = self.supply_systems._prop_supply_systems

        self.rc_model = BuildingRCModel(locator, building_names, prop_typology, prop_envelope, prop_geometry, prop_hvac)
        prop_rc_model = self.rc_model._prop_rc_model

        self.solar = BuildingSolar(locator, building_names, prop_rc_model, prop_envelope, weather_data)
        prop_solar = self.solar._prop_solar

        # df_windows = geometry_reader.create_windows(surface_properties, prop_envelope)
        # TODO: to check if the Win_op and height of window is necessary.
        # TODO: maybe mergin branch i9 with CItyGML could help with this
        print("done")

        # save resulting data
        self._prop_supply_systems = prop_supply_systems
        self._prop_geometry = prop_geometry
        self._prop_envelope = prop_envelope
        self._prop_typology = prop_typology
        self._prop_HVAC_result = prop_hvac
        self._prop_comfort = prop_comfort
        self._prop_internal_loads = prop_internal_loads
        self._prop_age = prop_typology[['year']]
        self._solar = prop_solar
        self._prop_RC_model = prop_rc_model


    def __len__(self):
        """return length of list_building_names"""
        return len(self.building_names)

    def list_building_names(self):
        """get list of all building names"""
        return self.building_names

    def list_uses(self):
        """get list of all uses (typology types)"""
        return list(set(self._prop_typology['USE'].values))

    def get_prop_age(self, name_building):
        """get age properties of a building by name"""
        return self._prop_age.loc[name_building].to_dict()

    def get_solar(self, name_building):
        """get solar properties of a building by name"""
        return self._solar.loc[name_building]

    def __getitem__(self, building_name):
        """return a (read-only) BuildingPropertiesRow for the building"""
        return BuildingPropertiesRow.from_dataframes(name=building_name,
                                                     geometry=self.geometry[building_name],
                                                     envelope=self.envelope[building_name],
                                                     typology=self.typology[building_name],
                                                     hvac=self.hvac[building_name],
                                                     rc_model=self.rc_model[building_name],
                                                     comfort=self.comfort[building_name],
                                                     internal_loads=self.internal_loads[building_name],
                                                     age=self.get_prop_age(building_name),
                                                     solar=self.get_solar(building_name),
                                                     supply=self.supply_systems[building_name])
