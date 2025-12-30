from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any, cast

import os

import geopandas as gpd
import numpy as np
import pandas as pd

from cea.config import Configuration
from cea.inputlocator import InputLocator
from cea.analysis.lca.hourly_operational_emission import _tech_name_mapping
from cea.analysis.lca.emission_timeline import (
    TIMELINE_COMPONENTS as _TIMELINE_COMPONENTS,
    BaseEmissionTimeline as _BaseEmissionTimeline,
    phase_component_col as _phase_component_col,
    aggregate_operational_by_demand as _aggregate_operational_by_demand,
    apply_feedstock_policies_inplace as _apply_feedstock_policies_inplace,
    apply_pv_offset_decarbonisation_inplace as _apply_pv_offset_decarbonisation_inplace,
)
from cea.datamanagement.database.envelope_lookup import EnvelopeLookup
from cea.demand.building_properties import BuildingProperties
from cea.utilities import epwreader
from cea.datamanagement.district_level_states.timeline_years import (
    ensure_state_years_exist,
    get_building_construction_years,
    get_required_state_years,
    reconcile_states_to_cumulative_modifications,
)


_COMP_AREA_MAP: list[tuple[str, str, str]] = [
    ("wall_ag", "wall", "Awall_ag"),
    ("roof", "roof", "Aroof"),
    ("base", "base", "Abase"),
    ("underside", "base", "Aunderside"),
    ("wall_bg", "base", "Awall_bg"),
]


@dataclass(frozen=True)
class MaterialLayer:
    name: str
    thickness_m: float


