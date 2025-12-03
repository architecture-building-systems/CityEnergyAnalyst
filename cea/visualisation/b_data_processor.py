"""
PlotFormatter – prepares the formatting settings for the Plotly graph

"""

import os
import pandas as pd
import numpy as np
from cea.import_export.result_summary import month_names, month_hours, season_mapping, emission_timeline_hourly_operational_colnames_nounit, emission_timeline_yearly_colnames_nounit


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

x_to_plot_building = ['building', 'building_faceted_by_months', 'building_faceted_by_seasons', 'building_faceted_by_construction_type', 'building_faceted_by_main_use_type', 'building_faceted_by_decades']

class data_processor:
    """Cleans and processes the CSV data for visualization."""

    def __init__(self, plot_config, plot_config_general, plots_building_filter, plot_instance, plot_cea_feature, df_summary_data, df_architecture_data, solar_panel_types_list, scenario=None):
        self.df_summary_data = df_summary_data
        self.df_architecture_data = df_architecture_data
        self.buildings = plots_building_filter.buildings
        self.scenario_path = scenario

        # For lifecycle-emissions and emission-timeline, generate y_metric_to_plot from new parameters
        if plot_cea_feature in ('lifecycle-emissions', 'emission-timeline'):
            self.y_metric_to_plot = self._generate_lifecycle_emission_columns(plot_config)
        elif plot_cea_feature == 'operational-emissions':
            self.y_metric_to_plot = self._generate_operational_emission_columns(plot_config)
        else:
            self.y_metric_to_plot = plot_config.y_metric_to_plot

        self.y_metric_unit = plot_config.y_metric_unit
        self.y_normalised_by = plot_config.y_normalised_by
        self.x_to_plot = plot_instance.x
        self.x_facet = plot_instance.x_facet
        self.x_sorted_by = plot_config_general.x_sorted_by
        self.x_sorted_reversed = plot_config_general.x_sorted_reversed
        self.integer_year_start = plots_building_filter.filter_buildings_by_year_start
        self.integer_year_end = plots_building_filter.filter_buildings_by_year_end
        self.list_construction_type = plots_building_filter.filter_buildings_by_construction_type
        self.list_use_type = plots_building_filter.filter_buildings_by_use_type
        self.min_ratio_as_main_use = plots_building_filter.min_ratio_as_main_use

        if plot_cea_feature in ('pv', 'sc'):
            self.appendix = f"{plot_cea_feature}_{solar_panel_types_list[0]}"
        elif plot_cea_feature == 'pvt':
            if len(solar_panel_types_list) == 2:
                self.appendix = f"{plot_cea_feature}_{solar_panel_types_list[0]}_{solar_panel_types_list[1]}"
            else:
                raise ValueError("PVT requires two solar panel types.")
        else:
            self.appendix = plot_cea_feature

    def _generate_lifecycle_emission_columns(self, plot_config):
        """
        Generate column names for lifecycle emissions based on four config parameters.

        Parameters from plot_config:
        - y_category_to_plot: list of ['operation', 'production', 'demolition', 'biogenic']
        - operation_services: list of ['electricity', 'space_heating', 'space_cooling', 'dhw',
                                       'pv_electricity_offset', 'pv_electricity_export']
        - envelope_components: list of ['wall_ag', 'wall_bg', 'wall_part', 'win_ag', 'roof',
                                        'upperside', 'underside', 'floor', 'base', 'technical_systems', 'pv']
        - pv_code: str, single PV panel code (e.g., 'PV1')

        Returns:
        - list of column names (without unit suffix)
        """
        # Service name to tech name mapping
        service_to_tech = {
            'electricity': 'E_sys',
            'space_heating': 'Qhs_sys',
            'space_cooling': 'Qcs_sys',
            'dhw': 'Qww_sys',
        }

        categories = plot_config.y_category_to_plot
        operation_services = getattr(plot_config, 'operation_services', [])
        envelope_components = getattr(plot_config, 'envelope_components', [])
        pv_code = getattr(plot_config, 'pv_code', None)

        columns = []

        # Generate operation columns
        if 'operation' in categories:
            for service in operation_services:
                if service in service_to_tech:
                    # Regular operation service: operation_E_sys, operation_Qhs_sys, etc.
                    columns.append(f"operation_{service_to_tech[service]}")
                elif service == 'pv_electricity_offset' and pv_code:
                    # PV offset column: PV_{pv_code}_GRID_offset
                    columns.append(f"PV_{pv_code}_GRID_offset")
                elif service == 'pv_electricity_export' and pv_code:
                    # PV export column: PV_{pv_code}_GRID_export
                    columns.append(f"PV_{pv_code}_GRID_export")

        # Generate embodied columns (production, demolition, biogenic)
        for category in ['production', 'demolition', 'biogenic']:
            if category in categories:
                for component in envelope_components:
                    if component == 'pv' and pv_code:
                        # PV embodied emissions: production_PV_{pv_code}, demolition_PV_{pv_code}, etc.
                        columns.append(f"{category}_PV_{pv_code}")
                    else:
                        # Regular component: production_wall_ag, demolition_roof, biogenic_floor, etc.
                        columns.append(f"{category}_{component}")

        return columns

    def _generate_operational_emission_columns(self, plot_config):
        """
        Generate column names for operational emissions based on four config parameters.

        Parameters from plot_config:
        - y_category_to_plot: list of ['operation', 'energy_carrier']
        - operation_services: list of ['electricity', 'space_heating', 'space_cooling', 'dhw',
                                       'pv_electricity_offset', 'pv_electricity_export']
        - energy_carriers: list of ['GRID', 'NATURALGAS', 'BIOGAS', 'SOLAR', 'DRYBIOMASS',
                                    'WETBIOMASS', 'COAL', 'WOOD', 'OIL', 'HYDROGEN', 'NONE']
        - pv_code: str, single PV panel code (e.g., 'PV1')

        Returns:
        - list of column names (without unit suffix)

        Logic:
        - Both operation AND energy_carrier: Generate hybrids (Qhs_sys_NATURALGAS, E_sys_GRID, etc.)
        - Only operation: Generate aggregated by service (Qhs_sys, E_sys, etc.) + PV if selected
        - Only energy_carrier: Generate aggregated by carrier (GRID, NATURALGAS, etc.)
        """
        # Service name to tech name mapping
        service_to_tech = {
            'electricity': 'E_sys',
            'space_heating': 'Qhs_sys',
            'space_cooling': 'Qcs_sys',
            'dhw': 'Qww_sys',
        }

        categories = plot_config.y_category_to_plot
        operation_services = getattr(plot_config, 'operation_services', [])
        energy_carriers = getattr(plot_config, 'energy_carriers', [])
        pv_code = getattr(plot_config, 'pv_code', None)

        columns = []

        # Check if both operation and energy_carrier are selected
        both_selected = 'operation' in categories and 'energy_carrier' in categories

        if both_selected:
            # Generate hybrids: service × carrier combinations (e.g., Qhs_sys_NATURALGAS)
            for service in operation_services:
                if service in service_to_tech:
                    service_name = service_to_tech[service]
                    for carrier in energy_carriers:
                        columns.append(f"{service_name}_{carrier}")

            # Add PV columns if selected (PV doesn't combine with carriers)
            for service in operation_services:
                if service == 'pv_electricity_offset' and pv_code:
                    columns.append(f"PV_{pv_code}_GRID_offset")
                elif service == 'pv_electricity_export' and pv_code:
                    columns.append(f"PV_{pv_code}_GRID_export")

        elif 'operation' in categories:
            # Only operation: aggregated by service
            for service in operation_services:
                if service in service_to_tech:
                    # Aggregated service: E_sys, Qhs_sys, Qcs_sys, Qww_sys
                    columns.append(service_to_tech[service])
                elif service == 'pv_electricity_offset' and pv_code:
                    # PV offset column: PV_{pv_code}_GRID_offset
                    columns.append(f"PV_{pv_code}_GRID_offset")
                elif service == 'pv_electricity_export' and pv_code:
                    # PV export column: PV_{pv_code}_GRID_export
                    columns.append(f"PV_{pv_code}_GRID_export")

        elif 'energy_carrier' in categories:
            # Only energy_carrier: aggregated by carrier
            for carrier in energy_carriers:
                # Carrier columns: GRID, NATURALGAS, BIOGAS, etc.
                columns.append(carrier)

        return columns

    def _calculate_plant_floor_area(self, plant_name, area_type='GFA_m2'):
        """
        Calculate floor area for a plant based on buildings it services.

        Plant area = Sum(area of serviced buildings) / Number of plants of same type

        Args:
            plant_name: Name of the plant (e.g., 'crycry_DC_plant_001')
            area_type: Type of area to calculate ('GFA_m2' or 'Af_m2')

        Returns:
            float: Calculated floor area for the plant
        """
        import pandas as pd

        # Determine network type from plant name
        if '_DC_plant_' in plant_name:
            network_type = 'DC'
        elif '_DH_plant_' in plant_name:
            network_type = 'DH'
        else:
            print(f"Warning: Cannot determine network type for plant {plant_name}, using GFA=0")
            return 0.0

        # Extract network name from plant name (e.g., 'crycry_DC_plant_001' -> 'validation')
        # The network name is stored in locator.get_thermal_network_folder_building_names
        try:
            from cea.inputlocator import InputLocator
            locator = InputLocator(self.scenario_path)

            # Get list of network names by scanning thermal network folder
            thermal_network_folder = locator.get_thermal_network_folder()
            if not os.path.exists(thermal_network_folder):
                print(f"Warning: Thermal network folder not found at {thermal_network_folder}")
                return 0.0

            # Get all subdirectories as network names
            network_names = [d for d in os.listdir(thermal_network_folder)
                           if os.path.isdir(os.path.join(thermal_network_folder, d)) and not d.startswith('.')]

            # For each network, check if the plant services any buildings
            serviced_buildings = []
            for network_name in network_names:
                try:
                    # Read the metadata nodes file to find which buildings are serviced
                    metadata_file = locator.get_thermal_network_node_types_csv_file(network_type, network_name)
                    if not os.path.exists(metadata_file):
                        continue

                    metadata_df = pd.read_csv(metadata_file)

                    # Get buildings where type == 'CONSUMER'
                    consumer_nodes = metadata_df[metadata_df['type'] == 'CONSUMER']
                    buildings = consumer_nodes['building'].tolist()
                    serviced_buildings.extend([b for b in buildings if b != 'NONE'])
                except Exception as e:
                    print(f"Warning: Could not read metadata for {network_type}/{network_name}: {e}")
                    continue

            if not serviced_buildings:
                print(f"Warning: No serviced buildings found for plant {plant_name}, using GFA=0")
                return 0.0

            # Get GFA for serviced buildings from architecture data
            arch_data = self.df_architecture_data.set_index('name')
            available_buildings = [b for b in serviced_buildings if b in arch_data.index]

            if not available_buildings:
                print(f"Warning: No architecture data for buildings serviced by {plant_name}, using area=0")
                return 0.0

            # Sum the specified area type for serviced buildings
            total_area = arch_data.loc[available_buildings, area_type].sum()

            # Count number of plants of same type
            # Get all entities from summary data
            all_entities = self.df_summary_data['name'].tolist()
            plant_suffix = f'_{network_type}_plant_'
            num_plants = sum(1 for entity in all_entities if plant_suffix in entity)

            if num_plants == 0:
                print(f"Warning: No plants of type {network_type} found, using area=0")
                return 0.0

            plant_area = total_area / num_plants
            area_name = 'GFA' if area_type == 'GFA_m2' else 'Af'
            print(f"Calculated {area_name} for {plant_name}: {plant_area:.2f} m² "
                  f"(total: {total_area:.2f} m² / {num_plants} {network_type} plant(s))")

            return plant_area

        except Exception as e:
            print(f"Warning: Error calculating GFA for plant {plant_name}: {e}")
            return 0.0

    def process_architecture_data(self, plot_cea_feature=None):
        # For heat-rejection, include ALL entities from summary data (buildings + plants)
        if plot_cea_feature == 'heat-rejection' and self.df_summary_data is not None:
            # Get all entities from the summary data
            all_entities = set(self.df_summary_data['name'].unique())
            buildings_to_use = list(all_entities)
        else:
            # Filter to only buildings that exist in architecture data
            # (some buildings may be filtered out by year/type/use criteria)
            available_buildings = set(self.df_architecture_data['name'].unique())
            buildings_to_use = [b for b in self.buildings if b in available_buildings]

            if not buildings_to_use:
                raise ValueError(f"None of the requested buildings are in the architecture data. "
                               f"Requested: {self.buildings}, Available: {list(available_buildings)}")

            missing = set(self.buildings) - available_buildings
            if missing:
                print(f"Warning: {len(missing)} buildings filtered out from architecture data: {sorted(missing)}")

        if self.y_normalised_by == 'gross_floor_area':
            # Get architecture data for buildings that exist in it
            arch_data = self.df_architecture_data.set_index('name')
            buildings_in_arch = [b for b in buildings_to_use if b in arch_data.index]
            normaliser_m2 = arch_data.loc[buildings_in_arch, ['GFA_m2']].copy()
            normaliser_m2 = normaliser_m2.rename(columns={'GFA_m2': 'normaliser_m2'})

            # For heat-rejection, calculate GFA for plants
            if plot_cea_feature == 'heat-rejection':
                plants = [b for b in buildings_to_use if b not in buildings_in_arch]
                for plant in plants:
                    plant_area = self._calculate_plant_floor_area(plant, area_type='GFA_m2')
                    normaliser_m2.loc[plant] = plant_area

        elif self.y_normalised_by == 'conditioned_floor_area':
            arch_data = self.df_architecture_data.set_index('name')
            buildings_in_arch = [b for b in buildings_to_use if b in arch_data.index]
            normaliser_m2 = arch_data.loc[buildings_in_arch, ['Af_m2']].copy()
            normaliser_m2 = normaliser_m2.rename(columns={'Af_m2': 'normaliser_m2'})

            # For heat-rejection, calculate conditioned floor area for plants
            if plot_cea_feature == 'heat-rejection':
                plants = [b for b in buildings_to_use if b not in buildings_in_arch]
                for plant in plants:
                    plant_area = self._calculate_plant_floor_area(plant, area_type='Af_m2')
                    normaliser_m2.loc[plant] = plant_area

        elif self.y_normalised_by == 'no_normalisation':
            # Create normaliser with value 1 for ALL entities (including plants)
            import pandas as pd
            normaliser_m2 = pd.DataFrame({'normaliser_m2': 1}, index=buildings_to_use)
            normaliser_m2.index.name = 'name'
        else:
            raise ValueError(f"Invalid y-normalised-by: {self.y_normalised_by}")

        # Ensure only the 'normaliser_m2' column is retained
        normaliser_m2 = normaliser_m2[['normaliser_m2']]

        return normaliser_m2

    def process_sorting_key(self):
        if self.x_sorted_by == 'default':
            sorting_key = self.df_architecture_data.set_index('name').loc[self.buildings].copy()
            sorting_key['sorting_key'] = self.df_architecture_data.reset_index().index
        elif self.x_sorted_by == 'construction_year':
            sorting_key = self.df_architecture_data.set_index('name').loc[self.buildings, ['construction_year']].copy()
            sorting_key = sorting_key.rename(columns={'construction_year': 'sorting_key'})
        elif self.x_sorted_by == 'gross_floor_area':
            sorting_key = self.df_architecture_data.set_index('name').loc[self.buildings, ['GFA_m2']].copy()
            sorting_key = sorting_key.rename(columns={'GFA_m2': 'sorting_key'})
        elif self.x_sorted_by == 'conditioned_floor_area':
            sorting_key = self.df_architecture_data.set_index('name').loc[self.buildings, ['Af_m2']].copy()
            sorting_key = sorting_key.rename(columns={'Af_m2': 'sorting_key'})
        elif self.x_sorted_by == 'roof_area':
            sorting_key = self.df_architecture_data.set_index('name').loc[self.buildings, ['Aroof_m2']].copy()
            sorting_key = sorting_key.rename(columns={'Aroof_m2': 'sorting_key'})
        else:
            raise ValueError(f"Invalid x-sorted-by: {self.x_sorted_by}")

        sorting_key = sorting_key[['sorting_key']]

        return sorting_key


    def process_data(self, plot_cea_feature):
        if plot_cea_feature == 'demand':
            y_cea_metric_map = {
                'grid_electricity_consumption': 'GRID_kWh',
                'enduse_electricity_demand': 'E_sys_kWh',
                'enduse_cooling_demand': 'QC_sys_kWh',
                'enduse_space_cooling_demand': 'Qcs_sys_kWh',
                'enduse_heating_demand': 'QH_sys_kWh',
                'enduse_space_heating_demand': 'Qhs_sys_kWh',
                'enduse_dhw_demand': 'Qww_kWh',
            }

        elif plot_cea_feature == 'pv':
            y_cea_metric_map = {
                'total': ['E_PV_gen_kWh', 'area_PV_m2'],
                'roofs_top': ['PV_roofs_top_E_kWh', 'PV_roofs_top_m2'],
                'walls_north': ['PV_walls_north_E_kWh', 'PV_walls_north_m2'],
                'walls_east': ['PV_walls_east_E_kWh', 'PV_walls_east_m2'],
                'walls_south': ['PV_walls_south_E_kWh', 'PV_walls_south_m2'],
                'walls_west': ['PV_walls_west_E_kWh', 'PV_walls_west_m2'],
            }

        elif plot_cea_feature == 'pvt':
            if 'ET' in self.appendix:
                y_cea_metric_map = {
                    'total': ['E_PVT_gen_kWh', 'Q_PVT_gen_kWh', 'area_PVT_m2'],
                    'roofs_top': ['PVT_ET_roofs_top_E_kWh', 'PVT_ET_roofs_top_Q_kWh', 'PVT_ET_roofs_top_m2'],
                    'walls_north': ['PVT_ET_walls_north_E_kWh', 'PVT_ET_walls_north_Q_kWh', 'PVT_ET_walls_north_m2'],
                    'walls_east': ['PVT_ET_walls_east_E_kWh', 'PVT_ET_walls_east_Q_kWh', 'PVT_ET_walls_east_m2'],
                    'walls_south': ['PVT_ET_walls_south_E_kWh', 'PVT_ET_walls_south_Q_kWh', 'PVT_ET_walls_south_m2'],
                    'walls_west': ['PVT_ET_walls_west_E_kWh', 'PVT_ET_walls_west_Q_kWh', 'PVT_ET_walls_west_m2'],
                }
            elif 'FP' in self.appendix:
                y_cea_metric_map = {
                    'total': ['E_PVT_gen_kWh', 'Q_PVT_gen_kWh', 'area_PVT_m2'],
                    'roofs_top': ['PVT_FP_roofs_top_E_kWh', 'PVT_FP_roofs_top_Q_kWh', 'PVT_FP_roofs_top_m2'],
                    'walls_north': ['PVT_FP_walls_north_E_kWh', 'PVT_FP_walls_north_Q_kWh', 'PVT_FP_walls_north_m2'],
                    'walls_east': ['PVT_FP_walls_east_E_kWh', 'PVT_FP_walls_east_Q_kWh', 'PVT_FP_walls_east_m2'],
                    'walls_south': ['PVT_FP_walls_south_E_kWh', 'PVT_FP_walls_south_Q_kWh', 'PVT_FP_walls_south_m2'],
                    'walls_west': ['PVT_FP_walls_west_E_kWh', 'PVT_FP_walls_west_Q_kWh', 'PVT_FP_walls_west_m2'],
                }
            else:
                raise ValueError(f"Invalid PVT collector type in appendix: {self.appendix}")

        elif plot_cea_feature == 'sc':
            if 'ET' in self.appendix:
                y_cea_metric_map = {
                    'total': ['Q_SC_gen_kWh', 'area_SC_m2'],
                    'roofs_top': ['SC_ET_roofs_top_Q_kWh', 'SC_ET_roofs_top_m2'],
                    'walls_north': ['SC_ET_walls_north_Q_kWh', 'SC_ET_walls_north_m2'],
                    'walls_east': ['SC_ET_walls_east_Q_kWh', 'SC_ET_walls_east_m2'],
                    'walls_south': ['SC_ET_walls_south_Q_kWh', 'SC_ET_walls_south_m2'],
                    'walls_west': ['SC_ET_walls_west_Q_kWh', 'SC_ET_walls_west_m2'],
                }
            elif 'FP' in self.appendix:
                y_cea_metric_map = {
                    'total': ['Q_SC_gen_kWh', 'area_SC_m2'],
                    'roofs_top': ['SC_FP_roofs_top_Q_kWh', 'SC_FP_roofs_top_m2'],
                    'walls_north': ['SC_FP_walls_north_Q_kWh', 'SC_FP_walls_north_m2'],
                    'walls_east': ['SC_FP_walls_east_Q_kWh', 'SC_FP_walls_east_m2'],
                    'walls_south': ['SC_FP_walls_south_Q_kWh', 'SC_FP_walls_south_m2'],
                    'walls_west': ['SC_FP_walls_west_Q_kWh', 'SC_FP_walls_west_m2'],
                }
            else:
                raise ValueError(f"Invalid SC collector type in appendix: {self.appendix}")
        elif plot_cea_feature == 'operational-emissions':
            y_cea_metric_map = {
                key: [key+"_kgCO2e"] for key in emission_timeline_hourly_operational_colnames_nounit
            }
        elif plot_cea_feature == 'lifecycle-emissions':
            y_cea_metric_map = {
                key: [key+"_kgCO2e"] for key in emission_timeline_yearly_colnames_nounit
            }
        elif plot_cea_feature == 'heat-rejection':
            y_cea_metric_map = {
                'heat_rejection': 'heat_rejection_kWh'
            }

        else:
            raise ValueError(f"Unknown plot_cea_feature: '{plot_cea_feature}'")

        # Flatten metric list and remove any invalid entries
        list_columns = []
        for key in self.y_metric_to_plot:
            if key not in y_cea_metric_map:
                print(f"⚠️ Warning: '{key}' not found in metric map for {plot_cea_feature}. Skipped.")
                continue
            val = y_cea_metric_map[key]
            list_columns.extend(val if isinstance(val, list) else [val])

        # Debug: Check what columns are available
        if not list_columns:
            print(f"❌ No valid columns found for {plot_cea_feature} with metrics {self.y_metric_to_plot}")
            print(f"Available columns in data: {list(self.df_summary_data.columns)}")
            return pd.DataFrame(), []
        
        # Check if the required columns exist in the data
        missing_columns = [col for col in list_columns if col not in self.df_summary_data.columns]
        if missing_columns:
            # Check if missing columns are PV-related
            pv_missing_columns = [col for col in missing_columns if col.startswith('PV_') or '_PV_' in col]

            if pv_missing_columns:
                # Extract PV panel codes from missing column names
                # Format: PV_{code}_GRID_offset, PV_{code}_GRID_export, production_PV_{code}, etc.
                pv_codes = set()
                for col in pv_missing_columns:
                    if col.startswith('PV_'):
                        # Format: PV_{code}_GRID_offset or PV_{code}_GRID_export
                        parts = col.split('_')
                        if len(parts) >= 2:
                            pv_codes.add(parts[1])  # Extract code from PV_{code}_...
                    elif '_PV_' in col:
                        # Format: production_PV_{code}, demolition_PV_{code}, biogenic_PV_{code}
                        parts = col.split('_PV_')
                        if len(parts) == 2:
                            pv_codes.add(parts[1])  # Extract code from ..._PV_{code}

                if pv_codes:
                    pv_codes_list = sorted(pv_codes)
                    error_msg = (
                        f"PV electricity results missing for panel type(s): {', '.join(pv_codes_list)}. "
                        f"Please run the 'photovoltaic (PV) panels' script first to generate PV potential results for these panel types."
                    )
                    print(f"ERROR: {error_msg}")
                    raise FileNotFoundError(error_msg)

            # For non-PV missing columns, just warn and filter
            print(f"⚠️ Missing columns in data: {missing_columns}")
            print(f"Available columns: {list(self.df_summary_data.columns)}")
            # Filter out missing columns
            list_columns = [col for col in list_columns if col in self.df_summary_data.columns]
            if not list_columns:
                print("❌ No valid columns remaining after filtering")
                return pd.DataFrame(), []

        # Select proper index
        if self.x_to_plot == 'by_building':
            df_y_metrics = self.df_summary_data.set_index('name')[list_columns]
        elif self.x_to_plot == 'by_period':
            df_y_metrics = self.df_summary_data.set_index('period')[list_columns]
        else:
            raise ValueError(f"Invalid x_to_plot: {self.x_to_plot}")

        return df_y_metrics, list_columns


