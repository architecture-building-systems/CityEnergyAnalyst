import os
import pandas as pd

from cea.config import Configuration
from cea.inputlocator import InputLocator

from cea.analysis.lca.emission_timeline import BuildingEmissionTimeline
from cea.analysis.lca.hourly_operational_emission import OperationalHourlyTimeline
from cea.demand.building_properties import BuildingProperties
from cea.datamanagement.database.envelope_lookup import EnvelopeLookup
from cea.datamanagement.database.components import Feedstocks
from cea.utilities import epwreader


def operational(config: Configuration) -> None:
    locator = InputLocator(config.scenario)
    buildings = config.emission_time_dependent.buildings
    weather_path = locator.get_weather_file()
    weather_data = epwreader.epw_reader(weather_path)[
        ["year", "drybulb_C", "wetbulb_C", "relhum_percent", "windspd_ms", "skytemp_C"]
    ]
    building_properties = BuildingProperties(locator, weather_data, buildings)
    feedstock_db = Feedstocks.from_locator(locator)
    results: list[tuple[str, pd.DataFrame]] = []

    for building in buildings:
        bpr = building_properties[building]
        timeline = OperationalHourlyTimeline(locator, bpr, feedstock_db)
        timeline.calculate_operational_emission()
        timeline.save_results()
        print(
            f"Hourly operational emissions for {building} calculated and saved in: {locator.get_lca_operational_hourly_building(building)}."
        )
        results.append([building, timeline.operational_emission_timeline])

    df_by_building = sum_by_building(results)
    df_by_hour = sum_by_index([df for _, df in results])
    df_by_building.to_csv(
        os.path.join(
            locator.get_lca_timeline_folder(),
            "Total_yearly_operational_per_building.csv",
        )
    )
    df_by_hour.to_csv(
        os.path.join(
            locator.get_lca_timeline_folder(), "Total_yearly_operational_per_hour.csv"
        )
    )
    print(
        f"District-level operational emissions saved in: {locator.get_lca_timeline_folder()}"
    )


def embodied(config: Configuration) -> None:
    locator = InputLocator(scenario=config.scenario)
    buildings: list[str] = config.emission_time_dependent.buildings
    end_year: int = config.emission_time_dependent.end_year

    envelope_lookup = EnvelopeLookup.from_locator(locator)
    weather_path = locator.get_weather_file()
    weather_data = epwreader.epw_reader(weather_path)[
        ["year", "drybulb_C", "wetbulb_C", "relhum_percent", "windspd_ms", "skytemp_C"]
    ]
    building_properties = BuildingProperties(locator, weather_data, buildings)
    results: list[tuple[str, pd.DataFrame]] = []
    for building in buildings:
        timeline = BuildingEmissionTimeline(
            building_properties=building_properties,
            envelope_lookup=envelope_lookup,
            building_name=building,
            locator=locator,
        )
        timeline.generate_timeline(end_year)
        timeline.save_timeline()
        print(
            f"Embodied and operational emissions timeline for {building} calculated and saved in: {locator.get_lca_timeline_building(building)}."
        )
        results.append((building, timeline.timeline))

    df_by_building = sum_by_building(results)
    df_by_year = sum_by_index([df for _, df in results])
    df_by_building.to_csv(
        os.path.join(
            locator.get_lca_timeline_folder(), "Total_embodied_per_building.csv"
        )
    )
    df_by_year.to_csv(
        os.path.join(locator.get_lca_timeline_folder(), "Total_embodied_per_year.csv")
    )
    print(
        f"District-level embodied emissions saved in: {locator.get_lca_timeline_folder()}"
    )


def sum_by_building(result_list: list[tuple[str, pd.DataFrame]]) -> pd.DataFrame:
    """Sum the dataframes in the result list by building. Result in a new dataframe
    with buildings as index and summed values as data.

    For example:
    ```
    building_1:             col1    col2
                idx
                0           1       2
                1           3
    building_2:             col1    col2
                idx
                0           5       6
                1           7       8
    ```
    The result would be:
    ```
    output:                 col1    col2
                name
                building_1  4       6
                building_2  12      14
    ```

    :param result_list: a list of tuple, contains building name and its corresponding dataframe.
    :type result_list: list[tuple[str, pd.DataFrame]]
    :return: a dataframe with buildings as index and summed values as data.
        It has the same columns as the input dataframes.
    :rtype: pd.DataFrame
    """
    # create a new df, each row is the summed value for a building across all its df's indices
    summed_df = pd.DataFrame(
        data=0.0,
        index=[building for building, _ in result_list],
        columns=result_list[0][1].columns,
    )
    summed_df.index.rename("name", inplace=True)
    for building, df in result_list:
        summed_df.loc[building] += df.sum(axis=0).to_numpy()
    return summed_df


def sum_by_index(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Sum all values across all dataframes that share the same index.
    Useful for getting district-level time-dependent data across multiple buildings.

    For example:
    ```
    building_1:             col1    col2
                index
                2000        1       2
                2001        3       4
    building_2:             col1    col2
                index
                1999        5       6
                2000        7       8
    building_3:             col1    col2
                index
                2005        1       2
                2006        3       4

    ```
    The result would be:
    ```
    output:                 col1    col2
                index
                1999        5       6
                2000        8       10
                2001        3       4
                2002        0       0
                2003        0       0
                2004        0       0
                2005        1       2
                2006        3       4
    ```

    :param result_list: A list of dataframes to sum.
    :type result_list: list[pd.DataFrame]
    :return: A dataframe with the summed values.
    :rtype: pd.DataFrame
    """
    if not dfs:
        raise ValueError("result_list must be non-empty")
    index_min = min(df.index.min() for df in dfs)
    index_max = max(df.index.max() for df in dfs)
    out = (
        pd.concat(dfs)
        .groupby(level=0, sort=True)
        .sum(numeric_only=True)
        .reindex(pd.RangeIndex(index_min, index_max + 1), fill_value=float(0))
    )
    out.index.rename(dfs[0].index.name, inplace=True)
    return out


def main(config: Configuration) -> None:
    operational(config)
    embodied(config)


if __name__ == "__main__":
    main(Configuration())
