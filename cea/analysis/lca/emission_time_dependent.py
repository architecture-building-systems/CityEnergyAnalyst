import os
import warnings

import pandas as pd
from pandas.errors import EmptyDataError, ParserError

from cea.analysis.lca.emission_timeline import BuildingEmissionTimeline
from cea.analysis.lca.hourly_operational_emission import OperationalHourlyTimeline
from cea.config import Configuration
from cea.datamanagement.database.envelope_lookup import EnvelopeLookup
from cea.demand.building_properties import BuildingProperties
from cea.inputlocator import InputLocator
from cea.utilities import epwreader

__author__ = "Yiqiao Wang, Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Yiqiao Wang", "Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def _load_grid_emission_intensity_override(config: Configuration):
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
    emissions_cfg = config.emissions
    buildings = emissions_cfg.buildings

    # Validate zone geometry EARLY before expensive calculations
    print("Validating zone geometry...")
    import geopandas as gpd
    from cea.utilities.standardize_coordinates import get_lat_lon_projected_shapefile
    try:
        zone_gdf = gpd.read_file(locator.get_zone_geometry())
        # This will raise ValueError with detailed message if geometries are invalid
        get_lat_lon_projected_shapefile(zone_gdf)
        print("Zone geometry validation passed.")
    except ValueError as e:
        print(f"ERROR: {e}")
        raise

    # Check PV requirements BEFORE processing any buildings
    consider_pv = emissions_cfg.include_pv
    pv_codes: list[str] = [] # prevent unbound variable error later in apply_pv_offsetting
    if consider_pv:
        pv_codes = emissions_cfg.pv_codes
        first_building = buildings[0]

        # Check which panels are missing
        missing_panels = []
        for pv_code in (pv_codes if pv_codes else []):
            pv_path = locator.PV_results(first_building, pv_code)
            if not os.path.exists(pv_path):
                missing_panels.append(pv_code)

        if missing_panels:
            missing_list = ', '.join(missing_panels)
            error_msg = (
                f"PV electricity results missing for panel type(s): {missing_list}. "
                f"Please run the 'photovoltaic (PV) panels' script first to generate PV potential results for these panel types."
            )
            print(f"ERROR: {error_msg}")
            raise FileNotFoundError(error_msg)

    weather_path = locator.get_weather_file()
    weather_data = epwreader.epw_reader(weather_path)[
        ["year", "drybulb_C", "wetbulb_C", "relhum_percent", "windspd_ms", "skytemp_C"]
    ]
    building_properties = BuildingProperties(locator, weather_data, buildings)
    results: list[tuple[str, pd.DataFrame]] = []
    # Load optional GRID carbon intensity override once for all buildings
    override_grid_emission, grid_emission_final_g = _load_grid_emission_intensity_override(config)
    grid_emission_final = grid_emission_final_g / 1000.0 if grid_emission_final_g is not None else None  # convert g to kg
    for building in buildings:
        bpr = building_properties[building]
        hourly_timeline = OperationalHourlyTimeline(locator, bpr)

        if override_grid_emission and grid_emission_final is not None:
            hourly_timeline.emission_intensity_timeline["GRID"] = grid_emission_final

        hourly_timeline.calculate_operational_emission()

        if consider_pv:
            hourly_timeline.apply_pv_offsetting(pv_codes)

        hourly_timeline.save_results()
        print(
            f"Hourly operational emissions for {building} calculated and saved in: {locator.get_lca_operational_hourly_building(building)}."
        )
        results.append((building, hourly_timeline.operational_emission_timeline_extended))

    # df_by_building = to_ton(sum_by_building(results))
    df_by_building = sum_by_building(results)
    # df_by_hour = to_ton(sum_by_hour([df for _, df in results]))
    df_by_hour = sum_by_hour([df for _, df in results])
    df_by_building.to_csv(locator.get_total_yearly_operational_building(), float_format='%.2f')
    df_by_hour.to_csv(locator.get_total_yearly_operational_hour(), index=False, float_format='%.2f')
    print(
        f"District-level operational emissions saved in: {locator.get_lca_emissions_results_folder()}"
    )


