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
        'date': demand_df['date'],
        'Qhs_sys_kWh': demand_df['Qhs_sys_kWh'],
        'Qww_sys_kWh': demand_df['Qww_sys_kWh'],
        'Qcs_sys_kWh': demand_df['Qcs_sys_kWh'],
        'E_sys_kWh': demand_df['E_sys_kWh'],
    })

    # Step 2: Load supply configuration
    supply_config = load_supply_configuration(building_name, locator, config)

    # Step 3: Calculate final energy for each service
    # Space heating
    if supply_config['space_heating'] and supply_config['space_heating']['scale'] == 'BUILDING':
        # Building-scale: use component efficiency
        carrier = supply_config['space_heating']['carrier']
        efficiency = supply_config['space_heating']['efficiency']
        final_energy[f'Qhs_sys_{carrier}_kWh'] = demand_df['Qhs_sys_kWh'] / efficiency
    elif supply_config['space_heating'] and supply_config['space_heating']['scale'] == 'DISTRICT':
        # District heating: read from thermal-network
        network_name = supply_config['space_heating']['network_name']
        dh_data = load_district_heating_data(building_name, network_name, locator)
        final_energy['Qhs_sys_DH_kWh'] = dh_data['DH_hs_kWh']
    else:
        # No heating system
        final_energy['Qhs_sys_NONE_kWh'] = 0.0

    # Hot water (DHW)
    if supply_config['hot_water'] and supply_config['hot_water']['scale'] == 'BUILDING':
        carrier = supply_config['hot_water']['carrier']
        efficiency = supply_config['hot_water']['efficiency']
        final_energy[f'Qww_sys_{carrier}_kWh'] = demand_df['Qww_sys_kWh'] / efficiency
    elif supply_config['hot_water'] and supply_config['hot_water']['scale'] == 'DISTRICT':
        network_name = supply_config['hot_water']['network_name']
        dh_data = load_district_heating_data(building_name, network_name, locator)
        final_energy['Qww_sys_DH_kWh'] = dh_data['DH_ww_kWh']
    else:
        final_energy['Qww_sys_NONE_kWh'] = 0.0

    # Space cooling
    if supply_config['space_cooling'] and supply_config['space_cooling']['scale'] == 'BUILDING':
        carrier = supply_config['space_cooling']['carrier']
        efficiency = supply_config['space_cooling']['efficiency']
        final_energy[f'Qcs_sys_{carrier}_kWh'] = demand_df['Qcs_sys_kWh'] / efficiency
    elif supply_config['space_cooling'] and supply_config['space_cooling']['scale'] == 'DISTRICT':
        network_name = supply_config['space_cooling']['network_name']
        dc_data = load_district_cooling_data(building_name, network_name, locator)
        final_energy['Qcs_sys_DC_kWh'] = dc_data['DC_cs_kWh']
    else:
        final_energy['Qcs_sys_NONE_kWh'] = 0.0

    # Electricity (always GRID)
    final_energy['E_sys_GRID_kWh'] = demand_df['E_sys_kWh']

    # Step 4: Handle booster systems (if applicable)
    # Auto-detect boosters from thermal-network files (production mode)
    # or use configured boosters (what-if mode)

    # For production mode: check if building has district heating with potential boosters
    has_dh_heating = (supply_config['space_heating'] and
                      supply_config['space_heating']['scale'] == 'DISTRICT')
    has_dh_dhw = (supply_config['hot_water'] and
                  supply_config['hot_water']['scale'] == 'DISTRICT')

    # Space heating booster
    if supply_config['space_heating_booster'] and supply_config['space_heating_booster']['network_name']:
        # What-if mode: booster explicitly configured
        network_name = supply_config['space_heating_booster']['network_name']
        try:
            booster_data = load_booster_data(building_name, network_name, 'hs', locator)
            if booster_data['Qhs_booster_kWh'].sum() > 0:
                carrier = supply_config['space_heating_booster']['carrier']
                efficiency = supply_config['space_heating_booster']['efficiency']
                final_energy[f'Qhs_booster_{carrier}_kWh'] = booster_data['Qhs_booster_kWh'] / efficiency
        except FileNotFoundError:
            pass
    elif has_dh_heating:
        # Production mode: auto-detect booster from thermal-network
        network_name = supply_config['space_heating']['network_name']
        if network_name:
            try:
                booster_data = load_booster_data(building_name, network_name, 'hs', locator)
                if booster_data['Qhs_booster_kWh'].sum() > 0:
                    # Auto-detect booster: assume natural gas boiler (most common)
                    # TODO: Read booster type from thermal-network metadata
                    carrier = 'NATURALGAS'
                    efficiency = 0.85  # Default booster efficiency
                    final_energy[f'Qhs_booster_{carrier}_kWh'] = booster_data['Qhs_booster_kWh'] / efficiency
            except FileNotFoundError:
                pass

    # Hot water booster
    if supply_config['hot_water_booster'] and supply_config['hot_water_booster']['network_name']:
        # What-if mode: booster explicitly configured
        network_name = supply_config['hot_water_booster']['network_name']
        try:
            booster_data = load_booster_data(building_name, network_name, 'dhw', locator)
            if booster_data['Qww_booster_kWh'].sum() > 0:
                carrier = supply_config['hot_water_booster']['carrier']
                efficiency = supply_config['hot_water_booster']['efficiency']
                final_energy[f'Qww_booster_{carrier}_kWh'] = booster_data['Qww_booster_kWh'] / efficiency
        except FileNotFoundError:
            pass
    elif has_dh_dhw:
        # Production mode: auto-detect booster from thermal-network
        network_name = supply_config['hot_water']['network_name']
        if network_name:
            try:
                booster_data = load_booster_data(building_name, network_name, 'dhw', locator)
                if booster_data['Qww_booster_kWh'].sum() > 0:
                    # Auto-detect booster: assume natural gas boiler (most common)
                    # TODO: Read booster type from thermal-network metadata
                    carrier = 'NATURALGAS'
                    efficiency = 0.85  # Default booster efficiency
                    final_energy[f'Qww_booster_{carrier}_kWh'] = booster_data['Qww_booster_kWh'] / efficiency
            except FileNotFoundError:
                pass

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
        return load_production_supply_configuration(building_name, locator, config)