def normalise_dataframe_by_index(dataframe_A, dataframe_B):
    """
    Normalize each column in dataframe_A by the corresponding value in dataframe_B based on index matching.

    Parameters:
    - dataframe_A (pd.DataFrame): A DataFrame with potentially repeated index values and one or more columns.
    - dataframe_B (pd.DataFrame): A DataFrame with unique index values and exactly one column (the normaliser).

    Returns:
    - pd.DataFrame: A normalized version of dataframe_A with the same shape.
    """

    # Ensure both inputs are DataFrames
    if not isinstance(dataframe_A, pd.DataFrame) or not isinstance(dataframe_B, pd.DataFrame):
        raise ValueError("Both inputs must be pandas DataFrames.")

    # Check that dataframe_B has only one column
    if dataframe_B.shape[1] != 1:
        raise ValueError("dataframe_B must have exactly one column.")

    # Copy inputs to avoid modifying them
    dfA = dataframe_A.copy()
    dfB = dataframe_B.copy()

    # Reset index for merge
    dfA_reset = dfA.reset_index()
    dfB_reset = dfB.reset_index()

    # Get index name for merge
    key_column = dfB.index.name if dfB.index.name is not None else 'index'
    dfB_reset.columns = [key_column, 'normaliser']

    if key_column not in dfA_reset.columns:
        dfA_reset[key_column] = dataframe_A.index

    # Merge
    merged = dfA_reset.merge(dfB_reset, on=key_column, how='left')

    # Normalize original columns
    original_columns = dataframe_A.columns
    for col in original_columns:
        merged[col] = merged[col] / merged['normaliser']

    # Drop normaliser column
    merged = merged.drop(columns=['normaliser'])

    # Restore original index
    merged.set_index(key_column, inplace=True)

    return merged


