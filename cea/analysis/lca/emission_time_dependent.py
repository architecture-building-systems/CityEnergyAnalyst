import pandas as pd
import warnings
from typing import Optional
from pandas.errors import EmptyDataError, ParserError

from cea.config import Configuration
from cea.inputlocator import InputLocator

from cea.analysis.lca.emission_timeline import BuildingEmissionTimeline
from cea.analysis.lca.hourly_operational_emission import OperationalHourlyTimeline
from cea.demand.building_properties import BuildingProperties
from cea.datamanagement.database.envelope_lookup import EnvelopeLookup
from cea.datamanagement.database.components import Feedstocks
from cea.utilities import epwreader


def _load_grid_intensity_override(config: Configuration):
    """Load and validate an optional external CSV for grid carbon intensity.

    Returns a tuple (override, values) where:
    - override: bool indicating whether to override GRID intensity timeline
    - values: numpy array of length 8760 if override is True; otherwise None

    Rules:
    - If grid_carbon_intensity_dataset_csv is not provided, returns (False, None)
    - If provided, csv_carbon_intensity_column_name must also be provided
    - Accepts 8760 rows; if 8784 rows, drops Feb 29 (hours 1416..1439) and warns
    - Raises with clear messages on missing file/column, parse errors, or NaNs
    """
    emissions_cfg = getattr(config, 'emissions')
    intensity_csv_path = getattr(emissions_cfg, 'grid_carbon_intensity_dataset_csv', None)
    intensity_column_name = getattr(emissions_cfg, 'csv_carbon_intensity_column_name', None)

    if not intensity_csv_path:
        return False, None
    if not intensity_column_name:
        raise ValueError(
            "If grid_carbon_intensity_dataset_csv is provided, csv_carbon_intensity_column_name must also be provided."
        )

    try:
        series: pd.Series = pd.read_csv(
            intensity_csv_path,
            usecols=[intensity_column_name],
            dtype={intensity_column_name: "float64"},
        )[intensity_column_name]
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Could not find the provided CSV file '{intensity_csv_path}'."
        ) from e
    except PermissionError as e:
        raise PermissionError(
            f"Permission denied reading '{intensity_csv_path}'. It may be open in another program."
        ) from e
    except (EmptyDataError, ParserError, OSError, ValueError) as e:
        raise ValueError(
            f"Could not parse '{intensity_csv_path}' with column '{intensity_column_name}': {e}"
        ) from e

    n = len(series)
    if n == 8760:
        pass
    elif n == 8784:
        # Drop Feb 29 (hours 1416..1439) for a non-leap-year 8760-hour year
        series = series.drop(index=range(1416, 1440))
        warnings.warn(
            "Emission intensity CSV has 8784 rows; dropped Feb 29 to produce 8760 rows.",
            RuntimeWarning,
        )
    else:
        raise ValueError(
            f"Emission intensity dataset CSV file must have 8760 or 8784 rows, but has {n} rows."
        )

    if series.isna().any():
        na_count = int(series.isna().sum())
        raise ValueError(
            f"Emission intensity contains {na_count} NaN values; please clean or impute the data."
        )

    return True, series.to_numpy(dtype=float)


def operational_hourly(config: Configuration) -> None:
    locator = InputLocator(config.scenario)
    emissions_cfg = getattr(config, 'emissions')
    buildings = list(getattr(emissions_cfg, 'buildings', []))
    weather_path = locator.get_weather_file()
    weather_data = epwreader.epw_reader(weather_path)[
        ["year", "drybulb_C", "wetbulb_C", "relhum_percent", "windspd_ms", "skytemp_C"]
    ]
    building_properties = BuildingProperties(locator, weather_data, buildings)
    feedstock_db = Feedstocks.from_locator(locator)
    results: list[tuple[str, pd.DataFrame]] = []
    # Load optional GRID carbon intensity override once for all buildings
    override_grid_emission, grid_emission_final_g = _load_grid_intensity_override(config)
    grid_emission_final = grid_emission_final_g / 1000.0 if grid_emission_final_g is not None else None  # convert g to kg
    for building in buildings:
        bpr = building_properties[building]

        timeline = OperationalHourlyTimeline(locator, bpr, feedstock_db)
        if override_grid_emission and grid_emission_final is not None:
            timeline.emission_intensity_timeline["GRID"] = grid_emission_final
        timeline.calculate_operational_emission()
        timeline.save_results()
        print(
            f"Hourly operational emissions for {building} calculated and saved in: {locator.get_lca_operational_hourly_building(building)}."
        )
        results.append((building, timeline.operational_emission_timeline))

    # df_by_building = to_ton(sum_by_building(results))
    df_by_building = sum_by_building(results)
    # df_by_hour = to_ton(sum_by_index([df for _, df in results]))
    df_by_hour = sum_by_index([df for _, df in results])
    df_by_building.to_csv(locator.get_total_yearly_operational_building(), float_format='%.2f')
    df_by_hour.to_csv(locator.get_total_yearly_operational_hour(), index=False, float_format='%.2f')
    print(
        f"District-level operational emissions saved in: {locator.get_lca_timeline_folder()}"
    )