def total_yearly(config: Configuration) -> None:
    locator = InputLocator(scenario=config.scenario)
    emissions_cfg = config.emissions
    buildings = emissions_cfg.buildings
    year_end_val = emissions_cfg.year_end
    if year_end_val is None:
        end_year: int = 2100
    else:
        # Coerce to int if provided as string
        end_year = int(year_end_val)

    # Validate zone geometry EARLY before expensive calculations
    print("Validating zone geometry...")
    import geopandas as gpd
    from cea.utilities.standardize_coordinates import get_lat_lon_projected_shapefile
    try:
        zone_gdf = gpd.read_file(locator.get_zone_geometry())
        # This will raise ValueError with detailed message if geometries are invalid
        get_lat_lon_projected_shapefile(zone_gdf)
        print("Zone geometry validation passed.")
    except ValueError as e:
        print(f"ERROR: {e}")
        raise

    # Check PV requirements BEFORE processing any buildings
    consider_pv: bool = getattr(emissions_cfg, "include_pv", False)
    pv_codes: list[str] = []

    if consider_pv:
        # Get PV codes from configuration (user must specify which PV types to include)
        pv_codes = getattr(emissions_cfg, "pv_codes", [])

        if not pv_codes:
            print("  Warning: include-pv is True but no PV codes specified in pv-codes parameter.")
            print("           No PV embodied emissions will be included.")
            consider_pv = False
        else:
            # Validate that results exist for all configured PV codes
            missing_panels = []
            for pv_code in pv_codes:
                pv_total_path = locator.PV_total_buildings(pv_code)
                if not os.path.exists(pv_total_path):
                    missing_panels.append(pv_code)

            if missing_panels:
                missing_list = ', '.join(missing_panels)
                error_msg = (
                    f"PV electricity results missing for panel type(s): {missing_list}. "
                    f"Please run the 'photovoltaic (PV) panels' script first to generate PV potential results for these panel types."
                )
                print(f"ERROR: {error_msg}")
                raise FileNotFoundError(error_msg)

            print(f"  Including PV life cycle emissions for panel types: {', '.join(pv_codes)}")

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
        if consider_pv:
            timeline.fill_pv_embodied_emissions(pv_codes=pv_codes)
        # Handle optional grid decarbonisation policy inputs
        ref_yr = emissions_cfg.grid_decarbonise_reference_year
        tar_yr = emissions_cfg.grid_decarbonise_target_year
        tar_ef = emissions_cfg.grid_decarbonise_target_emission_factor

        if ref_yr is not None and tar_yr is not None and tar_ef is not None: # all exist
            feedstock_policies_arg = {"GRID": (ref_yr, tar_yr, tar_ef)}
        elif ref_yr is None and tar_yr is None and tar_ef is None: # all None
            feedstock_policies_arg = None
        else:
            raise ValueError(
                "If one of grid_decarbonise_reference_year, grid_decarbonise_target_year, or grid_decarbonise_target_emission_factor is set, all must be set."
            )
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
    # df_by_year = to_ton(sum_by_year([df for _, df in results]))
    df_by_year = sum_by_year([df for _, df in results])
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


