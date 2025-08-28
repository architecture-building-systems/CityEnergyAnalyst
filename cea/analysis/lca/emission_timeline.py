from __future__ import annotations
import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cea.inputlocator import InputLocator
    from cea.demand.building_properties import BuildingProperties


class BuildingEmissionTimeline:
    def __init__(
        self,
        building_properties: BuildingProperties,
        building_name: str,
        locator: InputLocator,
    ):
        self.name = building_name
        self.locator = locator
        self.building_properties = building_properties
        self.geometry = self.building_properties.geometry[self.name]
        self.envelope = self.building_properties.envelope[self.name]
        self.generate_timeline()

    def generate_timeline(self, end_year: int) -> None:
        self.initialize_timeline(end_year)
        self.get_component_db()
        self.get_component_quantity()
        self.fill_embodied_emissions()
        self.fill_operational_emissions()

    def initialize_timeline(self, end_year: int) -> pd.DataFrame:
        # Placeholder for the actual implementation
        # timeline should have the following columns:
        # year,
        # embodied_(
        #           wall_ag, wall_bg, wall_int, win_ag,
        #           roof, upperside, underside, ceiling, base,
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
                "embodied_wall_int": 0.0,
                "embodied_win_ag": 0.0,
                "embodied_roof": 0.0,
                "embodied_upperside": 0.0,
                "embodied_underside": 0.0,
                "embodied_ceiling": 0.0,
                "embodied_base": 0.0,
                "embodied_others": 0.0,
                "operational": 0.0,
            }
        )
        self.timeline.set_index("year", inplace=True)

    def log_emission_in_timeline(
        self, emission: float, year: int | list[int], col: str
    ) -> None:
        self.timeline.loc[year, col] += emission

    def get_component_db(self) -> None:
        self.wall_db = pd.read_csv(self.locator.get_database_assemblies_envelope_wall())
        self.roof_db = pd.read_csv(self.locator.get_database_assemblies_envelope_roof())
        self.floor_db = pd.read_csv(
            self.locator.get_database_assemblies_envelope_floor()
        )
        self.window_db = pd.read_csv(
            self.locator.get_database_assemblies_envelope_window()
        )

    def get_component_quantity(self) -> None:
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
        self.rc_model_props = self.building_properties.rc_model[self.name]

        # select only useful fields
        useful_fields = [
            "GFA_m2",
            "Awin_ag",
            "Aroof",
            "Aunderside",
            "Awall_ag",
            "footprint",
        ]
        self.rc_model_props = self.rc_model_props[useful_fields]

        # also add floor_ag, floor_bg and void_deck to the dict from geometry
        self.rc_model_props["floor_ag"] = self.geometry.loc[self.name, "floors_ag"]
        self.rc_model_props["floor_bg"] = self.geometry.loc[self.name, "floors_bg"]
        self.rc_model_props["void_deck"] = self.geometry.loc[self.name, "void_deck"]

        # calculate the area of each component
        # horizontal: roof, ceiling, underside, upperside (not implemented), base
        # vertical: wall_ag, wall_bg, wall_int (not implemented), win_ag
        self.rc_model_props["Aupperside"] = 0.0  # not implemented
        self.rc_model_props["Abase"] = self.rc_model_props["footprint"]
        # internal floors that are not base, not upperside and not underside
        self.rc_model_props["Aceiling"] = (
            self.rc_model_props[
                "GFA_m2"
            ]  # GFA = footprint * (floor_ag + floor_bg - void_deck)
            - self.rc_model_props["Aunderside"]
            - self.rc_model_props["Aupperside"]
            - self.rc_model_props["Abase"]
        )
        self.rc_model_props["Awall_bg"] = (
            self.geometry["perimeter"] * self.geometry["height_bg"]
        )
