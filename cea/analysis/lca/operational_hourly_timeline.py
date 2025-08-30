import numpy as np
import pandas as pd
from cea.datamanagement.database.assemblies import Supply
from cea.datamanagement.database.components import Feedstocks
from cea.inputlocator import InputLocator


class OperationalHourlyTimeline:
    def __init__(
        self,
        locator: InputLocator,
        building: str,
        supply_db: Supply,
        feedstock_db: Feedstocks,
    ):
        self.locator = locator
        self.name = building
        self.supply_db = supply_db  # contains COP data in `efficiency` column and fuel in `feedstock` column
        self.emission_intensity_timeline = self._expand_feedstock_emissions(
            feedstock_db
        )

        self.supply_system = pd.read_csv(locator.get_building_supply())
        self.demand_timeseries = pd.read_csv(locator.get_demand_results_file(self.name))

        self.operational_emission_timeline = self._create_operational_timeline()

    @staticmethod
    def _create_operational_timeline() -> pd.DataFrame:
        """
        Create an operational timeline DataFrame with four columns:
        - `hs_kgCO2`: emission for heating supply
        - `cs_kgCO2`: emission for cooling supply
        - `ww_kgCO2`: emission for hot water supply
        - `ee_kgCO2`: emission for electricity supply
        The dataframe should have 8760 rows, one for each hour of the year, indexed by hour.

        :return: A DataFrame with 8760 rows and 4 columns indexed by hours of the year,
            representing the operational emission timeline.
        :rtype: pd.DataFrame
        """
        timeline = pd.DataFrame(
            index=range(8760), columns=["hs_kgCO2", "cs_kgCO2", "ww_kgCO2", "ee_kgCO2"]
        )
        timeline.loc[:, :] = 0.0  # Initialize all values to zero

        return timeline

    @staticmethod
    def _expand_feedstock_emissions(feedstock_db: Feedstocks) -> pd.DataFrame:
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
            index=range(8760), columns=feedstock_db._library.keys()
        )
        for feedstock, df in feedstock_db._library.items():
            expanded_timeline[feedstock] = np.resize(
                df["GHG_kgCO2MJ"].to_numpy(), len(expanded_timeline)
            )
            expanded_timeline[feedstock] = expanded_timeline[feedstock].astype(float)

        return expanded_timeline

    def calculate_operational_emission(self) -> None:
        pass
