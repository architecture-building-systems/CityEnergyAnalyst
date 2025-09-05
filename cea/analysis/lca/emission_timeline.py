from __future__ import annotations
import os
import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator
    from cea.datamanagement.database.envelope_lookup import EnvelopeLookup
    from cea.demand.building_properties import BuildingProperties


class BuildingEmissionTimeline:
    """
    A class to manage the emission timeline for a building.
    The core attribute of this class is the timeline DataFrame indexed by year,
    which stores the emissions data over years.
    It logs emission for building components separately, so that the impact
    of each component can be tracked over time.

    Each building component has two main types of emissions associated with it:
    - `embodied`: the emissions associated with the materials and
    construction processes used to create the building component.
    - `biogenic`: the emissions that are stored within the material that
    would have otherwise been released during other processes or
    because of decay or wasting. In some results it's also called `uptake`.
    - `demolition`: the emissions associated with the deconstruction and 
    disposal of building materials at the end of their service life.

    The components include:
    - vertical surfaces (excluding windows)
        - `wall_ag`: external wall that is above ground level and insulates
        the building from outside air.
        - `wall_bg`: external wall that is below ground level and typically
        insulates the building from ground temperature.
        - `wall_part`: partitional wall within the footprint of the building,
        typically not insulated.
    - windows on external vertical walls
        - `win_ag`: external window that is above ground level and typically
        has a lower U-value than the walls.
    - horizontal surfaces
        - `roof`: the top covering of the building, typically insulated.
        - `upperside`: the horizontal surface between interior space (below)
        and void deck (above), typically insulated, currently not implemented.
        - `underside`: the horizontal surface between the void deck (below)
        and the interior space (above), typically insulated.
        - `floor`: the interior horizontal surface of the building
        between two floors, typically uninsulated.
        - `base`: the part of the building that is in contact with the ground,
            typically insulated.
    - `others`: other components that are not part of the building envelope,
        such as HVAC systems, elevators, etc. Currently not implemented.
    - `deconstruction`: the emissions associated with the deconstruction
        and disposal of building materials at the end of their service life.

    Therefore, the column name is `{type}_{component}`, e.g., `embodied_wall_ag`,
    `biogenic_roof`.

    Finally, the yearly operational emission `operational` is also tracked
    in the timeline.
    """

    _MAPPING_DICT = {
        "wall_ag": "wall",
        "wall_bg": "base",
        "wall_part": "part",
        "win_ag": "win",
        "roof": "roof",
        "upperside": "roof",
        "underside": "base",
        "floor": "floor",
        "base": "base",
    }
    _OPERATIONAL_COLS = [
        "heating_kgCO2",
        "cooling_kgCO2",
        "hot_water_kgCO2",
        "electricity_kgCO2",
    ]

    def __init__(
        self,
        building_properties: BuildingProperties,
        envelope_lookup: EnvelopeLookup,
        building_name: str,
        locator: InputLocator,
        end_year: int,
    ):
        """Initialize the BuildingEmissionTimeline object.

        :param building_properties: the BuildingProperties object containing the geometric,
            envelope and database data for all buildings in the district.
        :type building_properties: BuildingProperties
        :param envelope_lookup: the EnvelopeLookup object to access the envelope database.
        :type envelope_lookup: EnvelopeLookup
        :param building_name: the name of the building.
        :type building_name: str
        :param locator: the InputLocator object to locate input files.
        :type locator: InputLocator
        :param end_year: The last year that should exist in the building timeline.
        :type end_year: int
        """
        self.name = building_name
        self.locator = locator
        # self.building_properties = building_properties
        self.envelope_lookup = envelope_lookup
        self.geometry = building_properties.geometry[self.name]
        self.envelope = building_properties.envelope[self.name]
        self.surface_area = self.get_component_quantity(building_properties)
        self.timeline = self.initialize_timeline(end_year)

    def fill_timeline(self) -> None:
        """Fills up the timeline with emissions data, both embodied and operational.
        """
        self.fill_embodied_emissions()
        self.fill_operational_emissions()

    def save_timeline(self):
        """Save the timeline DataFrame to a CSV file.
        If the folder does not exist, it will be created.
        """
        # first, check if timeline folder exist, if not create it
        if not os.path.exists(self.locator.get_lca_timeline_folder()):
            os.makedirs(self.locator.get_lca_timeline_folder())

        self.timeline.to_csv(self.locator.get_lca_timeline_building(self.name))

    def fill_embodied_emissions(self) -> None:
        """
        Log the embodied emissions for the building components for
        the beginning construction year into the timeline,
        and whenever any component needs to be renovated.
        """
        for key, value in self._MAPPING_DICT.items():
            type_str = f"type_{value}"
            lifetime: int = self.envelope_lookup.get_item_value(
                code=self.envelope[type_str], field="Service_Life"
            )
            ghg: float = self.envelope_lookup.get_item_value(
                code=self.envelope[type_str], field="GHG_kgCO2m2"
            )
            biogenic: float = self.envelope_lookup.get_item_value(
                code=self.envelope[type_str], field="GHG_biogenic_kgCO2m2"
            )
            area: float = self.surface_area[f"A{key}"]
            self.log_emission_with_lifetime(
                emission=ghg * area, lifetime=lifetime, col=f"production_{key}_kgCO2"
            )
            self.log_emission_with_lifetime(
                emission=-biogenic * area, lifetime=lifetime, col=f"biogenic_{key}_kgCO2"
            )

    def fill_operational_emissions(self) -> None:
        operational_emissions = pd.read_csv(self.locator.get_lca_operational_hourly_building(self.name), index_col="hour")
        if len(operational_emissions) != 8760:
            raise ValueError(f"Operational emission timeline expected 8760 rows, get {len(operational_emissions)} rows. Please check file integrity!")
        # self.timeline.loc[:, operational_emissions.columns] += operational_emissions.sum(axis=0)
        self.timeline.loc[:, self._OPERATIONAL_COLS] += operational_emissions[self._OPERATIONAL_COLS].sum(axis=0)

    def initialize_timeline(self, end_year: int) -> pd.DataFrame:
        """Initialize the timeline as a dataframe of `0.0`s, 
        indexed by year, for the building emissions.

        :param end_year: The year to end the timeline.
        :type end_year: int
        :raises ValueError: If the start year is not less than the end year.
        :return: The initialized timeline DataFrame.
        :rtype: pd.DataFrame
        """
        start_year = self.geometry["year"]
        if start_year >= end_year:
            raise ValueError("The starting year must be less than the ending year.")
        component_types = self._MAPPING_DICT.keys()
        emission_types = ["production", "biogenic", "demolition"]

        timeline = pd.DataFrame(
            {
                "year": range(start_year, end_year + 1),
                **{
                    f"{emission}_{component}_kgCO2": 0.0
                    for emission in emission_types
                    for component in component_types
                },
                # "heating_kgCO2": 0.0,
                # "cooling_kgCO2": 0.0,
                # "hot_water_kgCO2": 0.0,
                # "electricity_kgCO2": 0.0,
                **{col: 0.0 for col in self._OPERATIONAL_COLS},
            }
        )
        timeline.set_index("year", inplace=True)
        return timeline

    def log_emission_with_lifetime(
        self, emission: float, lifetime: int, col: str
    ) -> None:
        """The function logs emission once every "lifetime" years in the desired column.

        :param emission: The amount of emission to log.
        :type emission: float
        :param lifetime: The lifetime of the component in years. Minimum 1.
        :type lifetime: int
        :param col: The column to log the emission in.
        :type col: str
        """
        if lifetime < 1:
            raise ValueError("Lifetime must be at least 1 year.")

        years = list(
            range(self.geometry["year"], self.timeline.index.max() + 1, lifetime)
        )
        self.log_emission_in_timeline(emission, years, col)

    def log_emission_in_timeline(
        self, emission: float, year: int | list[int], col: str
    ) -> None:
        self.timeline.loc[year, col] += emission

    def get_component_quantity(self, building_properties: BuildingProperties) -> dict[str, float]:
        """
        Get the area for each building component.
        During Daysim simulation, the types of surfaces are categorized in detail,
        so we need the radiation results
        to extract surface area information, as done in demand calculation as well.
        The radiation results are stored in `building_properties.rc_model._rc_model_props`.
        A lot of fields exist, but the useful ones are:
        - `GFA_m2`: total floor area of building
        - `Awall_ag`: total area of external walls above ground
        - `Awin_ag`: total area of windows
        - `Aroof`: total area of roof
        - `Aunderside`: total area of bottom surface, if the bottom surface is above ground level.
            In case where building touches the ground, this value is zero.
        - `footprint`: the area of the building footprint, equivalent to `Abase`.

        Calculated area:
        - `Awall_bg`: total area of below-ground walls
        - `Awall_part`: total area of partition walls. Currently dummy value 0.0
        - `Aupperside`: total area of upper side. Currently not available in Daysim
            radiation results, so this value is set to `0.0`.
        - `Afloor`: total area of internal floors.
            If the floor area is neither touching the ground nor the outside air,
            it should be internal. Therefore, the calculation formula thus is:
            `Afloor = GFA_m2 - Aunderside - footprint`

        :param building_properties: The building properties object containing results
            for all buildings in the district. Two attributes are relevant
            for the surface area calculation: the `rc_model` and `geometry` attributes.

            The `geometry` attribute simply returns what's inside the `zone.shp` file,
            along with the footprint and perimeter;
            The `rc_model` attribute contains the areas along with other parameters.
            Whole list of parameters (details see `BuildingRCModel.calc_prop_rc_model`)
        :type building_properties: BuildingProperties

        :return: A dictionary with the area of each building component.
        :rtype: dict[str, float]
        """
        rc_model_props = building_properties.rc_model[self.name]

        surface_area = {}
        surface_area["Awall_ag"] = rc_model_props["Awall_ag"]
        surface_area["Awall_bg"] = (
            self.geometry["perimeter"] * self.geometry["height_bg"]
        )
        surface_area["Awall_part"] = 0.0  # not implemented
        surface_area["Awin_ag"] = rc_model_props["Awin_ag"]

        # calculate the area of each component
        # horizontal: roof, floor, underside, upperside (not implemented), base
        # vertical: wall_ag, wall_bg, wall_part (not implemented), win_ag
        surface_area["Aroof"] = rc_model_props["Aroof"]
        surface_area["Aupperside"] = 0.0  # not implemented
        surface_area["Aunderside"] = rc_model_props["Aunderside"]
        # internal floors that are not base, not upperside and not underside

        # check if building ever have base
        if self.geometry["floors_bg"] == 0 and self.geometry["void_deck"] > 0:
            # building is completely floating and does not have a base
            area_base = 0.0
        else:
            area_base = float(rc_model_props["footprint"])
        surface_area["Afloor"] = max(
            0.0,
            rc_model_props[
                "GFA_m2"
            ]  # GFA = footprint * (floor_ag + floor_bg - void_deck)
            - surface_area["Aunderside"]
            - area_base,
        )
        surface_area["Abase"] = area_base
        return surface_area
