"""
InputProcessor - Determines the correct CSV file in the summary folder and triggers the summary feature to generate this file.
Ensure this file exists or break the script.

"""
import os

import geopandas as gpd
import pandas as pd

from cea.import_export.result_summary import (
    get_emission_context,
    process_building_summary,
    exec_aggregate_time_period,
    slice_hourly_results_for_custom_time_period,
)
from cea.inputlocator import InputLocator
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def _annotate_plant_display_name(original_name, row):
    """Append -DH or -DC suffix to plant names for display.

    Parameters
    ----------
    original_name : str
        Original entity name (e.g. 'NODE16')
    row : dict or pd.Series
        Must have 'type' and 'case_description' keys.

    Returns
    -------
    str
        Annotated name (e.g. 'NODE16-DH') for plants, unchanged for buildings.
    """
    if row.get('type') != 'plant':
        return original_name
    case_desc = str(row.get('case_description') or '')
    if 'DH' in case_desc:
        return f"{original_name}-DH"
    elif 'DC' in case_desc:
        return f"{original_name}-DC"
    return original_name


def _filter_by_entity_type(df, include_entities, buildings=None):
    """Filter DataFrame rows by entity type (buildings/plants) and building name selection.

    Parameters
    ----------
    df : pd.DataFrame
        Must have a 'type' column with values 'building' or 'plant'.
        If no 'type' column exists, only the building name filter is applied.
    include_entities : list[str]
        Subset of ['buildings', 'plants'] indicating which to keep.
    buildings : list[str] or None
        If provided, filter building-type rows to only those in this list.
        Plant-type rows are never filtered by name.

    Returns
    -------
    pd.DataFrame
    """
    include_buildings = 'buildings' in include_entities
    include_plants = 'plants' in include_entities

    if 'type' not in df.columns:
        # No type column — treat all rows as buildings
        if buildings and include_buildings:
            return df[df['name'].isin(list(buildings))].copy()
        return df if include_buildings else df.iloc[0:0].copy()

    # Split into buildings and plants
    mask_plant = df['type'] == 'plant'
    parts = []
    if include_buildings:
        bldg_df = df[~mask_plant]
        if buildings:
            bldg_df = bldg_df[bldg_df['name'].isin(list(buildings))]
        parts.append(bldg_df)
    if include_plants:
        parts.append(df[mask_plant])

    if not parts:
        return df.iloc[0:0].copy()
    return pd.concat(parts, ignore_index=False)


def get_building_names_from_zone(locator):
    """
    Get building names from zone geometry.

    Parameters
    ----------
    locator : InputLocator
        File path resolver

    Returns
    -------
    pd.DataFrame
        Zone geometry with 'Name' or 'name' column (caller should check both)
    """

    zone_path = locator.get_zone_geometry()
    crs = get_geographic_coordinate_system()
    zone_df = gpd.read_file(zone_path).to_crs(crs)

    return zone_df


def raise_missing_pv_error(pv_codes, context='file'):
    """
    Raise FileNotFoundError for missing PV results.

    :param pv_codes: Single PV code (str) or list of PV codes (list)
    :param context: 'file' for missing PV files, 'emission' for missing PV data in emission results
    :raises FileNotFoundError: Always raises with formatted error message
    """
    if isinstance(pv_codes, str):
        pv_codes = [pv_codes]

    if context == 'emission':
        # Error when PV columns are missing from emission results
        if len(pv_codes) == 1:
            error_msg = (
                f"PV data missing for panel type: {pv_codes[0]} in emission results. "
                f"Please run the 'emissions' script with include_pv=True and pv_codes=['{pv_codes[0]}'] "
                f"to include PV offsetting in emission calculations."
            )
        else:
            pv_list = ', '.join([f"'{code}'" for code in sorted(pv_codes)])
            error_msg = (
                f"PV data missing for panel type(s): {', '.join(sorted(pv_codes))} in emission results. "
                f"Please run the 'emissions' script with include_pv=True and pv_codes=[{pv_list}] "
                f"to include PV offsetting in emission calculations."
            )
    else:
        # Error when PV result files don't exist
        if len(pv_codes) == 1:
            error_msg = (
                f"PV electricity results missing for panel type: {pv_codes[0]}. "
                f"Please run the 'photovoltaic (PV) panels' script first to generate PV potential results for this panel type."
            )
        else:
            error_msg = (
                f"PV electricity results missing for panel type(s): {', '.join(sorted(pv_codes))}. "
                f"Please run the 'photovoltaic (PV) panels' script first to generate PV potential results for these panel types."
            )

    print(f"ERROR: {error_msg}")
    raise FileNotFoundError(error_msg)


demand_metrics = ['grid_electricity_consumption', 'enduse_electricity_demand', 'enduse_electricity', 'enduse_cooling_demand', 'enduse_space_cooling_demand', 'enduse_space_cooling', 'enduse_heating_demand', 'enduse_space_heating_demand', 'enduse_space_heating', 'enduse_dhw_demand', 'enduse_dhw']
demand_analytics = ['EUI_grid_electricity',	'EUI_enduse_electricity', 'EUI_enduse_cooling',	'EUI_enduse_space cooling',	'EUI_enduse_heating', 'EUI_enduse_space_heating', 'EUI_enduse_dhw']

final_energy_metrics = ['grid_electricity', 'natural_gas', 'oil', 'coal', 'wood']

solar_metrics = ['total', 'roofs_top', 'walls_north', 'walls_east', 'walls_south', 'walls_west']
solar_analytics = ['solar_energy_penetration', 'self_consumption', 'self_sufficiency']


def get_plot_metrics_dict(locator):
    """Get dictionary of plot metrics for each CEA feature, with lazy emission context initialisation."""
    emission_context = get_emission_context(locator)
    lifecycle_emission_metrics = emission_context["yearly_colnames"]
    operational_emission_metrics = emission_context["hourly_colnames"]

    return {
        'demand': demand_metrics,
        'final-energy': final_energy_metrics,
        'pv': solar_metrics,
        'pvt': solar_metrics,
        'sc': solar_metrics,
        'lifecycle-emissions': lifecycle_emission_metrics,
        'operational-emissions': operational_emission_metrics,
        'emission-timeline': lifecycle_emission_metrics,
        'heat-rejection': ['heat_rejection']
    }