class MaterialChangeEmissionTimeline(_BaseEmissionTimeline):
    """Building-level *event* timeline driven by the district YAML log."""

    def __init__(self, *, name: str, timeline: pd.DataFrame):
        self.name = name
        self.construction_year: int | None = None
        self.demolition_year: int | None = None
        super().__init__(timeline)

    def set_existence(self, *, construction_year: int, demolition_year: int | None) -> None:
        self.construction_year = int(construction_year)
        self.demolition_year = int(demolition_year) if demolition_year is not None else None

    def exists_at(self, year: int) -> bool:
        if self.construction_year is None:
            return False
        if year < self.construction_year:
            return False
        if self.demolition_year is not None and year >= self.demolition_year:
            return False
        return True

    @staticmethod
    def layers_snapshot_at_or_before(
        layers_by_year: Mapping[int, dict[str, dict[str, list[MaterialLayer] | None]]],
        years_sorted: list[int],
        year: int,
    ) -> dict[str, dict[str, list[MaterialLayer] | None]] | None:
        if year in layers_by_year:
            return layers_by_year.get(year)
        prior_years = [y for y in years_sorted if y <= year]
        if not prior_years:
            return None
        return layers_by_year.get(prior_years[-1])

    def fill_operational_step_function(
        self,
        *,
        years_sorted: list[int],
        end_year: int,
        operational_by_state_year: Mapping[int, pd.DataFrame | None],
        allow_missing_operational: bool,
        feedstock_policies: Mapping[str, tuple[int, int, float]] | None,
    ) -> None:
        """Fill `operation_*_kgCO2e` between available state years.

        Source of truth is the per-state-year operational-by-building output (from the `emissions` script).
        This method:
        - selects the latest known per-building *per-demand/per-feedstock* emissions for each state year
        - carries them forward until the next state year (step function on demand / technology)
        - applies any configured `feedstock_policies` (e.g., GRID decarbonisation) per timeline year

        Operational is set to 0 for years before construction, and for years >= demolition (if any).
        """
        if self.construction_year is None:
            return
        construction_year = self.construction_year
        demolition_year = self.demolition_year

        last_known: pd.Series | None = None
        for i, state_year in enumerate(years_sorted):
            df_op = operational_by_state_year.get(state_year)
            if df_op is not None and self.name in df_op.index:
                cols_in = _operational_factor_columns(df_op)
                series = df_op.loc[[self.name], cols_in].iloc[0] if cols_in else pd.Series(dtype=float)
                last_known = series
            else:
                if allow_missing_operational and last_known is not None:
                    series = last_known
                else:
                    series = pd.Series(dtype=float)

            next_state_year = years_sorted[i + 1] if i + 1 < len(years_sorted) else (end_year + 1)
            interval_years = [
                y
                for y in range(state_year, min(next_state_year, end_year + 1))
                if y >= construction_year and (demolition_year is None or y < demolition_year)
            ]
            if not interval_years:
                continue

            idx_interval = [f"Y_{y}" for y in interval_years]
            operational_multi_years = pd.DataFrame(index=idx_interval)
            for c in series.index:
                operational_multi_years[c] = float(series.get(c, 0.0))

            if feedstock_policies:
                demand_types = list(_tech_name_mapping.keys())
                feedstocks = _extract_feedstocks_from_columns(operational_multi_years.columns, demand_types=demand_types)
                _apply_feedstock_policies_inplace(
                    operational_multi_years,
                    index=operational_multi_years.index,
                    feedstock_policies=feedstock_policies,
                    feedstocks=feedstocks,
                    demand_types=demand_types,
                )
                _apply_pv_offset_decarbonisation_inplace(
                    operational_multi_years,
                    index=operational_multi_years.index,
                    feedstock_policies=feedstock_policies,
                )

            out = _aggregate_operational_by_demand(
                operational_multi_years,
                index=operational_multi_years.index,
                demand_types=list(_tech_name_mapping.keys()),
            )
            for d in _tech_name_mapping.keys():
                col = f"operation_{d}_kgCO2e"
                self.timeline.loc[idx_interval, col] = out[col].to_numpy(dtype=float)

    def build_embodied_from_log(
        self,
        *,
        const_type: str,
        areas: dict[str, float],
        materials: pd.DataFrame,
        years_sorted: list[int],
        start_year: int,
        end_year: int,
        archetype_layers_at_year: Mapping[int, dict[str, dict[str, list[MaterialLayer] | None]]],
        archetype_events_by_year: Mapping[int, dict[str, dict[str, list[tuple[str, MaterialLayer]]]]],
        service_life_by_src_component: Mapping[str, int | None],
    ) -> None:
        if self.construction_year is None:
            return
        construction_year = self.construction_year

        layers_snapshot = self.layers_snapshot_at_or_before(archetype_layers_at_year, years_sorted, construction_year)
        if layers_snapshot is None:
            return
        self.add_initial_construction(
            year=construction_year,
            const_type=const_type,
            areas=areas,
            materials=materials,
            layers_snapshot=layers_snapshot,
            comp_area_map=_COMP_AREA_MAP,
        )

        # --- Mandatory service-life replacements ---------------------------------
        # Behaviour:
        # - Each envelope component has a service life (years) from the envelope DB.
        # - Starting from construction, a full replacement is scheduled every service_life years.
        # - Any modification event to that component resets its replacement clock (but does not force a full
        #   replacement in that year; only the logged delta is applied).
        end_active_year = end_year
        if self.demolition_year is not None:
            end_active_year = min(end_active_year, self.demolition_year - 1)
        if end_active_year < construction_year:
            return

        areas_by_src_component: dict[str, float] = {}
        for _, comp_src, area_key in _COMP_AREA_MAP:
            areas_by_src_component[comp_src] = areas_by_src_component.get(comp_src, 0.0) + float(areas.get(area_key, 0.0))

        lifetimes: dict[str, int] = {}
        for src_component, total_area in areas_by_src_component.items():
            if total_area <= 0:
                continue
            lifetime_any = service_life_by_src_component.get(src_component)
            if lifetime_any is None:
                raise ValueError(
                    f"Missing Service_Life for component '{src_component}' (const_type={const_type}). "
                    "Service life is mandatory for the district material timeline replacement scheduling."
                )
            lifetime = int(lifetime_any)
            if lifetime <= 0:
                raise ValueError(
                    f"Invalid Service_Life={lifetime} for component '{src_component}' (const_type={const_type})."
                )
            lifetimes[src_component] = lifetime

        modification_years: list[int] = [
            y
            for y in years_sorted
            if self.exists_at(y)
            and const_type in (archetype_events_by_year.get(y, {}) or {})
        ]
        mod_by_year: dict[int, dict[str, list[tuple[str, MaterialLayer]]]] = {}
        for y in modification_years:
            year_events = archetype_events_by_year.get(y, {}) or {}
            mod_by_year[y] = dict(year_events.get(const_type, {}) or {})

        # Track the next replacement year per component.
        next_due: dict[str, int] = {src: construction_year + lt for src, lt in lifetimes.items()}
        mod_idx = 0
        while True:
            next_mod_year = modification_years[mod_idx] if mod_idx < len(modification_years) else None
            next_rep_year = min(next_due.values()) if next_due else None
            if next_mod_year is None and next_rep_year is None:
                break
            candidates = [y for y in (next_mod_year, next_rep_year) if y is not None]
            year = min(candidates) if candidates else None
            if year is None or year > end_active_year:
                break

            # Apply any modifications first (they reset the clock).
            if next_mod_year == year:
                year_mods = mod_by_year.get(year, {})
                for src_component, events in year_mods.items():
                    self.add_modification_events(
                        year=year,
                        events=events,
                        src_component=src_component,
                        areas=areas,
                        materials=materials,
                        comp_area_map=_COMP_AREA_MAP,
                    )
                    if src_component in lifetimes:
                        next_due[src_component] = year + lifetimes[src_component]
                mod_idx += 1

            # Apply any replacements due this year (after modifications, so same-year mods supersede them).
            due_components = [src for src, due in next_due.items() if due == year]
            if due_components:
                layers_snapshot = self.layers_snapshot_at_or_before(archetype_layers_at_year, years_sorted, year)
                if layers_snapshot is not None:
                    current_layers = layers_snapshot.get(const_type, {})
                    for src_component in due_components:
                        layers = current_layers.get(src_component)
                        if layers:
                            self.add_full_replacement(
                                year=year,
                                src_component=src_component,
                                areas=areas,
                                materials=materials,
                                layers=layers,
                                comp_area_map=_COMP_AREA_MAP,
                            )
                        next_due[src_component] = year + lifetimes[src_component]

        if self.demolition_year is not None and start_year <= self.demolition_year <= end_year:
            layers_snapshot = self.layers_snapshot_at_or_before(
                archetype_layers_at_year, years_sorted, self.demolition_year
            )
            if layers_snapshot is None:
                return
            self.add_demolition(
                year=self.demolition_year,
                const_type=const_type,
                areas=areas,
                materials=materials,
                layers_snapshot=layers_snapshot,
                comp_area_map=_COMP_AREA_MAP,
            )

    def add_full_replacement(
        self,
        *,
        year: int,
        src_component: str,
        areas: dict[str, float],
        materials: pd.DataFrame,
        layers: list[MaterialLayer],
        comp_area_map: list[tuple[str, str, str]],
    ) -> None:
        """Log a full replacement of the given component (demolish old + rebuild same).

        Biogenic uptake/release is logged in the same year (net may be ~0 if identical materials).
        """
        for comp, comp_src, area_key in comp_area_map:
            if comp_src != src_component:
                continue
            area = float(areas.get(area_key, 0.0))
            if area <= 0:
                continue
            for layer in layers:
                prod, demo, bio = _material_intensity_per_m2(materials, layer)
                # Demolish old
                self.add_phase_component(year=year, phase="demolition", component=comp, value_kgco2e=demo * area)
                self.add_phase_component(year=year, phase="biogenic", component=comp, value_kgco2e=(+bio) * area)
                # Build new
                self.add_phase_component(year=year, phase="production", component=comp, value_kgco2e=prod * area)
                self.add_phase_component(year=year, phase="biogenic", component=comp, value_kgco2e=(-bio) * area)
    def add_initial_construction(
        self,
        *,
        year: int,
        const_type: str,
        areas: dict[str, float],
        materials: pd.DataFrame,
        layers_snapshot: dict[str, dict[str, list[MaterialLayer] | None]],
        comp_area_map: list[tuple[str, str, str]],
    ) -> None:
        current_layers = layers_snapshot.get(const_type, {})
        for comp, src_component, area_key in comp_area_map:
            area = float(areas.get(area_key, 0.0))
            if area <= 0:
                continue
            layers = current_layers.get(src_component)
            for _, layer in _diff_layers(None, layers):
                prod, _, bio = _material_intensity_per_m2(materials, layer)
                self.add_phase_component(year=year, phase="production", component=comp, value_kgco2e=prod * area)
                self.add_phase_component(year=year, phase="biogenic", component=comp, value_kgco2e=(-bio) * area)

    def add_modification_events(
        self,
        *,
        year: int,
        events: list[tuple[str, MaterialLayer]],
        src_component: str,
        areas: dict[str, float],
        materials: pd.DataFrame,
        comp_area_map: list[tuple[str, str, str]],
    ) -> None:
        for comp, comp_src, area_key in comp_area_map:
            if comp_src != src_component:
                continue
            area = float(areas.get(area_key, 0.0))
            if area <= 0:
                continue
            for action, layer in events:
                prod, demo, bio = _material_intensity_per_m2(materials, layer)
                if action == "add":
                    self.add_phase_component(year=year, phase="production", component=comp, value_kgco2e=prod * area)
                    self.add_phase_component(year=year, phase="biogenic", component=comp, value_kgco2e=(-bio) * area)
                else:
                    self.add_phase_component(year=year, phase="demolition", component=comp, value_kgco2e=demo * area)
                    self.add_phase_component(year=year, phase="biogenic", component=comp, value_kgco2e=(+bio) * area)

    def add_demolition(
        self,
        *,
        year: int,
        const_type: str,
        areas: dict[str, float],
        materials: pd.DataFrame,
        layers_snapshot: dict[str, dict[str, list[MaterialLayer] | None]],
        comp_area_map: list[tuple[str, str, str]],
    ) -> None:
        current_layers = layers_snapshot.get(const_type, {})
        for comp, src_component, area_key in comp_area_map:
            area = float(areas.get(area_key, 0.0))
            if area <= 0:
                continue
            layers = current_layers.get(src_component)
            for _, layer in _diff_layers(None, layers):
                _, demo, bio = _material_intensity_per_m2(materials, layer)
                self.add_phase_component(year=year, phase="demolition", component=comp, value_kgco2e=demo * area)
                self.add_phase_component(year=year, phase="biogenic", component=comp, value_kgco2e=(+bio) * area)