def total_yearly(config: Configuration) -> None:
    locator = InputLocator(scenario=config.scenario)
    emissions_cfg = getattr(config, 'emissions')
    buildings = list(getattr(emissions_cfg, 'buildings', []))
    year_end_val: Optional[int] = getattr(emissions_cfg, 'year_end', None)
    if year_end_val is None:
        end_year: int = 2100
    else:
        # Coerce to int if provided as string
        end_year = int(year_end_val)

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
            end_year=end_year,
        )
        timeline.fill_embodied_emissions()
        # Handle optional grid decarbonisation policy inputs
        ref_yr_val = getattr(emissions_cfg, 'grid_decarbonise_reference_year', None)
        tar_yr_val = getattr(emissions_cfg, 'grid_decarbonise_target_year', None)
        tar_ef_val = getattr(emissions_cfg, 'grid_decarbonise_target_emission_factor', None)
        ref_yr: int | None = int(ref_yr_val) if ref_yr_val is not None and ref_yr_val != '' else None
        tar_yr: int | None = int(tar_yr_val) if tar_yr_val is not None and tar_yr_val != '' else None
        tar_ef: float | None = float(tar_ef_val) if tar_ef_val is not None and tar_ef_val != '' else None

        all_none = ref_yr is None and tar_yr is None and tar_ef is None
        all_exist = ref_yr is not None and tar_yr is not None and tar_ef is not None
        if not (all_none or all_exist):
            raise ValueError(
                "If one of grid_decarbonise_reference_year, grid_decarbonise_target_year, or grid_decarbonise_target_emission_factor is set, all must be set."
            )
        # Build feedstock policies only when all values are provided; otherwise pass None
        feedstock_policies_arg: dict[str, tuple[int, int, float]] | None
        if all_none:
            feedstock_policies_arg = None
        else:
            if ref_yr is None or tar_yr is None or tar_ef is None:
                raise ValueError(f"Grid decarbonisation parameters should all be present: Reference year, target year, target emission factor. "
                                 f"Got: {ref_yr}, {tar_yr}, {tar_ef}")
            
            # Validate grid decarbonisation parameters
            if ref_yr >= tar_yr:
                raise ValueError(
                    f"Invalid grid decarbonisation configuration: reference year ({ref_yr}) must be before target year ({tar_yr})."
                )
            if tar_ef < 0:
                raise ValueError(
                    f"Invalid grid decarbonisation configuration: target emission factor ({tar_ef}) must be non-negative."
                )
            feedstock_policies_arg = {"GRID": (ref_yr, tar_yr, tar_ef)}
        timeline.fill_operational_emissions(
            feedstock_policies=feedstock_policies_arg
        )

        timeline.demolish(demolition_year=end_year + 1)  # no demolition by default
        timeline.save_timeline()
        print(
            f"Emission timeline for {building} calculated and saved in: {locator.get_lca_timeline_building(building)}."
        )
        results.append((building, timeline.timeline))
    #
    # df_by_building = to_ton(sum_by_building(results))
    df_by_building = sum_by_building(results)
    # df_by_year = to_ton(sum_by_index([df for _, df in results]))
    df_by_year = sum_by_index([df for _, df in results])
    df_by_building.to_csv(locator.get_total_emissions_building_year_end(year_end=end_year), float_format='%.2f')
    df_by_year.to_csv(locator.get_total_emissions_timeline_year_end(year_end=end_year), index=False, float_format='%.2f')
    print(
        f"District-level total emissions saved in: {locator.get_lca_timeline_folder()}"
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
    columns_without_date = [col for col in result_list[0][1].columns if col not in ['date', 'name']]
    summed_df = pd.DataFrame(
        data=0.0,
        index=[building for building, _ in result_list],
        columns=columns_without_date,
    )
    summed_df.index.rename("name", inplace=True)
    for building, df in result_list:
        df_copy = df.copy()
        if 'date' in df_copy.columns:
            df_copy.pop('date')
        if 'name' in df_copy.columns:
            df_copy.pop('name')
        summed_df.loc[building] += df_copy.sum(axis=0).to_numpy()
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

    :param dfs: A list of dataframes to sum.
    :type dfs: list[pd.DataFrame]
    :return: A dataframe with the summed values.
    :rtype: pd.DataFrame
    """
    if not dfs:
        raise ValueError("dfs must be non-empty")

    # Get sample dataframe to understand structure
    sample_df = dfs[0]
    has_date_column = 'date' in sample_df.columns
    has_year_index = isinstance(sample_df.index[0], str) and sample_df.index[0].startswith('Y_')

    # Create copies of dataframes without the date column for summing
    dfs_for_sum = []
    date_series = None
    year_series = None

    for df in dfs:
        df_copy = df.copy()
        if 'date' in df_copy.columns:
            if date_series is None:
                date_series = df_copy['date'].copy()
            df_copy = df_copy.drop(columns=['date'])
        # Extract year values from index if it's a year index
        if has_year_index and year_series is None:
            year_series = pd.Series(df_copy.index.values, index=df_copy.index)
        dfs_for_sum.append(df_copy)

    # Perform the sum operation on numeric columns only
    if has_year_index:
        # Extract numeric years from 'Y_XXXX' formatted indices
        min_year = min(int(str(df.index.min()).replace('Y_', '')) for df in dfs_for_sum)
        max_year = max(int(str(df.index.max()).replace('Y_', '')) for df in dfs_for_sum)
        reindex_range = [f"Y_{year}" for year in range(min_year, max_year + 1)]
    else:
        # Handle numeric indices by coercing to int
        index_min = min(int(df.index.min()) for df in dfs_for_sum)
        index_max = max(int(df.index.max()) for df in dfs_for_sum)
        reindex_range = pd.RangeIndex(index_min, index_max + 1)

    out = (
        pd.concat(dfs_for_sum)
        .groupby(level=0, sort=True)
        .sum()
        .reindex(reindex_range, fill_value=0.0)
    )

    # Add date or year column as first column if it existed, but don't reset index
    if has_date_column and date_series is not None:
        # Reset index temporarily to add date column
        out_with_index = out.reset_index(drop=True)

        # Ensure date_series has the right length
        if len(date_series) >= len(out_with_index):
            out_with_index.insert(0, 'date', date_series.iloc[:len(out_with_index)].to_list())
        else:
            # If date_series is shorter, repeat the pattern
            full_dates = pd.concat([date_series] * (len(out_with_index) // len(date_series) + 1))
            out_with_index.insert(0, 'date', full_dates.iloc[:len(out_with_index)].to_list())

        # Reorder columns: date first, then emission columns
        date_cols = ['date']
        emission_cols = [col for col in out_with_index.columns if col not in date_cols]
        out = out_with_index[date_cols + emission_cols]
    elif has_year_index and year_series is not None:
        # Reset index temporarily to add year column
        out_with_index = out.reset_index(drop=True)

        # Ensure year_series has the right length
        if len(year_series) >= len(out_with_index):
            out_with_index.insert(0, 'period', year_series.iloc[:len(out_with_index)].to_list())
        else:
            # If year_series is shorter, repeat the pattern
            full_years = pd.concat([year_series] * (len(out_with_index) // len(year_series) + 1))
            out_with_index.insert(0, 'period', full_years.iloc[:len(out_with_index)].to_list())

        # Reorder columns: year first, then emission columns
        year_cols = ['period']
        emission_cols = [col for col in out_with_index.columns if col not in year_cols]
        out = out_with_index[year_cols + emission_cols]
    else:
        # No date or year column, just reset index without keeping it
        out = out.reset_index(drop=True)

    return out


def to_ton(df: pd.DataFrame) -> pd.DataFrame:
    """Convert a dataframe in kgCO2e to tonCO2e by dividing all values by 1000, and also rename the columns by changing 'kgCO2e' to 'tonCO2e'.

    :param df: A dataframe with values in kgCO2e.
    :type df: pd.DataFrame
    :return: A dataframe with values in tonCO2e.
    :rtype: pd.DataFrame
    """
    df_ton = df / 1000.0
    df_ton.columns = df_ton.columns.str.replace("kgCO2e", "tonCO2e")
    return df_ton


def main(config: Configuration) -> None:
    operational_hourly(config)
    total_yearly(config)


if __name__ == "__main__":
    main(Configuration())
