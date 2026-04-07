# -*- coding: utf-8 -*-
"""Plot district pathway emission timelines.

This module provides a dedicated plot entry for pathway timelines that is separate
from the standard lifecycle emission timeline plot.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

import cea.config
from cea.demand.building_properties.useful_areas import calc_useful_areas
from cea.import_export.result_summary import filter_buildings
from cea.inputlocator import InputLocator
from cea.visualisation.special.emission_timeline import EmissionTimelinePlot

__author__ = "Yiqiao Wang, Zhongming Shi"
__copyright__ = "Copyright 2026, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Yiqiao Wang", "Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

_SERVICE_TO_TECH = {
    "electricity": "E_sys",
    "space_heating": "Qhs_sys",
    "space_cooling": "Qcs_sys",
    "dhw": "Qww_sys",
}

_UNIT_SCALE = {
    "tonCO2e": 1.0 / 1000.0,
    "kgCO2e": 1.0,
    "gCO2e": 1000.0,
}


@dataclass
class _TimelineConfigAdapter:
    """Adapter so EmissionTimelinePlot can reuse existing config field names."""

    plots_emission_timeline: Any


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, tuple):
        return [str(v) for v in value]
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return [str(value)]


def _to_int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _resolve_period_bounds(context: dict[str, Any]) -> tuple[int | None, int | None]:
    """Return safe (period_start, period_end) bounds for timeline filtering.

    GUI and saved config contexts may carry placeholder values like (0, 0),
    which should mean "no filter" for year-based timelines.
    """

    start = _to_int_or_none(context.get("period_start"))
    end = _to_int_or_none(context.get("period_end"))

    if (start is None or start <= 0) and (end is None or end <= 0):
        return None, None

    if start is not None and start <= 0:
        start = None
    if end is not None and end <= 0:
        end = None

    if start is not None and end is not None and end < start:
        return None, None

    return start, end


def _period_years(df: pd.DataFrame) -> pd.Series:
    years = df["period"].astype(str).str.replace("Y_", "", regex=False)
    return pd.to_numeric(years, errors="coerce")


def _apply_cutoff_year(
    timeline_df: pd.DataFrame,
    cutoff_year: int | None,
) -> pd.DataFrame:
    if cutoff_year is None:
        return timeline_df

    years = _period_years(timeline_df)
    filtered = timeline_df.loc[years >= int(cutoff_year)].copy()
    if filtered.empty:
        raise ValueError(
            f"No pathway emission data remain at or after cutoff year {int(cutoff_year)}."
        )
    return filtered.reset_index(drop=True)


def _resolve_effective_year_bounds(
    context: dict[str, Any],
    cutoff_year: int | None,
) -> tuple[int | None, int | None]:
    period_start, period_end = _resolve_period_bounds(context)

    if cutoff_year is not None:
        if period_end is not None and period_end < int(cutoff_year):
            raise ValueError(
                f"Cutoff year {int(cutoff_year)} is after the selected period end year {int(period_end)}."
            )
        period_start = (
            max(period_start, int(cutoff_year))
            if period_start is not None
            else int(cutoff_year)
        )

    return period_start, period_end


def _read_timeline_csv(path: str) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Pathway emissions timeline file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    if "period" not in df.columns:
        unnamed = next(
            (
                c
                for c in df.columns
                if isinstance(c, str) and c.lower().startswith("unnamed")
            ),
            None,
        )
        if unnamed is not None:
            df = df.rename(columns={unnamed: "period"})

    if "period" not in df.columns:
        raise ValueError(
            f"Timeline file does not contain a 'period' column: {csv_path}"
        )

    return df


def _sort_period(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    years = out["period"].astype(str).str.replace("Y_", "", regex=False)
    out["_year"] = pd.to_numeric(years, errors="coerce")
    out = out.sort_values("_year").drop(columns=["_year"])
    return out.reset_index(drop=True)


def _aggregate_building_pathway_timelines(
    locator: InputLocator,
    pathway_name: str,
    selected_buildings: list[str],
) -> tuple[pd.DataFrame | None, list[str]]:
    frames: list[pd.DataFrame] = []
    missing_files: list[str] = []

    for building_name in selected_buildings:
        building_path = locator.get_building_pathway_emissions_timeline_file(
            pathway_name, building_name
        )
        if not Path(building_path).exists():
            missing_files.append(building_name)
            continue

        df = _read_timeline_csv(building_path)
        tech_quarter_cols = [
            "production_technical_system_hs_kgCO2e",
            "production_technical_system_cs_kgCO2e",
            "production_technical_system_dhw_kgCO2e",
            "production_technical_system_el_kgCO2e",
        ]
        if all(col in df.columns for col in tech_quarter_cols):
            df["production_technical_systems_kgCO2e"] = (
                df[tech_quarter_cols].sum(axis=1, min_count=1).fillna(0.0)
            )
        numeric_cols = [
            col
            for col in df.columns
            if col != "period" and pd.api.types.is_numeric_dtype(df[col])
        ]
        frames.append(df[["period", *numeric_cols]])

    if not frames:
        return None, missing_files

    combined = pd.concat(frames, ignore_index=True)
    aggregated = combined.groupby("period", as_index=False).sum(numeric_only=True)
    return _sort_period(aggregated), missing_files


def _get_filtered_buildings(
    locator: InputLocator,
    building_filter: Any,
) -> list[str]:
    _, selected = filter_buildings(
        locator,
        building_filter.buildings,
        building_filter.filter_buildings_by_year_start,
        building_filter.filter_buildings_by_year_end,
        building_filter.filter_buildings_by_construction_type,
        building_filter.filter_buildings_by_use_type,
        building_filter.min_ratio_as_main_use,
    )
    return selected


def _load_pathway_timeline_for_selection(
    locator: InputLocator,
    pathway_name: str,
    selected_buildings: list[str],
) -> pd.DataFrame:
    aggregated, missing_files = _aggregate_building_pathway_timelines(
        locator,
        pathway_name,
        selected_buildings,
    )

    if missing_files:
        # We only allow district fallback when no per-building files can be loaded
        # and the request is for the full district.
        all_zone_buildings = list(locator.get_zone_building_names())
        full_district_requested = set(selected_buildings) == set(all_zone_buildings)
        if aggregated is None and full_district_requested:
            district_path = locator.get_district_pathway_emissions_timeline_path(pathway_name)
            return _sort_period(_read_timeline_csv(district_path))

        missing_sorted = ", ".join(sorted(missing_files)[:10])
        raise FileNotFoundError(
            "Missing per-building pathway emissions timeline files for the selected buildings. "
            "Please regenerate pathway emissions timelines before plotting. "
            f"Examples: {missing_sorted}"
        )

    if aggregated is not None:
        return aggregated

    district_path = locator.get_district_pathway_emissions_timeline_path(pathway_name)
    return _sort_period(_read_timeline_csv(district_path))


def _build_requested_base_columns(plot_config: Any) -> list[str]:
    categories = _as_list(getattr(plot_config, "y_category_to_plot", []))
    operation_services = _as_list(getattr(plot_config, "operation_services", []))
    envelope_components = _as_list(getattr(plot_config, "envelope_components", []))

    pv_code_raw = getattr(plot_config, "pv_code", None)
    pv_code = str(pv_code_raw).strip() if pv_code_raw is not None else ""
    if not pv_code:
        pv_code = ""

    requested: list[str] = []

    if "operation" in categories:
        for service in operation_services:
            if service in _SERVICE_TO_TECH:
                requested.append(f"operation_{_SERVICE_TO_TECH[service]}")
            elif service == "pv_electricity_offset" and pv_code:
                requested.append(f"PV_{pv_code}_GRID_offset")
            elif service == "pv_electricity_export" and pv_code:
                requested.append(f"PV_{pv_code}_GRID_export")

    for phase in ("production", "demolition", "biogenic"):
        if phase not in categories:
            continue
        for component in envelope_components:
            if component == "pv" and pv_code:
                requested.append(f"{phase}_PV_{pv_code}")
            else:
                requested.append(f"{phase}_{component}")

    return list(dict.fromkeys(requested))


def _get_normalisation_denominator(
    *,
    locator: InputLocator,
    selected_buildings: list[str],
    mode: str,
) -> float | None:
    if mode == "no_normalisation":
        return None

    zone_df = gpd.read_file(locator.get_zone_geometry())
    if "Name" in zone_df.columns:
        name_col = "Name"
    elif "name" in zone_df.columns:
        name_col = "name"
    else:
        raise KeyError(
            "Zone geometry must include either 'Name' or 'name' for normalisation."
        )

    architecture_df = pd.read_csv(locator.get_building_architecture())
    if "name" not in architecture_df.columns:
        raise KeyError("Building architecture must include a 'name' column.")

    useful_areas = calc_useful_areas(
        zone_df.set_index(name_col),
        architecture_df.set_index("name"),
    )

    selected_index = useful_areas.index.intersection(selected_buildings)
    if selected_index.empty:
        raise ValueError("No selected buildings found for area normalisation.")

    if mode == "gross_floor_area":
        denominator = float(useful_areas.loc[selected_index, "GFA_m2"].sum())
    elif mode == "conditioned_floor_area":
        denominator = float(useful_areas.loc[selected_index, "Af"].sum())
    else:
        raise ValueError(f"Unsupported normalisation mode: {mode}")

    if denominator <= 0:
        raise ValueError(
            f"Area normalisation denominator must be positive, got {denominator}."
        )

    return denominator


def _prepare_plot_dataframe(
    timeline_df: pd.DataFrame,
    selected_columns_kg: list[str],
    *,
    y_metric_unit: str,
    normalisation_denominator: float | None,
) -> tuple[pd.DataFrame, list[str]]:
    scale = _UNIT_SCALE.get(y_metric_unit, 1.0)
    normalisation_suffix = "/m2" if normalisation_denominator is not None else ""

    out = pd.DataFrame({"X": timeline_df["period"]})
    y_columns: list[str] = []

    for col in selected_columns_kg:
        values = pd.to_numeric(timeline_df[col], errors="coerce").fillna(0.0)
        values = values * scale
        if normalisation_denominator is not None:
            values = values / normalisation_denominator

        base_name = col[: -len("_kgCO2e")]
        out_col = f"{base_name}_{y_metric_unit}{normalisation_suffix}"
        out[out_col] = values
        y_columns.append(out_col)

    return out, y_columns


def create_pathway_emission_timeline_plot(config: cea.config.Configuration):
    locator = InputLocator(config.scenario)
    plot_config = config.sections["plots-pathway-emission-timeline"]
    building_filter = config.sections["plots-building-filter"]

    pathway_names = getattr(plot_config, "existing_pathway_names", [])
    if isinstance(pathway_names, str):
        pathway_names = [p.strip() for p in pathway_names.split(",") if p.strip()]
    if not pathway_names:
        # Backward compatibility: try old singular parameter
        pathway_name = str(getattr(plot_config, "existing_pathway_name", "") or "").strip()
        if pathway_name:
            pathway_names = [pathway_name]
        else:
            raise ValueError(
                "Please select at least one pathway in plots-pathway-emission-timeline."
            )

    selected_buildings = _get_filtered_buildings(locator, building_filter)
    if not selected_buildings:
        raise ValueError("No buildings remain after applying the building filters.")

    # Use first pathway for the main timeline (multi-pathway overlay is a future enhancement)
    pathway_name = pathway_names[0]
    timeline_df = _load_pathway_timeline_for_selection(
        locator,
        pathway_name,
        selected_buildings,
    )
    cutoff_year = _to_int_or_none(getattr(plot_config, "cutoff_year", None))
    timeline_df = _apply_cutoff_year(timeline_df, cutoff_year)

    requested_base_columns = _build_requested_base_columns(plot_config)
    requested_columns_kg = [f"{base}_kgCO2e" for base in requested_base_columns]
    selected_columns_kg = [c for c in requested_columns_kg if c in timeline_df.columns]

    if not selected_columns_kg:
        raise ValueError(
            "None of the requested emission columns are available in the selected pathway timeline. "
            "Please review y-category-to-plot, operation-services, envelope-components, and pv-code settings."
        )

    normalisation_mode = str(getattr(plot_config, "y_normalised_by", "no_normalisation"))
    normalisation_denominator = _get_normalisation_denominator(
        locator=locator,
        selected_buildings=selected_buildings,
        mode=normalisation_mode,
    )

    y_metric_unit = str(getattr(plot_config, "y_metric_unit", "kgCO2e"))
    df_to_plotly, y_columns = _prepare_plot_dataframe(
        timeline_df,
        selected_columns_kg,
        y_metric_unit=y_metric_unit,
        normalisation_denominator=normalisation_denominator,
    )

    context = getattr(plot_config, "context", None) or {}
    period_start, period_end = _resolve_effective_year_bounds(
        context,
        cutoff_year,
    )

    plot_adapter = _TimelineConfigAdapter(plots_emission_timeline=plot_config)
    plot_title = f"CEA-4 Pathway Emission Timeline ({pathway_name})"

    plot_obj = EmissionTimelinePlot(
        plot_adapter,
        df_to_plotly,
        y_columns,
        plot_title=plot_title,
        bool_accumulated=True,
        period_start=period_start,
        period_end=period_end,
    )

    return plot_obj.create_plot()


def main(config: cea.config.Configuration):
    fig = create_pathway_emission_timeline_plot(config)
    return fig.to_html(full_html=False, include_plotlyjs="cdn")


if __name__ == "__main__":
    output = main(cea.config.Configuration())
    print(output)
