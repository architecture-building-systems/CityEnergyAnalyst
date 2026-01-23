import glob
import os
import json
import shutil

import pandas as pd
import geopandas as gpd

from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
from cea.interfaces.dashboard.map_layers.base import MapLayer, ParameterDefinition, FileRequirement, cache_output
from cea.interfaces.dashboard.map_layers.thermal_network import ThermalNetworkCategory
from cea.plots.colors import color_to_hex
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system


logger = getCEAServerLogger("ThermalNetworkMapLayer")


class ThermalNetworkMapLayer(MapLayer):
    category = ThermalNetworkCategory
    name = "thermal-network"
    label = "Thermal Network"
    description = "Thermal Network Design"

    _network_types = ["DC", "DH"]

    def _get_network_types(self):
        # Return both choices and default (DC is default)
        return {"choices": self._network_types, "default": self._network_types[0]}

    def _migrate_old_format(self, network_folder):
        # Check if the old format exists
        if not any(os.path.exists(os.path.join(network_folder, network_type)) for network_type in self._network_types):
            return

        network_name = "existing_network"
        if os.path.exists(os.path.join(network_folder, network_name)):
            # Default network folder already exists, no need to migrate
            return

        for network_type in self._network_types:
            network_name_type = f"{network_name}_{network_type}"
            # Migrate old layout folder {network_folder}/DC to new folder e.g. {network_folder}/baseline/DC/
            old_layout_folder = os.path.join(network_folder, network_type)
            new_network_folder = os.path.join(network_folder, network_name_type, network_type)
            if os.path.exists(old_layout_folder):
                new_layout_folder = os.path.join(new_network_folder, "layout")
                shutil.move(old_layout_folder, new_layout_folder)

                # copy edge shapefile as layout shapefile
                extensions = ['shp', 'shx', 'dbf', 'prj']
                edge_shapefile_files = [
                    f for ext in extensions 
                    for f in glob.glob(os.path.join(new_layout_folder, f"edges.{ext}"))
                ]
                if all([os.path.exists(f) for f in edge_shapefile_files]):
                    for ext in extensions:
                        old_edge_file = os.path.join(new_layout_folder, f"edges.{ext}")
                        new_layout_file = os.path.join(network_folder, network_name_type, f"layout.{ext}")
                        shutil.copy(old_edge_file, new_layout_file)

            
            # Migrate old results files {network_folder}/DC__*.csv to new name e.g. {network_folder}/DC_baseline_*.csv
            old_results_files = glob.glob(os.path.join(network_folder, f"{network_type}__*.csv"))
            for old_results_file in old_results_files:
                filename = os.path.basename(old_results_file)
                new_filename = filename.replace(f"{network_type}__", f"{network_type}_{network_name_type}_", 1)
                new_results_file = os.path.join(new_network_folder, new_filename)
                shutil.move(old_results_file, new_results_file)
        
        logger.debug(f"Migrated old thermal network format in {network_folder} to new format.")

    def _check_valid_network(self, network_name: str, network_type: str):
        """Check if a network nodes and edges files exist for the given network type"""
        edges_path = self.locator.get_network_layout_edges_shapefile(network_type, network_name)
        nodes_path = self.locator.get_network_layout_nodes_shapefile(network_type, network_name)
        return os.path.exists(edges_path) and os.path.exists(nodes_path)
    
    def _check_potential_network(self, network_name: str, network_type: str):
        """Check if a potential network layout and network nodes exist for the given network type"""
        layout_path = self.locator.get_network_layout_shapefile(network_name)
        nodes_path = self.locator.get_network_layout_nodes_shapefile(network_type, network_name)
        return os.path.exists(layout_path) and os.path.exists(nodes_path)

    def _get_network_names(self, parameters):
        """Get list of available network layouts for the selected network type"""
        try:
            network_folder = self.locator.get_thermal_network_folder()
            # Try to migrate old format if detected
            self._migrate_old_format(network_folder)

            network_type = parameters.get('network-type')

            # Return placeholder option if network type not selected yet
            if not network_type:
                return ["No network available"]

            available_networks = []

            # Scan regular single-phase networks
            for file in os.listdir(network_folder):
                # Ignore old format files and phasing-plans folder
                if not os.path.isdir(os.path.join(network_folder, file)) or file.startswith(".") or \
                   any(file.startswith(nt) for nt in self._network_types) or file == 'phasing-plans':
                    continue

                network_name = file
                # Check if valid network or potential network exists
                if self._check_valid_network(network_name, network_type) or self._check_potential_network(network_name, network_type):
                    nodes_path = self.locator.get_network_layout_nodes_shapefile(network_type, network_name)
                    mod_time = os.path.getmtime(nodes_path)
                    available_networks.append((network_name, mod_time))

            # Scan phasing plans folder
            phasing_folder = self.locator.get_thermal_network_phasing_plans_folder()
            if os.path.exists(phasing_folder):
                for plan_name in os.listdir(phasing_folder):
                    plan_path = os.path.join(phasing_folder, plan_name)
                    if not os.path.isdir(plan_path) or plan_name.startswith("."):
                        continue

                    # Check if this phasing plan has the selected network type
                    plan_type_path = os.path.join(plan_path, network_type)
                    if not os.path.exists(plan_type_path):
                        continue

                    # Check if it has valid phases
                    phases = self.locator.get_thermal_network_phasing_plan_phases(network_type, plan_name)
                    if phases:
                        # Add with (Multi-Phase) suffix to distinguish from regular networks
                        display_name = f"{plan_name} (Multi-Phase)"
                        # Use modification time of the first phase for sorting
                        first_phase_path = os.path.join(plan_type_path, phases[0], 'layout', 'nodes.shp')
                        if os.path.exists(first_phase_path):
                            mod_time = os.path.getmtime(first_phase_path)
                            available_networks.append((display_name, mod_time))

            # Sort by modification time (most recent first)
            available_networks.sort(key=lambda x: x[1], reverse=True)

            logger.debug(f"Found {len(available_networks)} networks: {[name for name, _ in available_networks]}")

            # If no networks found, return a placeholder option
            if not available_networks:
                logger.debug("No networks found, returning placeholder option")
                return {"choices": ["No network available"], "default": "No network available"}

            # Return both choices and default (most recent network)
            choices = [name for name, _ in available_networks]
            return {"choices": choices, "default": choices[0]}

        except Exception as e:
            logger.error(f"Error in _get_network_names: {e}")
            return {"choices": ["No network available"], "default": "No network available"}

    def _get_phase_choices(self, parameters):
        """Get list of available phases for multi-phase plans"""
        try:
            network_name = parameters.get('network-name', '')
            network_type = parameters.get('network-type', '')

            # Only show phase selector for multi-phase plans
            if not network_name or not network_name.endswith('(Multi-Phase)'):
                return {"choices": [], "default": ""}

            # Extract plan name (remove suffix)
            plan_name = network_name.replace(' (Multi-Phase)', '')

            # Get available phases
            phases = self.locator.get_thermal_network_phasing_plan_phases(network_type, plan_name)

            if not phases:
                logger.debug(f"No phases found for plan {plan_name}")
                return {"choices": [], "default": ""}

            # Create human-readable labels
            phase_choices = []
            for phase in phases:
                # Extract year from phase folder name (e.g., "phase1_2030" → "Phase 1 - 2030")
                parts = phase.split('_')
                if len(parts) == 2:
                    phase_num = parts[0].replace('phase', '')
                    year = parts[1]
                    label = f"Phase {phase_num} - {year}"
                    phase_choices.append((phase, label))
                else:
                    # Fallback if naming doesn't match expected pattern
                    phase_choices.append((phase, phase))

            # Add timeline view option
            phase_choices.append(('timeline', 'Timeline View (All Phases)'))

            logger.debug(f"Found {len(phase_choices)} phase choices for {plan_name}: {phase_choices}")

            # Return choices (values) and default (first phase)
            choices = [value for value, label in phase_choices]
            return {"choices": choices, "default": phases[0] if phases else "timeline"}

        except Exception as e:
            logger.error(f"Error in _get_phase_choices: {e}")
            return {"choices": [], "default": ""}

    def _get_network_layout_files(self, parameters):
        network_name = parameters.get('network-name')

        # Handle None, undefined, or empty string
        if network_name is None or network_name == 'undefined':
            network_name = ''

        # Multi-phase plans don't have layout shapefiles (optional)
        if network_name.endswith('(Multi-Phase)'):
            return []

        return [
            self.locator.get_network_layout_shapefile(network_name),
        ]

    def _get_network_results_files(self, parameters):
        network_type = parameters.get('network-type')
        network_name = parameters.get('network-name')

        # Handle None, undefined, or empty string
        if network_name is None or network_name == 'undefined':
            network_name = ''

        # Multi-phase plans don't have massflow files (optional)
        if network_name.endswith('(Multi-Phase)'):
            return []

        return [
            self.locator.get_thermal_network_layout_massflow_edges_file(network_type, network_name),
        ]

    def _get_network_nodes_files(self, parameters):
        network_type = parameters.get('network-type')
        network_name = parameters.get('network-name')
        phase = parameters.get('phase', '')

        # Handle None, undefined, or empty string
        if network_name is None or network_name == 'undefined':
            network_name = ''

        # Check if multi-phase plan
        if network_name.endswith('(Multi-Phase)'):
            plan_name = network_name.replace(' (Multi-Phase)', '')
            # Use timeline view by default if no phase specified
            if not phase:
                phase = 'timeline'
            return [
                self.locator.get_thermal_network_phase_nodes_shapefile(network_type, plan_name, phase),
            ]

        return [
            self.locator.get_network_layout_nodes_shapefile(network_type, network_name),
        ]

    def _get_network_edges_files(self, parameters):
        network_type = parameters.get('network-type')
        network_name = parameters.get('network-name')
        phase = parameters.get('phase', '')

        # Handle None, undefined, or empty string
        if network_name is None or network_name == 'undefined':
            network_name = ''

        # Check if multi-phase plan
        if network_name.endswith('(Multi-Phase)'):
            plan_name = network_name.replace(' (Multi-Phase)', '')
            # Use timeline view by default if no phase specified
            if not phase:
                phase = 'timeline'
            return [
                self.locator.get_thermal_network_phase_edges_shapefile(network_type, plan_name, phase),
            ]

        return [
            self.locator.get_network_layout_edges_shapefile(network_type, network_name),
        ]

    # TODO: Add width parameter
    @classmethod
    def expected_parameters(cls):
        return {
            'network-name':
                ParameterDefinition(
                    "Network Name",
                    "string",
                    default="",
                    description="Name of the network layout to visualise (leave empty to show base layer only)",
                    selector="choice",
                    depends_on=["network-type"],
                    options_generator="_get_network_names",
                ),
            'network-type':
                ParameterDefinition(
                    "Network Type",
                    "string",
                    description="Type of the network",
                    options_generator="_get_network_types",
                    selector="choice",
                ),
            'phase':
                ParameterDefinition(
                    "Phase",
                    "string",
                    default="",
                    description="Select phase for multi-phase plans (Timeline View shows all phases)",
                    selector="choice",
                    depends_on=["network-name", "network-type"],
                    options_generator="_get_phase_choices",
                ),
            'scale':
                ParameterDefinition(
                    "Scale",
                    "number",
                    default=1,
                    description="Scale of pipe width",
                    selector="input",
                    range=[0.1, 100],
                    filter="scale",
                ),
        }

    @classmethod
    def file_requirements(cls):
        return [
            FileRequirement(
                "Zone Buildings Geometry",
                file_locator="locator:get_zone_geometry",
            ),
            FileRequirement(
                "Network Layout",
                file_locator="layer:_get_network_layout_files",
                depends_on=["network-name"],
                optional=True,  # layout file is optional to support old network format without layout
            ),
            FileRequirement(
                "Network Nodes",
                file_locator="layer:_get_network_nodes_files",
                depends_on=["network-name", "network-type"],
            ),
            # Edges files are optional, we can still show potential layout
            FileRequirement(
                "Network Edges",
                file_locator="layer:_get_network_edges_files",
                depends_on=["network-name", "network-type"],
                optional=True,
            ),
            # Results files are optional, we can still show layout without mass flow data
            FileRequirement(
                "Network Results",
                file_locator="layer:_get_network_results_files",
                depends_on=["network-name", "network-type"],
                optional=True,
            ),
        ]

    @cache_output
    def generate_data(self, parameters):
        """Generates the output for this layer"""
        network_type = parameters.get('network-type')
        network_name = parameters.get('network-name')
        phase = parameters.get('phase', '')

        # Handle None, undefined, empty string, or placeholder value
        if network_name is None or network_name == 'undefined' or network_name == 'No network available':
            raise ValueError("No valid network name provided")

        if network_type not in self._network_types:
            raise ValueError(f"Invalid network type: {network_type}")

        # Check if this is a multi-phase plan
        is_phasing_plan = network_name.endswith('(Multi-Phase)')

        # Determine file paths based on whether it's a phasing plan
        if is_phasing_plan:
            plan_name = network_name.replace(' (Multi-Phase)', '')

            # Use timeline view by default if no phase specified
            if not phase:
                phase = 'timeline'

            # Get phase-specific or timeline paths
            edges_path = self.locator.get_thermal_network_phase_edges_shapefile(network_type, plan_name, phase)
            nodes_path = self.locator.get_thermal_network_phase_nodes_shapefile(network_type, plan_name, phase)

            # For enrichment data, use the phase-specific folder (or last phase for timeline)
            if phase == 'timeline':
                # Get the last phase for enrichment data in timeline view
                phases = self.locator.get_thermal_network_phasing_plan_phases(network_type, plan_name)
                enrichment_network_name = phases[-1] if phases else None
                # Need to construct path to last phase folder
                if enrichment_network_name:
                    enrichment_base = os.path.join(
                        self.locator.get_thermal_network_phasing_plans_folder(),
                        plan_name,
                        network_type,
                        enrichment_network_name
                    )
                else:
                    enrichment_base = None
            else:
                # Use phase-specific folder for enrichment
                enrichment_base = os.path.join(
                    self.locator.get_thermal_network_phasing_plans_folder(),
                    plan_name,
                    network_type,
                    phase
                )

            layout_path = None  # No potential layout for phasing plans
            massflow_edges_path = None  # Will be constructed later if needed
        else:
            # Regular single-phase network
            layout_path = self.locator.get_network_layout_shapefile(network_name)
            edges_path = self.locator.get_network_layout_edges_shapefile(network_type, network_name)
            nodes_path = self.locator.get_network_layout_nodes_shapefile(network_type, network_name)
            massflow_edges_path = self.locator.get_thermal_network_layout_massflow_edges_file(network_type, network_name)
            enrichment_base = None

        primary_colour = color_to_hex("blue") if network_type == "DC" else color_to_hex("red")

        output = {
            "nodes": None,
            "edges": None,
            "properties": {
                "name": self.name,
                "label": self.label,
                "description": self.description,
                "colours": {
                    "edges": primary_colour,
                    "nodes": {
                        "plant": primary_colour,
                        "consumer": color_to_hex("white"),
                    }
                }
            }
        }

        # Decide which files to load: either the full network (edges + nodes) or potential layout + nodes
        _edges_path = edges_path
        if not is_phasing_plan:
            if not self._check_valid_network(network_name, network_type):
                if self._check_potential_network(network_name, network_type):
                    logger.debug(f"Valid network files don't exist for {network_name} ({network_type}), loading potential layout instead.")
                    _edges_path = layout_path
                else:
                    logger.debug(f"Network files don't exist at {edges_path}.")
                    return output
        else:
            # For phasing plans, check if files exist
            if not os.path.exists(edges_path) or not os.path.exists(nodes_path):
                logger.debug(f"Phase files don't exist at {edges_path}.")
                return output

        logger.debug(f"Loading network from {_edges_path}")
        crs = get_geographic_coordinate_system()
        edges_df = gpd.read_file(_edges_path).to_crs(crs).set_index("name")
        nodes_df = gpd.read_file(nodes_path).to_crs(crs).set_index("name")

        # Only load massflow data if it exists
        if not is_phasing_plan and massflow_edges_path and os.path.exists(massflow_edges_path):
            logger.debug(f"Loading massflow from {massflow_edges_path}")
            massflow_edges_df = pd.read_csv(massflow_edges_path)
            edges_df["peak_mass_flow"] = massflow_edges_df.max().round(1)
        else:
            logger.debug("Massflow file doesn't exist or not applicable, skipping")

        # Enrich nodes with substation and plant performance data
        if is_phasing_plan:
            # For phasing plans, pass the phase-specific network name for enrichment
            if phase == 'timeline':
                # Timeline view: don't enrich (would need per-phase data)
                logger.debug("Timeline view: skipping node enrichment")
            else:
                # Individual phase: use phase folder for enrichment
                nodes_df = self._enrich_nodes_with_data_phasing(nodes_df, network_type, enrichment_base)
        else:
            nodes_df = self._enrich_nodes_with_data(nodes_df, network_type, network_name)

        # Add timeline-specific color coding if applicable
        if is_phasing_plan and phase == 'timeline':
            output['properties']['timeline'] = True
            output['properties']['colours']['edges_by_phase'] = {
                1: color_to_hex('blue'),
                2: color_to_hex('green'),
                3: color_to_hex('red'),
                # Add more colors if needed for more phases
            }

        output['nodes'] = json.loads(nodes_df.to_json())
        output['edges'] = json.loads(edges_df.to_json())

        return output

    def _enrich_nodes_with_data(self, nodes_df, network_type, network_name):
        """
        Enrich nodes dataframe with substation and plant performance metrics.

        For building nodes: Add annual energy, peak loads, temperatures, HEX area
        For plant nodes: Add annual output, capacity factor, operating hours, temperature ranges
        """
        # Iterate through nodes and add metrics based on type
        for node_id in nodes_df.index:
            node_type = nodes_df.loc[node_id, 'type']

            if node_type == 'CONSUMER':
                # Building node - add substation metrics
                building_name = nodes_df.loc[node_id, 'building']
                metrics = self._calculate_substation_metrics(building_name, network_type, network_name)

                # Add all metrics to the dataframe
                for key, value in metrics.items():
                    nodes_df.loc[node_id, key] = value

            elif node_type.startswith('PLANT'):
                # Plant node - add plant performance metrics
                # Node type can be 'PLANT_hs_ww', 'PLANT_cs', etc.
                metrics = self._calculate_plant_metrics(network_type, network_name, node_id)

                # Add all metrics to the dataframe
                for key, value in metrics.items():
                    nodes_df.loc[node_id, key] = value

        return nodes_df

    def _enrich_nodes_with_data_phasing(self, nodes_df, network_type, enrichment_base):
        """
        Enrich nodes dataframe with substation and plant performance metrics for phasing plans.

        For building nodes: Add annual energy, peak loads, temperatures, HEX area
        For plant nodes: Add annual output, capacity factor, operating hours, temperature ranges

        :param enrichment_base: Base path to phase folder (e.g., .../three-phased-2/DH/phase1_2030/)
        """
        if not enrichment_base or not os.path.exists(enrichment_base):
            logger.debug(f"Enrichment base path doesn't exist: {enrichment_base}")
            return nodes_df

        # Iterate through nodes and add metrics based on type
        for node_id in nodes_df.index:
            node_type = nodes_df.loc[node_id, 'type']

            if node_type == 'CONSUMER':
                # Building node - add substation metrics
                building_name = nodes_df.loc[node_id, 'building']
                substation_file = os.path.join(enrichment_base, 'substation', f'{building_name}.csv')
                metrics = self._calculate_substation_metrics_from_file(substation_file, network_type)

                # Add all metrics to the dataframe
                for key, value in metrics.items():
                    nodes_df.loc[node_id, key] = value

            elif node_type.startswith('PLANT'):
                # Plant node - add plant performance metrics
                plant_file = os.path.join(enrichment_base, f'{network_type}_Plant_thermal_load_kW.csv')
                temp_supply_file = os.path.join(enrichment_base, f'T_supply_{network_type}_nodes_K.csv')
                temp_return_file = os.path.join(enrichment_base, f'T_return_{network_type}_nodes_K.csv')
                metrics = self._calculate_plant_metrics_from_files(plant_file, temp_supply_file, temp_return_file, node_id)

                # Add all metrics to the dataframe
                for key, value in metrics.items():
                    nodes_df.loc[node_id, key] = value

        return nodes_df

    def _calculate_substation_metrics_from_file(self, substation_file, network_type):
        """Calculate substation metrics from a direct file path (for phasing plans)"""
        try:
            if not os.path.exists(substation_file):
                logger.debug(f"Substation file doesn't exist: {substation_file}")
                return {}

            # Read the building's hourly data
            df = pd.read_csv(substation_file)

            # Calculate annual energy from DH/DC network
            if network_type == 'DH':
                # For DH: sum of space heating and DHW from network (excluding booster)
                Q_dh_W = df.get('Qhs_dh_W', pd.Series([0])).fillna(0) + \
                         df.get('Qww_dh_W', pd.Series([0])).fillna(0)
                Q_booster_W = df.get('Qhs_booster_W', pd.Series([0])).fillna(0) + \
                              df.get('Qww_booster_W', pd.Series([0])).fillna(0)

                annual_energy_MWh = (Q_dh_W.sum() / 1000) / 1000
                annual_booster_MWh = (Q_booster_W.sum() / 1000) / 1000
                peak_load_kW = (Q_dh_W.max() / 1000)

            elif network_type == 'DC':
                Q_dc_W = df.get('Qcs_W', pd.Series([0])).fillna(0)
                annual_energy_MWh = (Q_dc_W.sum() / 1000) / 1000
                annual_booster_MWh = 0
                peak_load_kW = (Q_dc_W.max() / 1000)
            else:
                raise ValueError(f"Invalid network type: {network_type}")

            # Average temperatures during active hours
            mdot_col = f'mdot_{network_type}_result_kgpers'
            T_supply_col = f'T_supply_{network_type}_result_C'
            T_return_col = f'T_return_{network_type}_result_C'

            required_cols = {mdot_col, T_supply_col, T_return_col}
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                avg_supply_temp = 0
                avg_return_temp = 0
                avg_delta_t = 0
            else:
                active_hours = df[mdot_col] > 0.01
                if active_hours.sum() > 0:
                    avg_supply_temp = df.loc[active_hours, T_supply_col].mean()
                    avg_return_temp = df.loc[active_hours, T_return_col].mean()
                    avg_delta_t = abs(avg_supply_temp - avg_return_temp)
                else:
                    avg_supply_temp = 0
                    avg_return_temp = 0
                    avg_delta_t = 0

            # Heat exchanger area
            if network_type == 'DH':
                hex_area_m2 = df.get('HEX_hs_area_m2', pd.Series([0])).max() + \
                              df.get('HEX_ww_area_m2', pd.Series([0])).max()
            else:
                hex_area_m2 = df.get('HEX_cs_area_m2', pd.Series([0])).max()

            metrics = {
                'annual_energy_MWh': round(annual_energy_MWh, 2),
                'peak_load_kW': round(peak_load_kW, 1),
                'avg_supply_temp_C': round(avg_supply_temp, 1),
                'avg_return_temp_C': round(avg_return_temp, 1),
                'avg_delta_t_C': round(avg_delta_t, 1),
                'hex_area_m2': round(hex_area_m2, 1),
            }

            if network_type == 'DH':
                metrics['annual_booster_MWh'] = round(annual_booster_MWh, 2)

            return metrics

        except Exception as e:
            logger.error(f"Error calculating substation metrics from {substation_file}: {e}")
            return {}

    def _calculate_plant_metrics_from_files(self, plant_file, temp_supply_file, temp_return_file, plant_id):
        """Calculate plant metrics from direct file paths (for phasing plans)"""
        try:
            if not os.path.exists(plant_file):
                logger.debug(f"Plant file doesn't exist: {plant_file}")
                return {}

            # Read hourly plant load
            plant_df = pd.read_csv(plant_file)

            # Annual output
            annual_output_MWh = plant_df['thermal_load_kW'].sum() / 1000
            peak_load_kW = plant_df['thermal_load_kW'].max()

            # Capacity factor and operating hours
            capacity_factor_pct = 0
            operating_hours = 0
            operating_hours_pct = 0

            if peak_load_kW > 0:
                potential_output_MWh = peak_load_kW * 8760 / 1000
                capacity_factor_pct = (annual_output_MWh / potential_output_MWh) * 100
                operating_threshold = peak_load_kW * 0.01
                operating_hours = (plant_df['thermal_load_kW'] > operating_threshold).sum()
                operating_hours_pct = (operating_hours / 8760) * 100

            # Temperature statistics
            if os.path.exists(temp_supply_file):
                temp_df = pd.read_csv(temp_supply_file)
                if plant_id in temp_df.columns:
                    avg_supply_temp_C = temp_df[plant_id].mean() - 273.15
                    min_supply_temp_C = temp_df[plant_id].min() - 273.15
                    max_supply_temp_C = temp_df[plant_id].max() - 273.15
                else:
                    avg_supply_temp_C = 0
                    min_supply_temp_C = 0
                    max_supply_temp_C = 0
            else:
                avg_supply_temp_C = 0
                min_supply_temp_C = 0
                max_supply_temp_C = 0

            if os.path.exists(temp_return_file):
                temp_df = pd.read_csv(temp_return_file)
                if plant_id in temp_df.columns:
                    avg_return_temp_C = temp_df[plant_id].mean() - 273.15
                else:
                    avg_return_temp_C = 0
            else:
                avg_return_temp_C = 0

            return {
                'annual_output_MWh': round(annual_output_MWh, 2),
                'peak_load_kW': round(peak_load_kW, 1),
                'capacity_factor_pct': round(capacity_factor_pct, 1),
                'operating_hours': int(operating_hours),
                'operating_hours_pct': round(operating_hours_pct, 1),
                'avg_supply_temp_C': round(avg_supply_temp_C, 1),
                'avg_return_temp_C': round(avg_return_temp_C, 1),
                'min_supply_temp_C': round(min_supply_temp_C, 1),
                'max_supply_temp_C': round(max_supply_temp_C, 1),
            }

        except Exception as e:
            import traceback
            logger.error(f"Error calculating plant metrics from {plant_file}: {e}")
            logger.error(traceback.format_exc())
            return {
                'annual_output_MWh': 0,
                'peak_load_kW': 0,
                'capacity_factor_pct': 0,
                'operating_hours': 0,
                'operating_hours_pct': 0,
                'avg_supply_temp_C': 0,
                'avg_return_temp_C': 0,
                'min_supply_temp_C': 0,
                'max_supply_temp_C': 0,
            }

    def _calculate_substation_metrics(self, building_name, network_type, network_name):
        """
        Calculate substation performance metrics for a building node.

        Returns dict with:
        - annual_energy_MWh: Total annual energy from DH/DC
        - annual_booster_MWh: Annual booster energy (DH networks only)
        - peak_load_kW: Peak thermal load
        - avg_supply_temp_C: Average supply temperature during operation
        - avg_return_temp_C: Average return temperature during operation
        - avg_delta_t_C: Average temperature difference
        - hex_area_m2: Heat exchanger area
        """
        try:
            # Load substation results file for this specific building
            substation_file = self.locator.get_thermal_network_substation_results_file(
                building_name, network_type, network_name
            )

            if not os.path.exists(substation_file):
                logger.debug(f"Substation file doesn't exist: {substation_file}")
                return {}

            # Read the building's hourly data
            df = pd.read_csv(substation_file)

            # Calculate annual energy from DH/DC network
            if network_type == 'DH':
                # For DH: sum of space heating and DHW from network (excluding booster)
                Q_dh_W = df.get('Qhs_dh_W', pd.Series([0])).fillna(0) + \
                         df.get('Qww_dh_W', pd.Series([0])).fillna(0)
                Q_booster_W = df.get('Qhs_booster_W', pd.Series([0])).fillna(0) + \
                              df.get('Qww_booster_W', pd.Series([0])).fillna(0)

                annual_energy_MWh = (Q_dh_W.sum() / 1000) / 1000  # W to kW to MWh
                annual_booster_MWh = (Q_booster_W.sum() / 1000) / 1000

                peak_load_kW = (Q_dh_W.max() / 1000)  # W to kW

            elif network_type == 'DC':
                # For DC: cooling energy
                Q_dc_W = df.get('Qcs_W', pd.Series([0])).fillna(0)
                annual_energy_MWh = (Q_dc_W.sum() / 1000) / 1000
                annual_booster_MWh = 0  # No boosters in cooling

                peak_load_kW = (Q_dc_W.max() / 1000)

            else:
                raise ValueError(f"Invalid network type: {network_type}")

            # Average temperatures during active hours
            mdot_col = f'mdot_{network_type}_result_kgpers'
            T_supply_col = f'T_supply_{network_type}_result_C'
            T_return_col = f'T_return_{network_type}_result_C'

            required_cols = {mdot_col, T_supply_col, T_return_col}
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                avg_supply_temp = 0
                avg_return_temp = 0
                avg_delta_t = 0
            else:
                active_hours = df[mdot_col] > 0.01

                if active_hours.sum() > 0:
                    avg_supply_temp = df.loc[active_hours, T_supply_col].mean()
                    avg_return_temp = df.loc[active_hours, T_return_col].mean()
                    avg_delta_t = abs(avg_supply_temp - avg_return_temp)
                else:
                    avg_supply_temp = 0
                    avg_return_temp = 0
                    avg_delta_t = 0

            # Heat exchanger area (total for heating and DHW)
            if network_type == 'DH':
                hex_area_m2 = df.get('HEX_hs_area_m2', pd.Series([0])).max() + \
                              df.get('HEX_ww_area_m2', pd.Series([0])).max()
            else:
                hex_area_m2 = df.get('HEX_cs_area_m2', pd.Series([0])).max()

            metrics = {
                'annual_energy_MWh': round(annual_energy_MWh, 2),
                'peak_load_kW': round(peak_load_kW, 1),
                'avg_supply_temp_C': round(avg_supply_temp, 1),
                'avg_return_temp_C': round(avg_return_temp, 1),
                'avg_delta_t_C': round(avg_delta_t, 1),
                'hex_area_m2': round(hex_area_m2, 1),
            }

            # Add booster metrics for DH only
            if network_type == 'DH':
                metrics['annual_booster_MWh'] = round(annual_booster_MWh, 2)

            return metrics

        except Exception as e:
            logger.error(f"Error calculating substation metrics for {building_name}: {e}")
            return {}

    def _calculate_plant_metrics(self, network_type, network_name, plant_id):
        """
        Calculate plant performance metrics.

        Returns dict with:
        - annual_output_MWh: Total annual thermal output
        - peak_load_kW: Peak thermal load
        - capacity_factor_pct: Capacity factor (actual / potential at peak)
        - operating_hours: Hours with load > 1% of peak
        - operating_hours_pct: Percentage of year operating
        - avg_supply_temp_C: Average supply temperature
        - avg_return_temp_C: Average return temperature
        - min_supply_temp_C: Minimum supply temperature
        - max_supply_temp_C: Maximum supply temperature
        """
        try:
            # Load plant thermal load file
            plant_file = self.locator.get_thermal_network_plant_heat_requirement_file(network_type, network_name)

            if not os.path.exists(plant_file):
                logger.debug(f"Plant file doesn't exist: {plant_file}")
                return {}

            # Read hourly plant load
            plant_df = pd.read_csv(plant_file)

            # Annual output
            annual_output_MWh = plant_df['thermal_load_kW'].sum() / 1000

            # Peak load
            peak_load_kW = plant_df['thermal_load_kW'].max()

            # Capacity factor and operating hours
            capacity_factor_pct = 0
            operating_hours = 0
            operating_hours_pct = 0

            if peak_load_kW > 0:
                # Potential output if running at peak 24/7
                potential_output_MWh = peak_load_kW * 8760 / 1000

                # Actual capacity factor
                capacity_factor_pct = (annual_output_MWh / potential_output_MWh) * 100

                # Operating hours (hours with load > 1% of peak)
                operating_threshold = peak_load_kW * 0.01
                operating_hours = (plant_df['thermal_load_kW'] > operating_threshold).sum()
                operating_hours_pct = (operating_hours / 8760) * 100

            # Temperature statistics from supply temperature file
            temp_supply_file = self.locator.get_network_temperature_supply_nodes_file(network_type, network_name)

            if os.path.exists(temp_supply_file):
                temp_df = pd.read_csv(temp_supply_file)
                if plant_id in temp_df.columns:
                    # Convert K to C
                    avg_supply_temp_C = temp_df[plant_id].mean() - 273.15
                    min_supply_temp_C = temp_df[plant_id].min() - 273.15
                    max_supply_temp_C = temp_df[plant_id].max() - 273.15
                else:
                    avg_supply_temp_C = 0
                    min_supply_temp_C = 0
                    max_supply_temp_C = 0
            else:
                avg_supply_temp_C = 0
                min_supply_temp_C = 0
                max_supply_temp_C = 0

            # Return temperature statistics
            temp_return_file = self.locator.get_network_temperature_return_nodes_file(network_type, network_name)

            if os.path.exists(temp_return_file):
                temp_df = pd.read_csv(temp_return_file)
                if plant_id in temp_df.columns:
                    avg_return_temp_C = temp_df[plant_id].mean() - 273.15
                else:
                    avg_return_temp_C = 0
            else:
                avg_return_temp_C = 0

            return {
                'annual_output_MWh': round(annual_output_MWh, 2),
                'peak_load_kW': round(peak_load_kW, 1),
                'capacity_factor_pct': round(capacity_factor_pct, 1),
                'operating_hours': int(operating_hours),
                'operating_hours_pct': round(operating_hours_pct, 1),
                'avg_supply_temp_C': round(avg_supply_temp_C, 1),
                'avg_return_temp_C': round(avg_return_temp_C, 1),
                'min_supply_temp_C': round(min_supply_temp_C, 1),
                'max_supply_temp_C': round(max_supply_temp_C, 1),
            }

        except Exception as e:
            import traceback
            logger.error(f"Error calculating plant metrics: {e}")
            logger.error(traceback.format_exc())
            # Return empty values instead of empty dict to maintain consistency
            return {
                'annual_output_MWh': 0,
                'peak_load_kW': 0,
                'capacity_factor_pct': 0,
                'operating_hours': 0,
                'operating_hours_pct': 0,
                'avg_supply_temp_C': 0,
                'avg_return_temp_C': 0,
                'min_supply_temp_C': 0,
                'max_supply_temp_C': 0,
            }
