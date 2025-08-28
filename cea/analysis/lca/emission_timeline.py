from __future__ import annotations
import os
import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator
    from cea.utilities.assemblies_db_reader import EnvelopeDBReader
    from cea.demand.building_properties import BuildingProperties


class BuildingEmissionTimeline:
    def __init__(
        self,
        building_properties: BuildingProperties,
        envelope_db: EnvelopeDBReader,
        building_name: str,
        locator: InputLocator,
    ):
        self.name = building_name
        self.locator = locator
        # self.building_properties = building_properties
        self.envelope_db = envelope_db
        self.geometry = building_properties.geometry[self.name]
        self.envelope = building_properties.envelope[self.name]
        self.get_component_quantity(building_properties)

    def generate_timeline(self, end_year: int) -> None:
        self.initialize_timeline(end_year)
        self.fill_embodied_emissions()
        self.fill_operational_emissions()

    def save_timeline(self):
        # first, check if timeline folder exist, if not create it
        if not os.path.exists(self.locator.get_lca_timeline_folder()):
            os.makedirs(self.locator.get_lca_timeline_folder())

        self.timeline.to_csv(self.locator.get_lca_timeline_building(self.name))

    def fill_embodied_emissions(self) -> None:
        mapping_dict = {
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
        for key, value in mapping_dict.items():
            type_str = f"type_{value}"
            lifetime: int = self.envelope_db.get_item_value(
                code=self.envelope[type_str], col="Service_Life"
            )
            ghg: float = self.envelope_db.get_item_value(
                code=self.envelope[type_str], col="GHG_kgCO2m2"
            )
            biogenic: float = self.envelope_db.get_item_value(
                code=self.envelope[type_str], col="GHG_biogenic_kgCO2m2"
            )
            area: float = self.surface_area[f"A{key}"]
            self.log_emission_with_lifetime(
                emission=ghg * area, lifetime=lifetime, col=f"embodied_{key}"
            )
            self.log_emission_with_lifetime(
                emission=-biogenic * area, lifetime=lifetime, col=f"biogenic_{key}"
            )

    def fill_operational_emissions(self) -> None:
        pass

    def initialize_timeline(self, end_year: int) -> pd.DataFrame:
        # Placeholder for the actual implementation
        # timeline should have the following columns:
        # year,
        # embodied_(
        #           wall_ag, wall_bg, wall_part, win_ag,
        #           roof, upperside, underside, floor, base,
        #           others,
        #           ),
        # operational

        # 0. read the year-of-built of building
        # 1. initialize the dataframe
        start_year = self.geometry["year"]
        if start_year >= end_year:
            raise ValueError("The starting year must be less than the ending year.")
        # initialize the dataframe with years
        self.timeline = pd.DataFrame(
            {
                "year": range(start_year, end_year + 1),
                "embodied_wall_ag": 0.0,
                "embodied_wall_bg": 0.0,
                "embodied_wall_part": 0.0,
                "embodied_win_ag": 0.0,
                "embodied_roof": 0.0,
                "embodied_upperside": 0.0,
                "embodied_underside": 0.0,
                "embodied_floor": 0.0,
                "embodied_base": 0.0,
                "embodied_deconstruction": 0.0,
                "embodied_others": 0.0,
                "biogenic_wall_ag": 0.0,
                "biogenic_wall_bg": 0.0,
                "biogenic_wall_part": 0.0,
                "biogenic_win_ag": 0.0,
                "biogenic_roof": 0.0,
                "biogenic_upperside": 0.0,
                "biogenic_underside": 0.0,
                "biogenic_floor": 0.0,
                "biogenic_base": 0.0,
                "biogenic_deconstruction": 0.0,
                "operational": 0.0,
            }
        )
        self.timeline.set_index("year", inplace=True)

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

    def get_component_quantity(self, building_properties: BuildingProperties) -> None:
        # fields = ['Atot', 'Awin_ag', 'Am', 'Aef', 'Af', 'Cm', 'Htr_is', 'Htr_em', 'Htr_ms', 'Htr_op', 'Hg', 'HD',
        #           'Aroof', 'Aunderside', 'U_wall', 'U_roof', 'U_win', 'U_base', 'Htr_w', 'GFA_m2', 'Aocc', 'Aop_bg',
        #           'Awall_ag', 'footprint', 'Hs_ag']
        # useful fields for LCA calculation:
        # GFA_m2:       total floor area of building
        # Awin_ag:      total area of windows
        # Aroof:        total area of roof
        # Aunderside:   total area of bottom surface, if the bottom surface is above ground level.
        #               In case where building touches the ground, this value is zero.
        # Awall_ag:     total area of walls
        # footprint:    the area of the building footprint
        rc_model_props = building_properties.rc_model[self.name]

        self.surface_area = {}
        self.surface_area["Awall_ag"] = rc_model_props["Awall_ag"]
        self.surface_area["Awall_bg"] = (
            self.geometry["perimeter"] * self.geometry["height_bg"]
        )
        self.surface_area["Awall_part"] = 0.0  # not implemented
        self.surface_area["Awin_ag"] = rc_model_props["Awin_ag"]

        # calculate the area of each component
        # horizontal: roof, floor, underside, upperside (not implemented), base
        # vertical: wall_ag, wall_bg, wall_part (not implemented), win_ag
        self.surface_area["Aroof"] = rc_model_props["Aroof"]
        self.surface_area["Aupperside"] = 0.0  # not implemented
        self.surface_area["Aunderside"] = rc_model_props["Aunderside"]
        # internal floors that are not base, not upperside and not underside
        self.surface_area["Afloor"] = (
            rc_model_props["GFA_m2"]  # GFA = footprint * (floor_ag + floor_bg - void_deck)
            - self.surface_area["Aunderside"]
            - self.surface_area["Aupperside"]
            - rc_model_props["footprint"]
        )
        self.surface_area["Abase"] = rc_model_props["footprint"]
