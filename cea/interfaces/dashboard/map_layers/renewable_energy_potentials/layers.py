import os
from typing import List

import pandas as pd
import geopandas as gpd
from pyproj import CRS

from cea.config import DEFAULT_CONFIG, Configuration
from cea.inputlocator import InputLocator
from cea.interfaces.dashboard.map_layers import day_range_to_hour_range
from cea.interfaces.dashboard.map_layers.base import MapLayer, cache_output, ParameterDefinition, FileRequirement
from cea.interfaces.dashboard.map_layers.renewable_energy_potentials import RenewableEnergyPotentialsCategory
from cea.plots.colors import color_to_hex


def safe_filter_buildings_with_geometry(locator, buildings: list) -> tuple:
    """
    Filter buildings to only include those that exist in zone geometry.
    Returns tuple of (filtered_buildings, geometry_df, centroids).
    Gracefully handles missing buildings by excluding them.
    """
    if not buildings:
        return [], None, []

    try:
        zone_gdf = gpd.read_file(locator.get_zone_geometry()).set_index("name")

        # Filter to only buildings that exist in geometry
        existing_buildings = [b for b in buildings if b in zone_gdf.index]

        if not existing_buildings:
            return [], None, []

        geometry_df = zone_gdf.loc[existing_buildings]
        centroids = geometry_df.geometry.centroid.to_crs(CRS.from_epsg(4326))

        return existing_buildings, geometry_df, centroids
    except Exception as e:
        print(f"Warning: Error reading zone geometry: {e}")
        return [], None, []