def sum_by_hour(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Sum hourly emission DataFrames across buildings into a district total.

    Each DataFrame has a numeric hour index (0-8759) and a ``date`` column.
    The ``date`` column is taken from the first DataFrame and prepended to the
    result; all other columns are summed element-wise.

    :param dfs: Per-building hourly emission DataFrames.
    :type dfs: list[pd.DataFrame]
    :return: District-level hourly emissions with ``date`` as the first column.
    :rtype: pd.DataFrame
    """
    if not dfs:
        raise ValueError("dfs must be non-empty")

    date_series = dfs[0]['date'].copy()
    dfs_for_sum = [df.drop(columns=['date', 'name'], errors='ignore') for df in dfs]

    out = pd.concat(dfs_for_sum).groupby(level=0, sort=True).sum()
    out.insert(0, 'date', date_series.to_list())
    return out


def sum_by_year(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Sum yearly emission DataFrames across buildings into a district total.

    Each DataFrame has a ``Y_XXXX``-formatted string index. Buildings may span
    different year ranges; missing years are filled with 0. The result has a
    ``period`` column (``Y_XXXX``) as the first column.

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

    :param dfs: Per-building yearly emission DataFrames.
    :type dfs: list[pd.DataFrame]
    :return: District-level yearly emissions with ``period`` as the first column.
    :rtype: pd.DataFrame
    """
    if not dfs:
        raise ValueError("dfs must be non-empty")

    dfs_for_sum = [df.drop(columns=['name'], errors='ignore') for df in dfs]

    min_year = min(int(str(df.index.min()).replace('Y_', '')) for df in dfs_for_sum)
    max_year = max(int(str(df.index.max()).replace('Y_', '')) for df in dfs_for_sum)
    reindex_range = [f"Y_{year}" for year in range(min_year, max_year + 1)]

    out = (
        pd.concat(dfs_for_sum)
        .groupby(level=0, sort=True)
        .sum()
        .reindex(reindex_range, fill_value=0.0)
        .reset_index()
        .rename(columns={'index': 'period'})
    )
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


# ── What-if scenario emissions ────────────────────────────────────────────────

import json
import numpy as np

from cea.constants import HOURS_IN_YEAR
from cea.datamanagement.database.components import Feedstocks

_ZERO_EMISSION_CARRIERS = {'DH', 'DC', 'NONE'}

# Prefixes identifying carrier-consumption columns in final-energy B####.csv
_CARRIER_COLUMN_PREFIXES = ('Qhs_sys_', 'Qww_sys_', 'Qcs_sys_', 'E_sys_',
                             'Qhs_booster_', 'Qww_booster_')

# Solar column detection helpers (based on actual final-energy column naming):
#   PV electric  : PV_{facade}_kWh          → starts with 'PV_'
#   PVT electric : PVT_{type}_{facade}_E_kWh → starts with 'PVT_', ends with '_E_kWh'
#   PVT thermal  : PVT_{type}_{facade}_Q_kWh → starts with 'PVT_', ends with '_Q_kWh'
#   SC thermal   : SC_{type}_{facade}_kWh    → starts with 'SC_'

def _is_solar_thermal_col(col: str) -> bool:
    return (col.startswith('PVT_') and col.endswith('_Q_kWh')) or col.startswith('SC_')

def _is_solar_electric_col(col: str) -> bool:
    return col.startswith('PV_') or (col.startswith('PVT_') and col.endswith('_E_kWh'))


def _expand_feedstock_emissions(feedstock_db) -> pd.DataFrame:
    """Build an 8760-row DataFrame of emission intensities in kgCO2/kWh, one column per carrier."""
    expanded = pd.DataFrame(
        index=range(HOURS_IN_YEAR),
        columns=list(feedstock_db._library.keys()),
        dtype=float,
    )
    for feedstock, df in feedstock_db._library.items():
        expanded[feedstock] = np.resize(df['GHG_kgCO2MJ'].to_numpy(dtype=float), HOURS_IN_YEAR)
        expanded[feedstock] *= 3.6  # kgCO2/MJ → kgCO2/kWh
    expanded['NONE'] = 0.0
    return expanded


def _calc_operational_emissions_from_fe(
    fe_df: pd.DataFrame,
    emission_intensity: pd.DataFrame,
    supply_cfg: dict,
) -> pd.DataFrame:
    """Calculate hourly operational emissions from a final-energy B####.csv DataFrame.

    Scans all ``{service}_{CARRIER}_kWh`` columns. DH/DC/NONE produce zero building-scale
    emissions. Adds negative offset columns for solar thermal (PVT/SC) and solar electric
    (PV/PVT) production.

    :param fe_df: 8760-row hourly final-energy DataFrame for one building.
    :param emission_intensity: 8760-row DataFrame with one column per carrier (kgCO2/kWh).
    :param supply_cfg: Supply configuration dict for this building (from configuration.json).
    :return: 8760-row hourly emissions DataFrame.
    """
    result: dict[str, 'np.ndarray'] = {}
    if 'date' in fe_df.columns:
        result['date'] = fe_df['date'].values

    for col in fe_df.columns:
        if not col.endswith('_kWh'):
            continue
        for prefix in _CARRIER_COLUMN_PREFIXES:
            if col.startswith(prefix):
                carrier = col[len(prefix):-4]  # strip prefix and '_kWh'
                if not carrier or carrier in _ZERO_EMISSION_CARRIERS:
                    break
                if carrier in emission_intensity.columns:
                    em_col = f'{col[:-4]}_kgCO2e'  # replace _kWh with _kgCO2e
                    result[em_col] = fe_df[col].values * emission_intensity[carrier].values
                break

    # Solar thermal offset: aggregate PVT_Q and SC_Q across all facades into two columns
    # 1 kWh of solar heat offsets 1 kWh × emission_factor of the heating carrier (η=1, same as electric).
    hs_carrier = (supply_cfg.get('space_heating') or {}).get('carrier', '')
    if hs_carrier and hs_carrier not in _ZERO_EMISSION_CARRIERS and hs_carrier in emission_intensity.columns:
        hs_intensity = emission_intensity[hs_carrier].values
        pvt_q_total = np.zeros(len(fe_df))
        sc_q_total = np.zeros(len(fe_df))
        for col in fe_df.columns:
            if not col.endswith('_kWh'):
                continue
            if col.startswith('PVT_') and col.endswith('_Q_kWh'):
                pvt_q_total += fe_df[col].values
            elif col.startswith('SC_'):
                sc_q_total += fe_df[col].values
        if pvt_q_total.sum() > 0:
            result['PVT_Q_offset_kgCO2e'] = -pvt_q_total * hs_intensity
        if sc_q_total.sum() > 0:
            result['SC_Q_offset_kgCO2e'] = -sc_q_total * hs_intensity

    # Solar electric offset: aggregate PV and PVT_E across all facades into two columns
    if 'GRID' in emission_intensity.columns:
        grid_intensity = emission_intensity['GRID'].values
        pv_e_total = np.zeros(len(fe_df))
        pvt_e_total = np.zeros(len(fe_df))
        for col in fe_df.columns:
            if not col.endswith('_kWh'):
                continue
            if col.startswith('PV_'):
                pv_e_total += fe_df[col].values
            elif col.startswith('PVT_') and col.endswith('_E_kWh'):
                pvt_e_total += fe_df[col].values
        if pv_e_total.sum() > 0:
            result['PV_E_offset_kgCO2e'] = -pv_e_total * grid_intensity
        if pvt_e_total.sum() > 0:
            result['PVT_E_offset_kgCO2e'] = -pvt_e_total * grid_intensity

    return pd.DataFrame(result, index=fe_df.index)


def _calc_plant_operational_emissions_from_fe(
    plant_df: pd.DataFrame,
    emission_intensity: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate hourly operational emissions for a district plant from its final-energy file.

    Scans ``plant_primary_{NT}_{CARRIER}_kWh``, ``plant_tertiary_{NT}_{CARRIER}_kWh``,
    and ``plant_pumping_GRID_kWh`` columns.

    :param plant_df: 8760-row hourly final-energy DataFrame for one plant.
    :param emission_intensity: 8760-row DataFrame with one column per carrier (kgCO2/kWh).
    :return: 8760-row hourly emissions DataFrame.
    """
    result: dict[str, 'np.ndarray'] = {}
    if 'date' in plant_df.columns:
        result['date'] = plant_df['date'].values

    plant_prefixes = ('plant_primary_', 'plant_tertiary_', 'plant_pumping_')
    for col in plant_df.columns:
        if not col.endswith('_kWh'):
            continue
        for prefix in plant_prefixes:
            if col.startswith(prefix):
                # Format: plant_primary_DH_GRID_kWh → carrier = GRID
                # Split and take second-to-last part (last is 'kWh')
                parts = col[len(prefix):].split('_')
                carrier = parts[-2] if len(parts) >= 2 else parts[0]
                if carrier in _ZERO_EMISSION_CARRIERS:
                    break
                if carrier in emission_intensity.columns:
                    em_col = f'{col[:-4]}_kgCO2e'
                    result[em_col] = plant_df[col].values * emission_intensity[carrier].values
                break

    return pd.DataFrame(result, index=plant_df.index)


def _build_feedstock_policies(ref_yr, tar_yr, tar_ef):
    """Return a feedstock_policies dict suitable for BuildingEmissionTimeline."""
    if ref_yr is not None and tar_yr is not None and tar_ef is not None:
        return {'GRID': (ref_yr, tar_yr, tar_ef)}
    if ref_yr is None and tar_yr is None and tar_ef is None:
        return None
    raise ValueError(
        'If one of grid_decarbonise_reference_year, grid_decarbonise_target_year, or '
        'grid_decarbonise_target_emission_factor is set, all must be set.'
    )


def calculate_emissions_for_whatif(whatif_name: str, config: Configuration) -> None:
    """Calculate emissions for one what-if scenario.

    Reads supply configuration from ``configuration.json`` and energy flows from
    final-energy ``B####.csv`` files. Writes operational hourly files and summary
    CSVs to ``outputs/data/analysis/{whatif_name}/emissions/``.

    :param whatif_name: What-if scenario identifier.
    :param config: CEA Configuration instance.
    """
    locator = InputLocator(config.scenario)
    print(f'Calculating emissions for what-if scenario: {whatif_name}')

    # Load configuration.json
    config_file = locator.get_analysis_configuration_file(whatif_name)
    if not os.path.exists(config_file):
        raise FileNotFoundError(
            f"configuration.json not found for what-if '{whatif_name}': {config_file}\n"
            "Please run 'final-energy' first."
        )
    with open(config_file) as f:
        config_data = json.load(f)
    building_configs = config_data.get('buildings', {})
    plant_configs = config_data.get('plants', {})
    network_name = config_data.get('metadata', {}).get('network_name')

    # Emission intensity (8760 rows, kgCO2/kWh per carrier)
    feedstock_db = Feedstocks.from_locator(locator)
    emission_intensity = _expand_feedstock_emissions(feedstock_db)
    override_grid, grid_arr = _load_grid_emission_intensity_override(config)
    if override_grid and grid_arr is not None:
        emission_intensity['GRID'] = grid_arr / 1000.0  # g → kg

    # Output folder
    out_folder = locator.get_emissions_whatif_folder(whatif_name)
    os.makedirs(out_folder, exist_ok=True)

    # Final-energy summary for metadata and building/plant list
    summary_path = locator.get_final_energy_buildings_file(whatif_name)
    if not os.path.exists(summary_path):
        raise FileNotFoundError(
            f"final_energy_buildings.csv not found for what-if '{whatif_name}': {summary_path}\n"
            "Please run 'final-energy' first."
        )
    summary_df = pd.read_csv(summary_path)

    # Resources for embodied emissions
    emissions_cfg = config.emissions
    year_end_val = emissions_cfg.year_end
    end_year = int(year_end_val) if year_end_val is not None else 2100
    feedstock_policies = _build_feedstock_policies(
        emissions_cfg.grid_decarbonise_reference_year,
        emissions_cfg.grid_decarbonise_target_year,
        emissions_cfg.grid_decarbonise_target_emission_factor,
    )

    weather_data = epwreader.epw_reader(locator.get_weather_file())[
        ['year', 'drybulb_C', 'wetbulb_C', 'relhum_percent', 'windspd_ms', 'skytemp_C']
    ]
    building_rows_df = summary_df[summary_df['type'] == 'building'] if 'type' in summary_df.columns else summary_df
    building_names = building_rows_df['name'].dropna().tolist()
    building_properties = BuildingProperties(locator, weather_data, building_names)
    envelope_lookup = EnvelopeLookup.from_locator(locator)

    # --- Process buildings ---
    operational_results = []   # (name, hourly_df)
    timeline_results = []      # (name, yearly_df)
    buildings_rows_out = []    # one dict per building/plant for summary

    # Per-building DH/DC demand and construction year for proportional plant emission allocation
    # {building_name: (construction_year, {'DH': annual_kwh, 'DC': annual_kwh})}
    building_network_demand = {}

    for _, row in building_rows_df.iterrows():
        building_name = row['name']
        supply_cfg = building_configs.get(building_name, {})

        fe_path = locator.get_final_energy_building_file(building_name, whatif_name)
        if not os.path.exists(fe_path):
            print(f'  Skipping {building_name}: final-energy hourly file not found at {fe_path}')
            continue

        fe_df = pd.read_csv(fe_path)

        # Track per-building DH/DC demand for proportional plant emission allocation
        construction_year = int(building_properties.typology[building_name]['year'])
        bld_network = {'DH': 0.0, 'DC': 0.0}
        for carrier in ('DH', 'DC'):
            for col in fe_df.columns:
                if col.endswith(f'_{carrier}_kWh'):
                    bld_network[carrier] += float(fe_df[col].sum())
        if bld_network['DH'] > 0 or bld_network['DC'] > 0:
            building_network_demand[building_name] = (construction_year, bld_network)

        hourly_op = _calc_operational_emissions_from_fe(fe_df, emission_intensity, supply_cfg)

        # Save per-building hourly operational emissions
        operational_file = locator.get_emissions_whatif_building_file(building_name, whatif_name)
        os.makedirs(os.path.dirname(operational_file), exist_ok=True)
        hourly_op.to_csv(operational_file, index=False, float_format='%.2f')
        print(f'  Hourly operational emissions for {building_name} saved.')
        operational_results.append((building_name, hourly_op))

        # Annual operational total for summary (sum all emission columns except date/name)
        op_cols = [c for c in hourly_op.columns if c not in ('date', 'name')]
        op_total = float(hourly_op[op_cols].sum().sum()) if op_cols else 0.0

        # Yearly emission timeline (embodied + operational)
        production_total = 0.0
        biogenic_total = 0.0
        demolition_total = 0.0
        try:
            timeline = BuildingEmissionTimeline(
                building_properties=building_properties,
                envelope_lookup=envelope_lookup,
                building_name=building_name,
                locator=locator,
                end_year=end_year,
            )
            timeline.fill_embodied_emissions()
            solar_config = supply_cfg.get('solar', {})
            if solar_config:
                timeline.fill_solar_embodied_emissions(solar_config)
            timeline.fill_operational_emissions(
                feedstock_policies=feedstock_policies,
                operational_df=hourly_op,
            )
            timeline.demolish(demolition_year=end_year + 1)
            timeline_results.append((building_name, timeline.timeline))

            # Save per-building timeline
            building_timeline_file = locator.get_emissions_whatif_building_timeline_file(
                building_name, whatif_name
            )
            os.makedirs(os.path.dirname(building_timeline_file), exist_ok=True)
            timeline.timeline.to_csv(building_timeline_file, float_format='%.2f')
            print(f'  Emission timeline for {building_name} saved.')
            # Sum each lifecycle category across all years
            production_total = float(timeline.timeline[
                [c for c in timeline.timeline.columns if c.startswith('production_')]
            ].sum().sum())
            biogenic_total = float(timeline.timeline[
                [c for c in timeline.timeline.columns if c.startswith('biogenic_')]
            ].sum().sum())
            demolition_total = float(timeline.timeline[
                [c for c in timeline.timeline.columns if c.startswith('demolition_')]
            ].sum().sum())
        except Exception as e:
            print(f'  Warning: could not compute emission timeline for {building_name}: {e}')
            production_total = 0.0
            biogenic_total = 0.0
            demolition_total = 0.0

        buildings_rows_out.append({
            'name': building_name,
            'type': 'building',
            'GFA_m2': row.get('GFA_m2'),
            'x_coord': row.get('x_coord'),
            'y_coord': row.get('y_coord'),
            'scale': row.get('scale', 'BUILDING'),
            'case': row.get('case'),
            'case_description': row.get('case_description'),
            'operation_kgCO2e': op_total,
            'production_kgCO2e': production_total,
            'biogenic_kgCO2e': biogenic_total,
            'demolition_kgCO2e': demolition_total,
            'whatif_name': whatif_name,
        })

    # --- Process plants ---
    plant_rows_df = summary_df[summary_df['type'] == 'plant'] if 'type' in summary_df.columns else pd.DataFrame()
    for _, row in plant_rows_df.iterrows():
        plant_name = row.get('name', '')
        case_desc = str(row.get('case_description') or '')

        if 'DH' in case_desc:
            network_type = 'DH'
        elif 'DC' in case_desc:
            network_type = 'DC'
        else:
            continue

        plant_fe_path = locator.get_final_energy_plant_file(network_name or '', network_type, plant_name, whatif_name)
        if not os.path.exists(plant_fe_path):
            continue

        plant_df = pd.read_csv(plant_fe_path)
        hourly_plant = _calc_plant_operational_emissions_from_fe(plant_df, emission_intensity)
        plant_operational_file = locator.get_emissions_whatif_building_file(plant_name, whatif_name)
        os.makedirs(os.path.dirname(plant_operational_file), exist_ok=True)
        hourly_plant.to_csv(plant_operational_file, index=False, float_format='%.2f')
        print(f'  Hourly operational emissions for plant {plant_name} saved.')
        operational_results.append((plant_name, hourly_plant))

        op_cols = [c for c in hourly_plant.columns if c not in ('date', 'name')]
        op_total = float(hourly_plant[op_cols].sum().sum()) if op_cols else 0.0

        # Save per-plant timeline and add to district aggregate
        # Plant emissions are stored as operation_DH_kgCO2e or operation_DC_kgCO2e
        # Proportionally allocated across years based on when connected buildings exist
        if timeline_results:
            # Full district year range
            all_years = set()
            for _, tl in timeline_results:
                all_years.update(tl.index)
            year_index = pd.Index(sorted(all_years))
            plant_annual_total = float(hourly_plant[op_cols].sum().sum()) if op_cols else 0.0

            # Compute per-year demand weight based on building construction years
            # Total demand from all buildings connected to this network type
            total_demand = sum(
                nd[network_type] for _, (_, nd) in building_network_demand.items()
                if nd.get(network_type, 0) > 0
            )

            # For each year, sum demand from buildings that exist (construction_year <= year)
            year_weights = {}
            for yr_str in year_index:
                yr_int = int(str(yr_str).replace('Y_', ''))
                yr_demand = sum(
                    nd[network_type]
                    for _, (constr_yr, nd) in building_network_demand.items()
                    if nd.get(network_type, 0) > 0 and constr_yr <= yr_int
                )
                year_weights[yr_str] = yr_demand / total_demand if total_demand > 0 else 0.0

            # Build plant timeline with proportional emissions
            ref_cols = list(timeline_results[0][1].columns)
            plant_op_col = f'operation_{network_type}_kgCO2e'
            if plant_op_col not in ref_cols:
                ref_cols.append(plant_op_col)
            plant_timeline_df = pd.DataFrame(0.0, index=year_index, columns=ref_cols)
            plant_timeline_df['name'] = plant_name
            plant_timeline_df[plant_op_col] = [
                plant_annual_total * year_weights[yr] for yr in year_index
            ]

            # Add to timeline_results for district aggregation
            timeline_results.append((plant_name, plant_timeline_df))

            plant_timeline_file = locator.get_emissions_whatif_building_timeline_file(
                plant_name, whatif_name
            )
            os.makedirs(os.path.dirname(plant_timeline_file), exist_ok=True)
            plant_timeline_df.to_csv(plant_timeline_file, float_format='%.2f')
            print(f'  Emission timeline for plant {plant_name} saved.')
        buildings_rows_out.append({
            'name': plant_name,
            'type': 'plant',
            'GFA_m2': row.get('GFA_m2'),
            'x_coord': row.get('x_coord'),
            'y_coord': row.get('y_coord'),
            'scale': 'DISTRICT',
            'case': row.get('case'),
            'case_description': case_desc,
            'operation_kgCO2e': op_total,
            'production_kgCO2e': 0.0,
            'biogenic_kgCO2e': 0.0,
            'demolition_kgCO2e': 0.0,
            'whatif_name': whatif_name,
        })

    # --- Save summary outputs ---
    if buildings_rows_out:
        buildings_df = pd.DataFrame(buildings_rows_out)
        buildings_df.to_csv(
            locator.get_emissions_whatif_buildings_file(whatif_name),
            index=False,
            float_format='%.2f',
        )
        print(f'  Emissions buildings summary saved to: {locator.get_emissions_whatif_buildings_file(whatif_name)}')

    if operational_results:
        df_by_hour = sum_by_hour([df for _, df in operational_results])
        df_by_hour.to_csv(
            locator.get_emissions_whatif_operational_file(whatif_name),
            index=False,
            float_format='%.2f',
        )
        print(f'  District operational emissions saved to: {locator.get_emissions_whatif_operational_file(whatif_name)}')

    if timeline_results:
        df_by_year = sum_by_year([df for _, df in timeline_results])
        df_by_year.to_csv(
            locator.get_emissions_whatif_timeline_file(whatif_name),
            index=False,
            float_format='%.2f',
        )
        print(f'  District emission timeline saved to: {locator.get_emissions_whatif_timeline_file(whatif_name)}')

    print(f"Emissions for what-if '{whatif_name}' complete. Results in: {out_folder}")
