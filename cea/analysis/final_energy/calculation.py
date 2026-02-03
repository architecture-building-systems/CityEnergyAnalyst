"""
Final Energy Calculation - Core Logic

This module implements the core calculation logic for converting building demand
to final energy consumption by carrier.

Key approach (from IMPLEMENTATION_PLAN.md):
- Use constant efficiency from COMPONENTS database (not part-load curves)
- Assembly → Component → Feedstock workflow
- District systems read from thermal-network results
- Booster systems handled separately

"""

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

import os
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple

import cea.config
import cea.inputlocator
from cea.utilities.dbf import dbf_to_dataframe


# Constants
HOURS_IN_YEAR = 8760


def calculate_building_final_energy(
    building_name: str,
    locator: cea.inputlocator.InputLocator,
    config: cea.config.Configuration
) -> pd.DataFrame:
    """
    Calculate hourly final energy consumption by carrier for one building.

    Workflow:
    1. Read hourly demand from demand/{building}.csv
    2. Load supply system configuration (from supply.csv or config parameters)
    3. For each service (heating, cooling, DHW):
       - Get assembly code → load component → get feedstock
       - Apply constant efficiency: final_energy = demand / efficiency
    4. Handle district heating/cooling (read from thermal-network results)
    5. Handle booster systems (read from booster substation files)
    6. Return DataFrame with 8760 rows and carrier columns

    :param building_name: Name of the building (e.g., 'B1001')
    :param locator: InputLocator instance
    :param config: Configuration instance
    :return: DataFrame with columns: date, Qhs_sys_kWh, ..., scale, case, case_description
    """
    # Step 1: Read demand
    demand_file = locator.get_demand_results_file(building_name)
    if not os.path.exists(demand_file):
        raise FileNotFoundError(
            f"Demand file not found for building {building_name}: {demand_file}\n"
            f"Please run 'cea demand' first."
        )

    demand_df = pd.read_csv(demand_file)

    # Initialize output DataFrame with demand columns
    final_energy = pd.DataFrame({
        'date': demand_df['DATE'],  # Assuming DATE column exists
        'Qhs_sys_kWh': demand_df['Qhs_sys_kWh'],
        'Qww_sys_kWh': demand_df['Qww_sys_kWh'],
        'Qcs_sys_kWh': demand_df['Qcs_sys_kWh'],
        'E_sys_kWh': demand_df['E_sys_kWh'],
    })

    # Step 2: Load supply configuration
    supply_config = load_supply_configuration(building_name, locator, config)

    # Step 3: Calculate final energy for each service
    # Space heating
    if supply_config['space_heating']['scale'] == 'BUILDING':
        # Building-scale: use component efficiency
        carrier = supply_config['space_heating']['carrier']
        efficiency = supply_config['space_heating']['efficiency']
        final_energy[f'Qhs_sys_{carrier}_kWh'] = demand_df['Qhs_sys_kWh'] / efficiency
    elif supply_config['space_heating']['scale'] == 'DISTRICT':
        # District heating: read from thermal-network
        network_name = supply_config['space_heating']['network_name']
        dh_data = load_district_heating_data(building_name, network_name, locator)
        final_energy['Qhs_sys_DH_kWh'] = dh_data['DH_hs_kWh']
    else:
        # No heating system
        final_energy['Qhs_sys_NONE_kWh'] = 0.0

    # Hot water (DHW)
    if supply_config['hot_water']['scale'] == 'BUILDING':
        carrier = supply_config['hot_water']['carrier']
        efficiency = supply_config['hot_water']['efficiency']
        final_energy[f'Qww_sys_{carrier}_kWh'] = demand_df['Qww_sys_kWh'] / efficiency
    elif supply_config['hot_water']['scale'] == 'DISTRICT':
        network_name = supply_config['hot_water']['network_name']
        dh_data = load_district_heating_data(building_name, network_name, locator)
        final_energy['Qww_sys_DH_kWh'] = dh_data['DH_ww_kWh']
    else:
        final_energy['Qww_sys_NONE_kWh'] = 0.0

    # Space cooling
    if supply_config['space_cooling']['scale'] == 'BUILDING':
        carrier = supply_config['space_cooling']['carrier']
        efficiency = supply_config['space_cooling']['efficiency']
        final_energy[f'Qcs_sys_{carrier}_kWh'] = demand_df['Qcs_sys_kWh'] / efficiency
    elif supply_config['space_cooling']['scale'] == 'DISTRICT':
        network_name = supply_config['space_cooling']['network_name']
        dc_data = load_district_cooling_data(building_name, network_name, locator)
        final_energy['Qcs_sys_DC_kWh'] = dc_data['DC_cs_kWh']
    else:
        final_energy['Qcs_sys_NONE_kWh'] = 0.0

    # Electricity (always GRID)
    final_energy['E_sys_GRID_kWh'] = demand_df['E_sys_kWh']

    # Step 4: Handle booster systems (if applicable)
    if supply_config['space_heating_booster']:
        booster_data = load_booster_data(building_name, network_name, 'hs', locator)
        carrier = supply_config['space_heating_booster']['carrier']
        efficiency = supply_config['space_heating_booster']['efficiency']
        final_energy[f'Qhs_booster_{carrier}_kWh'] = booster_data['Qhs_booster_kWh'] / efficiency

    if supply_config['hot_water_booster']:
        booster_data = load_booster_data(building_name, network_name, 'dhw', locator)
        carrier = supply_config['hot_water_booster']['carrier']
        efficiency = supply_config['hot_water_booster']['efficiency']
        final_energy[f'Qww_booster_{carrier}_kWh'] = booster_data['Qww_booster_kWh'] / efficiency

    # Step 5: Add metadata columns
    final_energy['scale'] = 'BUILDING'
    case_num, case_desc = determine_case(supply_config)
    final_energy['case'] = case_num
    final_energy['case_description'] = case_desc

    return final_energy


