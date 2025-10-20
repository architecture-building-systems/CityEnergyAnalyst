"""
Classes of building properties
"""
from __future__ import annotations

from cea.demand.building_properties.building_comfort import BuildingComfort
from cea.demand.building_properties.building_envelope import BuildingEnvelope
from cea.demand.building_properties.building_geometry import BuildingGeometry
from cea.demand.building_properties.building_hvac import BuildingHVAC
from cea.demand.building_properties.building_internal_loads import BuildingInternalLoads
from cea.demand.building_properties.building_properties_row import BuildingPropertiesRow
from cea.demand.building_properties.building_rc_model import BuildingRCModel
from cea.demand.building_properties.building_solar import BuildingSolar
from cea.demand.building_properties.building_supply_systems import BuildingSupplySystems
from cea.demand.building_properties.building_typology import BuildingTypology

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
        self.typology = BuildingTypology(locator, building_names)

        # Building properties mapped from CEA Archetypes
        self.comfort = BuildingComfort(locator, building_names)
        self.internal_loads = BuildingInternalLoads(locator, building_names)

        # Building properties mapped from CEA databases
        self.envelope = BuildingEnvelope(locator, building_names)
        self.hvac = BuildingHVAC(locator, building_names)
        self.supply_systems = BuildingSupplySystems(locator, building_names)

        self.rc_model = BuildingRCModel(locator, building_names,
                                        self.typology._prop_typology,
                                        self.envelope._prop_envelope,
                                        self.geometry._prop_geometry,
                                        self.hvac._prop_hvac)

        self.solar = BuildingSolar(locator, building_names,
                                   self.rc_model._prop_rc_model,
                                   self.envelope._prop_envelope,
                                   weather_data)

        # df_windows = geometry_reader.create_windows(surface_properties, prop_envelope)
        # TODO: to check if the Win_op and height of window is necessary.
        # TODO: maybe mergin branch i9 with CItyGML could help with this
        print("done")

    def __len__(self):
        """return length of list_building_names"""
        return len(self.building_names)

    def list_building_names(self):
        """get list of all building names"""
        return self.building_names

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
                                                     solar=self.solar[building_name],
                                                     supply=self.supply_systems[building_name])

    def check_buildings(self, min_gfa: float = 100):
        """
        Check the buildings for potential issues that might cause problems in the demand calculations.

        This includes checking for buildings with less than 100 m2 of gross floor area.
        """

        # FIXME: This is not a very good indicator of potential issue which causes overheating problems in some cases.
        GFA_m2 = self.rc_model._prop_rc_model['GFA_m2']
        small_buildings = GFA_m2[GFA_m2 < min_gfa]

        if len(small_buildings) > 0:
            print(f'Warning! The following list of buildings have less than 100 m2 of gross floor area, '
                  f'this might cause potential issues with demand calculation: {small_buildings.index.tolist()}')