def convert_energy_units(dataframe, target_unit, normalised=False, plot_cea_feature=None):
    """
    Converts energy unit columns in a DataFrame to the specified unit.

    Parameters:
        dataframe (pd.DataFrame): The input DataFrame with energy columns.
        target_unit (str): One of ['Wh', 'kWh', 'MWh'].
        normalised (bool): If True, appends '/m2' to the renamed unit.

    Returns:
        pd.DataFrame: A new DataFrame with converted energy units and renamed columns.
    """
    if plot_cea_feature in ('operational-emissions', 'lifecycle-emissions'):
        assert target_unit in ['gCO2e', 'kgCO2e', 'tonCO2e'], "target_unit must be one of ['gCO2e', 'kgCO2e', 'tonCO2e']"

        conversion_to_wh = {'gCO2e': 1, 'kgCO2e': 1_000, 'tonCO2e': 1_000_000}
        df = dataframe.copy()
        new_columns = {}

        for col in df.columns:
            for unit in conversion_to_wh:
                if col.endswith(f"_{unit}"):
                    # Convert values
                    factor = conversion_to_wh[unit] / conversion_to_wh[target_unit]
                    df[col] = df[col] * factor

                    # Rename column
                    suffix = f"{target_unit}/m2" if normalised else target_unit
                    new_col = col.replace(f"_{unit}", f"_{suffix}")
                    new_columns[col] = new_col
                    break  # Stop after first match

    else:
        assert target_unit in ['Wh', 'kWh', 'MWh'], "target_unit must be one of ['Wh', 'kWh', 'MWh']"

        conversion_to_wh = {'Wh': 1, 'kWh': 1_000, 'MWh': 1_000_000}
        df = dataframe.copy()
        new_columns = {}

        for col in df.columns:
            for unit in conversion_to_wh:
                if col.endswith(f"_{unit}"):
                    # Convert values
                    factor = conversion_to_wh[unit] / conversion_to_wh[target_unit]
                    df[col] = df[col] * factor

                    # Rename column
                    suffix = f"{target_unit}/m2" if normalised else target_unit
                    new_col = col.replace(f"_{unit}", f"_{suffix}")
                    new_columns[col] = new_col
                    break  # Stop after first match

    df.rename(columns=new_columns, inplace=True)
    return df