def get_plot_analytics_dict(locator):
    """Get dictionary of plot analytics for each CEA feature."""
    # This doesn't need emission context, but kept for consistency
    return {
        'demand': demand_analytics,
        'final-energy': [],
        'pv': solar_analytics,
        'pvt': [],
        'sc': [],
        'lifecycle-emissions': [],
        'operational-emissions': [],
        'heat-rejection': []
    }

def _export_final_energy_to_plots_folder(locator, whatif_names, buildings, bool_aggregate_by_building, time_period, period_start, period_end, include_entities=None):
    """
    Read final-energy results for one or more what-if scenarios and write an
    intermediate CSV to the standard export/plots path expected by the pipeline.

    For building-level annual view: reads final_energy_buildings.csv (annual totals),
    converts MWh → kWh.  Multiple what-if names are prefixed on the building name.

    For building-level monthly/seasonal view and all district time-series views:
    reads per-building B####.csv hourly files, sums carrier columns, then aggregates
    via exec_aggregate_time_period() — the same pattern used by heat-rejection.

    Carrier column mapping:
        GRID_MWh / *_GRID_kWh      → GRID_kWh
        NATURALGAS_MWh / *_NATURALGAS_kWh → NATURALGAS_kWh
        OIL_MWh / *_OIL_kWh       → OIL_kWh
        COAL_MWh / *_COAL_kWh     → COAL_kWh
        WOOD_MWh / *_WOOD_kWh     → WOOD_kWh
    """
    from cea.utilities.date import get_date_range_hours_from_year

    if include_entities is None:
        include_entities = ['plants', 'buildings']

    if isinstance(whatif_names, str):
        whatif_names = [whatif_names]

    carriers = ['GRID', 'NATURALGAS', 'OIL', 'COAL', 'WOOD']
    carrier_rename = {f'{c}_MWh': f'{c}_kWh' for c in carriers}
    multi = len(whatif_names) > 1

    if bool_aggregate_by_building and time_period == 'annually':
        # Fast path: read annual summary CSV (no hourly files needed)
        dfs = []
        for whatif_name in whatif_names:
            src_path = locator.get_final_energy_buildings_file(whatif_name)
            if not os.path.exists(src_path):
                continue
            df = pd.read_csv(src_path)
            df = _filter_by_entity_type(df, include_entities, buildings=buildings)
            # Annotate plant names with network type suffix for display
            if 'type' in df.columns and 'case_description' in df.columns:
                df['name'] = df.apply(lambda r: _annotate_plant_display_name(r['name'], r), axis=1)
            keep_cols = ['name', 'GFA_m2'] + [c for c in carrier_rename if c in df.columns]
            df_out = df[keep_cols].copy()
            for mwh_col in carrier_rename:
                if mwh_col in df_out.columns:
                    df_out[mwh_col] = df_out[mwh_col] * 1000.0
            df_out = df_out.rename(columns=carrier_rename)
            if multi:
                df_out['name'] = whatif_name + '/' + df_out['name']
            df_out['period'] = 'annually'
            dfs.append(df_out)
        if not dfs:
            return
        df_out = pd.concat(dfs, ignore_index=True)
        out_path = locator.get_export_plots_cea_feature_time_resolution_buildings_file(
            'final-energy', 'final-energy', 'annually', period_start, period_end
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        df_out.to_csv(out_path, index=False, float_format='%.3f')

    elif bool_aggregate_by_building:
        # Building monthly/seasonal view — read per-building hourly files
        dates = get_date_range_hours_from_year(2005)
        dfs = []
        for whatif_name in whatif_names:
            summary_path = locator.get_final_energy_buildings_file(whatif_name)
            if not os.path.exists(summary_path):
                continue
            summary_df = pd.read_csv(summary_path)
            summary_df = _filter_by_entity_type(summary_df, include_entities, buildings=buildings)
            gfa_map = summary_df.set_index('name')['GFA_m2'].to_dict() if 'GFA_m2' in summary_df.columns else {}
            # Build display name map for plant annotation
            display_name_map = {}
            for _, srow in summary_df.iterrows():
                display_name_map[srow['name']] = _annotate_plant_display_name(srow['name'], srow)

            for building_name in summary_df['name'].tolist():
                building_file = locator.get_final_energy_building_file(building_name, whatif_name)
                if not os.path.exists(building_file):
                    continue
                bdf = pd.read_csv(building_file)
                n = min(len(bdf), len(dates))
                row = {'date': dates[:n]}
                for carrier in carriers:
                    cols = [c for c in bdf.columns if c.endswith(f'_{carrier}_kWh')]
                    if cols:
                        row[f'{carrier}_kWh'] = bdf[cols].sum(axis=1).values[:n]
                hourly_df = pd.DataFrame(row)
                hourly_df = slice_hourly_results_for_custom_time_period(period_start, period_end, hourly_df)

                list_list_df, _ = exec_aggregate_time_period(True, [[hourly_df]], [time_period])
                if not list_list_df or not list_list_df[0]:
                    continue
                agg_df = list_list_df[0][0]
                annotated = display_name_map.get(building_name, building_name)
                display_name = f'{whatif_name}/{annotated}' if multi else annotated
                agg_df.insert(0, 'name', display_name)
                agg_df['GFA_m2'] = gfa_map.get(building_name, 0.0)
                dfs.append(agg_df)

        if not dfs:
            return
        df_out = pd.concat(dfs, ignore_index=True)
        out_path = locator.get_export_plots_cea_feature_time_resolution_buildings_file(
            'final-energy', 'final-energy', time_period, period_start, period_end
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        df_out.to_csv(out_path, index=False, float_format='%.3f')

    else:
        # District views
        if time_period == 'annually':
            # Annual district view: sum per-building annual totals to a single district row
            dfs = []
            for whatif_name in whatif_names:
                src_path = locator.get_final_energy_buildings_file(whatif_name)
                if not os.path.exists(src_path):
                    continue
                df = pd.read_csv(src_path)
                df = _filter_by_entity_type(df, include_entities, buildings=buildings)
                keep_cols = [c for c in carrier_rename if c in df.columns]
                df_out = df[keep_cols].copy()
                for mwh_col in carrier_rename:
                    if mwh_col in df_out.columns:
                        df_out[mwh_col] = df_out[mwh_col] * 1000.0
                df_out = df_out.rename(columns=carrier_rename)
                dfs.append(df_out)
            if not dfs:
                return
            totals = pd.concat(dfs, ignore_index=True).sum(numeric_only=True)
            df_out = pd.DataFrame([totals])
            df_out.insert(0, 'period', 'annually')
        else:
            # District time-series: read all buildings' hourly files, sum per carrier, aggregate
            whatif_name = whatif_names[0]
            dates = get_date_range_hours_from_year(2005)
            summary_path = locator.get_final_energy_buildings_file(whatif_name)
            if not os.path.exists(summary_path):
                return
            summary_df = pd.read_csv(summary_path)
            summary_df = _filter_by_entity_type(summary_df, include_entities, buildings=buildings)

            entity_dfs = []
            for building_name in summary_df['name'].tolist():
                building_file = locator.get_final_energy_building_file(building_name, whatif_name)
                if not os.path.exists(building_file):
                    continue
                bdf = pd.read_csv(building_file)
                n = min(len(bdf), len(dates))
                row = {'date': dates[:n]}
                for carrier in carriers:
                    cols = [c for c in bdf.columns if c.endswith(f'_{carrier}_kWh')]
                    if cols:
                        row[f'{carrier}_kWh'] = bdf[cols].sum(axis=1).values[:n]
                hourly_df = pd.DataFrame(row)
                hourly_df = slice_hourly_results_for_custom_time_period(period_start, period_end, hourly_df)
                entity_dfs.append(hourly_df)

            if not entity_dfs:
                return
            list_list_df, _ = exec_aggregate_time_period(True, [entity_dfs], [time_period])
            if not list_list_df or not list_list_df[0]:
                return
            df_out = list_list_df[0][0]

        out_path = locator.get_export_results_summary_cea_feature_time_period_file(
            locator.get_export_plots_folder(), 'final-energy', 'final-energy', time_period, period_start, period_end
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        df_out.to_csv(out_path, index=False, float_format='%.3f')


def _export_heat_rejection_to_plots_folder(locator, whatif_names, buildings, bool_aggregate_by_building, time_period, period_start, period_end, include_entities=None):
    """
    Read heat rejection results for one or more what-if scenarios and write an
    intermediate CSV to the standard export/plots path expected by the pipeline.

    For building-level annual view: reads heat_rejection_buildings.csv, converts
    heat_rejection_annual_MWh → heat_rejection_kWh.

    For district time-series views: sums hourly files across all entities and
    aggregates to the requested time resolution using result_summary machinery.
    """
    from cea.utilities.date import get_date_range_hours_from_year

    if include_entities is None:
        include_entities = ['plants', 'buildings']

    if isinstance(whatif_names, str):
        whatif_names = [whatif_names]

    if bool_aggregate_by_building:
        dfs = []
        multi = len(whatif_names) > 1
        for whatif_name in whatif_names:
            src_path = locator.get_heat_rejection_whatif_buildings_file(whatif_name)
            if not os.path.exists(src_path):
                continue
            df = pd.read_csv(src_path)
            df = _filter_by_entity_type(df, include_entities, buildings=buildings)
            # Annotate plant names with network type suffix for display
            if 'type' in df.columns and 'case_description' in df.columns:
                df['name'] = df.apply(lambda r: _annotate_plant_display_name(r['name'], r), axis=1)
            keep_cols = [c for c in ['name', 'GFA_m2', 'heat_rejection_annual_MWh'] if c in df.columns]
            df_out = df[keep_cols].copy()
            if 'heat_rejection_annual_MWh' in df_out.columns:
                df_out['heat_rejection_kWh'] = df_out['heat_rejection_annual_MWh'] * 1000.0
                df_out = df_out.drop(columns=['heat_rejection_annual_MWh'])
            if multi:
                df_out['name'] = whatif_name + '/' + df_out['name']
            dfs.append(df_out)
        if not dfs:
            return
        df_out = pd.concat(dfs, ignore_index=True)
        df_out['period'] = 'annually'
        out_path = locator.get_export_plots_cea_feature_time_resolution_buildings_file(
            'heat-rejection', 'heat-rejection', 'annually', period_start, period_end
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        df_out.to_csv(out_path, index=False, float_format='%.3f')

    else:
        # District time-series view — use first whatif_name
        whatif_name = whatif_names[0]
        buildings_file = locator.get_heat_rejection_whatif_buildings_file(whatif_name)
        if not os.path.exists(buildings_file):
            return
        buildings_df = pd.read_csv(buildings_file)
        buildings_df = _filter_by_entity_type(buildings_df, include_entities, buildings=buildings)
        entity_names = buildings_df['name'].tolist()

        dates = get_date_range_hours_from_year(2005)
        entity_dfs = []
        for entity_name in entity_names:
            entity_file = locator.get_heat_rejection_whatif_building_file(entity_name, whatif_name)
            if not os.path.exists(entity_file):
                continue
            entity_df = pd.read_csv(entity_file)
            if 'heat_rejection_kW' not in entity_df.columns:
                continue
            n = min(len(entity_df), len(dates))
            df = pd.DataFrame({
                'date': dates[:n],
                'heat_rejection_kWh': entity_df['heat_rejection_kW'].values[:n],
            })
            df = slice_hourly_results_for_custom_time_period(period_start, period_end, df)
            entity_dfs.append(df)

        if not entity_dfs:
            return

        list_list_df, _ = exec_aggregate_time_period(True, [entity_dfs], [time_period])
        if not list_list_df or not list_list_df[0]:
            return

        df_result = list_list_df[0][0]
        out_path = locator.get_export_results_summary_cea_feature_time_period_file(
            locator.get_export_plots_folder(), 'heat-rejection', 'heat-rejection', time_period, period_start, period_end
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        df_result.to_csv(out_path, index=False, float_format='%.3f')


def _collect_lifecycle_rows(locator, whatif_names, buildings, include_entities=None):
    """Build a list of per-building annual lifecycle emission rows from what-if results.

    All values (operational, embodied, solar offset) are summed over the full
    lifecycle timeline so they are on the same time scope.  Booster operational
    columns are merged into their parent service (Qhs_booster → Qhs_sys,
    Qww_booster → Qww_sys).
    """
    if include_entities is None:
        include_entities = ['plants', 'buildings']
    # Maps timeline column → output service key (boosters merged into parent)
    _TIMELINE_SERVICE_MAP = {
        'operation_Qhs_sys_kgCO2e': 'operation_Qhs_sys_kgCO2e',
        'operation_Qww_sys_kgCO2e': 'operation_Qww_sys_kgCO2e',
        'operation_Qcs_sys_kgCO2e': 'operation_Qcs_sys_kgCO2e',
        'operation_E_sys_kgCO2e': 'operation_E_sys_kgCO2e',
        'operation_Qhs_booster_kgCO2e': 'operation_Qhs_sys_kgCO2e',
        'operation_Qww_booster_kgCO2e': 'operation_Qww_sys_kgCO2e',
        'operation_DH_kgCO2e': 'operation_DH_kgCO2e',
        'operation_DC_kgCO2e': 'operation_DC_kgCO2e',
    }
    _SOLAR_OFFSETS = ('PV_E_offset_kgCO2e', 'PVT_E_offset_kgCO2e', 'PVT_Q_offset_kgCO2e', 'SC_Q_offset_kgCO2e')
    multi = len(whatif_names) > 1
    rows = []
    for whatif_name in whatif_names:
        buildings_summary_path = locator.get_emissions_whatif_buildings_file(whatif_name)
        if not os.path.exists(buildings_summary_path):
            continue
        summary_df = pd.read_csv(buildings_summary_path)
        summary_df = _filter_by_entity_type(summary_df, include_entities, buildings=buildings)
        for _, row in summary_df.iterrows():
            building_name = row['name']
            # Read timeline (lifecycle) for operational + solar offset totals
            timeline_path = locator.get_emissions_whatif_building_timeline_file(building_name, whatif_name)
            if not os.path.exists(timeline_path):
                continue
            tdf = pd.read_csv(timeline_path)
            annotated_name = _annotate_plant_display_name(building_name, row)
            out_row = {
                'name': f'{whatif_name}/{annotated_name}' if multi else annotated_name,
                'GFA_m2': row.get('GFA_m2', 0.0),
            }
            # Operational per-service totals from timeline (full lifecycle scope)
            service_totals = {}
            for tl_col, dest_col in _TIMELINE_SERVICE_MAP.items():
                if tl_col in tdf.columns:
                    service_totals[dest_col] = service_totals.get(dest_col, 0.0) + tdf[tl_col].sum()
            out_row.update(service_totals)
            # Solar offsets from timeline
            for solar_col in _SOLAR_OFFSETS:
                if solar_col in tdf.columns:
                    out_row[solar_col] = tdf[solar_col].sum()
            # Embodied totals from summary (already lifecycle-scoped)
            for emb_col in ('production_kgCO2e', 'biogenic_kgCO2e', 'demolition_kgCO2e'):
                out_row[emb_col] = row.get(emb_col, 0.0)
            out_row['period'] = 'annually'
            rows.append(out_row)
    return rows


def _export_lifecycle_emissions_to_plots_folder(locator, whatif_names, buildings, bool_aggregate_by_building, period_start, period_end, include_entities=None):
    """
    Read lifecycle emissions results for one or more what-if scenarios and write an
    intermediate CSV to the standard export/plots path expected by the pipeline.
    """
    if include_entities is None:
        include_entities = ['plants', 'buildings']

    if isinstance(whatif_names, str):
        whatif_names = [whatif_names]

    rows = _collect_lifecycle_rows(locator, whatif_names, buildings, include_entities=include_entities)
    if not rows:
        return
    df_all = pd.DataFrame(rows)

    if bool_aggregate_by_building:
        df_out = df_all
        out_path = locator.get_export_plots_cea_feature_time_resolution_buildings_file(
            'lifecycle-emissions', 'lifecycle-emissions', 'annually', period_start, period_end
        )
    else:
        # District annual: sum numeric columns across all buildings
        numeric_cols = df_all.select_dtypes(include='number').columns.tolist()
        totals = df_all[numeric_cols].sum(numeric_only=True)
        df_out = pd.DataFrame([totals])
        df_out.insert(0, 'period', 'annually')
        out_path = locator.get_export_results_summary_cea_feature_time_period_file(
            locator.get_export_plots_folder(), 'lifecycle-emissions', 'lifecycle-emissions', 'annually', period_start, period_end
        )

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df_out.to_csv(out_path, index=False, float_format='%.3f')


def _aggregate_op_emission_row(hdf, n=None):
    """
    Aggregate one building's hourly operational emission DataFrame into derived columns.

    Returns a dict with three levels of aggregation (all with _kgCO2e suffix):
    - Service totals:       operation_Qhs_sys_kgCO2e, operation_E_sys_kgCO2e, ...
    - Carrier totals:       GRID_kgCO2e, NATURALGAS_kgCO2e, ...
    - Service×carrier:      Qhs_sys_NATURALGAS_kgCO2e, E_sys_GRID_kgCO2e, ...  (kept as-is)
    - Solar offsets:        PV_E_offset_kgCO2e, PVT_E_offset_kgCO2e, ...
    """
    # Maps hourly-file column prefix → (service_dest for totals, canonical_service for hybrid col)
    _PREFIXES = {
        'Qhs_sys_':     ('operation_Qhs_sys', 'Qhs_sys'),
        'Qww_sys_':     ('operation_Qww_sys', 'Qww_sys'),
        'Qcs_sys_':     ('operation_Qcs_sys', 'Qcs_sys'),
        'E_sys_':       ('operation_E_sys',   'E_sys'),
        'Qhs_booster_': ('operation_Qhs_sys', 'Qhs_sys'),  # boosters fold into Qhs_sys
        'Qww_booster_': ('operation_Qww_sys', 'Qww_sys'),
    }
    _SOLAR_OFFSETS = ('PV_E_offset_kgCO2e', 'PVT_E_offset_kgCO2e',
                      'PVT_Q_offset_kgCO2e', 'SC_Q_offset_kgCO2e')

    out = {}
    cols_data = {col: (hdf[col].values[:n] if n is not None else hdf[col].values)
                 for col in hdf.columns if col not in ('date', 'name')}

    for col, vals in cols_data.items():
        if not col.endswith('_kgCO2e'):
            continue

        # Solar offset columns — keep as-is
        if col in _SOLAR_OFFSETS:
            out[col] = out.get(col, 0.0) + (vals.sum() if n is None else vals.sum())
            continue

        # Plant columns (e.g. plant_primary_DH_NATURALGAS_kgCO2e) → map to operation_DH / operation_DC
        if col.startswith('plant_'):
            col_sum = vals.sum()
            # Parse: plant_{role}_{network_type}_{carrier}_kgCO2e
            parts = col[:-len('_kgCO2e')].split('_')
            # parts = ['plant', 'primary', 'DH', 'NATURALGAS'] or ['plant', 'pumping', 'GRID']
            carrier = parts[-1] if parts else 'GRID'
            # Detect network type (DH or DC) from column name
            network_type = None
            for p in parts:
                if p in ('DH', 'DC'):
                    network_type = p
                    break
            service_dest = f'operation_{network_type}' if network_type else 'operation_E_sys'
            canonical_service = network_type if network_type else 'E_sys'
            svc_col = f'{service_dest}_kgCO2e'
            out[svc_col] = out.get(svc_col, 0.0) + col_sum
            car_col = f'{carrier}_kgCO2e'
            out[car_col] = out.get(car_col, 0.0) + col_sum
            hybrid_col = f'{canonical_service}_{carrier}_kgCO2e'
            out[hybrid_col] = out.get(hybrid_col, 0.0) + col_sum
            continue

        # Operational service×carrier columns
        for prefix, (service_dest, canonical_service) in _PREFIXES.items():
            if col.startswith(prefix):
                carrier = col[len(prefix):-len('_kgCO2e')]
                col_sum = vals.sum()
                # service total
                svc_col = f'{service_dest}_kgCO2e'
                out[svc_col] = out.get(svc_col, 0.0) + col_sum
                # carrier total
                car_col = f'{carrier}_kgCO2e'
                out[car_col] = out.get(car_col, 0.0) + col_sum
                # service×carrier (canonical service name, not booster)
                hybrid_col = f'{canonical_service}_{carrier}_kgCO2e'
                out[hybrid_col] = out.get(hybrid_col, 0.0) + col_sum
                break

    return out


def _aggregate_op_emission_hourly(hdf, n):
    """
    Same as _aggregate_op_emission_row but returns numpy arrays for district time-series.
    Columns: service totals, carrier totals, service×carrier, solar offsets.
    """

    _PREFIXES = {
        'Qhs_sys_':     ('operation_Qhs_sys', 'Qhs_sys'),
        'Qww_sys_':     ('operation_Qww_sys', 'Qww_sys'),
        'Qcs_sys_':     ('operation_Qcs_sys', 'Qcs_sys'),
        'E_sys_':       ('operation_E_sys',   'E_sys'),
        'Qhs_booster_': ('operation_Qhs_sys', 'Qhs_sys'),
        'Qww_booster_': ('operation_Qww_sys', 'Qww_sys'),
    }
    _SOLAR_OFFSETS = ('PV_E_offset_kgCO2e', 'PVT_E_offset_kgCO2e',
                      'PVT_Q_offset_kgCO2e', 'SC_Q_offset_kgCO2e')

    out = {}
    for col in hdf.columns:
        if col in ('date', 'name') or not col.endswith('_kgCO2e'):
            continue
        vals = hdf[col].values[:n]

        if col in _SOLAR_OFFSETS:
            out[col] = out[col] + vals if col in out else vals.copy()
            continue

        # Plant columns (e.g. plant_primary_DH_NATURALGAS_kgCO2e) → map to operation_DH / operation_DC
        if col.startswith('plant_'):
            parts = col[:-len('_kgCO2e')].split('_')
            carrier = parts[-1] if parts else 'GRID'
            network_type = None
            for p in parts:
                if p in ('DH', 'DC'):
                    network_type = p
                    break
            service_dest = f'operation_{network_type}' if network_type else 'operation_E_sys'
            canonical_service = network_type if network_type else 'E_sys'
            svc_col = f'{service_dest}_kgCO2e'
            car_col = f'{carrier}_kgCO2e'
            hybrid_col = f'{canonical_service}_{carrier}_kgCO2e'
            out[svc_col]    = out[svc_col]    + vals if svc_col    in out else vals.copy()
            out[car_col]    = out[car_col]    + vals if car_col    in out else vals.copy()
            out[hybrid_col] = out[hybrid_col] + vals if hybrid_col in out else vals.copy()
            continue

        for prefix, (service_dest, canonical_service) in _PREFIXES.items():
            if col.startswith(prefix):
                carrier = col[len(prefix):-len('_kgCO2e')]
                svc_col = f'{service_dest}_kgCO2e'
                car_col = f'{carrier}_kgCO2e'
                hybrid_col = f'{canonical_service}_{carrier}_kgCO2e'
                out[svc_col]    = out[svc_col]    + vals if svc_col    in out else vals.copy()
                out[car_col]    = out[car_col]    + vals if car_col    in out else vals.copy()
                out[hybrid_col] = out[hybrid_col] + vals if hybrid_col in out else vals.copy()
                break

    return out


def _export_operational_emissions_to_plots_folder(locator, whatif_names, buildings, bool_aggregate_by_building, time_period, period_start, period_end, include_entities=None):
    """
    Read operational emissions results for one or more what-if scenarios and write an
    intermediate CSV to the standard export/plots path expected by the pipeline.

    Exports three levels of aggregation so all y-category-to-plot combinations work:
    - Service totals:    operation_Qhs_sys_kgCO2e  (for 'operation' only)
    - Carrier totals:    GRID_kgCO2e               (for 'energy_carrier' only)
    - Service×carrier:   Qhs_sys_NATURALGAS_kgCO2e (for both selected)
    - Solar offsets:     PV_E_offset_kgCO2e        (always)
    """
    from cea.utilities.date import get_date_range_hours_from_year

    if include_entities is None:
        include_entities = ['plants', 'buildings']

    if isinstance(whatif_names, str):
        whatif_names = [whatif_names]

    multi = len(whatif_names) > 1

    if bool_aggregate_by_building:
        dfs = []
        for whatif_name in whatif_names:
            buildings_summary_path = locator.get_emissions_whatif_buildings_file(whatif_name)
            if not os.path.exists(buildings_summary_path):
                continue
            summary_df = pd.read_csv(buildings_summary_path)
            summary_df = _filter_by_entity_type(summary_df, include_entities, buildings=buildings)

            for _, row in summary_df.iterrows():
                building_name = row['name']
                hourly_path = locator.get_emissions_whatif_building_file(building_name, whatif_name)
                if not os.path.exists(hourly_path):
                    continue
                hdf = pd.read_csv(hourly_path)
                annotated_name = _annotate_plant_display_name(building_name, row)
                out_row = {
                    'name': f'{whatif_name}/{annotated_name}' if multi else annotated_name,
                    'GFA_m2': row.get('GFA_m2', 0.0),
                }
                out_row.update(_aggregate_op_emission_row(hdf))
                out_row['period'] = 'annually'
                dfs.append(out_row)

        if not dfs:
            return
        df_out = pd.DataFrame(dfs)
        out_path = locator.get_export_plots_cea_feature_time_resolution_buildings_file(
            'operational-emissions', 'operational-emissions', 'annually', period_start, period_end
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        df_out.to_csv(out_path, index=False, float_format='%.3f')

    else:
        # District time-series view — use first whatif_name
        whatif_name = whatif_names[0]
        buildings_summary_path = locator.get_emissions_whatif_buildings_file(whatif_name)
        if not os.path.exists(buildings_summary_path):
            return
        summary_df = pd.read_csv(buildings_summary_path)
        summary_df = _filter_by_entity_type(summary_df, include_entities, buildings=buildings)

        dates = get_date_range_hours_from_year(2005)
        entity_dfs = []
        for building_name in summary_df['name'].tolist():
            hourly_path = locator.get_emissions_whatif_building_file(building_name, whatif_name)
            if not os.path.exists(hourly_path):
                continue
            hdf = pd.read_csv(hourly_path)
            n = min(len(hdf), len(dates))
            row_dict = {'date': dates[:n]}
            row_dict.update(_aggregate_op_emission_hourly(hdf, n))
            hourly_df = pd.DataFrame(row_dict)
            hourly_df = slice_hourly_results_for_custom_time_period(period_start, period_end, hourly_df)
            entity_dfs.append(hourly_df)

        if not entity_dfs:
            return
        list_list_df, _ = exec_aggregate_time_period(True, [entity_dfs], [time_period])
        if not list_list_df or not list_list_df[0]:
            return
        df_result = list_list_df[0][0]
        out_path = locator.get_export_results_summary_cea_feature_time_period_file(
            locator.get_export_plots_folder(), 'operational-emissions', 'operational-emissions', time_period, period_start, period_end
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        df_result.to_csv(out_path, index=False, float_format='%.3f')


# Trigger the summary feature and point to the csv results file
class csv_pointer:
    """Maps user input combinations to pre-defined CSV file paths."""

    def __init__(self, plot_config, plots_building_filter, scenario, plot_cea_feature, period_start, period_end, solar_panel_types_list, whatif_names=None, include_entities=None):
        """
        :param plot_config: User-defined configuration settings.
        :param scenario: CEA scenario path.
        :param plot_cea_feature: The feature to plot.
        :param period_start: Start hour for analysis.
        :param period_end: End hour for analysis.
        """

        x, x_facet = get_x_and_x_facet(plot_config.x_to_plot)
        self.config = plot_config
        self.whatif_names = whatif_names or []
        self.scenario = scenario
        self.locator = InputLocator(scenario=scenario)
        self.plot_cea_feature = plot_cea_feature
        self.period_start = period_start
        self.period_end = period_end
        self.buildings = plots_building_filter.buildings
        self.include_entities = include_entities if include_entities is not None else ['plants', 'buildings']

        # For lifecycle-emissions, emission-timeline, and operational-emissions,
        # y_metric_to_plot is generated in b_data_processor from multiple parameters
        # For other features, read it from config
        if plot_cea_feature in ('lifecycle-emissions', 'emission-timeline', 'operational-emissions'):
            self.y_metric_to_plot = []  # Will be generated later in b_data_processor
        else:
            self.y_metric_to_plot = plot_config.y_metric_to_plot
            # Legacy PV handling for other plots if needed
            if hasattr(plot_config, 'pv_code') and plot_config.pv_code is not None:
                pv_code = plot_config.pv_code
                self.y_metric_to_plot.append(f"PV_{pv_code}_offset_total")

        self.y_normalised_by = plot_config.y_normalised_by
        self.x = x
        self.x_to_plot = plot_config.x_to_plot
        self.x_facet = x_facet
        self.integer_year_start = plots_building_filter.filter_buildings_by_year_start
        self.integer_year_end = plots_building_filter.filter_buildings_by_year_end
        self.list_construction_type = plots_building_filter.filter_buildings_by_construction_type
        self.list_use_type = plots_building_filter.filter_buildings_by_use_type
        self.min_ratio_as_main_use = plots_building_filter.min_ratio_as_main_use
        self.plot = True

        if plot_cea_feature in ('pv', 'sc'):
            self.appendix = f"{plot_cea_feature}_{solar_panel_types_list[0]}"
        elif plot_cea_feature == 'pvt':
            if len(solar_panel_types_list) == 2:
                self.appendix = f"{plot_cea_feature}_{solar_panel_types_list[0]}_{solar_panel_types_list[1]}"
            else:
                raise ValueError("PVT requires two solar panel types.")
        else:
            self.appendix = plot_cea_feature

        self.bool_aggregate_by_building = self.x == "by_building"

        time_period_map = {
            "building": "annually",
            "building_faceted_by_decades": "annually",
            "building_faceted_by_months": "monthly",
            "building_faceted_by_seasons": "seasonally",
            "building_faceted_by_construction_type": "annually",
            "building_faceted_by_main_use_type": "annually",
            "district_and_hourly": 'hourly',
            "district_and_hourly_faceted_by_months": 'hourly',
            "district_and_hourly_faceted_by_seasons": 'hourly',
            "district_and_daily": "daily",
            "district_and_daily_faceted_by_months": "daily",
            "district_and_daily_faceted_by_seasons": "daily",
            "district_and_monthly": "monthly",
            "district_and_monthly_faceted_by_seasons": "monthly",
            "district_and_seasonally": "seasonally",
            "district_and_annually_or_selected_period": "annually",
            "district_and_annually_faceted_by_decades": "annually",
            "district_and_annually": "timeline",

        }
        self.time_period = time_period_map.get(self.x_to_plot)

    def execute_summary(self, bool_include_advanced_analytics):
        """Executes the summary feature to generate the required CSV output."""
        if self.plot_cea_feature == 'heat-rejection':
            if not self.whatif_names:
                return
            _export_heat_rejection_to_plots_folder(
                self.locator, self.whatif_names, self.buildings,
                self.bool_aggregate_by_building, self.time_period,
                self.period_start, self.period_end,
                include_entities=self.include_entities
            )
            return

        if self.plot_cea_feature == 'final-energy':
            if not self.whatif_names:
                return
            _export_final_energy_to_plots_folder(
                self.locator, self.whatif_names, self.buildings,
                self.bool_aggregate_by_building, self.time_period,
                self.period_start, self.period_end,
                include_entities=self.include_entities
            )
            return

        if self.plot_cea_feature == 'lifecycle-emissions' and self.whatif_names:
            _export_lifecycle_emissions_to_plots_folder(
                self.locator, self.whatif_names, self.buildings,
                self.bool_aggregate_by_building,
                self.period_start, self.period_end,
                include_entities=self.include_entities
            )
            return

        if self.plot_cea_feature == 'operational-emissions' and self.whatif_names:
            _export_operational_emissions_to_plots_folder(
                self.locator, self.whatif_names, self.buildings,
                self.bool_aggregate_by_building, self.time_period,
                self.period_start, self.period_end,
                include_entities=self.include_entities
            )
            return

        list_metrics_analytics = get_plot_analytics_dict(self.locator).get(self.plot_cea_feature, [])
        if any(item in list_metrics_analytics for item in self.y_metric_to_plot):
            bool_include_advanced_analytics = True

        bool_use_acronym = True

        bool_use_conditioned_floor_area_for_normalisation = self.y_normalised_by == "conditioned_floor_area"
        # bool_use_solar_technology_area_installed_for_respective_surface = self.y_normalised_by == "solar_technology_area_installed_for_respective_surface"

        process_building_summary(
            self.config, self.locator,
            self.period_start, self.period_end, self.buildings,
            self.integer_year_start, self.integer_year_end, self.list_construction_type,
            self.list_use_type, self.min_ratio_as_main_use,
            bool_use_acronym, self.bool_aggregate_by_building,
            bool_include_advanced_analytics, [self.time_period],
            bool_use_conditioned_floor_area_for_normalisation,
            plot=True, list_cea_feature_to_plot=[self.plot_cea_feature]
        )

    def get_summary_results_csv_path(self):
        """Returns the correct path for the summary results CSV file based on user inputs."""
        summary_folder = self.locator.get_export_plots_folder()
        list_metrics_non_analytics = get_plot_metrics_dict(self.locator).get(self.plot_cea_feature, [])
        list_metrics_analytics = get_plot_analytics_dict(self.locator).get(self.plot_cea_feature, [])

        if all(item in list_metrics_non_analytics for item in self.y_metric_to_plot):
            return self._get_non_analytics_summary_path(summary_folder)
        elif all(item in list_metrics_analytics for item in self.y_metric_to_plot):
            return self._get_analytics_summary_path(summary_folder)
        else:
            raise ValueError(f"Invalid y-metric-to-plot: {self.y_metric_to_plot}. Current combination is not supported.")

    def _get_non_analytics_summary_path(self, summary_folder):
        """Helper function to retrieve the non-analytics summary CSV path."""
        cea_feature = self.plot_cea_feature if not self.plot else self.plot_cea_feature.replace('_', '-')
        appendix = self.appendix if not self.plot else self.appendix.replace('_', '-')

        if self.bool_aggregate_by_building:
            return self.locator.get_export_plots_cea_feature_time_resolution_buildings_file(
                cea_feature, appendix, self.time_period, self.period_start, self.period_end
            )
        else:
            return self.locator.get_export_results_summary_cea_feature_time_period_file(
                summary_folder, cea_feature, appendix, self.time_period, self.period_start, self.period_end
            )

    def _get_analytics_summary_path(self, summary_folder):
        """Helper function to retrieve the analytics summary CSV path."""
        if self.bool_aggregate_by_building:
            return self.locator.get_export_plots_cea_feature_analytics_time_resolution_buildings_file(
                self.plot_cea_feature, self.appendix, self.time_period, self.period_start, self.period_end
            )
        else:
            return self.locator.get_export_results_summary_cea_feature_analytics_time_resolution_file(
                summary_folder, self.plot_cea_feature, self.appendix, self.time_period, self.period_start, self.period_end
            )


# from X-to-plot to X and X_facet
def get_x_and_x_facet(x_to_plot):
    if x_to_plot == "building":
        x = 'by_building'
        x_facet = None
    elif x_to_plot == "building_faceted_by_months":
        x = 'by_building'
        x_facet = 'months'
    elif x_to_plot == "building_faceted_by_seasons":
        x = 'by_building'
        x_facet = 'seasons'
    elif x_to_plot == "building_faceted_by_decades":
        x = 'by_building'
        x_facet = 'decades'
    elif x_to_plot == "building_faceted_by_construction_type":
        x = 'by_building'
        x_facet = 'construction_type'
    elif x_to_plot == "building_faceted_by_main_use_type":
        x = 'by_building'
        x_facet = 'main_use_type'
    elif x_to_plot == "district_and_hourly":
        x = 'by_period'
        x_facet = None
    elif x_to_plot == "district_and_hourly_faceted_by_months":
        x = 'by_period'
        x_facet = 'months'
    elif x_to_plot == "district_and_hourly_faceted_by_seasons":
        x = 'by_period'
        x_facet = 'seasons'
    elif x_to_plot == "district_and_annually_faceted_by_decades":
        x = 'by_period'
        x_facet = 'decades'
    elif x_to_plot == "district_and_daily":
        x = 'by_period'
        x_facet = None
    elif x_to_plot == "district_and_daily_faceted_by_months":
        x = 'by_period'
        x_facet = 'months'
    elif x_to_plot == "district_and_daily_faceted_by_seasons":
        x = 'by_period'
        x_facet = 'seasons'
    elif x_to_plot == "district_and_monthly":
        x = 'by_period'
        x_facet = None
    elif x_to_plot == "district_and_monthly_faceted_by_seasons":
        x = 'by_period'
        x_facet = 'seasons'
    elif x_to_plot == "district_and_seasonally":
        x = 'by_period'
        x_facet = None
    elif x_to_plot == "district_and_annually_or_selected_period":
        x = 'by_period'
        x_facet = None
    elif x_to_plot == "district_and_annually":
        x = 'by_period'
        x_facet = None
    else:
        raise ValueError(f"Invalid x-to-plot: {x_to_plot}")

    return x, x_facet


# Main function
def plot_input_processor(plot_config, plots_building_filter, scenario, plot_cea_feature, period_start, period_end, solar_panel_types_list, bool_include_advanced_analytics=False, whatif_names=None, include_entities=None):
    """
    Processes and exports building summary results, filtering buildings based on user-defined criteria.

    Args:
        config: Configuration object containing user inputs.
        scenario: Path to the scenario folder.
        plot_cea_feature: The plot_cea_feature to process.
        period_start (int): Start hour for analysis.
        hour_end (int): End hour for analysis.

    Returns:
        None
    """
    # Instantiate the csv_pointer class
    plot_instance_a = csv_pointer(plot_config, plots_building_filter, scenario, plot_cea_feature, period_start, period_end, solar_panel_types_list, whatif_names=whatif_names, include_entities=include_entities)

    # Get the summary results CSV path
    summary_results_csv_path = plot_instance_a.get_summary_results_csv_path()

    # Delete the existing file if it exists to prevent loading stale cached data
    if os.path.exists(summary_results_csv_path):
        os.remove(summary_results_csv_path)

    # Execute the summary process
    plot_instance_a.execute_summary(bool_include_advanced_analytics)

    # Load the summary results data
    try:
        df_summary_data = pd.read_csv(summary_results_csv_path)

        # Validate data structure based on time period
        # Hourly/daily data should have 'date' column
        # Monthly/seasonal/annual/timeline data should have 'period' column
        if plot_instance_a.time_period in ('hourly', 'daily'):
            # For hourly/daily operational emissions, expect 'date' column
            if 'period' in df_summary_data.columns and 'date' not in df_summary_data.columns:
                error_msg = (
                    f"Data structure error in summary file: {summary_results_csv_path}\n"
                    f"Expected {plot_instance_a.time_period} data with 'date' column, but found 'period' column.\n"
                    f"This suggests aggregated period data was incorrectly written to the {plot_instance_a.time_period} summary file.\n"
                    f"Available columns: {df_summary_data.columns.tolist()}\n"
                    "File will be deleted and regenerated."
                )
                print(error_msg)
                # Delete the incorrect file
                os.remove(summary_results_csv_path)
                raise ValueError(error_msg)
        elif plot_instance_a.time_period in ('monthly', 'seasonally', 'annually', 'timeline'):
            # For monthly/seasonal/annual/timeline data, expect 'period' column
            if 'date' in df_summary_data.columns and 'period' not in df_summary_data.columns:
                error_msg = (
                    f"Data structure error in summary file: {summary_results_csv_path}\n"
                    f"Expected {plot_instance_a.time_period} data with 'period' column, but found 'date' column.\n"
                    f"This suggests hourly/daily data was incorrectly written to the {plot_instance_a.time_period} summary file.\n"
                    f"Available columns: {df_summary_data.columns.tolist()}\n"
                    "File will be deleted and regenerated."
                )
                print(error_msg)
                # Delete the incorrect file
                os.remove(summary_results_csv_path)
                raise ValueError(error_msg)

    except Exception as e:
        print(f"Error loading csv file: {e}")
        df_summary_data = None

    # Load the architecture data
    try:
        df_architecture_data = pd.read_csv(plot_instance_a.locator.get_export_plots_selected_building_file())
    except Exception as e:
        print(f"Error loading csv file: {e}")
        df_architecture_data = None

    return df_summary_data, df_architecture_data, plot_instance_a



