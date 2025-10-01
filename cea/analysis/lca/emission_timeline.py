from __future__ import annotations
import os
import pandas as pd
from cea.constants import (
    SERVICE_LIFE_OF_TECHNICAL_SYSTEMS,
    CONVERSION_AREA_TO_FLOOR_AREA_RATIO,
    EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS,
)
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
    - `production`: the emissions associated with the materials and
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
    - `technical_systems`: the technical systems of the building, including
        heating, cooling, ventilation, domestic hot water, electrical systems,

    Therefore, the column name is `{type}_{component}`, e.g., `production_wall_ag`,
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
        "technical_systems": "technical_systems", # not implemented in CEA, dummy value
    }
    _OPERATIONAL_COLS = [
        "operation_heating_kgCO2",
        "operation_cooling_kgCO2",
        "operation_hot_water_kgCO2",
        "operation_electricity_kgCO2",
    ]
    _EMISSION_TYPES = ["production", "biogenic", "demolition"]

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
        self.typology = building_properties.typology[self.name]
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

        self.timeline.to_csv(self.locator.get_lca_timeline_building(self.name), float_format='%.2f')

    def fill_embodied_emissions(self) -> None:
        """
        Log the embodied emissions for the building components for
        the beginning construction year into the timeline,
        and whenever any component needs to be renovated.
        """

        def log_emissions(area, ghg, biogenic, demolition, lifetime, key):
            self.log_emission_with_lifetime(
                emission=ghg * area, lifetime=lifetime, col=f"production_{key}_kgCO2"
            )
            self.log_emission_with_lifetime(
                emission=-biogenic * area,
                lifetime=lifetime,
                col=f"biogenic_{key}_kgCO2",
            )
            self.log_emission_with_lifetime(
                emission=demolition * area,
                lifetime=lifetime,
                col=f"demolition_{key}_kgCO2",
            )
            self.log_emission_in_timeline(
                emission=0.0,  # when building is first built, no demolition emission
                year=self.typology["year"],
                col=f"demolition_{key}_kgCO2",
                additive=False,
            )

        for key, value in self._MAPPING_DICT.items():
            area: float = self.surface_area[f"A{key}"]

            if key == "technical_systems":
                lifetime = SERVICE_LIFE_OF_TECHNICAL_SYSTEMS
                ghg = EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS
                biogenic = 0.0
                demolition = 0.0  # dummy value, not implemented yet
            else:
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
                demolition: float = 0.0  # dummy value, not implemented yet

            log_emissions(area, ghg, biogenic, demolition, lifetime, key)

    def fill_operational_emissions(self) -> None:
        operational_emissions = pd.read_csv(
            self.locator.get_lca_operational_hourly_building(self.name),
            index_col="hour",
        )
        if len(operational_emissions) != 8760:
            raise ValueError(
                f"Operational emission timeline expected 8760 rows, get {len(operational_emissions)} rows. Please check file integrity!"
            )

        # Rename columns to add operation_ prefix
        column_mapping = {
            "heating_kgCO2": "operation_heating_kgCO2",
            "cooling_kgCO2": "operation_cooling_kgCO2",
            "hot_water_kgCO2": "operation_hot_water_kgCO2",
            "electricity_kgCO2": "operation_electricity_kgCO2"
        }
        operational_emissions = operational_emissions.rename(columns=column_mapping)

        # self.timeline.loc[:, operational_emissions.columns] += operational_emissions.sum(axis=0)
        self.timeline.loc[:, self._OPERATIONAL_COLS] += operational_emissions[
            self._OPERATIONAL_COLS
        ].sum(axis=0)

    def demolish(self, demolition_year: int) -> None:
        """
        1. Erase all future emissions after demolition year, including operational emissions.
        2. Log demolition emissions in the demolition year.

        :param demolition_year: the year, after end of which the building does not exist anymore.
        :type demolition_year: int
        """
        # if demolition_year < self.geometry["year"], raise error
        if demolition_year < self.typology["year"]:
            raise ValueError(
                "Demolition year must be greater than or equal to the construction year."
            )

        # Convert demolition_year to string format for comparison with timeline index
        demolition_year_str = f"Y_{demolition_year}"
        self.timeline.loc[self.timeline.index >= demolition_year_str, :] = 0.0
        for key, value in self._MAPPING_DICT.items():
            demolition: float = 0.0  # dummy value, not implemented yet
            area: float = self.surface_area[f"A{key}"]
            # Convert max year to int for comparison
            max_year_str = self.timeline.index.max()
            max_year = int(max_year_str.replace("Y_", ""))
            # if demolition_year > max_year, do nothing
            if demolition_year <= max_year:
                self.log_emission_in_timeline(
                    emission=demolition * area,
                    year=demolition_year,
                    col=f"demolition_{key}_kgCO2",
                )

    def initialize_timeline(self, end_year: int) -> pd.DataFrame:
        """Initialize the timeline as a dataframe of `0.0`s,
        indexed by year, for the building emissions.

        :param end_year: The year to end the timeline.
        :type end_year: int
        :raises ValueError: If the start year is not less than the end year.
        :return: The initialized timeline DataFrame.
        :rtype: pd.DataFrame
        """
        start_year = self.typology["year"]
        if start_year >= end_year:
            raise ValueError("The starting year must be less than the ending year.")

        timeline = pd.DataFrame(
            {
                "year": [f"Y_{year}" for year in range(start_year, end_year + 1)],
                **{
                    f"{emission}_{component}_kgCO2": 0.0
                    for emission in self._EMISSION_TYPES
                    for component in list(self._MAPPING_DICT.keys())
                    + ["technical_systems"]
                },
                **{col: 0.0 for col in self._OPERATIONAL_COLS},
            }
        )
        timeline['name'] = self.name  # add building name column for easier identification
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

        # Extract numeric year from string format Y_XXXX
        start_year = self.typology["year"]
        max_year_str = self.timeline.index.max()
        max_year = int(max_year_str.replace("Y_", ""))

        numeric_years = list(range(start_year, max_year + 1, lifetime))
        # Convert back to string format
        years = [f"Y_{year}" for year in numeric_years]
        self.log_emission_in_timeline(emission, years, col)

    def log_emission_in_timeline(
        self, emission: float, year: int | list[int] | str | list[str], col: str, additive: bool = True
    ) -> None:
        # Convert single year to Y_ format if it's an integer
        if isinstance(year, int):
            year = f"Y_{year}"
        # Convert list of years to Y_ format if they're integers
        elif isinstance(year, list) and len(year) > 0 and isinstance(year[0], int):
            year = [f"Y_{y}" for y in year]

        if additive:
            self.timeline.loc[year, col] += emission
        else:
            self.timeline.loc[year, col] = emission

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
        - `Atechnical_systems`: total area of technical systems. Same as GFA.

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
        envelope_props = building_properties.envelope[self.name]

        surface_area = {}
        surface_area["Awall_ag"] = envelope_props["Awall_ag"]
        surface_area["Awall_bg"] = (
            self.geometry["perimeter"] * self.geometry["height_bg"]
        )
        surface_area["Awall_part"] = rc_model_props["GFA_m2"] * CONVERSION_AREA_TO_FLOOR_AREA_RATIO
        surface_area["Awin_ag"] = envelope_props["Awin_ag"]

        # calculate the area of each component
        # horizontal: roof, floor, underside, upperside (not implemented), base
        # vertical: wall_ag, wall_bg, wall_part (not implemented), win_ag
        surface_area["Aroof"] = envelope_props["Aroof"]
        surface_area["Aupperside"] = 0.0  # not implemented
        surface_area["Aunderside"] = envelope_props["Aunderside"]
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
        surface_area["Atechnical_systems"] = rc_model_props["GFA_m2"]
        return surface_area