def _load_building_const_types(locator: InputLocator) -> dict[str, str]:
    """Return {building_name: const_type} from `zone.shp`.

    The `district_timeline_log.yml` stores modifications keyed by archetype / construction standard
    (e.g., `STANDARD1`). Buildings map to those standards via the `const_type` attribute.
    """
    zone = gpd.read_file(locator.get_zone_geometry())
    if "name" not in zone.columns:
        raise ValueError("Zone geometry is missing required 'name' column.")
    if "const_type" not in zone.columns:
        raise ValueError("Zone geometry is missing required 'const_type' column.")

    out: dict[str, str] = {}
    for _, row in zone.iterrows():
        name = str(row["name"])
        const_type = row["const_type"]
        if const_type is None or (isinstance(const_type, float) and np.isnan(const_type)):
            continue
        out[name] = str(const_type)
    return out


def _building_demolition_years(log_data: dict[int, dict[str, Any]]) -> dict[str, int]:
    """Return {building_name: demolition_year} from YAML building_events."""
    out: dict[str, int] = {}
    for year in sorted(int(y) for y in log_data.keys()):
        entry = log_data.get(year, {}) or {}
        events = entry.get("building_events", {}) or {}
        demolished = events.get("demolished_buildings", []) or []
        for b in demolished:
            name = str(b)
            out.setdefault(name, int(year))
    return out