def load_supply_configuration(
    building_name: str,
    locator: cea.inputlocator.InputLocator,
    config: cea.config.Configuration
) -> Dict:
    """
    Load supply system configuration for a building.

    Returns dict with structure:
    {
        'space_heating': {'scale': 'BUILDING'|'DISTRICT', 'carrier': 'NATURALGAS', 'efficiency': 0.85, ...},
        'hot_water': {...},
        'space_cooling': {...},
        'space_heating_booster': {...} or None,
        'hot_water_booster': {...} or None,
    }

    :param building_name: Name of the building
    :param locator: InputLocator instance
    :param config: Configuration instance
    :return: Supply configuration dict
    """
    if config.final_energy.overwrite_supply_settings:
        # What-if mode: use config parameters
        return load_whatif_supply_configuration(building_name, locator, config)
    else:
        # Production mode: use supply.csv
        return load_production_supply_configuration(building_name, locator)


def load_production_supply_configuration(
    building_name: str,
    locator: cea.inputlocator.InputLocator
) -> Dict:
    """
    Load supply configuration from supply.csv (production mode).

    :param building_name: Name of the building
    :param locator: InputLocator instance
    :return: Supply configuration dict
    """
    from cea.datamanagement.database.assemblies import Supply

    # Read supply.csv
    supply_df = pd.read_csv(locator.get_building_supply()).set_index('name')
    if building_name not in supply_df.index:
        raise ValueError(f"Building {building_name} not found in supply.csv")

    building_supply = supply_df.loc[building_name]

    # Load supply database
    supply_db = Supply.from_locator(locator)

    # Initialize config dict
    config = {
        'space_heating': None,
        'hot_water': None,
        'space_cooling': None,
        'space_heating_booster': None,
        'hot_water_booster': None,
    }

    # Parse space heating
    if 'supply_type_hs' in building_supply and building_supply['supply_type_hs']:
        config['space_heating'] = parse_supply_assembly(
            building_supply['supply_type_hs'],
            supply_db.heating,
            locator,
            'heating'
        )

    # Parse hot water (DHW)
    if 'supply_type_dhw' in building_supply and building_supply['supply_type_dhw']:
        config['hot_water'] = parse_supply_assembly(
            building_supply['supply_type_dhw'],
            supply_db.hot_water,
            locator,
            'hot_water'
        )

    # Parse space cooling
    if 'supply_type_cs' in building_supply and building_supply['supply_type_cs']:
        config['space_cooling'] = parse_supply_assembly(
            building_supply['supply_type_cs'],
            supply_db.cooling,
            locator,
            'cooling'
        )

    # TODO: Handle booster systems - check if building is connected to district network
    # and if booster substation files exist

    return config


