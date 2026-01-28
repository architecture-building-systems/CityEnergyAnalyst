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

# Multi-phase plan suffix
MULTI_PHASE_SUFFIX = " (Multi-Phase)"


class ThermalNetworkMapLayer(MapLayer):
    category = ThermalNetworkCategory
    name = "thermal-network"
    label = "Thermal Network"
    description = "Thermal Network Design"

    _network_types = ["DC", "DH"]

    def _get_network_types(self):
        # Return both choices and default (DC is default)
        return {"choices": self._network_types, "default": self._network_types[0]}

    def _is_multiphase(self, network_name: str) -> bool:
        """Check if a network name represents a multi-phase plan"""
        if not network_name:
            return False
        return network_name.endswith(MULTI_PHASE_SUFFIX)

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
    
    def _get_thermal_network_phasing_plan_phases(self, network_type, plan_name):
        """Get list of phase folders for a phasing plan, sorted by phase index"""
        plan_folder = self.locator.get_thermal_network_phasing_folder(network_type, plan_name)
        phases = []
        if os.path.exists(plan_folder):
            for item in os.listdir(plan_folder):
                # FIXME: Read phase names from phasing_summary.csv instead
                if os.path.isdir(os.path.join(plan_folder, item)) and item != "layout":
                    phases.append(item)

        def get_phase_index(phase_name):
            """Extract numeric index from phase folder name (e.g., 'phase10_2030' -> 10)"""
            try:
                # Extract the part between 'phase' and '_'
                index_str = phase_name[5:phase_name.index('_')]
                return int(index_str)
            except (ValueError, IndexError):
                return 0

        return sorted(phases, key=get_phase_index)

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
                    phases = self._get_thermal_network_phasing_plan_phases(network_type, plan_name)
                    if phases:
                        # Add with (Multi-Phase) suffix to distinguish from regular networks
                        display_name = f"{plan_name}{MULTI_PHASE_SUFFIX}"
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
            if not self._is_multiphase(network_name):
                return {"choices": [], "default": ""}

            # Extract plan name (remove suffix)
            plan_name = network_name.replace(MULTI_PHASE_SUFFIX, '')

            # Get available phases
            phases = self._get_thermal_network_phasing_plan_phases(network_type, plan_name)
            phase_summary = pd.read_csv(self.locator.get_thermal_network_phasing_summary_file(network_type, plan_name))

            if "network" not in phase_summary.columns or "year" not in phase_summary.columns:
                raise ValueError(f"Phase summary is missing required columns ('network', 'year') for plan {plan_name}")
            
            phase_summary = phase_summary.set_index('network')

            if not phases:
                logger.debug(f"No phases found for plan {plan_name}")
                return {"choices": [], "default": ""}

            # Create human-readable labels
            choices = []
            for phase in phases:
                # Extract year from phase to construct label (e.g., "2030 - phase name")
                year = phase_summary.loc[phase, 'year'] if phase in phase_summary.index else ''
                choices.append({"value": phase, "label": f"{year} - {phase}" })

            logger.debug(f"Found {len(choices)} phase choices for {plan_name}: {choices}")

            return {"choices": sorted(choices, key=lambda x: x["label"]), "default": phases[0] if phases else ""}

        except Exception as e:
            logger.error(f"Error in _get_phase_choices: {e}")
            return {"choices": [], "default": ""}

    def _get_network_layout_files(self, parameters):
        network_name = parameters.get('network-name')

        # Handle None, undefined, empty string, or placeholder text
        if network_name is None or network_name == 'undefined' or network_name == '' or network_name == 'No network available':
            return []

        # Multi-phase plans don't have layout shapefiles (optional)
        if self._is_multiphase(network_name):
            return []

        return [
            self.locator.get_network_layout_shapefile(network_name),
        ]

    def _get_network_results_files(self, parameters):
        network_type = parameters.get('network-type')
        network_name = parameters.get('network-name')

        # Handle None, undefined, or empty string
        if network_type is None or network_type == 'undefined':
            return []
        if network_name is None or network_name == 'undefined' or network_name == '' or network_name == 'No network available':
            return []

        # Multi-phase plans don't have massflow files (optional)
        if self._is_multiphase(network_name):
            return []

        return [
            self.locator.get_thermal_network_layout_massflow_edges_file(network_type, network_name),
        ]

    def _get_network_nodes_files(self, parameters):
        network_type = parameters.get('network-type')
        network_name = parameters.get('network-name')
        phase = parameters.get('phase', '')

        # Handle None, undefined, or empty string
        if network_type is None or network_type == 'undefined':
            return []
        if network_name is None or network_name == 'undefined' or network_name == '' or network_name == 'No network available':
            return []

        # Check if multi-phase plan
        if self._is_multiphase(network_name):
            plan_name = network_name.replace(MULTI_PHASE_SUFFIX, '')
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
        if network_type is None or network_type == 'undefined':
            return []
        if network_name is None or network_name == 'undefined' or network_name == '' or network_name == 'No network available':
            return []

        # Check if multi-phase plan
        if self._is_multiphase(network_name):
            plan_name = network_name.replace(MULTI_PHASE_SUFFIX, '')
            return [
                self.locator.get_thermal_network_phase_edges_shapefile(network_type, plan_name, phase),
            ]

        return [
            self.locator.get_network_layout_edges_shapefile(network_type, network_name),
        ]

    def _get_plant_files(self, parameters):
        """Get plant heat requirement file path for regular or phasing networks"""
        network_type = parameters.get('network-type')
        network_name = parameters.get('network-name')
        phase = parameters.get('phase', '')

        if not network_type or not network_name or network_name == 'No network available':
            return []

        if self._is_multiphase(network_name):
            plan_name = network_name.replace(MULTI_PHASE_SUFFIX, '')
            return [self.locator.get_thermal_network_phasing_plant_heat_requirement_file(
                network_type, plan_name, phase
            )]

        return [self.locator.get_thermal_network_plant_heat_requirement_file(network_type, network_name)]

    def _get_temperature_files(self, parameters):
        """Get temperature supply and return file paths for regular or phasing networks"""
        network_type = parameters.get('network-type')
        network_name = parameters.get('network-name')
        phase = parameters.get('phase', '')

        if not network_type or not network_name or network_name == 'No network available':
            return []

        if self._is_multiphase(network_name):
            plan_name = network_name.replace(MULTI_PHASE_SUFFIX, '')
            return [
                self.locator.get_thermal_network_phasing_temperature_supply_nodes_file(network_type, plan_name, phase),
                self.locator.get_thermal_network_phasing_temperature_return_nodes_file(network_type, plan_name, phase),
            ]

        return [
            self.locator.get_network_temperature_supply_nodes_file(network_type, network_name),
            self.locator.get_network_temperature_return_nodes_file(network_type, network_name),
        ]

    def _get_phasing_summary_file(self, parameters):
        """Get phasing summary file for multi-phase plans"""
        network_type = parameters.get('network-type')
        network_name = parameters.get('network-name')

        if not network_type or not network_name or network_name == 'No network available':
            return []

        if not self._is_multiphase(network_name):
            return []

        plan_name = network_name.replace(MULTI_PHASE_SUFFIX, '')
        return [self.locator.get_thermal_network_phasing_summary_file(network_type, plan_name)]

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
                    description="Select phase for multi-phase plans",
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
                depends_on=["network-name", "network-type", "phase"],
            ),
            # Edges files are optional, we can still show potential layout
            FileRequirement(
                "Network Edges",
                file_locator="layer:_get_network_edges_files",
                depends_on=["network-name", "network-type", "phase"],
                optional=True,
            ),
            # Results files are optional, we can still show layout without mass flow data
            FileRequirement(
                "Network Results",
                file_locator="layer:_get_network_results_files",
                depends_on=["network-name", "network-type"],
                optional=True,
            ),
            # Plant and temperature files for cache invalidation (results data)
            FileRequirement(
                "Plant Heat Requirement",
                file_locator="layer:_get_plant_files",
                depends_on=["network-name", "network-type", "phase"],
                optional=True,
            ),
            FileRequirement(
                "Temperature Files",
                file_locator="layer:_get_temperature_files",
                depends_on=["network-name", "network-type", "phase"],
                optional=True,
            ),
            # Phasing summary file (for multi-phase plans only)
            FileRequirement(
                "Phasing Summary",
                file_locator="layer:_get_phasing_summary_file",
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

        # Determine file paths based on whether it's a phasing plan
        is_phasing_plan: bool = self._is_multiphase(network_name)
        if is_phasing_plan:
            plan_name = network_name.replace(MULTI_PHASE_SUFFIX, '')

            edges_path = self.locator.get_thermal_network_phase_edges_shapefile(network_type, plan_name, phase)
            nodes_path = self.locator.get_thermal_network_phase_nodes_shapefile(network_type, plan_name, phase)
            massflow_edges_path = self.locator.get_thermal_network_phasing_massflow_edges_file(network_type, plan_name, phase)

            def get_substation_file(building):
                return self.locator.get_thermal_network_phasing_substation_results_file(
                    building, network_type, plan_name, phase
                )

            plant_file = self.locator.get_thermal_network_phasing_plant_heat_requirement_file(
                network_type, plan_name, phase
            )
            temp_supply_file = self.locator.get_thermal_network_phasing_temperature_supply_nodes_file(
                network_type, plan_name, phase
            )
            temp_return_file = self.locator.get_thermal_network_phasing_temperature_return_nodes_file(
                network_type, plan_name, phase
            )
        else:
            edges_path = self.locator.get_network_layout_edges_shapefile(network_type, network_name)
            nodes_path = self.locator.get_network_layout_nodes_shapefile(network_type, network_name)
            massflow_edges_path = self.locator.get_thermal_network_layout_massflow_edges_file(network_type, network_name)

            def get_substation_file(building):
                return self.locator.get_thermal_network_substation_results_file(
                    building, network_type, network_name
                )

            plant_file = self.locator.get_thermal_network_plant_heat_requirement_file(network_type, network_name)
            temp_supply_file = self.locator.get_network_temperature_supply_nodes_file(network_type, network_name)
            temp_return_file = self.locator.get_network_temperature_return_nodes_file(network_type, network_name)

        # Decide which files to load: either the full network (edges + nodes) or potential layout + nodes
        _edges_path = edges_path
        if not is_phasing_plan:
            if not self._check_valid_network(network_name, network_type):
                if self._check_potential_network(network_name, network_type):
                    logger.debug(f"Valid network files don't exist for {network_name} ({network_type}), loading potential layout instead.")
                    _edges_path = self.locator.get_network_layout_shapefile(network_name)

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
        if massflow_edges_path and os.path.exists(massflow_edges_path):
            logger.debug(f"Loading massflow from {massflow_edges_path}")
            massflow_edges_df = pd.read_csv(massflow_edges_path)
            edges_df["peak_mass_flow"] = massflow_edges_df.max().round(1)
        else:
            logger.debug("Massflow file doesn't exist or not applicable, skipping")

        # Enrich nodes with substation and plant performance data
        for node_id in nodes_df.index:
            node_type = str(nodes_df.loc[node_id, 'type'])

            if node_type == 'CONSUMER':
                building_name = nodes_df.loc[node_id, 'building']
                substation_file = get_substation_file(building_name)
                metrics = self._calculate_substation_metrics(substation_file, network_type)
                for key, value in metrics.items():
                    nodes_df.loc[node_id, key] = value

            elif node_type.startswith('PLANT'):
                metrics = self._calculate_plant_metrics(plant_file, temp_supply_file, temp_return_file, node_id)
                for key, value in metrics.items():
                    nodes_df.loc[node_id, key] = value

        output['nodes'] = json.loads(nodes_df.to_json())
        output['edges'] = json.loads(edges_df.to_json())

        return output


    def _calculate_substation_metrics(self, substation_file, network_type):
        """
        Calculate substation performance metrics from a substation file.

        :param substation_file: Path to the substation CSV file
        :param network_type: Network type ('DH' or 'DC')

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

    def _calculate_plant_metrics(self, plant_file, temp_supply_file, temp_return_file, plant_id):
        """
        Calculate plant performance metrics from plant files.

        :param plant_file: Path to the plant thermal load CSV file
        :param temp_supply_file: Path to the supply temperature CSV file
        :param temp_return_file: Path to the return temperature CSV file
        :param plant_id: Plant node ID

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