def generate_dataframe_for_plotly(plot_instance, df_summary_data, df_architecture_data, plot_cea_feature):
    """
    Generate a Plotly-ready DataFrame based on user-defined configuration.

    Parameters
    ----------
    plot_instance : object
        Configuration and logic object containing plotting parameters and methods.
    df_summary_data : pd.DataFrame
        Aggregated demand or generation results.
    df_architecture_data : pd.DataFrame
        Metadata for buildings (e.g., use type, construction year).
    plot_cea_feature : str
        Feature to be plotted: 'demand', 'pv', 'pvt', or 'sc'.

    Returns
    -------
    pd.DataFrame
        A processed DataFrame ready for Plotly visualization.
    list
        List of column names used for plotting Y-values.
    """
    # Step 1: Prepare normaliser and raw Y-axis metrics
    if plot_instance.y_normalised_by in ('no_normalisation', 'gross_floor_area', 'conditioned_floor_area'):
        normaliser_m2 = plot_instance.process_architecture_data(plot_cea_feature)
    df_y_metrics, list_y_columns = plot_instance.process_data(plot_cea_feature)

    # Step 2: Handle "by_building" mode
    if plot_instance.x_to_plot == 'by_building':
        if plot_cea_feature in ('demand',  'operational-emissions', 'lifecycle-emissions', 'heat-rejection'):
            df_to_plotly = normalise_dataframe_by_index(df_y_metrics, normaliser_m2)

        elif plot_cea_feature in ('pv', 'pvt', 'sc'):
            norm = plot_instance.y_normalised_by
            if norm == 'no_normalisation':
                df_to_plotly = remove_m2_columns(df_y_metrics)
            elif norm == 'solar_technology_area_installed_for_respective_surface':
                df_to_plotly = normalise_dataframe_columns_by_m2_columns(df_y_metrics)
            elif norm == 'gross_floor_area':
                df_to_plotly = normalise_dataframe_by_index(remove_m2_columns(df_y_metrics), normaliser_m2)
            else:
                raise ValueError(f"Invalid y_normalised_by: {norm}")
        else:
            raise ValueError(f"Invalid plot_cea_feature: {plot_cea_feature}")

        # Assign X and X_facet
        df_to_plotly = df_to_plotly.reset_index(drop=False).rename(columns={'name': 'X'})
        facet = plot_instance.x_facet
        if facet in ['months', 'seasons']:
            df_to_plotly['X_facet'] = df_summary_data['period']
        elif facet in ['construction_type', 'main_use_type']:
            df_to_plotly['X_facet'] = df_architecture_data[facet]
        elif facet is not None:
            raise ValueError(f"Invalid x_facet: {facet}")

    # Step 3: Handle "by_period" mode
    elif plot_instance.x_to_plot == 'by_period':
        norm = plot_instance.y_normalised_by
        if norm == 'no_normalisation':
            df_to_plotly = remove_m2_columns(df_y_metrics) if plot_cea_feature in ('pv', 'pvt', 'sc') else df_y_metrics
        elif norm == 'solar_technology_area_installed_for_respective_surface':
            if plot_cea_feature in ('pv', 'pvt', 'sc'):
                df_to_plotly = normalise_dataframe_columns_by_m2_columns(df_y_metrics)
            else:
                raise ValueError(f"Invalid plot_cea_feature: {plot_cea_feature}")
        else:
            total_area = normaliser_m2.iloc[:, 0].sum()
            df_to_plotly = df_y_metrics / total_area

        # Assign X and X_facet
        df_to_plotly = df_to_plotly.reset_index(drop=False).rename(columns={'period': 'X'})
        facet = plot_instance.x_facet
        if facet in ['months', 'seasons']:
            df_to_plotly = calc_x_facet(df_to_plotly, facet)
        elif facet is not None:
            raise ValueError(f"Invalid x_facet: {facet}")
    else:
        raise ValueError(f"Invalid x_to_plot: {plot_instance.x_to_plot}")

    # Step 4: Clean index
    df_to_plotly = df_to_plotly.reset_index(drop=True)

    # Step 5: Convert energy units
    is_normalised = plot_instance.y_normalised_by != 'no_normalisation'
    df_to_plotly = convert_energy_units(df_to_plotly, plot_instance.y_metric_unit, normalised=is_normalised, plot_cea_feature=plot_cea_feature)

    # Step 6: Refine list_y_columns
    valid_cols = df_to_plotly.columns.difference(['X', 'X_facet']).tolist()
    updated_list_y_columns = []
    for col in list_y_columns:
        if col.endswith('_m2'):
            continue
        if col in valid_cols:
            updated_list_y_columns.append(col)
        else:
            if plot_cea_feature in ('operational-emissions', 'lifecycle-emissions'):
                base = col.replace('_kgCO2e', f'_{plot_instance.y_metric_unit}')
            else:
                base = col.replace('_kWh', f'_{plot_instance.y_metric_unit}')
            maybe_col = f"{base}/m2" if is_normalised else base
            if maybe_col in valid_cols:
                updated_list_y_columns.append(maybe_col)
    list_y_columns = updated_list_y_columns

    # Step 7: Reorder columns for 'pvt' (electricity first, then heat)
    if plot_cea_feature == 'pvt':
        elec_cols = [c for c in list_y_columns if 'E_' in c]
        heat_cols = [c for c in list_y_columns if 'Q_' in c]
        list_y_columns = elec_cols + heat_cols
        essentials = ['X', 'X_facet'] if 'X_facet' in df_to_plotly.columns else ['X']
        df_to_plotly = df_to_plotly[essentials + list_y_columns]

    return df_to_plotly, list_y_columns