def parse_supply_assembly(
    assembly_code: str,
    assembly_df: pd.DataFrame,
    locator: cea.inputlocator.InputLocator,
    service_type: str  # 'heating', 'hot_water', or 'cooling'
) -> Dict:
    """
    Parse an assembly code and return its configuration.

    :param assembly_code: Assembly code (e.g., 'SUPPLY_HEATING_AS3')
    :param assembly_df: Supply assembly DataFrame
    :param locator: InputLocator instance
    :param service_type: Type of service
    :return: Dict with scale, carrier, efficiency, assembly_code, component_code
    """
    if assembly_code not in assembly_df.index:
        raise ValueError(f"Assembly {assembly_code} not found in database")

    assembly = assembly_df.loc[assembly_code]

    # Get scale
    scale = assembly['scale']

    if scale == 'NONE':
        return {
            'scale': 'NONE',
            'carrier': None,
            'efficiency': None,
            'assembly_code': assembly_code,
            'component_code': None,
        }

    # Get primary component
    component_code = assembly['primary_components']
    if pd.isna(component_code) or component_code == '-':
        raise ValueError(f"Assembly {assembly_code} has no primary component")

    # Load component from database
    component_info = load_component_info(component_code, locator)

    return {
        'scale': scale,
        'carrier': component_info['carrier'],
        'efficiency': component_info['efficiency'],
        'assembly_code': assembly_code,
        'component_code': component_code,
    }


def load_component_info(
    component_code: str,
    locator: cea.inputlocator.InputLocator
) -> Dict:
    """
    Load component information from COMPONENTS database.

    :param component_code: Component code (e.g., 'BO1', 'HP1', 'CH1')
    :param locator: InputLocator instance
    :return: Dict with carrier and efficiency
    """
    # Determine component type from code prefix
    if component_code.startswith('BO'):
        # Boiler
        component_file = locator.get_database_conversion_boilers()
        df = pd.read_csv(component_file)
        components = df[df['code'] == component_code]

        if components.empty:
            raise ValueError(f"Component {component_code} not found in BOILERS database")

        # Take first row (or average efficiency across capacity ranges)
        component = components.iloc[0]

        return {
            'carrier': map_fuel_code_to_carrier(component['fuel_code']),
            'efficiency': component['min_eff_rating']
        }

    elif component_code.startswith('HP'):
        # Heat pump
        component_file = locator.get_database_conversion_heat_pumps()
        df = pd.read_csv(component_file)
        components = df[df['code'] == component_code]

        if components.empty:
            raise ValueError(f"Component {component_code} not found in HEAT_PUMPS database")

        # Take first row (or average COP across capacity ranges)
        component = components.iloc[0]

        return {
            'carrier': 'GRID',  # Heat pumps use electricity
            'efficiency': component['min_eff_rating_seasonal']
        }

    elif component_code.startswith('CH'):
        # Chiller
        component_file = locator.get_database_conversion_vapor_compression_chillers()
        df = pd.read_csv(component_file)
        components = df[df['code'] == component_code]

        if components.empty:
            raise ValueError(f"Component {component_code} not found in CHILLERS database")

        # Take first row (or average COP across capacity ranges)
        component = components.iloc[0]

        return {
            'carrier': 'GRID',  # Chillers use electricity
            'efficiency': component['min_eff_rating']
        }

    else:
        raise ValueError(f"Unknown component type for code {component_code}")


def map_fuel_code_to_carrier(fuel_code: str) -> str:
    """
    Map database fuel codes to carrier names.

    :param fuel_code: Fuel code from database (e.g., 'Cgas', 'Coil', 'E230AC')
    :return: Carrier name (e.g., 'NATURALGAS', 'OIL', 'GRID')
    """
    fuel_mapping = {
        'Cgas': 'NATURALGAS',
        'Coil': 'OIL',
        'Ccoa': 'COAL',
        'Cwod': 'WOOD',
        'E230AC': 'GRID',
    }

    if fuel_code not in fuel_mapping:
        raise ValueError(f"Unknown fuel code: {fuel_code}")

    return fuel_mapping[fuel_code]