class SolarPotentialsLayer(MapLayer):
    category = RenewableEnergyPotentialsCategory
    name = "renewable-energy-potentials"
    label = "Renewable Energy Potentials [kWh]"
    description = "Renewable energy potentials of buildings"

    _technologies = {
        "PV": "Photovoltaic panels",
        "PVT": "Photovoltaic-thermal panels",
        "SC": "Solar collectors"
    }

    _data_columns = {
        "PV": "E_PV_gen_kWh",
        "PVT": "E_PVT_gen_kWh",
        "SC": "Q_SC_gen_kWh",
    }

    # Per-surface palette — mirrors ``cea/visualisation/format/plot_colours.py``
    # so the Plot Solar Technology legend and this map layer agree. Each
    # entry provides:
    #   base     — solid colour (PV electricity, PVT electricity)
    #   light    — middle shade (PVT thermal)
    #   lighter  — faint shade  (SC thermal)
    _SURFACE_PALETTE = {
        "roofs_top": {
            "base": "red",
            "light": "red_light",
            "lighter": "red_lighter",
        },
        "walls_north": {
            "base": "orange",
            "light": "orange_light",
            "lighter": "orange_lighter",
        },
        "walls_east": {
            "base": "blue",
            "light": "blue_light",
            "lighter": "blue_lighter",
        },
        "walls_south": {
            "base": "green",
            "light": "green_light",
            "lighter": "green_lighter",
        },
        "walls_west": {
            "base": "purple",
            "light": "purple_light",
            "lighter": "purple_lighter",
        },
    }

    # PVT encodes a second metric (thermal) alongside electricity. When
    # the user enables PVT, each surface becomes two stack segments — one
    # for electricity (``_E``, base shade) and one for thermal (``_Q``,
    # light shade). The suffixes are used both as dict keys in each
    # entity's ``values`` map and as the stacked category names.
    _METRIC_E = "E"
    _METRIC_Q = "Q"

    # Separator used to encode the PVT compound panel type (PV code + SC code)
    # as a single dropdown value in the frontend. Kept intentionally verbose so
    # it can't collide with any real panel code.
    _PVT_PANEL_TYPE_SEP = " + "

    # Hardcoded surface choices for the `surface` multi-choice. Matches the
    # y-metric-to-plot choices in [plots-solar] in default.config so the
    # plot-solar form can watch this field directly.
    _SURFACE_CHOICES = [
        "roofs_top",
        "walls_north",
        "walls_east",
        "walls_south",
        "walls_west",
    ]

    def _get_technologies(self) -> List[str]:
        return list(self._technologies.keys())

    def _split_pvt_panel_type(self, panel_type):
        """Return ``(pv_code, sc_code)`` from a compound PVT panel-type value.

        The compound value is emitted by ``_get_panel_types`` as
        ``"<pv_code> + <sc_code>"``. Raises a clear ``ValueError`` if the
        value is missing or malformed.
        """
        if not panel_type or self._PVT_PANEL_TYPE_SEP not in panel_type:
            raise ValueError(
                "Panel type for PVT must be provided as "
                f"'<PV_code>{self._PVT_PANEL_TYPE_SEP}<SC_code>'. "
                f"Got: {panel_type!r}"
            )
        pv_code, sc_code = (p.strip() for p in panel_type.split(self._PVT_PANEL_TYPE_SEP, 1))
        if not pv_code or not sc_code:
            raise ValueError(
                f"Both PV and SC codes are required in PVT panel type. Got: {panel_type!r}"
            )
        return pv_code, sc_code

    def _scan_available_panel_files(self, technology: str) -> List[tuple]:
        """Scan ``potentials/solar`` for pre-computed total files and return
        the panel codes that actually have results on disk.

        Mirrors ``SolarPanelChoicesMixin._get_available_solar_technologies``
        in ``cea/config.py`` so the map layer's `panel-type` dropdown and
        the solar-technology parameter in the final-energy form agree on
        which panels the scenario actually contains.

        Returns a list of tuples:
          - PV  → [(pv_code,), ...]
          - SC  → [(sc_code,), ...]
          - PVT → [(pv_code, sc_code), ...]
        """
        import glob

        solar_folder = self.locator.get_potentials_solar_folder()
        if not os.path.exists(solar_folder):
            return []

        if technology == "PV":
            results = []
            for filepath in glob.glob(os.path.join(solar_folder, "PV_*_total.csv")):
                stem = os.path.basename(filepath).replace("_total.csv", "")
                # PV_<code>  →  <code> (skip PVT_* which also starts with PV)
                if stem.startswith("PVT_"):
                    continue
                code = stem[len("PV_"):]
                if code:
                    results.append((code,))
            return sorted(set(results))

        if technology == "SC":
            results = []
            for filepath in glob.glob(os.path.join(solar_folder, "SC_*_total.csv")):
                stem = os.path.basename(filepath).replace("_total.csv", "")
                code = stem[len("SC_"):]
                if code:
                    results.append((code,))
            return sorted(set(results))

        if technology == "PVT":
            results = []
            for filepath in glob.glob(os.path.join(solar_folder, "PVT_*_total.csv")):
                stem = os.path.basename(filepath).replace("_total.csv", "")
                # PVT_<pv_code>_<sc_code>
                parts = stem[len("PVT_"):].split("_", 1)
                if len(parts) == 2 and parts[0] and parts[1]:
                    results.append((parts[0], parts[1]))
            return sorted(set(results))

        return []

    def _get_panel_types(self, parameters: dict) -> List[str]:
        technology = parameters.get("technology")
        available = self._scan_available_panel_files(technology)

        if technology in ("PV", "SC"):
            return [code for (code,) in available]

        if technology == "PVT":
            return [
                f"{pv}{self._PVT_PANEL_TYPE_SEP}{sc}"
                for (pv, sc) in available
            ]

        return None

    def _get_surfaces(self) -> List[str]:
        # No-argument signature is required because the parameter has no
        # `depends_on`; the base `generate_choices` calls this with zero
        # positional args in that branch.
        return list(self._SURFACE_CHOICES)

    def _get_results_files(self, parameters: dict):
        # FIXME: Hardcoded to zone buildings for now
        buildings = self.locator.get_zone_building_names()

        technology = parameters.get("technology")
        panel_type = parameters.get("panel-type")

        if technology == "PV":
            if panel_type is None:
                raise ValueError("Panel type is required for PV")
            return [self.locator.PV_results(building, panel_type) for building in buildings]
        elif technology == "PVT":
            pv_code, sc_code = self._split_pvt_panel_type(panel_type)
            return [
                self.locator.PVT_results(building, pv_code, sc_code)
                for building in buildings
            ]
        elif technology == "SC":
            if panel_type is None:
                raise ValueError("Panel type is required for SC")
            return [self.locator.SC_results(building, panel_type) for building in buildings]

        raise ValueError(f"Invalid technology specified: {technology}")

    @classmethod
    def expected_parameters(cls):
        return {
            'technology':
                ParameterDefinition(
                    "technology",
                    "string",
                    description="Technology of the layer",
                    options_generator="_get_technologies",
                    selector="choice",
                ),
            'panel-type':
                ParameterDefinition(
                    "type-panel",
                    "string",
                    description="Panel type of the layer. For PVT, the value is a "
                                "compound '<PV_code> + <SC_code>' string.",
                    options_generator="_get_panel_types",
                    depends_on=["technology"],
                    selector="choice",
                ),
            'surface':
                ParameterDefinition(
                    "surface",
                    "array",
                    default=list(cls._SURFACE_CHOICES),
                    description="Building surfaces to consider. Consumed by the "
                                "Plot Solar Technology form's y-metric-to-plot field.",
                    options_generator="_get_surfaces",
                    selector="choice",
                    multi=True,
                ),
            'period':
                ParameterDefinition(
                    "Period",
                    "array",
                    default=[1, 365],
                    description="Period to generate the data (start, end) in days",
                    selector="time-series",
                ),
            'radius':
                ParameterDefinition(
                    "Radius",
                    "number",
                    default=2,
                    description="Radius of hexagon bin in meters",
                    selector="input",
                    range=[0, 100],
                    filter="radius",
                ),
            'scale':
                ParameterDefinition(
                    "Scale",
                    "number",
                    default=1,
                    description="Scale of hexagon bin height",
                    selector="input",
                    range=[0.1, 10],
                    filter="scale",
                ),
        }

    @classmethod
    def file_requirements(cls):
        return [
            FileRequirement(
                "Zone Buildings geometry",
                file_locator="locator:get_zone_geometry",
            ),
            FileRequirement(
                "Solar potentials",
                file_locator="layer:_get_results_files",
                depends_on=["technology", "panel-type"],
                optional=True,  # Individual building files may be missing
            ),
        ]

    def _resolve_selected_surfaces(self, parameters):
        """Normalise the `surface` parameter into a sorted list of valid
        surface names. Falls back to all surfaces when nothing is set."""
        raw = parameters.get("surface")
        if raw is None:
            return list(self._SURFACE_CHOICES)
        if isinstance(raw, str):
            raw = [raw]
        if not isinstance(raw, (list, tuple)):
            return list(self._SURFACE_CHOICES)
        selected = [s for s in raw if s in self._SURFACE_CHOICES]
        if not selected:
            return list(self._SURFACE_CHOICES)
        # Preserve the canonical order so rendering is deterministic.
        return [s for s in self._SURFACE_CHOICES if s in set(selected)]

    @cache_output
    def generate_data(self, parameters):
        """Generates the output for this layer.

        Mirrors OperationalEmissionsMapLayer's per-category behaviour for
        the ``surface`` multi-choice:
        - single surface → flat HexagonLayer bins, tooltip shows the one
          surface's period value (same as the other bin layers).
        - multiple surfaces → stacked ColumnLayer, one colour per surface
          (``stacked: True`` in properties).
        """
        locator = InputLocator(os.path.join(self.project, self.scenario_name))

        # FIXME: Hardcoded to zone buildings for now
        buildings = locator.get_zone_building_names()
        period = parameters['period']
        start, end = day_range_to_hour_range(period[0], period[1])

        technology = parameters.get("technology")
        panel_type = parameters.get("panel-type")
        selected_surfaces = self._resolve_selected_surfaces(parameters)

        pvt_pv_code = None
        pvt_sc_code = None
        if technology == "PVT":
            pvt_pv_code, pvt_sc_code = self._split_pvt_panel_type(panel_type)

        # PVT always emits two stack segments per surface (electricity + thermal),
        # so it is always rendered as a stacked ColumnLayer regardless of how
        # many surfaces are selected. PV and SC still use the flat HexagonLayer
        # when a single surface is chosen.
        is_pvt = technology == "PVT"
        is_stacked = is_pvt or len(selected_surfaces) > 1

        # Column-name builder: PV has only electricity, SC has only thermal,
        # PVT exposes both so we read two columns per surface.
        def surface_columns_for(surface):
            if technology == "PV":
                return {self._METRIC_E: f"PV_{surface}_E_kWh"}
            if technology == "SC":
                return {self._METRIC_Q: f"SC_{panel_type}_{surface}_Q_kWh"}
            if technology == "PVT":
                return {
                    self._METRIC_E: f"PVT_{pvt_sc_code}_{surface}_E_kWh",
                    self._METRIC_Q: f"PVT_{pvt_sc_code}_{surface}_Q_kWh",
                }
            raise ValueError(f"Invalid technology specified: {technology}")

        # Route colour choice through the same helper Plot-Solar Technology
        # uses (``get_column_color``) on the exact CSV column name. This
        # guarantees map bars and plot bars share the same colour per
        # surface+metric — plot_colours.py is the single source of truth.
        # Falls back to the local palette only when the helper returns
        # None (unknown column).
        from cea.visualisation.format.plot_colours import get_column_color

        def colour_for(surface, metric):
            col_name = surface_columns_for(surface)[metric]
            via_plot = get_column_color(col_name)
            if via_plot:
                return via_plot
            palette = self._SURFACE_PALETTE.get(surface, {
                "base": "grey", "light": "grey_light", "lighter": "grey_lighter",
            })
            if technology == "SC":
                return palette["lighter"]
            if metric == self._METRIC_E:
                return palette["base"]
            return palette["light"]  # PVT_Q

        def category_key(surface, metric):
            # When both metrics are live (PVT) we need to distinguish
            # surface_E vs surface_Q; for PV / SC the surface name alone
            # is enough because there is only one metric.
            if is_pvt:
                return f"{surface}_{metric}"
            return surface

        def category_label(surface, metric):
            if is_pvt:
                return f"{surface} ({metric})"
            return surface

        # Ordered list of (surface, metric) tuples for the stack.
        stack_segments = []
        for surface in selected_surfaces:
            for metric in surface_columns_for(surface).keys():
                stack_segments.append((surface, metric))

        # Filter buildings that exist in geometry
        buildings, _, building_centroids = safe_filter_buildings_with_geometry(locator, buildings)

        empty_range = {
            'total': {'label': 'Total Range', 'min': 0.0, 'max': 0.0},
            'period': {'label': 'Period Range', 'min': 0.0, 'max': 0.0},
        }

        def build_categories_payload():
            out = []
            for surface, metric in stack_segments:
                colour_name = colour_for(surface, metric)
                hex_colour = color_to_hex(colour_name)
                r = int(hex_colour[1:3], 16)
                g = int(hex_colour[3:5], 16)
                b = int(hex_colour[5:7], 16)
                out.append({
                    "name": category_key(surface, metric),
                    "label": category_label(surface, metric),
                    "colour": hex_colour,
                    "rgb": [r, g, b],
                })
            return out

        def build_info_rows():
            rows = [
                {"label": "technology", "value": technology or ""},
                {"label": "type-panel", "value": panel_type or ""},
            ]
            return rows

        def empty_output():
            """Valid but empty output payload."""
            first_colour_name = (
                colour_for(stack_segments[0][0], stack_segments[0][1])
                if stack_segments
                else "yellow"
            )
            hex_colour = color_to_hex(first_colour_name)
            props = {
                "name": self.name,
                "label": self.label,
                "description": self.description,
                "colours": {
                    "colour_array": [
                        color_to_hex("grey_lighter"),
                        hex_colour,
                    ],
                    "points": 12,
                },
                "range": empty_range,
                "stacked": is_stacked,
                "info": build_info_rows(),
            }
            if is_stacked:
                props["categories"] = build_categories_payload()
            return {"data": [], "properties": props}

        if not buildings:
            return empty_output()

        def get_building_potential(building, centroid):
            try:
                if technology == "PV":
                    path = self.locator.PV_results(building, panel_type)
                elif technology == "PVT":
                    path = self.locator.PVT_results(building, pvt_pv_code, pvt_sc_code)
                elif technology == "SC":
                    path = self.locator.SC_results(building, panel_type)
                else:
                    raise ValueError(f"Invalid technology specified: {technology}")

                if not os.path.exists(path):
                    return None

                # Collect every column we need across all selected surfaces.
                wanted_cols = {}  # {(surface, metric): col_name}
                for surface, metric in stack_segments:
                    col_name = surface_columns_for(surface)[metric]
                    wanted_cols[(surface, metric)] = col_name

                header = pd.read_csv(path, nrows=0).columns
                cols_present = [c for c in set(wanted_cols.values()) if c in header]
                if not cols_present:
                    return None
                df = pd.read_csv(path, usecols=cols_present)

                values = {}  # keyed by category_key(...)
                for (surface, metric), col_name in wanted_cols.items():
                    key = category_key(surface, metric)
                    if col_name not in df.columns:
                        values[key] = 0.0
                        continue
                    series = df[col_name].astype(float)
                    if start < end:
                        period_value = series.iloc[start:end + 1].sum()
                    else:
                        period_value = (
                            series.iloc[start:].sum() + series.iloc[:end + 1].sum()
                        )
                    values[key] = float(period_value)

                return {
                    "name": building,
                    "position": [centroid.x, centroid.y],
                    "values": values,
                }
            except Exception as e:
                print(f"Warning: Error reading {technology} potentials for {building}: {e}")
                return None

        entities = [
            r
            for r in (
                get_building_potential(b, c)
                for b, c in zip(buildings, building_centroids)
            )
            if r is not None
        ]

        if not entities:
            return empty_output()

        # ---- Single-surface (PV or SC only): flat bins ----
        if not is_stacked:
            surface, metric = stack_segments[0]
            key = category_key(surface, metric)
            colour_name = colour_for(surface, metric)
            data_points = [
                {
                    "position": e["position"],
                    "value": e["values"].get(key, 0.0),
                    "name": e["name"],
                    "category": category_label(surface, metric),
                }
                for e in entities
            ]
            period_values = [p["value"] for p in data_points]
            return {
                "data": data_points,
                "properties": {
                    "name": self.name,
                    "label": f"{self.label} - {surface}",
                    "description": self.description,
                    "colours": {
                        "colour_array": [
                            color_to_hex("grey_lighter"),
                            color_to_hex(colour_name),
                        ],
                        "points": 12,
                    },
                    "range": {
                        "total": {
                            "label": "Total Range",
                            "min": 0.0,
                            "max": float(max(period_values)) if period_values else 0.0,
                        },
                        "period": {
                            "label": "Period Range",
                            "min": float(min(period_values)) if period_values else 0.0,
                            "max": float(max(period_values)) if period_values else 0.0,
                        },
                    },
                    "stacked": False,
                    "info": build_info_rows(),
                },
            }

        # ---- Stacked mode: multi-surface PV/SC, or any PVT ----
        categories_payload = build_categories_payload()
        stack_keys = [cat["name"] for cat in categories_payload]
        stack_totals = [
            sum(max(e["values"].get(k, 0.0), 0.0) for k in stack_keys)
            for e in entities
        ]

        return {
            "data": entities,
            "properties": {
                "name": self.name,
                "label": f"{self.label} - stacked",
                "description": self.description,
                "stacked": True,
                "categories": categories_payload,
                "info": build_info_rows(),
                "range": {
                    "total": {
                        "label": "Total Range",
                        "min": 0.0,
                        "max": float(max(stack_totals)) if stack_totals else 0.0,
                    },
                    "period": {
                        "label": "Period Range",
                        "min": 0.0,
                        "max": float(max(stack_totals)) if stack_totals else 0.0,
                    },
                },
            },
        }