def sort_df_by_sorting_key(df_1, df_2, descending=False):
    # Copy to avoid mutating original data
    df_1 = df_1.copy()
    df_2 = df_2.copy()

    # Map sorting_key to df_2 using df_2['X']
    sorting_map = df_1['sorting_key']
    df_2['_sorting_key'] = df_2['X'].map(sorting_map)

    # Sort with stable sort to preserve original order for ties
    df_2_sorted = df_2.sort_values(
        by='_sorting_key',
        ascending=not descending,
        kind='mergesort'
    )

    # Drop helper column
    df_2_sorted = df_2_sorted.drop(columns=['_sorting_key'])

    return df_2_sorted

def remove_m2_columns(df):
    """
    Remove all columns that end with '_m2' from the given DataFrame.

    Parameters:
    - df (pd.DataFrame): Input DataFrame.

    Returns:
    - pd.DataFrame: A new DataFrame without '_m2' columns.
    """
    return df[[col for col in df.columns if not col.endswith('_m2')]]


def calc_x_facet(df_to_plotly, facet_by):
    def get_month_from_x(x):
        if x.startswith("H_"):
            hour_index = int(x.replace("H_", ""))
            total = 0
            for i, m in enumerate(month_names):
                total += month_hours[m]
                if hour_index < total:
                    return m
        elif x.startswith("D_"):
            day_index = int(x.replace("D_", ""))
            total_days = 0
            for i, m in enumerate(month_names):
                days_in_month = month_hours[m] // 24
                total_days += days_in_month
                if day_index < total_days:
                    return m
        elif x in month_names:
            return x
        return None

    if facet_by not in ['months', 'seasons']:
        raise ValueError("facet_by must be either 'months' or 'season'")

    # Compute months first
    df_to_plotly['X_facet'] = df_to_plotly['X'].apply(get_month_from_x)

    # If facet_by is season, map month to season
    if facet_by == 'seasons':
        df_to_plotly['X_facet'] = df_to_plotly['X_facet'].map(lambda m: season_mapping[month_names.index(m) + 1] if m in month_names else None)

    return df_to_plotly