def load_whatif_supply_configuration(
    building_name: str,
    locator: cea.inputlocator.InputLocator,
    config: cea.config.Configuration
) -> Dict:
    """
    Load supply configuration from config parameters (what-if mode).

    :param building_name: Name of the building
    :param locator: InputLocator instance
    :param config: Configuration instance
    :return: Supply configuration dict
    """
    # TODO: Implement
    # 1. Get supply-type-* parameters from config
    # 2. Determine if building is connected to district network
    # 3. Select appropriate assembly (building-scale vs district-scale)
    # 4. Load assembly and component from database
    # 5. Return configuration dict

    raise NotImplementedError("What-if mode supply configuration not yet implemented")


def load_district_heating_data(
    building_name: str,
    network_name: str,
    locator: cea.inputlocator.InputLocator
) -> pd.DataFrame:
    """
    Load district heating consumption from thermal-network results.

    :param building_name: Name of the building
    :param network_name: Network layout name
    :param locator: InputLocator instance
    :return: DataFrame with columns: DH_hs_kWh, DH_ww_kWh
    """
    # Read substation file
    substation_file = locator.get_thermal_network_substation_results_file(
        building_name, 'DH', network_name
    )

    if not os.path.exists(substation_file):
        raise FileNotFoundError(
            f"District heating substation file not found for building {building_name}: {substation_file}\n"
            f"Please run 'cea thermal-network' first."
        )

    substation_df = pd.read_csv(substation_file)

    # Convert from W to kWh (Watts are hourly averages, so W = Wh for hourly data)
    result = pd.DataFrame({
        'DH_hs_kWh': substation_df['Qhs_dh_W'] / 1000.0,
        'DH_ww_kWh': substation_df['Qww_dh_W'] / 1000.0,
    })

    return result


def load_district_cooling_data(
    building_name: str,
    network_name: str,
    locator: cea.inputlocator.InputLocator
) -> pd.DataFrame:
    """
    Load district cooling consumption from thermal-network results.

    :param building_name: Name of the building
    :param network_name: Network layout name
    :param locator: InputLocator instance
    :return: DataFrame with columns: DC_cs_kWh, DC_cdata_kWh, DC_cre_kWh
    """
    # Read substation file
    substation_file = locator.get_thermal_network_substation_results_file(
        building_name, 'DC', network_name
    )

    if not os.path.exists(substation_file):
        raise FileNotFoundError(
            f"District cooling substation file not found for building {building_name}: {substation_file}\n"
            f"Please run 'cea thermal-network' first."
        )

    substation_df = pd.read_csv(substation_file)

    # Convert from W to kWh
    result = pd.DataFrame({
        'DC_cs_kWh': substation_df['Qcs_dc_W'] / 1000.0,
        'DC_cdata_kWh': substation_df['Qcdata_dc_W'] / 1000.0,
        'DC_cre_kWh': substation_df['Qcre_dc_W'] / 1000.0,
    })

    return result


def load_booster_data(
    building_name: str,
    network_name: str,
    service: str,  # 'hs' or 'dhw'
    locator: cea.inputlocator.InputLocator
) -> pd.DataFrame:
    """
    Load booster system demand from thermal-network booster results.

    :param building_name: Name of the building
    :param network_name: Network layout name
    :param service: 'hs' (space heating) or 'dhw' (hot water)
    :param locator: InputLocator instance
    :return: DataFrame with columns: Qhs_booster_kWh or Qww_booster_kWh
    """
    # Read substation file (booster data is in the same file as DH data)
    substation_file = locator.get_thermal_network_substation_results_file(
        building_name, 'DH', network_name
    )

    if not os.path.exists(substation_file):
        raise FileNotFoundError(
            f"District heating substation file not found for building {building_name}: {substation_file}\n"
            f"Please run 'cea thermal-network' first."
        )

    substation_df = pd.read_csv(substation_file)

    # Extract booster columns and convert from W to kWh
    if service == 'hs':
        result = pd.DataFrame({
            'Qhs_booster_kWh': substation_df['Qhs_booster_W'] / 1000.0
        })
    elif service == 'dhw':
        result = pd.DataFrame({
            'Qww_booster_kWh': substation_df['Qww_booster_W'] / 1000.0
        })
    else:
        raise ValueError(f"Invalid service type: {service}. Must be 'hs' or 'dhw'")

    return result