def load_production_supply_configuration(
    building_name: str,
    locator: cea.inputlocator.InputLocator,
    config: cea.config.Configuration
) -> Dict:
    """
    Load supply configuration from supply.csv (production mode).

    :param building_name: Name of the building
    :param locator: InputLocator instance
    :param config: Configuration instance
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

    # Get network name from config (if specified)
    network_name = config.final_energy.network_name

    # Initialize supply config dict
    supply_config = {
        'space_heating': None,
        'hot_water': None,
        'space_cooling': None,
        'space_heating_booster': None,
        'hot_water_booster': None,
    }

    # Parse space heating
    if 'supply_type_hs' in building_supply and building_supply['supply_type_hs']:
        supply_config['space_heating'] = parse_supply_assembly(
            building_supply['supply_type_hs'],
            supply_db.heating,
            locator,
            'heating',
            network_name
        )

    # Parse hot water (DHW)
    if 'supply_type_dhw' in building_supply and building_supply['supply_type_dhw']:
        supply_config['hot_water'] = parse_supply_assembly(
            building_supply['supply_type_dhw'],
            supply_db.hot_water,
            locator,
            'hot_water',
            network_name
        )

    # Parse space cooling
    if 'supply_type_cs' in building_supply and building_supply['supply_type_cs']:
        supply_config['space_cooling'] = parse_supply_assembly(
            building_supply['supply_type_cs'],
            supply_db.cooling,
            locator,
            'cooling',
            network_name
        )

    # TODO: Handle booster systems - check if building is connected to district network
    # and if booster substation files exist

    return supply_config


def parse_supply_assembly(
    assembly_code: str,
    assembly_df: pd.DataFrame,
    locator: cea.inputlocator.InputLocator,
    service_type: str,  # 'heating', 'hot_water', or 'cooling'
    network_name: Optional[str] = None
) -> Dict:
    """
    Parse an assembly code and return its configuration.

    :param assembly_code: Assembly code (e.g., 'SUPPLY_HEATING_AS3')
    :param assembly_df: Supply assembly DataFrame (from Supply.from_locator())
    :param locator: InputLocator instance
    :param service_type: Type of service
    :param network_name: Network name (required for DISTRICT scale)
    :return: Dict with scale, carrier, efficiency, assembly_code, component_code, network_name
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
            'network_name': None,
        }

    # Get primary component code
    component_code = assembly['primary_components']
    if pd.isna(component_code) or component_code == '-':
        raise ValueError(f"Assembly {assembly_code} has no primary component")

    # Load component information from COMPONENTS database
    component_info = load_component_info(component_code, locator)

    # For district systems, carrier is DH or DC, not the plant fuel
    if scale == 'DISTRICT':
        # Determine if it's heating or cooling based on service type
        if service_type in ['space_heating', 'hot_water']:
            carrier = 'DH'  # District heating
        elif service_type == 'space_cooling':
            carrier = 'DC'  # District cooling
        else:
            carrier = 'DH'  # Default to DH
        # District systems don't have efficiency at building level (handled at plant)
        efficiency = None
    else:
        # Building-scale: use component carrier and efficiency
        carrier = component_info['carrier']
        efficiency = component_info['efficiency']

    result = {
        'scale': scale,
        'carrier': carrier,
        'efficiency': efficiency,
        'assembly_code': assembly_code,
        'component_code': component_code,
        'network_name': network_name if scale == 'DISTRICT' else None,
    }

    return result


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
        component_file = locator.get_db4_components_conversion_conversion_technology_csv('BOILERS')
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
        component_file = locator.get_db4_components_conversion_conversion_technology_csv('HEAT_PUMPS')
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
        component_file = locator.get_db4_components_conversion_conversion_technology_csv('VAPOR_COMPRESSION_CHILLERS')
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

    Logic:
    1. Read building's configured scale from supply.csv
    2. Check if building is connected to network (substation file exists)
    3. Apply override logic:
       - supply.csv=DISTRICT + no connection → use building assembly (fallback)
       - supply.csv=DISTRICT + has connection → use district assembly (keep)
       - supply.csv=BUILDING + no connection → use building assembly (keep)
       - supply.csv=BUILDING + has connection → use district assembly (upgrade)

    :param building_name: Name of the building
    :param locator: InputLocator instance
    :param config: Configuration instance
    :return: Supply configuration dict
    """
    from cea.datamanagement.database.assemblies import Supply

    # Load supply database
    supply_db = Supply.from_locator(locator)

    # Get network name from config
    network_name = config.final_energy.network_name

    # Get supply type parameters from config
    # These are lists of assembly codes (can be multiple due to multi-select)
    supply_type_hs = config.final_energy.supply_type_hs if config.final_energy.supply_type_hs else []
    supply_type_dhw = config.final_energy.supply_type_dhw if config.final_energy.supply_type_dhw else []
    supply_type_cs = config.final_energy.supply_type_cs if config.final_energy.supply_type_cs else []

    # Booster parameters
    booster_hs = config.final_energy.hs_booster_type if config.final_energy.hs_booster_type else []
    booster_dhw = config.final_energy.dhw_booster_type if config.final_energy.dhw_booster_type else []

    # Initialize supply config dict
    supply_config = {
        'space_heating': None,
        'hot_water': None,
        'space_cooling': None,
        'space_heating_booster': None,
        'hot_water_booster': None,
    }

    # Helper function to strip scale labels from assembly codes
    def strip_scale_label(assembly_str: str) -> str:
        """Strip scale label from assembly code: 'SUPPLY_HEATING_AS3 (building)' -> 'SUPPLY_HEATING_AS3'"""
        if ' (' in assembly_str:
            return assembly_str.split(' (')[0]
        return assembly_str

    # Helper function to separate building and district assemblies
    def separate_assemblies(options: list, assembly_df: pd.DataFrame) -> tuple:
        """
        Separate assembly options into building-scale and district-scale.

        :param options: List of assembly codes with scale labels
        :param assembly_df: Assembly dataframe to look up scale
        :return: (building_assembly, district_assembly)
        """
        building_assembly = None
        district_assembly = None

        for option in options:
            assembly_code = strip_scale_label(option)
            if assembly_code in assembly_df.index:
                scale = assembly_df.loc[assembly_code, 'scale']
                if scale == 'BUILDING':
                    building_assembly = assembly_code
                elif scale == 'DISTRICT':
                    district_assembly = assembly_code

        return building_assembly, district_assembly

    # Read supply.csv to get building's configured scale
    supply_df = pd.read_csv(locator.get_building_supply()).set_index('name')
    if building_name not in supply_df.index:
        raise ValueError(f"Building {building_name} not found in supply.csv")

    building_supply = supply_df.loc[building_name]

    # Helper function to check network connectivity
    def is_connected_to_network(building_name: str, network_name: str, network_type: str) -> bool:
        """Check if building has substation file in network."""
        if not network_name:
            return False

        substation_file = locator.get_thermal_network_substation_results_file(
            building_name, network_type, network_name
        )
        return os.path.exists(substation_file)

    # Helper function to select assembly based on override logic
    def select_assembly_with_override(
        options: list,
        assembly_df: pd.DataFrame,
        configured_scale: str,
        is_connected: bool
    ) -> str:
        """
        Select assembly based on configured scale and actual connectivity.

        :param options: List of assembly options from config
        :param assembly_df: Assembly dataframe
        :param configured_scale: Scale from supply.csv ('BUILDING' or 'DISTRICT')
        :param is_connected: Whether building has substation file
        :return: Selected assembly code
        """
        # Separate building and district options
        building_assembly, district_assembly = separate_assemblies(options, assembly_df)

        # Apply override logic
        if configured_scale == 'DISTRICT':
            if is_connected:
                # supply.csv=DISTRICT + has connection → use district (keep)
                return district_assembly if district_assembly else building_assembly
            else:
                # supply.csv=DISTRICT + no connection → use building (fallback)
                return building_assembly if building_assembly else district_assembly
        else:  # configured_scale == 'BUILDING'
            if is_connected:
                # supply.csv=BUILDING + has connection → use district (upgrade)
                return district_assembly if district_assembly else building_assembly
            else:
                # supply.csv=BUILDING + no connection → use building (keep)
                return building_assembly if building_assembly else district_assembly

    # Parse space heating
    if supply_type_hs and len(supply_type_hs) > 0:
        # Get configured scale from supply.csv
        configured_scale_hs = 'BUILDING'  # Default
        if 'supply_type_hs' in building_supply and building_supply['supply_type_hs']:
            hs_assembly = building_supply['supply_type_hs']
            if hs_assembly in supply_db.heating.index:
                configured_scale_hs = supply_db.heating.loc[hs_assembly, 'scale']

        # Check network connectivity
        is_connected_dh = is_connected_to_network(building_name, network_name, 'DH')

        # Select assembly with override logic
        assembly_code = select_assembly_with_override(
            supply_type_hs,
            supply_db.heating,
            configured_scale_hs,
            is_connected_dh
        )

        if assembly_code:
            supply_config['space_heating'] = parse_supply_assembly(
                assembly_code,
                supply_db.heating,
                locator,
                'heating',
                network_name
            )

    # Parse hot water (DHW) - always building scale, never district
    if supply_type_dhw and len(supply_type_dhw) > 0:
        # DHW is always building-scale, so always select building assembly
        building_assembly, _ = separate_assemblies(supply_type_dhw, supply_db.hot_water)
        assembly_code = building_assembly

        if assembly_code:
            supply_config['hot_water'] = parse_supply_assembly(
                assembly_code,
                supply_db.hot_water,
                locator,
                'hot_water',
                network_name
            )

    # Parse space cooling
    if supply_type_cs and len(supply_type_cs) > 0:
        # Get configured scale from supply.csv
        configured_scale_cs = 'BUILDING'  # Default
        if 'supply_type_cs' in building_supply and building_supply['supply_type_cs']:
            cs_assembly = building_supply['supply_type_cs']
            if cs_assembly in supply_db.cooling.index:
                configured_scale_cs = supply_db.cooling.loc[cs_assembly, 'scale']

        # Check network connectivity
        is_connected_dc = is_connected_to_network(building_name, network_name, 'DC')

        # Select assembly with override logic
        assembly_code = select_assembly_with_override(
            supply_type_cs,
            supply_db.cooling,
            configured_scale_cs,
            is_connected_dc
        )

        if assembly_code:
            supply_config['space_cooling'] = parse_supply_assembly(
                assembly_code,
                supply_db.cooling,
                locator,
                'cooling',
                network_name
            )

    # Parse booster systems (always building-scale, ignore network preference)
    if booster_hs and len(booster_hs) > 0:
        assembly_code = strip_scale_label(booster_hs[0])
        if assembly_code:
            supply_config['space_heating_booster'] = parse_supply_assembly(
                assembly_code,
                supply_db.heating,
                locator,
                'heating',
                network_name
            )

    if booster_dhw and len(booster_dhw) > 0:
        assembly_code = strip_scale_label(booster_dhw[0])
        if assembly_code:
            supply_config['hot_water_booster'] = parse_supply_assembly(
                assembly_code,
                supply_db.hot_water,
                locator,
                'hot_water',
                network_name
            )

    return supply_config


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


def validate_district_assembly_consistency(building_configs: Dict[str, Dict]) -> None:
    """
    Validate that all buildings connected to district use the same assembly type.

    Raises ValueError if multiple district assembly types are detected.

    :param building_configs: Dict of building_name -> supply_configuration
    """
    # Collect district assemblies for each service
    dh_assemblies = set()
    dc_assemblies = set()

    for building_name, config in building_configs.items():
        # Check space heating
        if config.get('space_heating') and config['space_heating']['scale'] == 'DISTRICT':
            assembly_code = config['space_heating']['assembly_code']
            dh_assemblies.add(assembly_code)

        # Check hot water (rarely district, but check anyway)
        if config.get('hot_water') and config['hot_water']['scale'] == 'DISTRICT':
            assembly_code = config['hot_water']['assembly_code']
            dh_assemblies.add(assembly_code)

        # Check space cooling
        if config.get('space_cooling') and config['space_cooling']['scale'] == 'DISTRICT':
            assembly_code = config['space_cooling']['assembly_code']
            dc_assemblies.add(assembly_code)

    # Validate district heating assemblies
    if len(dh_assemblies) > 1:
        raise ValueError(
            f"Multiple district heating assembly types detected: {dh_assemblies}\n"
            f"All buildings in a district heating network must use the same assembly type.\n"
            f"Please select only one district heating assembly in supply-type-hs."
        )

    # Validate district cooling assemblies
    if len(dc_assemblies) > 1:
        raise ValueError(
            f"Multiple district cooling assembly types detected: {dc_assemblies}\n"
            f"All buildings in a district cooling network must use the same assembly type.\n"
            f"Please select only one district cooling assembly in supply-type-cs."
        )


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
    # Step 1: Read plant thermal load
    network_folder = locator.get_output_thermal_network_type_folder(network_type, network_name)

    if network_type == 'DH':
        plant_load_file = os.path.join(network_folder, f'DH_{network_name}_plant_thermal_load_kW.csv')
    elif network_type == 'DC':
        plant_load_file = os.path.join(network_folder, f'DC_{network_name}_plant_thermal_load_kW.csv')
    else:
        raise ValueError(f"Unknown network type: {network_type}")

    if not os.path.exists(plant_load_file):
        raise FileNotFoundError(
            f"Plant thermal load file not found: {plant_load_file}\n"
            f"Please run 'cea thermal-network' first."
        )

    plant_load_df = pd.read_csv(plant_load_file)

    # Convert kW to kWh (hourly average power -> hourly energy)
    thermal_load_kWh = plant_load_df['thermal_load_kW'].values

    # Step 2: Read plant pumping load
    if network_type == 'DH':
        pumping_file = os.path.join(network_folder, f'DH_{network_name}_plant_pumping_load_kW.csv')
    else:
        pumping_file = os.path.join(network_folder, f'DC_{network_name}_plant_pumping_load_kW.csv')

    if os.path.exists(pumping_file):
        pumping_df = pd.read_csv(pumping_file)
        pumping_load_kWh = pumping_df.iloc[:, 0].values  # First column is pumping load
    else:
        pumping_load_kWh = np.zeros(len(thermal_load_kWh))

    # Step 3: Get plant equipment configuration
    # For what-if mode: use config parameters
    # For production mode: read from network metadata or use defaults

    if config.final_energy.overwrite_supply_settings:
        # What-if mode: use configured plant type
        # TODO: Add plant-type parameter to config
        # For now, use default based on network type
        if network_type == 'DH':
            # Default: Natural gas boiler
            plant_carrier = 'NATURALGAS'
            plant_efficiency = 0.85
        else:
            # Default: Electric chiller
            plant_carrier = 'GRID'
            plant_efficiency = 3.0  # COP
    else:
        # Production mode: try to detect from network metadata
        # For now, use defaults (can be enhanced later)
        if network_type == 'DH':
            plant_carrier = 'NATURALGAS'
            plant_efficiency = 0.85
        else:
            plant_carrier = 'GRID'
            plant_efficiency = 3.0

    # Step 4: Calculate final energy consumption
    # Plant fuel/electricity = thermal load / efficiency
    final_energy_kWh = thermal_load_kWh / plant_efficiency

    # Step 5: Create output dataframe
    # Generate date column (assuming standard 8760 hours)
    import datetime
    start_date = datetime.datetime(2011, 1, 1)
    dates = [start_date + datetime.timedelta(hours=i) for i in range(len(thermal_load_kWh))]

    result = pd.DataFrame({
        'date': [d.strftime('%Y-%m-%d %H:%M:%S') for d in dates],
        'thermal_load_kWh': thermal_load_kWh,
        'pumping_load_kWh': pumping_load_kWh,
    })

    # Add carrier column
    if network_type == 'DH':
        result[f'plant_heating_{plant_carrier}_kWh'] = final_energy_kWh
    else:
        result[f'plant_cooling_{plant_carrier}_kWh'] = final_energy_kWh

    # Add pumping electricity
    result['plant_pumping_GRID_kWh'] = pumping_load_kWh

    # Add metadata
    result['scale'] = 'DISTRICT'
    result['plant_name'] = plant_name
    result['network_name'] = network_name
    result['network_type'] = network_type

    return result


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
    import geopandas as gpd

    # Read building metadata
    zone_gdf = gpd.read_file(locator.get_zone_geometry())
    zone_gdf = zone_gdf.set_index('name')

    # Read total demand for GFA
    total_demand_df = pd.read_csv(locator.get_total_demand()).set_index('name')

    summary_rows = []

    # Process buildings
    for building_name, df in building_dfs.items():
        # Get building metadata
        if building_name in zone_gdf.index:
            geom = zone_gdf.loc[building_name, 'geometry']
            x_coord = geom.centroid.x
            y_coord = geom.centroid.y
        else:
            x_coord = None
            y_coord = None

        GFA_m2 = total_demand_df.loc[building_name, 'GFA_m2'] if building_name in total_demand_df.index else None

        # Sum demand columns (kWh -> MWh)
        Qhs_sys_MWh = df['Qhs_sys_kWh'].sum() / 1000.0
        Qww_sys_MWh = df['Qww_sys_kWh'].sum() / 1000.0
        Qcs_sys_MWh = df['Qcs_sys_kWh'].sum() / 1000.0
        E_sys_MWh = df['E_sys_kWh'].sum() / 1000.0

        # Sum carrier columns by type
        carrier_totals = {}
        for col in df.columns:
            if col.endswith('_kWh') and col not in ['Qhs_sys_kWh', 'Qww_sys_kWh', 'Qcs_sys_kWh', 'E_sys_kWh']:
                # Extract carrier from column name
                # Format: Qhs_sys_NATURALGAS_kWh -> NATURALGAS
                parts = col.split('_')
                if len(parts) >= 3:
                    carrier = parts[2]  # Get carrier part
                    if carrier not in carrier_totals:
                        carrier_totals[carrier] = 0.0
                    carrier_totals[carrier] += df[col].sum() / 1000.0  # kWh -> MWh

        # Calculate total final energy
        TOTAL_MWh = sum(carrier_totals.values())

        # Calculate peak demand
        total_demand_kW = df['Qhs_sys_kWh'] + df['Qww_sys_kWh'] + df['Qcs_sys_kWh'] + df['E_sys_kWh']
        peak_idx = total_demand_kW.idxmax()
        peak_demand_kW = total_demand_kW.iloc[peak_idx] if len(total_demand_kW) > 0 else 0.0
        peak_datetime = df.loc[peak_idx, 'date'] if len(total_demand_kW) > 0 else None

        # Get case info
        scale = df['scale'].iloc[0] if 'scale' in df.columns else 'BUILDING'
        case = df['case'].iloc[0] if 'case' in df.columns else None
        case_description = df['case_description'].iloc[0] if 'case_description' in df.columns else None

        # Build row
        row = {
            'name': building_name,
            'type': 'building',
            'GFA_m2': GFA_m2,
            'x_coord': x_coord,
            'y_coord': y_coord,
            'scale': scale,
            'case': case,
            'case_description': case_description,
            'Qhs_sys_MWh': Qhs_sys_MWh,
            'Qww_sys_MWh': Qww_sys_MWh,
            'Qcs_sys_MWh': Qcs_sys_MWh,
            'E_sys_MWh': E_sys_MWh,
        }

        # Add carrier columns
        for carrier in ['NATURALGAS', 'OIL', 'COAL', 'WOOD', 'GRID', 'DH', 'DC', 'SOLAR']:
            row[f'{carrier}_MWh'] = carrier_totals.get(carrier, 0.0)

        row['TOTAL_MWh'] = TOTAL_MWh
        row['peak_demand_kW'] = peak_demand_kW
        row['peak_datetime'] = peak_datetime

        summary_rows.append(row)

    # Process plants
    for plant_key, df in plant_dfs.items():
        # Parse plant key: "DH_NODE5" or "DC_NODE1"
        parts = plant_key.split('_', 1)
        if len(parts) == 2:
            network_type = parts[0]
            plant_name = parts[1]
        else:
            plant_name = plant_key
            network_type = df['network_type'].iloc[0] if 'network_type' in df.columns else 'UNKNOWN'

        # Get plant metadata
        network_name = df['network_name'].iloc[0] if 'network_name' in df.columns else None

        # Sum thermal load
        thermal_load_MWh = df['thermal_load_kWh'].sum() / 1000.0 if 'thermal_load_kWh' in df.columns else 0.0
        pumping_MWh = df['pumping_load_kWh'].sum() / 1000.0 if 'pumping_load_kWh' in df.columns else 0.0

        # Sum carrier columns by type
        carrier_totals = {}
        for col in df.columns:
            if col.endswith('_kWh') and col not in ['thermal_load_kWh', 'pumping_load_kWh']:
                # Extract carrier from column name
                # Format: plant_heating_NATURALGAS_kWh -> NATURALGAS
                parts_col = col.split('_')
                if len(parts_col) >= 3:
                    carrier = parts_col[2]  # Get carrier part
                    if carrier not in carrier_totals:
                        carrier_totals[carrier] = 0.0
                    carrier_totals[carrier] += df[col].sum() / 1000.0  # kWh -> MWh

        # Calculate total final energy
        TOTAL_MWh = sum(carrier_totals.values())

        # Build row
        row = {
            'name': plant_name,
            'type': 'plant',
            'GFA_m2': None,
            'x_coord': None,
            'y_coord': None,
            'scale': 'DISTRICT',
            'case': None,
            'case_description': f'{network_type} plant',
            'Qhs_sys_MWh': thermal_load_MWh if network_type == 'DH' else 0.0,
            'Qww_sys_MWh': 0.0,
            'Qcs_sys_MWh': thermal_load_MWh if network_type == 'DC' else 0.0,
            'E_sys_MWh': pumping_MWh,
        }

        # Add carrier columns
        for carrier in ['NATURALGAS', 'OIL', 'COAL', 'WOOD', 'GRID', 'DH', 'DC', 'SOLAR']:
            row[f'{carrier}_MWh'] = carrier_totals.get(carrier, 0.0)

        row['TOTAL_MWh'] = TOTAL_MWh
        row['peak_demand_kW'] = None
        row['peak_datetime'] = None

        summary_rows.append(row)

    # Create summary DataFrame
    summary_df = pd.DataFrame(summary_rows)

    return summary_df


def create_final_energy_breakdown(
    building_dfs: Dict[str, pd.DataFrame],
    plant_dfs: Dict[str, pd.DataFrame],
    building_configs: Dict[str, Dict],
    locator: cea.inputlocator.InputLocator,
    config: cea.config.Configuration
) -> pd.DataFrame:
    """
    Create detailed carrier breakdown by service (final_energy.csv).

    :param building_dfs: Dict of building_name -> final_energy DataFrame
    :param plant_dfs: Dict of plant_name -> final_energy DataFrame
    :param building_configs: Dict of building_name -> supply_configuration
    :param locator: InputLocator instance
    :param config: Configuration instance
    :return: Breakdown DataFrame with multiple rows per building/plant
    """
    breakdown_rows = []

    # Service mapping
    service_map = {
        'space_heating': {
            'demand_col': 'Qhs_sys_kWh',
            'prefix': 'Qhs_sys',
        },
        'hot_water': {
            'demand_col': 'Qww_sys_kWh',
            'prefix': 'Qww_sys',
        },
        'space_cooling': {
            'demand_col': 'Qcs_sys_kWh',
            'prefix': 'Qcs_sys',
        },
        'electricity': {
            'demand_col': 'E_sys_kWh',
            'prefix': 'E_sys',
        },
    }

    # Process buildings
    for building_name, df in building_dfs.items():
        supply_config = building_configs.get(building_name, {})

        # Process each service
        for service_key, service_info in service_map.items():
            service_config = supply_config.get(service_key)

            if not service_config or service_config['scale'] == 'NONE':
                continue

            demand_col = service_info['demand_col']
            prefix = service_info['prefix']

            # Find carrier column
            carrier = service_config['carrier']
            carrier_col = f'{prefix}_{carrier}_kWh'

            if carrier_col not in df.columns:
                # Try alternative column names for district systems
                # District systems may use simplified names like Qhs_sys_DH_kWh
                continue

            # Calculate annual totals (kWh -> MWh)
            annual_demand_MWh = df[demand_col].sum() / 1000.0
            annual_final_energy_MWh = df[carrier_col].sum() / 1000.0

            # Calculate peaks
            peak_demand_idx = df[demand_col].idxmax()
            peak_demand_kW = df.loc[peak_demand_idx, demand_col] if len(df) > 0 else 0.0
            peak_final_energy_kW = df.loc[peak_demand_idx, carrier_col] if len(df) > 0 else 0.0
            peak_datetime = df.loc[peak_demand_idx, 'date'] if len(df) > 0 else None

            # Determine component type from component code
            component_code = service_config.get('component_code')
            if component_code:
                if component_code.startswith('BO'):
                    component_type = 'Boiler'
                elif component_code.startswith('HP'):
                    component_type = 'HeatPump'
                elif component_code.startswith('CH'):
                    component_type = 'VapourCompressionChiller'
                else:
                    component_type = 'Unknown'
            else:
                component_type = None

            # Build row
            row = {
                'name': building_name,
                'type': 'building',
                'scale': service_config['scale'],
                'service': service_key,
                'demand_column': demand_col,
                'carrier': carrier,
                'assembly_code': service_config.get('assembly_code'),
                'component_code': component_code,
                'component_type': component_type,
                'efficiency': service_config.get('efficiency'),
                'annual_demand_MWh': annual_demand_MWh,
                'annual_final_energy_MWh': annual_final_energy_MWh,
                'peak_demand_kW': peak_demand_kW,
                'peak_final_energy_kW': peak_final_energy_kW,
                'peak_datetime': peak_datetime,
            }

            breakdown_rows.append(row)

        # Process booster systems if present
        # Check both configured boosters and auto-detected boosters
        for booster_col in df.columns:
            if '_booster_' in booster_col and booster_col.endswith('_kWh'):
                annual_final_energy_MWh = df[booster_col].sum() / 1000.0
                if annual_final_energy_MWh > 0:
                    # Parse column name: Qhs_booster_NATURALGAS_kWh or Qww_booster_NATURALGAS_kWh
                    parts = booster_col.split('_')
                    if parts[0] == 'Qhs':
                        service = 'space_heating_booster'
                        demand_col = 'Qhs_booster_kWh'
                    elif parts[0] == 'Qww':
                        service = 'hot_water_booster'
                        demand_col = 'Qww_booster_kWh'
                    else:
                        continue

                    # Extract carrier from column name
                    carrier = parts[2]  # NATURALGAS, GRID, etc.

                    # Get booster config if available (what-if mode)
                    booster_config = supply_config.get(service)
                    if booster_config:
                        assembly_code = booster_config.get('assembly_code')
                        component_code = booster_config.get('component_code')
                        efficiency = booster_config.get('efficiency')
                    else:
                        # Auto-detected booster (production mode)
                        assembly_code = 'AUTO_DETECTED'
                        component_code = None
                        efficiency = 0.85  # Default

                    row = {
                        'name': building_name,
                        'type': 'building',
                        'scale': 'BUILDING',
                        'service': service,
                        'demand_column': demand_col,
                        'carrier': carrier,
                        'assembly_code': assembly_code,
                        'component_code': component_code,
                        'component_type': 'Booster',
                        'efficiency': efficiency,
                        'annual_demand_MWh': None,  # Booster demand is derived from network temp delta
                        'annual_final_energy_MWh': annual_final_energy_MWh,
                        'peak_demand_kW': None,
                        'peak_final_energy_kW': None,
                        'peak_datetime': None,
                    }
                    breakdown_rows.append(row)

    # Process plants
    for plant_key, df in plant_dfs.items():
        # Parse plant key: "DH_NODE5" or "DC_NODE1"
        parts = plant_key.split('_', 1)
        if len(parts) == 2:
            network_type = parts[0]
            plant_name = parts[1]
        else:
            plant_name = plant_key
            network_type = df['network_type'].iloc[0] if 'network_type' in df.columns else 'UNKNOWN'

        # Process heating/cooling carrier
        for col in df.columns:
            if col.startswith('plant_heating_') or col.startswith('plant_cooling_'):
                # Extract carrier: plant_heating_NATURALGAS_kWh -> NATURALGAS
                parts_col = col.split('_')
                if len(parts_col) >= 3:
                    carrier = parts_col[2]
                    service_type = 'heating' if 'heating' in col else 'cooling'

                    annual_final_energy_MWh = df[col].sum() / 1000.0

                    if annual_final_energy_MWh > 0:
                        row = {
                            'name': plant_name,
                            'type': 'plant',
                            'scale': 'DISTRICT',
                            'service': f'plant_{service_type}',
                            'demand_column': 'thermal_load_kWh',
                            'carrier': carrier,
                            'assembly_code': None,
                            'component_code': None,
                            'component_type': 'Boiler' if carrier == 'NATURALGAS' else 'Chiller',
                            'efficiency': 0.85 if carrier == 'NATURALGAS' else 3.0,
                            'annual_demand_MWh': df['thermal_load_kWh'].sum() / 1000.0 if 'thermal_load_kWh' in df.columns else None,
                            'annual_final_energy_MWh': annual_final_energy_MWh,
                            'peak_demand_kW': None,
                            'peak_final_energy_kW': None,
                            'peak_datetime': None,
                        }
                        breakdown_rows.append(row)

        # Process pumping electricity
        if 'plant_pumping_GRID_kWh' in df.columns:
            annual_pumping_MWh = df['plant_pumping_GRID_kWh'].sum() / 1000.0
            if annual_pumping_MWh > 0:
                row = {
                    'name': plant_name,
                    'type': 'plant',
                    'scale': 'DISTRICT',
                    'service': 'plant_pumping',
                    'demand_column': 'pumping_load_kWh',
                    'carrier': 'GRID',
                    'assembly_code': None,
                    'component_code': None,
                    'component_type': 'Pump',
                    'efficiency': 1.0,
                    'annual_demand_MWh': df['pumping_load_kWh'].sum() / 1000.0 if 'pumping_load_kWh' in df.columns else None,
                    'annual_final_energy_MWh': annual_pumping_MWh,
                    'peak_demand_kW': None,
                    'peak_final_energy_kW': None,
                    'peak_datetime': None,
                }
                breakdown_rows.append(row)

    # Create breakdown DataFrame
    breakdown_df = pd.DataFrame(breakdown_rows)

    return breakdown_df
