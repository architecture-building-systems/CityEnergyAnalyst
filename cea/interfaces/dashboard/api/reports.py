"""
Reports API — provides data for the comparison dashboard.

Endpoints:
  GET /api/reports/whatifs         — list what-if names available in a scenario
  GET /api/reports/summary        — KPI summary for a scenario + what-if + feature
  GET /api/reports/plot           — plot HTML div for a scenario + what-if + feature
"""

import os
from typing import Optional

import geopandas
import pandas as pd
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse

import cea.config
import cea.inputlocator
import cea.scripts
from cea.interfaces.dashboard.api.utils import CEAScenario, validate_scenario_name_or_subpath
from cea.interfaces.dashboard.dependencies import CEAConfig
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
from cea.interfaces.dashboard.lib.plot_dispatch import render_plot_html
from cea.interfaces.dashboard.utils import secure_join_under_root
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

logger = getCEAServerLogger("cea-server-reports")

router = APIRouter()



@router.get("/whatifs")
async def get_whatifs(scenario: CEAScenario):
    """List what-if names that have final-energy results in the given scenario."""
    locator = cea.inputlocator.InputLocator(scenario)

    analysis_parent = locator.get_analysis_parent_folder()
    if not os.path.isdir(analysis_parent):
        return {"whatifs": []}

    whatifs = []
    for name in sorted(os.listdir(analysis_parent)):
        folder = os.path.join(analysis_parent, name)
        if not os.path.isdir(folder):
            continue
        # Check if final-energy results exist (prerequisite for most analyses)
        fe_dir = os.path.join(folder, "final-energy")
        if os.path.isdir(fe_dir):
            whatifs.append(name)

    return {"whatifs": whatifs}


def _demand_summary(locator):
    """Compute demand KPIs from Total_demand.csv."""
    path = locator.get_total_demand()
    if not os.path.isfile(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demand results not found. Run the demand simulation first.",
        )

    df = pd.read_csv(path)

    # Key demand columns (kWh)
    demand_cols = {
        "QH_sys_MWhyr": "Heating demand",
        "QC_sys_MWhyr": "Cooling demand",
        "Qhs_sys_MWhyr": "Space heating",
        "Qcs_sys_MWhyr": "Space cooling",
        "Qww_sys_MWhyr": "Hot water",
        "E_sys_MWhyr": "Electricity",
    }

    kpis = []
    for col, label in demand_cols.items():
        if col in df.columns:
            total = float(df[col].sum())
            kpis.append({
                "key": col,
                "label": label,
                "value": round(total, 2),
                "unit": "MWh/yr",
            })

    # GFA and EUI
    if "GFA_m2" in df.columns:
        total_gfa = float(df["GFA_m2"].sum())
        kpis.append({
            "key": "GFA_m2",
            "label": "Gross floor area",
            "value": round(total_gfa, 1),
            "unit": "m\u00b2",
        })

        # EUI = total energy / GFA
        energy_col = "E_sys_MWhyr"
        if energy_col in df.columns and total_gfa > 0:
            total_energy = float(df[energy_col].sum())
            eui = total_energy * 1000 / total_gfa  # kWh/m2/yr
            kpis.append({
                "key": "EUI_kWhm2yr",
                "label": "Energy use intensity",
                "value": round(eui, 1),
                "unit": "kWh/m\u00b2/yr",
            })

    return {
        "feature": "demand",
        "building_count": len(df),
        "kpis": kpis,
    }


def _final_energy_summary(locator, whatif_name):
    """Compute final-energy KPIs from final_energy_buildings.csv."""
    path = locator.get_final_energy_buildings_file(whatif_name)
    if not os.path.isfile(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Final energy results not found for what-if '{whatif_name}'.",
        )

    df = pd.read_csv(path)

    # Sum all numeric columns except 'name' and 'type'
    kpis = []
    # Key columns from final_energy_buildings.csv
    carrier_cols = [c for c in df.columns if c.endswith("_MWhyr")]
    for col in carrier_cols:
        total = float(df[col].sum())
        label = col.replace("_MWhyr", "").replace("_", " ")
        kpis.append({
            "key": col,
            "label": label,
            "value": round(total, 2),
            "unit": "MWh/yr",
        })

    building_rows = df[df["type"] == "building"] if "type" in df.columns else df
    plant_rows = df[df["type"] == "plant"] if "type" in df.columns else pd.DataFrame()

    return {
        "feature": "final-energy",
        "whatif_name": whatif_name,
        "building_count": len(building_rows),
        "plant_count": len(plant_rows),
        "kpis": kpis,
    }