def _apply_layer_patch(
    old_layers: list[MaterialLayer] | None,
    patch: dict[str, Any],
) -> list[MaterialLayer] | None:
    """Apply a YAML layer patch (material_name_i / thickness_i_m) to a layer list.

    Patch semantics:
    - Updates only the specified fields.
    - Unspecified slots are carried forward.
    - Slots are 1..3.
    """
    old_layers = old_layers or []
    # Start from an editable (name, thickness) list for slots 1..3
    slots: list[tuple[str | None, float | None]] = []
    for i in range(3):
        if i < len(old_layers):
            slots.append((old_layers[i].name, float(old_layers[i].thickness_m)))
        else:
            slots.append((None, None))

    for i in (1, 2, 3):
        m_key = f"material_name_{i}"
        t_key = f"thickness_{i}_m"
        name, thickness = slots[i - 1]
        if m_key in patch:
            raw = patch.get(m_key)
            if raw is None or (isinstance(raw, float) and np.isnan(raw)):
                name = None
            else:
                name = str(raw).strip() or None
        if t_key in patch:
            raw = patch.get(t_key)
            if raw is None or (isinstance(raw, float) and np.isnan(raw)):
                thickness = None
            else:
                thickness = float(raw)
        slots[i - 1] = (name, thickness)

    new_layers: list[MaterialLayer] = []
    for name, thickness in slots:
        if name is None or thickness is None:
            continue
        if thickness <= 0:
            continue
        new_layers.append(MaterialLayer(name=name, thickness_m=float(thickness)))
    return new_layers