def determine_case(supply_config: Dict) -> Tuple[float, str]:
    """
    Determine case number and description based on supply configuration.

    Case definitions (from IMPLEMENTATION_PLAN.md):
    1: Standalone (all services building-scale)
    2: DH + DC (both heating and cooling from district)
    3: DH only (district heating + standalone cooling)
    4: DC only (standalone heating + district cooling)
    4.01: DC + booster for space heating
    4.02: DC + booster for hot water
    4.03: DC + booster for both

    :param supply_config: Supply configuration dict
    :return: (case_number, case_description)
    """
    hs_district = supply_config['space_heating']['scale'] == 'DISTRICT'
    dhw_district = supply_config['hot_water']['scale'] == 'DISTRICT'
    cs_district = supply_config['space_cooling']['scale'] == 'DISTRICT'

    hs_booster = supply_config['space_heating_booster'] is not None
    dhw_booster = supply_config['hot_water_booster'] is not None

    # Determine case
    if hs_district and dhw_district and cs_district:
        return (2, "DH + DC (centralized heating + cooling)")
    elif hs_district and dhw_district and not cs_district:
        return (3, "DH only (centralized heating + standalone cooling)")
    elif not hs_district and not dhw_district and cs_district:
        if hs_booster and dhw_booster:
            return (4.03, "DC + booster for both space heating and hot water")
        elif hs_booster:
            return (4.01, "DC + booster for space heating")
        elif dhw_booster:
            return (4.02, "DC + booster for hot water")
        else:
            return (4, "DC only (standalone heating + centralized cooling)")
    else:
        return (1, "Standalone (all services)")


def calculate_plant_final_energy(
    network_name: str,
    network_type: str,
    plant_name: str,
    locator: cea.inputlocator.InputLocator,
    config: cea.config.Configuration
) -> pd.DataFrame:
    """
    Calculate hourly final energy consumption for one district plant.

    :param network_name: Network layout name (e.g., 'xxx')
    :param network_type: 'DH' (district heating) or 'DC' (district cooling)
    :param plant_name: Plant node name from shapefile (e.g., 'NODE_001')
    :param locator: InputLocator instance
    :param config: Configuration instance
    :return: DataFrame with 8760 rows and carrier columns
    """
    # TODO: Implement
    # 1. Read plant configuration from network files
    # 2. Read plant energy consumption
    # 3. Apply plant equipment efficiency
    # 4. Return DataFrame with plant carrier columns

    raise NotImplementedError("Plant final energy calculation not yet implemented")


def aggregate_buildings_summary(
    building_dfs: Dict[str, pd.DataFrame],
    plant_dfs: Dict[str, pd.DataFrame],
    locator: cea.inputlocator.InputLocator
) -> pd.DataFrame:
    """
    Aggregate hourly data to annual summary (final_energy_buildings.csv).

    :param building_dfs: Dict of building_name -> final_energy DataFrame
    :param plant_dfs: Dict of plant_name -> final_energy DataFrame
    :param locator: InputLocator instance
    :return: Summary DataFrame with one row per building/plant
    """
    # TODO: Implement
    # 1. For each building/plant DataFrame:
    #    - Sum all carrier columns to get annual totals (MWh)
    #    - Find peak demand and timestamp
    #    - Get building metadata (GFA, coordinates)
    # 2. Combine into single summary DataFrame
    # 3. Return with columns from BACKEND_PLAN.md section 2.3

    raise NotImplementedError("Buildings summary aggregation not yet implemented")


def create_final_energy_breakdown(
    building_dfs: Dict[str, pd.DataFrame],
    plant_dfs: Dict[str, pd.DataFrame],
    locator: cea.inputlocator.InputLocator,
    config: cea.config.Configuration
) -> pd.DataFrame:
    """
    Create detailed carrier breakdown by service (final_energy.csv).

    :param building_dfs: Dict of building_name -> final_energy DataFrame
    :param plant_dfs: Dict of plant_name -> final_energy DataFrame
    :param locator: InputLocator instance
    :param config: Configuration instance
    :return: Breakdown DataFrame with multiple rows per building/plant
    """
    # TODO: Implement
    # 1. For each building/plant and service:
    #    - Extract carrier, assembly, component info
    #    - Calculate annual totals and peaks
    #    - Add demand_column reference
    # 2. Combine into single breakdown DataFrame
    # 3. Return with columns from BACKEND_PLAN.md section 2.4

    raise NotImplementedError("Final energy breakdown not yet implemented")