def normalise_dataframe_columns_by_m2_columns(df_y_metrics):
    """
    Normalize metric columns in the dataframe by their corresponding m2 columns and drop the m2 columns.

    If area is zero or missing for any row, the resulting value will be set to 0 (instead of dividing by zero).

    Parameters
    ----------
    df_y_metrics : pd.DataFrame
        Input dataframe with area and metric columns.

    Returns
    -------
    pd.DataFrame
        Normalized dataframe with area columns removed.
    """
    mapping = {
        'area_PV_m2': 'E_PV_gen_kWh',
        'PV_roofs_top_m2': 'PV_roofs_top_E_kWh',
        'PV_walls_north_m2': 'PV_walls_north_E_kWh',
        'PV_walls_east_m2': 'PV_walls_east_E_kWh',
        'PV_walls_south_m2': 'PV_walls_south_E_kWh',
        'PV_walls_west_m2': 'PV_walls_west_E_kWh',
        'area_PVT_m2': ['E_PVT_gen_kWh', 'Q_PVT_gen_kWh'],
        'PVT_ET_roofs_top_m2': ['PVT_ET_roofs_top_E_kWh', 'PVT_ET_roofs_top_Q_kWh'],
        'PVT_ET_walls_north_m2': ['PVT_ET_walls_north_E_kWh', 'PVT_ET_walls_north_Q_kWh'],
        'PVT_ET_walls_east_m2': ['PVT_ET_walls_east_E_kWh', 'PVT_ET_walls_east_Q_kWh'],
        'PVT_ET_walls_south_m2': ['PVT_ET_walls_south_E_kWh', 'PVT_ET_walls_south_Q_kWh'],
        'PVT_ET_walls_west_m2': ['PVT_ET_walls_west_E_kWh', 'PVT_ET_walls_west_Q_kWh'],
        'PVT_FP_roofs_top_m2': ['PVT_FP_roofs_top_E_kWh', 'PVT_FP_roofs_top_Q_kWh'],
        'PVT_FP_walls_north_m2': ['PVT_FP_walls_north_E_kWh', 'PVT_FP_walls_north_Q_kWh'],
        'PVT_FP_walls_east_m2': ['PVT_FP_walls_east_E_kWh', 'PVT_FP_walls_east_Q_kWh'],
        'PVT_FP_walls_south_m2': ['PVT_FP_walls_south_E_kWh', 'PVT_FP_walls_south_Q_kWh'],
        'PVT_FP_walls_west_m2': ['PVT_FP_walls_west_E_kWh', 'PVT_FP_walls_west_Q_kWh'],
        'area_SC_m2': 'Q_SC_gen_kWh',
        'SC_ET_roofs_top_m2': 'SC_ET_roofs_top_Q_kWh',
        'SC_ET_walls_north_m2': 'SC_ET_walls_north_Q_kWh',
        'SC_ET_walls_east_m2': 'SC_ET_walls_east_Q_kWh',
        'SC_ET_walls_south_m2': 'SC_ET_walls_south_Q_kWh',
        'SC_ET_walls_west_m2': 'SC_ET_walls_west_Q_kWh',
        'SC_FP_roofs_top_m2': 'SC_FP_roofs_top_Q_kWh',
        'SC_FP_walls_north_m2': 'SC_FP_walls_north_Q_kWh',
        'SC_FP_walls_east_m2': 'SC_FP_walls_east_Q_kWh',
        'SC_FP_walls_south_m2': 'SC_FP_walls_south_Q_kWh',
        'SC_FP_walls_west_m2': 'SC_FP_walls_west_Q_kWh',
    }

    df = df_y_metrics.copy()

    for area_col, metrics in mapping.items():
        if area_col not in df.columns:
            continue

        if isinstance(metrics, str):
            metrics = [metrics]

        for metric in metrics:
            if metric in df.columns:
                # Avoid division by 0 by masking
                with np.errstate(divide='ignore', invalid='ignore'):
                    area = df[area_col]
                    mask = area > 0
                    # Create normalized values: 0 where area <= 0, metric/area where area > 0
                    df[metric] = np.where(mask, df[metric] / area, 0.0)

    # Drop all *_m2 columns
    df.drop(columns=[col for col in df.columns if col.endswith('_m2')], inplace=True)

    return df


# Main function
def calc_x_y_metric(plot_config, plot_config_general, plots_building_filter, plot_instance_a, plot_cea_feature, df_summary_data, df_architecture_data, solar_panel_types_list, scenario=None):
    plot_instance_b = data_processor(plot_config, plot_config_general, plots_building_filter, plot_instance_a, plot_cea_feature, df_summary_data, df_architecture_data, solar_panel_types_list, scenario)

    if plot_cea_feature in ["demand", "pv", "pvt", "sc", "operational-emissions", "lifecycle-emissions", "heat-rejection"]:
        df_to_plotly, list_y_columns = generate_dataframe_for_plotly(plot_instance_b, df_summary_data, df_architecture_data, plot_cea_feature)

        if plot_instance_b.x_to_plot in x_to_plot_building:
            df_to_plotly = sort_df_by_sorting_key(plot_instance_b.process_sorting_key(), df_to_plotly, descending=plot_instance_b.x_sorted_reversed)

    else:
        print("Error: Unsupported feature:", plot_cea_feature)
        df_to_plotly = pd.DataFrame()   # This is unlikely to be used
        list_y_columns = []
    return df_to_plotly, list_y_columns