def _parse_density(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s or s == "-":
        return None
    # Handle ranges like '1200-2000'
    if "-" in s and all(p.strip().replace(".", "", 1).isdigit() for p in s.split("-")):
        lo, hi = s.split("-", 1)
        return 0.5 * (float(lo) + float(hi))
    try:
        return float(s)
    except Exception:
        return None


def _to_float(value: Any, default: float = 0.0) -> float:
    """Convert a value to float with defensive handling for pandas artefacts.

    Note:
        This function may call itself when `value` is a `pd.Series`. That is deliberate:
        it unwraps the first element (`value.iloc[0]`) and then re-applies the same
        conversion rules to the scalar (None/NaN/str/number). This is not unbounded
        recursion because the second call is typically on a non-Series value.
    """
    if value is None:
        return float(default)
    # pandas often yields NaN floats
    if isinstance(value, float) and np.isnan(value):
        return float(default)
    # guard against accidental Series
    if isinstance(value, pd.Series):
        if len(value) == 0:
            return float(default)
        # Intentional re-entry: unwrap the Series to a scalar and re-apply rules.
        return _to_float(value.iloc[0], default=default)
    try:
        return float(value)
    except Exception:
        return float(default)


def _read_material_db(locator: InputLocator) -> pd.DataFrame:
    path = locator.get_database_components_materials()
    if not os.path.exists(path):
        raise FileNotFoundError(f"Materials database not found: {path}")
    df = pd.read_csv(path)
    if "name" not in df.columns:
        raise ValueError("Materials database missing required 'name' column")
    return df.set_index("name", drop=False)


def _layers_from_envelope_row(row: pd.Series) -> list[MaterialLayer]:
    layers: list[MaterialLayer] = []
    for i in (1, 2, 3):
        material = row.get(f"material_name_{i}")
        thickness = row.get(f"thickness_{i}_m")
        if material is None or (isinstance(material, float) and np.isnan(material)):
            continue
        if thickness is None or (isinstance(thickness, float) and np.isnan(thickness)):
            continue
        name = str(material).strip()
        if not name:
            continue
        thickness = float(thickness)
        layers.append(MaterialLayer(name=name, thickness_m=thickness))
    return layers


def _get_component_layers(
    env: EnvelopeLookup,
    *,
    db_name: str,
    code: str,
) -> list[MaterialLayer] | None:
    df = getattr(env.envelope, db_name)
    if df is None:
        return None
    if code not in df.index:
        raise ValueError(f"Envelope code '{code}' not found in DB '{db_name}'.")
    row = df.loc[code]
    required = {"material_name_1", "thickness_1_m"}
    if not required.issubset(set(df.columns)):
        return None
    return _layers_from_envelope_row(row)


def _material_intensity_per_m2(materials: pd.DataFrame, layer: MaterialLayer) -> tuple[float, float, float]:
    if layer.name not in materials.index:
        raise ValueError(f"Material '{layer.name}' not found in MATERIALS.csv")
    rec = materials.loc[layer.name]
    unit = str(rec.get("unit", "")).strip().lower()
    if unit != "kg":
        raise ValueError(
            f"Material '{layer.name}' has unit '{rec.get('unit')}', expected 'kg' for layered constructions."
        )

    density = _parse_density(rec.get("density"))
    if density is None or density <= 0:
        raise ValueError(f"Material '{layer.name}' has invalid density: {rec.get('density')}")

    mass_per_m2 = density * float(layer.thickness_m)

    prod = _to_float(rec.get("GHG_emission_production"), default=0.0) * mass_per_m2
    demo = _to_float(rec.get("GHG_emission_recycling"), default=0.0) * mass_per_m2
    bio = _to_float(rec.get("biogenic_carbon_in_product"), default=0.0) * mass_per_m2
    return prod, demo, bio


def _diff_layers(old_layers: list[MaterialLayer] | None, new_layers: list[MaterialLayer] | None) -> list[tuple[str, MaterialLayer]]:
    """Return event list of ('remove'|'add', layer) comparing per-position (1..3) definitions.

    We intentionally diff *by layer slot* to match how envelope definitions are authored:
    changing thickness or material in a slot implies replacement of that slot.
    """
    old_layers = old_layers or []
    new_layers = new_layers or []

    # Compare by index
    events: list[tuple[str, MaterialLayer]] = []
    for idx in range(max(len(old_layers), len(new_layers))):
        old_layer = old_layers[idx] if idx < len(old_layers) else None
        new_layer = new_layers[idx] if idx < len(new_layers) else None
        if old_layer is None and new_layer is None:
            continue
        if old_layer is None and new_layer is not None:
            events.append(("add", new_layer))
            continue
        if old_layer is not None and new_layer is None:
            events.append(("remove", old_layer))
            continue
        assert old_layer is not None and new_layer is not None
        if old_layer.name != new_layer.name or abs(old_layer.thickness_m - new_layer.thickness_m) > 1e-9:
            events.append(("remove", old_layer))
            events.append(("add", new_layer))
    return events


def _surface_areas(building_properties: BuildingProperties, building_name: str) -> dict[str, float]:
    bpr_rc = building_properties.rc_model[building_name]
    bpr_env = building_properties.envelope[building_name]
    geom = building_properties.geometry[building_name]

    areas: dict[str, float] = {}
    areas["Awall_ag"] = float(bpr_env["Awall_ag"])
    areas["Aroof"] = float(bpr_env["Aroof"])
    areas["Awin_ag"] = float(bpr_env.get("Awin_ag", 0.0))
    areas["Awall_bg"] = float(geom["perimeter"]) * float(geom["height_bg"])
    areas["Aunderside"] = float(bpr_env.get("Aunderside", 0.0))

    if geom["floors_bg"] == 0 and geom.get("void_deck", 0) > 0:
        area_base = 0.0
    else:
        area_base = float(bpr_rc["footprint"])

    areas["Abase"] = area_base
    return areas


def _load_state_building_properties(locator: InputLocator, buildings: list[str]) -> BuildingProperties:
    weather_path = locator.get_weather_file()
    weather_data = epwreader.epw_reader(weather_path)[
        ["year", "drybulb_C", "wetbulb_C", "relhum_percent", "windspd_ms", "skytemp_C"]
    ]
    return BuildingProperties(locator, weather_data, buildings)


def _operational_factor_columns(df: pd.DataFrame) -> list[str]:
    """Return per-demand/per-feedstock and PV offset columns suitable for policy scaling.

    These columns are treated as emissions already attributed to a feedstock (e.g., `E_sys_GRID_kgCO2e`).
    If decarbonisation policies are configured, these are scaled per timeline year.
    """
    demand_types = list(_tech_name_mapping.keys())
    cols: list[str] = []
    for c in df.columns:
        if not (isinstance(c, str) and c.endswith("_kgCO2e")):
            continue
        # Keep per-demand/per-feedstock columns like `Qhs_sys_GRID_kgCO2e`
        if any(c.startswith(f"{d}_") for d in demand_types) and c.count("_") >= 3:
            cols.append(c)
            continue
        # Keep PV emission offset columns if present (these are also scaled if GRID is decarbonised)
        if c.startswith("PV_"):
            cols.append(c)
            continue
    return cols


def _extract_feedstocks_from_columns(columns: pd.Index, *, demand_types: list[str]) -> list[str]:
    """Extract feedstock tokens from per-demand/per-feedstock emission columns."""
    feedstocks: set[str] = set()
    for c in columns:
        if not isinstance(c, str):
            continue
        if not c.endswith("_kgCO2e"):
            continue
        for d in demand_types:
            prefix = f"{d}_"
            if not c.startswith(prefix):
                continue
            # expect `{demand}_{feedstock}_kgCO2e`
            tail = c[len(prefix) :]
            if tail.endswith("_kgCO2e"):
                feedstock = tail[: -len("_kgCO2e")]
                if feedstock:
                    feedstocks.add(feedstock)
    feedstocks.add("NONE")
    return sorted(feedstocks)


def _feedstock_policies_from_config(config: Configuration) -> Mapping[str, tuple[int, int, float]] | None:
    emissions_cfg = config.emissions
    ref_yr = getattr(emissions_cfg, "grid_decarbonise_reference_year", None)
    tar_yr = getattr(emissions_cfg, "grid_decarbonise_target_year", None)
    tar_ef = getattr(emissions_cfg, "grid_decarbonise_target_emission_factor", None)

    if ref_yr is not None and tar_yr is not None and tar_ef is not None:
        return {"GRID": (int(ref_yr), int(tar_yr), float(tar_ef))}
    if ref_yr is None and tar_yr is None and tar_ef is None:
        return None
    raise ValueError(
        "If one of grid_decarbonise_reference_year, grid_decarbonise_target_year, "
        "or grid_decarbonise_target_emission_factor is set, all must be set."
    )


def create_district_material_timeline(
    config: Configuration,
    *,
    allow_missing_operational: bool = False,
) -> pd.DataFrame:
    """Create a district-level *event* emissions timeline driven by the YAML log.

        Key idea (mirrors the standard district emissions timeline):
        1) Generate a *building-level* event timeline for each building using:
             - the building's `const_type` (archetype / construction standard) from `zone.shp`
             - the per-year `modifications` in `district_timeline_log.yml` (assumed authoritative)
             - building birth / demolition events in `building_events`
        2) Aggregate to district level by summing all building timelines.

        Operational emissions are still sourced from state simulations (stepwise by state year),
        but embodied changes are attributed from the log (not by diffing state folders).

        Output:
        - Index is 'Y_YYYY'.
        - Columns include per-component/per-phase embodied columns (matching emissions timelines),
            plus `production_kgCO2e`, `demolition_kgCO2e`, `biogenic_kgCO2e`, and per-demand operational columns.

        Naming convention:
        - This function only outputs emission columns; all columns end with `_kgCO2e`.
        """

    main_locator = InputLocator(config.scenario)

    years = get_required_state_years(config)
    log_data = ensure_state_years_exist(config, years, update_yaml=True)
    reconcile_states_to_cumulative_modifications(config, years, log_data=log_data)

    # Determine overall year range
    start_year = min(years)
    year_end_val = getattr(config.emissions, "year_end", None)
    end_year = int(year_end_val) if year_end_val is not None else max(years)

    idx = [f"Y_{y}" for y in range(start_year, end_year + 1)]
    base_cols: list[str] = []
    for phase in ("production", "biogenic", "demolition"):
        for comp in _TIMELINE_COMPONENTS:
            base_cols.append(_phase_component_col(phase, comp))
    base_cols.extend(["production_kgCO2e", "demolition_kgCO2e", "biogenic_kgCO2e"])
    base_cols.extend([f"operation_{d}_kgCO2e" for d in _tech_name_mapping.keys()])

    def _empty_timeline() -> pd.DataFrame:
        df = pd.DataFrame(index=idx)
        df.index.name = "period"
        for c in base_cols:
            df[c] = 0.0
        return df

    out = _empty_timeline()

    years_sorted = sorted(years)
    feedstock_policies = _feedstock_policies_from_config(config)

    # Preflight: we require state outputs for this workflow.
    # - Radiation results are needed to compute surface areas via BuildingProperties.
    # - Operational-by-building results are needed for district operational step function.
    missing_radiation: dict[int, str] = {}
    missing_operational_years: list[int] = []

    for year in years_sorted:
        state_locator = InputLocator(main_locator.get_state_in_time_scenario_folder(year))
        buildings = list(state_locator.get_zone_building_names())
        if buildings:
            for b in buildings:
                rad_path = state_locator.get_radiation_building(b)
                if not os.path.exists(rad_path):
                    missing_radiation.setdefault(year, rad_path)
                    break
        op_path = state_locator.get_total_yearly_operational_building()
        if not os.path.exists(op_path):
            missing_operational_years.append(year)

    if missing_radiation:
        sample_lines = "\n".join(
            f"- {y}: missing {p}" for y, p in sorted(missing_radiation.items())
        )
        raise FileNotFoundError(
            "Some state years are missing solar-radiation outputs required for surface areas.\n"
            "Run the `state-simulations` script (includes Radiation) for all state years, then rerun this timeline.\n"
            "Missing examples:\n" + sample_lines
        )

    if missing_operational_years and not allow_missing_operational:
        years_str = ", ".join(map(str, sorted(set(missing_operational_years))))
        raise FileNotFoundError(
            "Missing operational-by-building results for some state years: "
            f"{years_str}.\n"
            "Run the `state-simulations` script (includes Emissions) to generate outputs for all state years, "
            "or call create_district_material_timeline(..., allow_missing_operational=True) for best-effort carry-forward."
        )

    # --- Inputs needed for per-building aggregation ---------------------------------
    building_construction_years = get_building_construction_years(main_locator)
    building_const_types = _load_building_const_types(main_locator)
    demolition_years = _building_demolition_years(log_data)

    # Cache areas per building (computed from BuildingProperties once the building exists in some state year).
    areas_by_building: dict[str, dict[str, float]] = {}

    # Cache per-state operational emissions by building (used for step function per building).
    operational_by_state_year: dict[int, pd.DataFrame] = {}

    for year in years_sorted:
        state_locator = InputLocator(main_locator.get_state_in_time_scenario_folder(year))
        buildings_in_state = list(state_locator.get_zone_building_names())
        if not buildings_in_state:
            continue

        # Operational-by-building results
        op_path = state_locator.get_total_yearly_operational_building()
        if os.path.exists(op_path):
            operational_by_state_year[year] = pd.read_csv(op_path, index_col="name")

        # Areas
        missing_area_buildings = [b for b in buildings_in_state if b not in areas_by_building]
        if missing_area_buildings:
            bp = _load_state_building_properties(state_locator, missing_area_buildings)
            for b in missing_area_buildings:
                areas_by_building[b] = _surface_areas(bp, b)

    # --- Archetype layer evolution from YAML log ------------------------------------
    # Baseline archetype codes come from the (main) construction types database.
    archetype_df = pd.read_csv(main_locator.get_database_archetypes_construction_type(), index_col="const_type")
    env_lookup = EnvelopeLookup.from_locator(main_locator)
    materials = _read_material_db(main_locator)

    # Track current layers per archetype and component (only for components we can resolve to materials).
    # Supported: wall -> envelope.wall, roof -> envelope.roof, base/floor -> envelope.floor
    supported_components = {"wall": "wall", "roof": "roof", "base": "floor", "floor": "floor"}
    archetypes_needed = sorted({v for v in building_const_types.values()})
    archetype_layers: dict[str, dict[str, list[MaterialLayer] | None]] = {}
    archetype_service_life: dict[str, dict[str, int | None]] = {}
    for archetype in archetypes_needed:
        if archetype not in archetype_df.index:
            raise ValueError(f"Archetype '{archetype}' not found in construction types database.")
        row = archetype_df.loc[archetype]
        code_wall = str(row.get("type_wall"))
        code_roof = str(row.get("type_roof"))
        code_base = str(row.get("type_base"))
        code_floor = str(row.get("type_floor"))
        archetype_layers[archetype] = {
            "wall": _get_component_layers(env_lookup, db_name="wall", code=code_wall),
            "roof": _get_component_layers(env_lookup, db_name="roof", code=code_roof),
            "base": _get_component_layers(env_lookup, db_name="floor", code=code_base),
            "floor": _get_component_layers(env_lookup, db_name="floor", code=code_floor),
        }
        archetype_service_life[archetype] = {
            "wall": cast(int | None, env_lookup.get_item_value(code_wall, "Service_Life")),
            "roof": cast(int | None, env_lookup.get_item_value(code_roof, "Service_Life")),
            "base": cast(int | None, env_lookup.get_item_value(code_base, "Service_Life")),
            "floor": cast(int | None, env_lookup.get_item_value(code_floor, "Service_Life")),
        }

    # For each state year, compute layer-change events per archetype/component.
    archetype_events_by_year: dict[int, dict[str, dict[str, list[tuple[str, MaterialLayer]]]]] = {}
    archetype_layers_at_year: dict[int, dict[str, dict[str, list[MaterialLayer] | None]]] = {}

    for year in years_sorted:
        entry = log_data.get(year, {}) or {}
        year_mods = entry.get("modifications", {}) or {}
        year_events: dict[str, dict[str, list[tuple[str, MaterialLayer]]]] = {}

        for archetype, components in year_mods.items():
            archetype = str(archetype)
            if archetype not in archetype_layers:
                continue
            for component, patch in (components or {}).items():
                component = str(component)
                if component not in supported_components:
                    raise ValueError(
                        f"Unsupported modified component '{component}' in district timeline log. "
                        f"Supported components: {sorted(supported_components.keys())}"
                    )
                old_layers = archetype_layers[archetype].get(component)
                new_layers = _apply_layer_patch(old_layers, patch or {})
                events = _diff_layers(old_layers, new_layers)
                if events:
                    year_events.setdefault(archetype, {})[component] = events
                archetype_layers[archetype][component] = new_layers

        archetype_events_by_year[year] = year_events
        # snapshot layers for this year (after applying modifications)
        archetype_layers_at_year[year] = {
            a: {c: (layers[:] if isinstance(layers, list) else layers) for c, layers in comps.items()}
            for a, comps in archetype_layers.items()
        }

    # --- Build per-building timelines, then sum -------------------------------------
    building_timelines: dict[str, MaterialChangeEmissionTimeline] = {}
    all_buildings = sorted(set(building_const_types.keys()) | set(building_construction_years.keys()))

    for b in all_buildings:
        tl_b = MaterialChangeEmissionTimeline(name=b, timeline=_empty_timeline())
        building_timelines[b] = tl_b

        c_year = building_construction_years.get(b)
        if c_year is None:
            continue
        if c_year < start_year or c_year > end_year:
            continue
        construction_year = int(c_year)
        d_year = demolition_years.get(b)

        tl_b.set_existence(construction_year=construction_year, demolition_year=d_year)

        # Operational emissions: only for years the building exists
        tl_b.fill_operational_step_function(
            years_sorted=years_sorted,
            end_year=end_year,
            operational_by_state_year=operational_by_state_year,
            allow_missing_operational=allow_missing_operational,
            feedstock_policies=feedstock_policies,
        )

        const_type = building_const_types.get(b)
        if const_type is None:
            continue

        areas = areas_by_building.get(b)
        if areas is None:
            # If the building never appears in any state year, we cannot compute its areas.
            continue

        tl_b.build_embodied_from_log(
            const_type=const_type,
            areas=areas,
            materials=materials,
            years_sorted=years_sorted,
            start_year=start_year,
            end_year=end_year,
            archetype_layers_at_year=archetype_layers_at_year,
            archetype_events_by_year=archetype_events_by_year,
            service_life_by_src_component=archetype_service_life.get(const_type, {}),
        )

    # Aggregate by summing all building timelines.
    for tl_b in building_timelines.values():
        out = out.add(tl_b.timeline, fill_value=0.0)

    # Convenience totals
    for label in out.index:
        out.at[label, "production_kgCO2e"] = float(out.filter(like="production_").loc[label].sum())
        out.at[label, "demolition_kgCO2e"] = float(out.filter(like="demolition_").loc[label].sum())
        out.at[label, "biogenic_kgCO2e"] = float(out.filter(like="biogenic_").loc[label].sum())

    # Persist under district timeline folder to avoid mixing with lifetime-based timelines.
    save_path = os.path.join(main_locator.get_district_timeline_states_folder(), "district_material_timeline.csv")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    try:
        out.to_csv(save_path, float_format="%.2f")
    except PermissionError as e:
        raise PermissionError(
            "Permission denied writing the district material timeline output. "
            "This often happens on Windows when the CSV is open in Excel or locked by OneDrive sync. "
            f"Close '{save_path}' and rerun."
        ) from e

    return out


def main(config: Configuration) -> None:
    df = create_district_material_timeline(config)
    print(f"District material timeline saved with {len(df)} years.")


if __name__ == "__main__":
    main(Configuration())
