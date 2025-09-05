from __future__ import annotations
import os
import numpy as np
import pandas as pd
from cea.constants import HOURS_IN_YEAR

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from cea.inputlocator import InputLocator
    from cea.datamanagement.database.components import Feedstocks
    from cea.demand.building_properties.building_properties_row import (
        BuildingPropertiesRow,
    )


class OperationalHourlyTimeline:

    _tech_name_mapping = {
        # tech_name: (<demand_col_name>, <supply_type_name>)
        "heating": ("Qhs_sys", "hs"),
        "hot_water": ("Qww_sys", "dhw"),
        "cooling": ("Qcs_sys", "cs"),
        "electricity": ("E_sys", "el"),
    }

    def __init__(
        self,
        locator: InputLocator,
        bpr: BuildingPropertiesRow,
        feedstock_db: Feedstocks,
    ):
        self.locator = locator
        self.bpr = bpr
        self.feedstock_db = feedstock_db
        self.emission_intensity_timeline = self.expand_feedstock_emissions()
        self.demand_timeseries = pd.read_csv(locator.get_demand_results_file(self.bpr.name))
        self.operational_emission_timeline = self.create_operational_timeline()

    def create_operational_timeline(self) -> pd.DataFrame:
        """
        Create an operational timeline DataFrame with four columns:
        - `heating_kgCO2`: emission for heating supply
        - `cooling_kgCO2`: emission for cooling supply
        - `hot_water_kgCO2`: emission for hot water supply
        - `electricity_kgCO2`: emission for electricity supply
        The dataframe should have 8760 rows, one for each hour of the year, indexed by hour.

        :return: A DataFrame with 8760 rows and 4 columns indexed by hours of the year,
            representing the operational emission timeline.
        :rtype: pd.DataFrame
        """
        timeline = pd.DataFrame(
            index=range(HOURS_IN_YEAR),
            columns=[
                f"{key}_kgCO2"
                for key in OperationalHourlyTimeline._tech_name_mapping.keys()
            ],
        )
        timeline.loc[:, :] = 0.0  # Initialize all values to zero
        timeline.index.name = "hour"

        return timeline

    def expand_feedstock_emissions(self) -> pd.DataFrame:
        """
        generate a hourly timeline of feedstock emission intensity
        by repeating the hourly values in the feedstock database.

        For example, the original feedstock database might have 24 rows,
        one for each hour of the day; or it could have 168 rows,
        one for each hour of the week. The values in the database represents a repetitive
        pattern of emissions throughout the `nrows` hours of a year, starting from hour 0.

        :param feedstock_db: The feedstock database containing hourly emission values.
            It has a `_library` attribute which is a dictionary of DataFrames,
            each representing the emissions for a specific feedstock type.
        :type feedstock_db: Feedstocks
        :return: A DataFrame with 8760 rows and columns of feedstocks indexed by hours of the year,
            representing the expanded feedstock emissions timeline, each value in unit of kgCO2/MJ.
        :rtype: pd.DataFrame
        """
        # The emission in feedstock databases are recorded for example in hours of a day.
        # To match the yearly operational timeline, expanded emission intensity timeline
        expanded_timeline = pd.DataFrame(
            index=range(HOURS_IN_YEAR), columns=self.feedstock_db._library.keys()
        )
        for feedstock, df in self.feedstock_db._library.items():
            # if original timeline is not n * 24 hours, throw warning that definition might be problematic
            if len(df) % 24 != 0:
                print(f"Warning: {feedstock} timeline is not n * 24 hours. The definition will not repeat in a daily basis.")
            expanded_timeline[feedstock] = np.resize(
                df["GHG_kgCO2MJ"].to_numpy(), len(expanded_timeline)
            )
            expanded_timeline[feedstock] = expanded_timeline[feedstock].astype(float)
            expanded_timeline[feedstock] *= 3.6  # convert from kgCO2/MJ to kgCO2/kWh

        expanded_timeline["NONE"] = 0.0

        return expanded_timeline

    def calculate_operational_emission(self) -> None:
        """
        This function calculates the emission timeline for heating,
        domestic hot water, cooling and electrical supply.
        """
        for demand_type, tech_tuple in self._tech_name_mapping.items():
            eff: float = self.bpr.supply[f"eff_{tech_tuple[1]}"]
            feedstock: str = self.bpr.supply[f"source_{tech_tuple[1]}"]

            self.operational_emission_timeline[f"{demand_type}_kgCO2"] = (
                self.demand_timeseries[f"{tech_tuple[0]}_kWh"]  # kWh
                / eff
                * self.emission_intensity_timeline[feedstock]  # kgCO2/kWh
            )

    def save_results(self) -> None:
        """
        Save the operational emission results to a CSV file.
        """
        if not os.path.exists(self.locator.get_lca_timeline_folder()):
            os.makedirs(self.locator.get_lca_timeline_folder())

        self.operational_emission_timeline.to_csv(
            self.locator.get_lca_operational_hourly_building(self.bpr.name)
        )


if __name__ == "__main__":
    from cea.config import Configuration
    from cea.inputlocator import InputLocator
    from cea.demand.building_properties import BuildingProperties
    from cea.datamanagement.database.components import Feedstocks
    from cea.utilities import epwreader

    config = Configuration()
    locator = InputLocator(config.scenario)
    weather_path = locator.get_weather_file()
    weather_data = epwreader.epw_reader(weather_path)[
        ["year", "drybulb_C", "wetbulb_C", "relhum_percent", "windspd_ms", "skytemp_C"]
    ]
    building_properties = BuildingProperties(
        locator, weather_data, config.demand.buildings
    )
    bpr = building_properties[config.demand.buildings[0]]
    feedstock_db = Feedstocks.init_database(locator)
    test_timeline = OperationalHourlyTimeline(locator, bpr, feedstock_db)
    test_timeline.calculate_operational_emission()
    test_timeline.save_results()