def _costs_summary(locator, whatif_name):
    """Compute cost KPIs from costs_buildings.csv."""
    path = locator.get_costs_whatif_buildings_file(whatif_name)
    if not os.path.isfile(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cost results not found for what-if '{whatif_name}'.",
        )

    df = pd.read_csv(path)

    kpis = []
    cost_cols = [c for c in df.columns if c.endswith("_USD")]
    for col in cost_cols:
        total = float(df[col].sum())
        label = col.replace("_USD", "").replace("_", " ")
        kpis.append({
            "key": col,
            "label": label,
            "value": round(total, 2),
            "unit": "USD",
        })

    return {
        "feature": "costs",
        "whatif_name": whatif_name,
        "building_count": len(df),
        "kpis": kpis,
    }


def _emissions_summary(locator, whatif_name):
    """Compute emissions KPIs from emissions_buildings.csv."""
    path = locator.get_emissions_whatif_buildings_file(whatif_name)
    if not os.path.isfile(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emissions results not found for what-if '{whatif_name}'.",
        )

    df = pd.read_csv(path)

    kpis = []
    emissions_cols = [c for c in df.columns if "CO2" in c or "co2" in c.lower() or c.endswith("_tonyr") or c.endswith("_kgyr")]
    for col in emissions_cols:
        total = float(df[col].sum())
        label = col.replace("_tonyr", "").replace("_kgyr", "").replace("_", " ")
        unit = "ton/yr" if col.endswith("_tonyr") else "kg/yr"
        kpis.append({
            "key": col,
            "label": label,
            "value": round(total, 2),
            "unit": unit,
        })

    return {
        "feature": "emissions",
        "whatif_name": whatif_name,
        "building_count": len(df),
        "kpis": kpis,
    }


def _heat_summary(locator, whatif_name):
    """Compute heat rejection KPIs from heat_rejection_buildings.csv."""
    path = locator.get_heat_rejection_whatif_buildings_file(whatif_name)
    if not os.path.isfile(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Heat rejection results not found for what-if '{whatif_name}'.",
        )

    df = pd.read_csv(path)

    kpis = []
    heat_cols = [c for c in df.columns if c.endswith("_MWhyr") or c.endswith("_kWhyr")]
    for col in heat_cols:
        total = float(df[col].sum())
        label = col.replace("_MWhyr", "").replace("_kWhyr", "").replace("_", " ")
        unit = "MWh/yr" if col.endswith("_MWhyr") else "kWh/yr"
        kpis.append({
            "key": col,
            "label": label,
            "value": round(total, 2),
            "unit": unit,
        })

    return {
        "feature": "heat-rejection",
        "whatif_name": whatif_name,
        "building_count": len(df),
        "kpis": kpis,
    }


FEATURE_SUMMARY_MAP = {
    "demand": lambda locator, _wn: _demand_summary(locator),
    "final-energy": _final_energy_summary,
    "costs": _costs_summary,
    "emissions": _emissions_summary,
    "heat-rejection": _heat_summary,
}

SUPPORTED_FEATURES = list(FEATURE_SUMMARY_MAP.keys())


@router.get("/summary")
async def get_summary(
    scenario: CEAScenario,
    feature: str,
    whatif: Optional[str] = None,
):
    """Return KPI summary for a scenario + feature (+ optional what-if)."""
    if feature not in FEATURE_SUMMARY_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported feature: {feature}. Supported: {SUPPORTED_FEATURES}",
        )

    locator = cea.inputlocator.InputLocator(scenario)

    summary_fn = FEATURE_SUMMARY_MAP[feature]
    return summary_fn(locator, whatif)


@router.get("/plot", response_class=HTMLResponse)
async def get_report_plot(
    config: CEAConfig,
    scenario: CEAScenario,
    feature: str,
    whatif: Optional[str] = None,
):
    """Generate a plot HTML div for a specific scenario + feature + what-if.

    Uses the existing plot_main infrastructure with a temporary config override.
    """
    from cea.visualisation.plot_main import plot_all

    scenario_path = scenario

    # Feature-to-plot-section mapping
    feature_map = {
        "demand": "demand",
        "final-energy": "energy-by-carrier",
        "costs": "cost-breakdown",
        "emissions": "operational-emissions",
        "heat-rejection": "heat",
    }

    plot_feature = feature_map.get(feature)
    if plot_feature is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported plot feature: {feature}",
        )

    # Build context dict for plot_all
    context = {"feature": plot_feature}

    config.project = os.path.dirname(scenario_path)
    config.scenario_name = os.path.basename(scenario_path)

    try:
        whatif_override = [whatif] if whatif else None
        fig = plot_all(config, scenario_path, context, hide_title=False,
                       whatif_names_override=whatif_override)
        fig.update_layout(autosize=True)
        html = fig.to_html(full_html=False, include_plotlyjs="cdn",
                           config={"responsive": True})
        return HTMLResponse(html, 200)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Missing data for plot: {e}",
        )
    except Exception as e:
        logger.error("Error generating report plot: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating plot: {e}",
        )


