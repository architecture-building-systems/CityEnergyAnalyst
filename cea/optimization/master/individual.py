"""
Contains information about individuals (in list and dict form)
"""
__author__ = "Daren Thomas"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

from typing import NewType, List, Union, NamedTuple, Dict

# Type used to represent an individual in the deap toolbox
from cea.optimization.constants import DC_CONVERSION_TECHNOLOGIES_SHARE, DC_ACRONYM, \
    DC_CONVERSION_TECHNOLOGIES_WITH_SPACE_RESTRICTIONS, DH_CONVERSION_TECHNOLOGIES_SHARE, DH_ACRONYM, \
    DH_CONVERSION_TECHNOLOGIES_WITH_SPACE_RESTRICTIONS

IndividualList = NewType("IndividualList", List[Union[float, int]])


class IndividualBlueprint(NamedTuple):
    """Describes the blueprint of an individual"""
    column_names: List[str]
    tech_names_share: List[str]
    building_columns: List[str]  # the columns names
    building_names: List[str]  # the names as they appear in zone.shp
    conversion_technologies: Dict[str, Dict[str, float]]
    conversion_technologies_with_space_restrictions: List[str]
    district_heating_network: bool  # district_cooling_network == not district_heating_network


class IndividualDict(Dict[str, Union[float, int]]):
    """
    Type name for the structure we use to represent an individual in dictionary form
    """

    @classmethod
    def from_individual_list(cls, individual: IndividualList,
                             blueprint: IndividualBlueprint) -> "IndividualDict":
        return IndividualDict(zip(blueprint.column_names, individual))

    def to_individual_list(self, blueprint: IndividualBlueprint, individual: List) -> IndividualList:
        """
        Implementation Note: individual is sometimes not just an IndividualList - it can also be a deap
        object - so we don't return a _new_ list, instead, we replace the _contents_ of the individual
        parameter. If you don't have such an individual, just pass in an empty list (e.g. when generating the first
        individuals).
        """
        individual[:] = [self[gene] for gene in blueprint.column_names]
        return IndividualList(individual)


def create_empty_individual(blueprint: IndividualBlueprint,
                            district_heating_network: bool,
                            district_cooling_network: bool) -> IndividualDict:
    assert_district_heating_xor_cooling_network(district_cooling_network, district_heating_network)

    individual: IndividualList = [0.0] * len(blueprint.tech_names_share) + [0] * len(blueprint.building_columns)
    return IndividualDict.from_individual_list(individual, blueprint)


def create_individual_blueprint(district_heating_network: bool,
                                district_cooling_network: bool,
                                building_names_heating: List[str],
                                building_names_cooling: List[str],
                                technologies_heating_allowed: List[str],
                                technologies_cooling_allowed: List[str]) -> IndividualBlueprint:
    assert_district_heating_xor_cooling_network(district_cooling_network, district_heating_network)

    if district_heating_network:
        return create_heating_blueprint(building_names_heating, technologies_heating_allowed)
    else:
        # local variables
        return create_cooling_blueprint(building_names_cooling, technologies_cooling_allowed)


def assert_district_heating_xor_cooling_network(district_cooling_network:bool, district_heating_network:bool) -> None:
    """
    Ensure that district_cooling_network (exclusive or) district_heating_network is True.

    :param district_cooling_network: True, if we're simulating a district cooling network
    :param district_heating_network: True, if we're simulationg a district heating network
    """
    assert district_heating_network != district_cooling_network, "Only one network type possible"
    assert district_heating_network or district_cooling_network, "No network type selected"


def create_cooling_blueprint(building_names_cooling: List[str],
                             technologies_cooling_allowed: List[str]) -> IndividualBlueprint:
    cooling_unit_names_share = [tech for tech in DC_CONVERSION_TECHNOLOGIES_SHARE.keys() if
                                tech in technologies_cooling_allowed]
    column_names_buildings_cooling = ["{building}_{DC}".format(building=building, DC=DC_ACRONYM)
                                      for building in building_names_cooling]
    column_names = cooling_unit_names_share + column_names_buildings_cooling
    return IndividualBlueprint(
        column_names=column_names,
        tech_names_share=cooling_unit_names_share,
        buildings=column_names_buildings_cooling,
        building_names=building_names_cooling,
        conversion_technologies=DC_CONVERSION_TECHNOLOGIES_SHARE,
        conversion_technologies_with_space_restrictions=DC_CONVERSION_TECHNOLOGIES_WITH_SPACE_RESTRICTIONS,
        district_heating_network=False)


def create_heating_blueprint(building_names_heating: List[str],
                             technologies_heating_allowed: List[str]) -> IndividualBlueprint:
    heating_unit_names_share = [tech for tech in DH_CONVERSION_TECHNOLOGIES_SHARE.keys() if
                                tech in technologies_heating_allowed]
    column_names_buildings_heating = ["{building}_{DH}".format(building=building, DH=DH_ACRONYM)
                                      for building in building_names_heating]
    column_names = heating_unit_names_share + column_names_buildings_heating
    return IndividualBlueprint(
        column_names=column_names,
        tech_names_share=heating_unit_names_share,
        buildings=column_names_buildings_heating,
        building_names=building_names_heating,
        conversion_technologies=DH_CONVERSION_TECHNOLOGIES_SHARE,
        conversion_technologies_with_space_restrictions=DH_CONVERSION_TECHNOLOGIES_WITH_SPACE_RESTRICTIONS,
        district_heating_network=True)