@router.post("/plot-custom", response_class=HTMLResponse)
async def get_custom_plot(
    config: CEAConfig,
    effective_scenario: CEAScenario,
    payload: dict,
):
    """Render a plot using the visualisation system with custom parameters.

    Accepts { script, parameters, scenario } and returns HTML div.
    The script must be a valid visualisation tool name (e.g. plot-demand).
    Parameters are applied to the config before running the plot.
    """
    script_name = payload.get("script")
    parameters = payload.get("parameters", {})
    scenario = payload.get("scenario")
    # Optional human-readable feature label derived from the
    # frontend's `PLOT_GROUPS` nesting (e.g. "Energy by Carrier").
    # Used in the styled mismatch overlay so the user sees the
    # familiar feature name instead of the CLI tool's `script_name`
    # — which is meaningless to non-developers.
    feature_label = payload.get("feature_label")

    if not script_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="script is required",
        )

    # Validate the script exists up-front so we can return a clean
    # 400 before mutating the config.
    try:
        cea.scripts.by_name(script_name, plugins=config.plugins)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Script not found: {script_name}",
        )

    if scenario:
        if not isinstance(scenario, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="scenario must be a string",
            )
        # Resolve the payload scenario against the project directory of the
        # effective scenario (from headers or config). Supports bare names and
        # relative sub-paths (e.g. canvas pathway-single child states).
        project_path = os.path.dirname(effective_scenario)
        scenario_path = secure_join_under_root(
            project_path, validate_scenario_name_or_subpath(scenario)
        )
        if not os.path.isdir(scenario_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Scenario not found: {scenario}",
            )
    else:
        scenario_path = effective_scenario

    try:
        html = render_plot_html(
            config,
            scenario_path=scenario_path,
            script_name=script_name,
            parameters=parameters,
            feature_label=feature_label,
        )
        return HTMLResponse(html, 200)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Missing data for plot: {e}",
        )
    except ValueError as e:
        # A required parameter (typically `what-if-name`) was missing
        # or empty. Happens when a comparison column's per-column
        # plotConfig has reset the parameter to `[]` because origin's
        # selection isn't in the column's `/choices`. Surface the
        # styled mismatch overlay instead of the generic 500 fallback,
        # using the column's available what-if-names as substitutes.
        from cea.visualisation.special._error_html import (
            whatif_mismatch_html,
        )
        logger.warning(
            "plot-custom rejected required parameter (%s); returning styled overlay",
            e,
        )
        # Frontend supplies the human-readable feature label from
        # its `PLOT_GROUPS` (e.g. "Energy by Carrier"). Falls back
        # to the script name if the client didn't send one.
        tool = feature_label or script_name or 'the upstream tool'
        scenario_name = os.path.basename(scenario_path)
        requested = (parameters or {}).get('what-if-name')
        if isinstance(requested, list):
            missing = requested[0] if requested else ''
        else:
            missing = requested or ''
        # No predicate at this layer — the dispatcher doesn't know
        # which per-script "is this what-if valid" check to apply,
        # so it lists every folder and lets the user pick.
        from cea.visualisation.special._error_html import (
            list_available_whatif_names,
        )
        available = list_available_whatif_names(
            cea.inputlocator.InputLocator(scenario_path),
        )
        return HTMLResponse(
            whatif_mismatch_html(
                scenario_name=scenario_name,
                whatif_name=missing or '(none selected)',
                label='Plot',
                tool=tool,
                available=available,
            ),
            200,
        )
    except Exception as e:
        logger.error("Error generating custom plot: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating plot: {e}",
        )


# TODO: Remove get_zone_geojson — duplicates GET /api/inputs/geojson/zone which already serves
#       zone geometry via CEAScenario. Frontend should call that endpoint instead.
@router.get("/zone-geojson")
async def get_zone_geojson(scenario: CEAScenario):
    """Return zone geometry as GeoJSON for map thumbnail rendering."""
    locator = cea.inputlocator.InputLocator(scenario)
    zone_path = locator.get_zone_geometry()

    if not os.path.isfile(zone_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone geometry not found for this scenario.",
        )

    try:
        gdf = geopandas.read_file(zone_path).to_crs(get_geographic_coordinate_system())
        return JSONResponse(content=gdf.__geo_interface__, media_type="application/json")
    except Exception as e:
        logger.error("Error reading zone geometry: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading zone geometry: {e}",
        )


@router.get("/features")
async def get_features():
    """List supported features for reports."""
    feature_labels = {
        "demand": "Building Energy Demand",
        "final-energy": "Energy by Carrier",
        "costs": "Cost Breakdown",
        "emissions": "Operational Emissions",
        "heat-rejection": "Anthropogenic Heat Rejection",
    }
    return {
        "features": [
            {"key": k, "label": v}
            for k, v in feature_labels.items()
        ]
    }
