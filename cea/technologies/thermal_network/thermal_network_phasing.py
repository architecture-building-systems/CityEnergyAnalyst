"""
Multi-phase thermal network expansion planning and optimization.

Orchestrates thermal network simulation across multiple phases and optimizes
pipe sizing decisions to minimize total NPV of capital and replacement costs.
"""

import os
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import geopandas as gpd

import cea.inputlocator
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2024, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def run_multi_phase(config, locator, network_names: List[str]):
    """
    Main entry point for multi-phase thermal network simulation and optimization.

    Steps:
    1. Load and validate phases
    2. Simulate each phase independently (thermal-hydraulic + sizing)
    3. Optimize pipe sizing across phases (NPV minimization)
    4. Save phasing results (timeline, schedules, sized networks)

    :param config: Configuration object
    :param locator: InputLocator object
    :param network_names: List of network layout names (one per phase)
    """
    print("\n" + "="*80)
    print("MULTI-PHASE THERMAL NETWORK OPTIMIZATION")
    print("="*80)

    # Step 1: Load and validate phases
    print("\nStep 1: Loading phases...")
    phases = load_phases(config, locator, network_names)
    validate_phases(phases)

    # Step 2: Simulate each phase
    print("\nStep 2: Simulating thermal-hydraulic performance for each phase...")
    phase_results = simulate_all_phases(config, locator, phases)

    # Step 3: Optimize pipe sizing
    print("\nStep 3: Optimizing pipe sizing across phases...")
    sizing_strategy = config.thermal_network_phasing.sizing_strategy
    sizing_decisions = optimize_pipe_sizing(
        config, locator, phases, phase_results, sizing_strategy
    )

    # Step 4: Save results
    print("\nStep 4: Saving phasing results...")
    save_phasing_results(config, locator, phases, phase_results, sizing_decisions)

    # Get phasing plan name for final message
    phasing_plan_name = config.thermal_network_phasing.phasing_plan_name
    if not phasing_plan_name:
        phasing_plan_name = network_names[0]

    network_type = config.thermal_network.network_type
    if isinstance(network_type, list):
        network_type = network_type[0] if len(network_type) > 0 else 'DH'

    print("\n" + "="*80)
    print("✅ MULTI-PHASE OPTIMIZATION COMPLETE")
    print("="*80)
    print(f"Results saved to: {locator.get_thermal_network_phasing_folder(network_type, phasing_plan_name)}")


def load_phases(config, locator, network_names: List[str]) -> List[Dict]:
    """
    Load phase configurations from network layouts and completion years.

    :param config: Configuration object
    :param locator: InputLocator object
    :param network_names: List of network layout names
    :return: List of phase dictionaries with metadata and network data
    """
    # Get completion years from config
    completion_years_str = config.thermal_network_phasing.phase_completion_year

    # Parse completion years (ListParameter returns list of strings)
    if isinstance(completion_years_str, str):
        completion_years = [int(y.strip()) for y in completion_years_str.split(',')]
    elif isinstance(completion_years_str, list):
        completion_years = [int(y) for y in completion_years_str]
    else:
        raise ValueError(f"Invalid phase_completion_year format: {completion_years_str}")

    # Validate counts match
    if len(network_names) != len(completion_years):
        raise ValueError(
            f"Number of networks ({len(network_names)}) must match "
            f"number of completion years ({len(completion_years)})\n"
            f"Networks: {network_names}\n"
            f"Years: {completion_years}"
        )

    # Get network type (DH or DC)
    network_types = config.thermal_network.network_type
    if isinstance(network_types, list):
        network_type = network_types[0] if len(network_types) > 0 else 'DH'
    else:
        network_type = network_types or 'DH'

    phases = []
    for i, (network_name, year) in enumerate(zip(network_names, completion_years)):
        print(f"  Loading phase {i+1}: {network_name} (Year {year})...")

        # Load network layout
        nodes_gdf, edges_gdf = load_network_layout(locator, network_name, network_type)

        # Extract building list from nodes
        building_nodes = nodes_gdf[
            nodes_gdf['building'].notna() &
            (nodes_gdf['building'].fillna('').str.upper() != 'NONE')
        ]
        buildings = building_nodes['building'].unique().tolist()

        phases.append({
            'index': i + 1,
            'name': f"phase{i+1}_{year}",
            'year': year,
            'network_name': network_name,
            'network_type': network_type,
            'buildings': sorted(buildings),
            'nodes_gdf': nodes_gdf,
            'edges_gdf': edges_gdf
        })

        print(f"    ✓ {len(buildings)} buildings, {len(edges_gdf)} edges")

    return phases


def load_network_layout(locator, network_name: str, network_type: str) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Load network nodes and edges shapefiles.

    New file structure:
    - Edges: thermal-network/{network-name}/layout.shp
    - Nodes: thermal-network/{network-name}/{network-type}/layout/nodes.shp

    :param locator: InputLocator object
    :param network_name: Name of network layout
    :param network_type: DH or DC
    :return: Tuple of (nodes_gdf, edges_gdf)
    """
    # Edges are now at network level (not under network_type subfolder)
    edges_path = locator.get_network_layout_shapefile(network_name)

    # Nodes are still under network_type/layout/ subfolder
    nodes_path = locator.get_network_layout_nodes_shapefile(network_type, network_name)

    if not os.path.exists(edges_path):
        raise FileNotFoundError(f"Network edges not found: {edges_path}")
    if not os.path.exists(nodes_path):
        raise FileNotFoundError(f"Network nodes not found: {nodes_path}")

    edges_gdf = gpd.read_file(edges_path)
    nodes_gdf = gpd.read_file(nodes_path)

    return nodes_gdf, edges_gdf


def validate_phases(phases: List[Dict]):
    """
    Validate phase compatibility:
    - Years must be in chronological order
    - Each phase must have >= buildings of previous phase (additive only)

    :param phases: List of phase dictionaries
    :raises ValueError: If validation fails
    """
    for i in range(1, len(phases)):
        prev_phase = phases[i-1]
        curr_phase = phases[i]

        # Check chronological order
        if curr_phase['year'] <= prev_phase['year']:
            raise ValueError(
                f"Phase years must be in chronological order.\n"
                f"Phase {i}: Year {prev_phase['year']} → Phase {i+1}: Year {curr_phase['year']}\n"
                f"Please reorder phases or adjust completion years."
            )

        # Check building compatibility (current ⊇ previous)
        prev_buildings = set(prev_phase['buildings'])
        curr_buildings = set(curr_phase['buildings'])

        if not prev_buildings <= curr_buildings:
            removed = prev_buildings - curr_buildings
            raise ValueError(
                f"Phase {i+1} ({curr_phase['network_name']}) cannot have fewer buildings than Phase {i} ({prev_phase['network_name']}).\n"
                f"Buildings removed: {sorted(removed)}\n"
                f"Multi-phase expansion must be additive only (each phase ⊇ previous phase)."
            )

    print(f"  ✓ Phase validation passed: {len(phases)} phases in chronological order")


def simulate_all_phases(config, locator, phases: List[Dict]) -> List[Dict]:
    """
    Run thermal-network simulation for each phase independently.

    This will call the existing thermal network simulation for each phase
    to get edge flows, temperatures, and pipe sizing.

    :param config: Configuration object
    :param locator: InputLocator object
    :param phases: List of phase dictionaries
    :return: List of phase result dictionaries
    """
    phase_results = []

    for phase in phases:
        print(f"\n{'='*80}")
        print(f"PHASE {phase['index']}: {phase['name']} (Year {phase['year']})")
        print(f"{'='*80}")
        print(f"Network: {phase['network_name']}")
        print(f"Buildings: {len(phase['buildings'])}")

        # TODO: Call existing thermal network simulation
        # For now, create placeholder result
        # This will be replaced with actual ThermalNetwork simulation call

        phase_result = simulate_single_phase(config, locator, phase)
        phase_results.append(phase_result)

        print(f"  ✓ Phase {phase['index']} simulation complete")
        print(f"    Edges: {len(phase_result['edge_mass_flows'])}")
        print(f"    Peak demand: {phase_result['total_demand_kw']:.0f} kW")

    return phase_results


def simulate_single_phase(config, locator, phase: Dict) -> Dict:
    """
    Simulate a single phase network.

    TODO: This is a placeholder. Will be replaced with actual ThermalNetwork class call.

    :param config: Configuration object
    :param locator: InputLocator object
    :param phase: Phase dictionary
    :return: Phase result dictionary
    """
    # Placeholder - extract edge data from loaded network
    edges_gdf = phase['edges_gdf']

    # Create mock results for testing
    edge_mass_flows = {}
    edge_diameters = {}
    edge_lengths = {}

    for idx, edge in edges_gdf.iterrows():
        edge_name = edge.get('name', f"PIPE{idx}")
        edge_mass_flows[edge_name] = 1.0  # Placeholder kg/s
        edge_diameters[edge_name] = 100  # Placeholder DN
        edge_lengths[edge_name] = edge.geometry.length if hasattr(edge.geometry, 'length') else 100.0

    return {
        'phase_index': phase['index'],
        'phase_name': phase['name'],
        'network_name': phase['network_name'],
        'year': phase['year'],
        'edge_mass_flows': edge_mass_flows,
        'edge_diameters': edge_diameters,
        'edge_lengths': edge_lengths,
        'total_demand_kw': len(phase['buildings']) * 100.0  # Placeholder
    }


def optimize_pipe_sizing(config, locator, phases: List[Dict],
                        phase_results: List[Dict], strategy: str) -> Dict:
    """
    Optimize pipe sizing decisions across all phases.

    For each edge, decide optimal DN for each phase based on strategy:
    - 'optimise': Minimize NPV (per-edge decision: size now vs replace later)
    - 'size-per-phase': Always size for current phase demand
    - 'pre-size-all': Always size for final phase demand

    :param config: Configuration object
    :param locator: InputLocator object
    :param phases: List of phase dictionaries
    :param phase_results: List of phase result dictionaries
    :param strategy: Sizing strategy choice
    :return: Dictionary of sizing decisions per edge
    """
    print(f"\n  Strategy: {strategy}")

    # Load pipe costs from database
    pipe_costs = load_pipe_costs(locator)

    # Get financial parameters from config
    discount_rate = config.thermal_network_phasing.discount_rate
    replacement_multiplier = config.thermal_network_phasing.replacement_cost_multiplier

    # Get all unique edges across all phases
    all_edges = get_all_edges_across_phases(phase_results)

    print(f"  Analyzing {len(all_edges)} unique edges across {len(phases)} phases...")

    sizing_decisions = {}

    for edge_id in all_edges:
        # Get DN required for each phase (from simulation)
        dn_per_phase = []
        length = None

        for phase_result in phase_results:
            if edge_id in phase_result['edge_diameters']:
                dn_per_phase.append(phase_result['edge_diameters'][edge_id])
                if length is None:
                    length = phase_result['edge_lengths'].get(edge_id, 100.0)
            else:
                dn_per_phase.append(None)  # Edge doesn't exist in this phase yet

        # Apply sizing strategy
        if strategy == 'optimise':
            decision = optimize_single_edge(
                edge_id, dn_per_phase, phases, length, pipe_costs,
                discount_rate, replacement_multiplier
            )
        elif strategy == 'size-per-phase':
            decision = size_per_phase_strategy(
                edge_id, dn_per_phase, phases, length, pipe_costs, discount_rate, replacement_multiplier
            )
        elif strategy == 'pre-size-all':
            decision = pre_size_all_strategy(
                edge_id, dn_per_phase, phases, length, pipe_costs
            )
        else:
            raise ValueError(f"Unknown sizing strategy: {strategy}")

        sizing_decisions[edge_id] = decision

    # Calculate summary statistics
    total_npv = sum(d['total_npv'] for d in sizing_decisions.values())
    total_replacements = sum(
        sum(1 for phase_key in d.keys()
            if phase_key.startswith('phase') and d[phase_key].get('action') == 'replace')
        for d in sizing_decisions.values()
    )

    print(f"\n  ✓ Optimization complete:")
    print(f"    Total NPV: €{total_npv:,.0f}")
    print(f"    Pipes requiring replacement: {total_replacements}")

    return sizing_decisions


def load_pipe_costs(locator) -> pd.DataFrame:
    """
    Load pipe costs from database THERMAL_GRID.csv.

    :param locator: InputLocator object
    :return: DataFrame with columns [DN, cost_per_m_eur]
    """
    thermal_grid_path = locator.get_database_components_distribution_thermal_grid()
    df = pd.read_csv(thermal_grid_path)

    # Extract DN and costs
    # Assuming columns: pipe_DN, CAPEX_pipe_USD_per_m (adjust based on actual structure)
    if 'pipe_DN' in df.columns and 'CAPEX_pipe_USD_per_m' in df.columns:
        pipe_costs = df[['pipe_DN', 'CAPEX_pipe_USD_per_m']].copy()
        pipe_costs.columns = ['DN', 'cost_per_m_eur']
        pipe_costs = pipe_costs.drop_duplicates(subset=['DN'])
        return pipe_costs
    else:
        # Fallback: create simple cost lookup
        print("  ⚠ Warning: Using default pipe costs (database columns not found)")
        return pd.DataFrame({
            'DN': [50, 80, 100, 125, 150, 200, 250, 300],
            'cost_per_m_eur': [100, 120, 150, 180, 220, 280, 350, 450]
        })


def get_all_edges_across_phases(phase_results: List[Dict]) -> List[str]:
    """
    Get list of all unique edge IDs across all phases.

    :param phase_results: List of phase result dictionaries
    :return: List of edge IDs
    """
    all_edges = set()
    for phase_result in phase_results:
        all_edges.update(phase_result['edge_diameters'].keys())
    return sorted(all_edges)


def optimize_single_edge(edge_id: str, dn_per_phase: List[Optional[int]],
                        phases: List[Dict], length: float, pipe_costs: pd.DataFrame,
                        discount_rate: float, replacement_multiplier: float) -> Dict:
    """
    Minimize NPV for a single edge by choosing optimal sizing path.

    Compares:
    - Option A: Size per phase (replace as needed)
    - Option B: Pre-size for final (no replacement)

    :return: Decision dictionary with DN per phase and costs
    """
    # Get final DN (maximum across all phases)
    dn_values = [dn for dn in dn_per_phase if dn is not None]
    if not dn_values:
        # Edge never exists
        return {'strategy': 'n/a', 'total_npv': 0}

    final_dn = max(dn_values)

    # Option A: Size per phase (replace when needed)
    cost_a = calculate_size_per_phase_cost(
        edge_id, dn_per_phase, phases, length, pipe_costs, discount_rate, replacement_multiplier
    )

    # Option B: Pre-size for final
    cost_b = calculate_pre_size_cost(
        edge_id, dn_per_phase, phases, final_dn, length, pipe_costs
    )

    # Choose cheaper option
    if cost_a['total_npv'] < cost_b['total_npv']:
        result = cost_a
        result['strategy'] = 'size-per-phase (optimized)'
    else:
        result = cost_b
        result['strategy'] = 'pre-size (optimized)'

    return result


def size_per_phase_strategy(edge_id: str, dn_per_phase: List[Optional[int]],
                            phases: List[Dict], length: float, pipe_costs: pd.DataFrame,
                            discount_rate: float, replacement_multiplier: float) -> Dict:
    """
    Size-per-phase strategy: Always size for current phase demand.

    :return: Decision dictionary with DN per phase and costs
    """
    return calculate_size_per_phase_cost(
        edge_id, dn_per_phase, phases, length, pipe_costs, discount_rate, replacement_multiplier
    )


def pre_size_all_strategy(edge_id: str, dn_per_phase: List[Optional[int]],
                          phases: List[Dict], length: float, pipe_costs: pd.DataFrame) -> Dict:
    """
    Pre-size-all strategy: Always size for final phase demand from the start.

    :return: Decision dictionary with DN per phase and costs
    """
    # Get final DN (maximum across all phases)
    dn_values = [dn for dn in dn_per_phase if dn is not None]
    if not dn_values:
        return {'strategy': 'n/a', 'total_npv': 0}

    final_dn = max(dn_values)

    return calculate_pre_size_cost(
        edge_id, dn_per_phase, phases, final_dn, length, pipe_costs
    )


def calculate_size_per_phase_cost(edge_id: str, dn_per_phase: List[Optional[int]],
                                  phases: List[Dict], length: float, pipe_costs: pd.DataFrame,
                                  discount_rate: float, replacement_multiplier: float) -> Dict:
    """
    Calculate cost for size-per-phase approach.

    :return: Dictionary with per-phase decisions and total NPV
    """
    result = {'strategy': 'size-per-phase', 'total_npv': 0}

    current_dn = None
    for i, (phase, dn) in enumerate(zip(phases, dn_per_phase)):
        phase_key = f"phase{i+1}"

        if dn is None:
            # Edge doesn't exist in this phase
            result[phase_key] = {'DN': None, 'action': 'none', 'cost': 0, 'cost_npv': 0}
            continue

        if current_dn is None:
            # Initial install
            cost = get_pipe_cost(dn, length, pipe_costs)
            result[phase_key] = {
                'DN': dn,
                'action': 'install',
                'cost': cost,
                'cost_npv': cost  # Year 0, no discounting for first phase
            }
            result['total_npv'] += cost
            current_dn = dn
        elif dn > current_dn:
            # Need to replace with larger pipe
            cost = get_pipe_cost(dn, length, pipe_costs) * replacement_multiplier
            years_from_start = phase['year'] - phases[0]['year']
            cost_npv = npv_discount(cost, years_from_start, discount_rate)
            result[phase_key] = {
                'DN': dn,
                'action': 'replace',
                'cost': cost,
                'cost_npv': cost_npv
            }
            result['total_npv'] += cost_npv
            current_dn = dn
        else:
            # Keep existing pipe
            result[phase_key] = {
                'DN': current_dn,
                'action': 'keep',
                'cost': 0,
                'cost_npv': 0
            }

    return result


def calculate_pre_size_cost(edge_id: str, dn_per_phase: List[Optional[int]],
                            phases: List[Dict], final_dn: int, length: float,
                            pipe_costs: pd.DataFrame) -> Dict:
    """
    Calculate cost for pre-size-all approach.

    :return: Dictionary with per-phase decisions and total NPV
    """
    result = {'strategy': 'pre-size-all', 'total_npv': 0}

    installed = False
    for i, (phase, dn) in enumerate(zip(phases, dn_per_phase)):
        phase_key = f"phase{i+1}"

        if dn is None:
            # Edge doesn't exist in this phase
            result[phase_key] = {'DN': None, 'action': 'none', 'cost': 0, 'cost_npv': 0}
            continue

        if not installed:
            # Install at final DN from the start
            cost = get_pipe_cost(final_dn, length, pipe_costs)
            result[phase_key] = {
                'DN': final_dn,
                'action': 'install',
                'cost': cost,
                'cost_npv': cost  # Year 0, no discounting
            }
            result['total_npv'] += cost
            installed = True
        else:
            # Keep existing pre-sized pipe
            result[phase_key] = {
                'DN': final_dn,
                'action': 'keep',
                'cost': 0,
                'cost_npv': 0
            }

    return result


def get_pipe_cost(dn: int, length: float, pipe_costs: pd.DataFrame) -> float:
    """
    Get pipe cost from cost lookup table.

    :param dn: Nominal diameter (mm)
    :param length: Pipe length (m)
    :param pipe_costs: DataFrame with DN and cost_per_m_eur columns
    :return: Total cost (EUR)
    """
    # Find closest DN in cost table
    closest_dn = pipe_costs.iloc[(pipe_costs['DN'] - dn).abs().argsort()[:1]]
    if len(closest_dn) == 0:
        # Fallback
        return 150 * length  # Default €150/m

    cost_per_m = closest_dn.iloc[0]['cost_per_m_eur']
    return cost_per_m * length


def npv_discount(cost: float, years_from_now: float, discount_rate: float) -> float:
    """
    Calculate NPV of a future cost.

    NPV = cost / (1 + rate)^years

    :param cost: Future cost (EUR)
    :param years_from_now: Years from present
    :param discount_rate: Annual discount rate (e.g., 0.03 for 3%)
    :return: Present value (EUR)
    """
    if years_from_now <= 0:
        return cost
    return cost / ((1 + discount_rate) ** years_from_now)


def save_phasing_results(config, locator, phases: List[Dict],
                        phase_results: List[Dict], sizing_decisions: Dict):
    """
    Save phasing results to:
    outputs/data/thermal-network/phasing-plans/{plan-name}/{network-type}/
        ├── phasing_summary.csv
        ├── pipe_sizing_decisions.csv
        ├── cost_breakdown_by_phase.csv
        ├── npv_analysis.csv
        └── phase_sizing/
            ├── phase1_YYYY_sized.csv
            ├── phase2_YYYY_sized.csv
            └── phase3_YYYY_sized.csv

    :param config: Configuration object
    :param locator: InputLocator object
    :param phases: List of phase dictionaries
    :param phase_results: List of phase result dictionaries
    :param sizing_decisions: Dictionary of sizing decisions per edge
    """
    # Get phasing plan name from config
    phasing_plan_name = config.thermal_network_phasing.phasing_plan_name
    if not phasing_plan_name:
        # Default to first network name if not specified
        phasing_plan_name = phases[0]['network_name']

    network_type = phases[0]['network_type']

    # Use locator methods for phasing paths
    phasing_folder = locator.get_thermal_network_phasing_folder(network_type, phasing_plan_name)
    os.makedirs(phasing_folder, exist_ok=True)

    # Save consolidated phasing summary (combines metrics and costs)
    save_phasing_summary(phasing_folder, phases, phase_results, sizing_decisions, config)

    # Save pipe sizing decisions
    save_pipe_sizing_decisions(phasing_folder, phases, sizing_decisions)

    # Save timeline CSVs
    save_edges_timeline_csv(phasing_folder, phases, phase_results, sizing_decisions)
    save_nodes_timeline_csv(phasing_folder, phases)

    # Save phase-specific shapefiles
    save_phase_network_shapefiles(locator, phases, phase_results, sizing_decisions, network_type, phasing_plan_name)

    # Save final network shapefiles
    save_final_network_shapefiles(locator, phases, phase_results, sizing_decisions, network_type, phasing_plan_name)

    # Save substation results per phase
    save_phase_substation_results(locator, phases, phase_results, network_type, phasing_plan_name)

    print(f"\n  ✓ Results saved to: {phasing_folder}/")
    print(f"    - phasing_summary.csv")
    print(f"    - pipe_sizing_decisions.csv")
    print(f"    - edges_timeline.csv")
    print(f"    - nodes_timeline.csv")
    print(f"    - layout/edges_final.shp")
    print(f"    - layout/nodes_final.shp")


def save_phasing_summary(folder: str, phases: List[Dict],
                        phase_results: List[Dict], sizing_decisions: Dict, config):
    """
    Save consolidated phasing summary CSV with metrics, costs, and NPV analysis.
    Combines what was previously in phasing_summary, cost_breakdown, and npv_analysis.
    """
    summary_data = []

    for phase, phase_result in zip(phases, phase_results):
        # Calculate costs broken down by action type
        install_cost = 0
        replace_cost = 0
        install_npv = 0
        replace_npv = 0
        num_installs = 0
        num_replacements = 0

        for edge_id, decision in sizing_decisions.items():
            phase_key = f"phase{phase['index']}"
            if phase_key not in decision:
                continue

            phase_decision = decision[phase_key]
            if phase_decision['action'] == 'install':
                install_cost += phase_decision['cost']
                install_npv += phase_decision['cost_npv']
                num_installs += 1
            elif phase_decision['action'] == 'replace':
                replace_cost += phase_decision['cost']
                replace_npv += phase_decision['cost_npv']
                num_replacements += 1

        summary_data.append({
            'Phase': phase['index'],
            'Name': phase['name'],
            'Year': phase['year'],
            'Network': phase['network_name'],
            'Buildings': len(phase['buildings']),
            'Edges': len(phase_result['edge_diameters']),
            'Peak_Demand_kW': phase_result['total_demand_kw'],
            'Install_Cost_USD2015': install_cost,
            'Replace_Cost_USD2015': replace_cost,
            'Total_Cost_USD2015': install_cost + replace_cost,
            'Install_NPV_USD2015': install_npv,
            'Replace_NPV_USD2015': replace_npv,
            'Total_NPV_USD2015': install_npv + replace_npv,
            'Num_Installs': num_installs,
            'Num_Replacements': num_replacements
        })

    df = pd.DataFrame(summary_data)
    df.to_csv(os.path.join(folder, 'phasing_summary.csv'), index=False)


def save_pipe_sizing_decisions(folder: str, phases: List[Dict], sizing_decisions: Dict):
    """Save pipe sizing decisions CSV with all pipe actions across phases."""
    decisions_data = []

    for phase in phases:
        for edge_id, decision in sizing_decisions.items():
            phase_key = f"phase{phase['index']}"
            if phase_key not in decision:
                continue

            phase_decision = decision[phase_key]
            decisions_data.append({
                'Edge': edge_id,
                'Phase': phase['index'],
                'Year': phase['year'],
                'Action': phase_decision['action'],
                'DN': phase_decision['DN'],
                'Old_DN': phase_decision.get('old_dn', 'n/a'),
                'Cost_USD2015': phase_decision['cost'],
                'Cost_NPV_USD2015': phase_decision['cost_npv'],
                'Strategy': decision.get('strategy', 'n/a')
            })

    df = pd.DataFrame(decisions_data)
    df = df.sort_values(['Edge', 'Phase'])
    df.to_csv(os.path.join(folder, 'pipe_sizing_decisions.csv'), index=False)


# Removed: save_cost_breakdown, save_npv_analysis, save_phase_sized_network
# These have been consolidated into save_phasing_summary and phase-specific shapefiles


def save_phase_network_shapefiles(locator, phases: List[Dict], phase_results: List[Dict],
                                   sizing_decisions: Dict, network_type: str, phasing_plan_name: str):
    """
    Save phase-specific network shapefiles showing spatial evolution.

    Creates for each phase:
    - edges_phaseN_YYYY.shp - All edges existing in that phase with sizing info
    - nodes_phaseN_YYYY.shp - All nodes existing in that phase (cumulative)

    :param locator: InputLocator object
    :param phases: List of phase dictionaries
    :param phase_results: List of phase result dictionaries
    :param sizing_decisions: Dictionary of sizing decisions per edge
    :param network_type: DH or DC
    :param phasing_plan_name: Name of phasing plan
    """
    layout_folder = os.path.join(
        locator.get_thermal_network_phasing_folder(network_type, phasing_plan_name),
        'layout'
    )
    os.makedirs(layout_folder, exist_ok=True)

    # Track all nodes seen so far (cumulative)
    cumulative_nodes = gpd.GeoDataFrame()

    for phase, phase_result in zip(phases, phase_results):
        phase_num = phase['index']
        year = phase['year']

        # Create edges shapefile for this phase
        edges_gdf = create_phase_edges_gdf(phase, phase_result, sizing_decisions)
        edges_filename = f"edges_phase{phase_num}_{year}.shp"
        edges_path = os.path.join(layout_folder, edges_filename)
        edges_gdf.to_file(edges_path)

        # Create nodes shapefile for this phase (cumulative)
        nodes_gdf = create_phase_nodes_gdf(phase, phase_result, cumulative_nodes)
        cumulative_nodes = nodes_gdf.copy()  # Update for next phase
        nodes_filename = f"nodes_phase{phase_num}_{year}.shp"
        nodes_path = os.path.join(layout_folder, nodes_filename)
        nodes_gdf.to_file(nodes_path)

    print(f"    - layout/ ({len(phases)} phase shapefiles)")


def create_phase_edges_gdf(phase: Dict, phase_result: Dict, sizing_decisions: Dict) -> gpd.GeoDataFrame:
    """
    Create GeoDataFrame for edges in a specific phase.

    :param phase: Phase dictionary
    :param phase_result: Phase result dictionary
    :param sizing_decisions: Sizing decisions dictionary
    :return: GeoDataFrame with edge geometries and attributes
    """
    edges_data = []
    phase_key = f"phase{phase['index']}"

    # Get original edges GeoDataFrame from phase
    original_edges = phase['edges_gdf'].copy()

    for edge_id in phase_result['edge_diameters'].keys():
        # Get decision for this edge in this phase
        decision = sizing_decisions.get(edge_id, {})
        phase_decision = decision.get(phase_key, {})

        # Get geometry from original edges
        edge_row = original_edges[original_edges['name'] == edge_id]
        if len(edge_row) == 0:
            continue

        geometry = edge_row.iloc[0].geometry
        type_mat = edge_row.iloc[0].get('type_mat', '')

        edges_data.append({
            'name': edge_id,
            'type_mat': type_mat,
            'length_m': phase_result['edge_lengths'][edge_id],
            'DN': phase_decision.get('DN', phase_result['edge_diameters'][edge_id]),
            'phase_num': phase['index'],
            'year': phase['year'],
            'action': phase_decision.get('action', 'existing'),
            'cost_USD': phase_decision.get('cost', 0),
            'is_new': phase_decision.get('action') == 'install',
            'geometry': geometry
        })

    gdf = gpd.GeoDataFrame(edges_data, crs=original_edges.crs)
    return gdf


def create_phase_nodes_gdf(phase: Dict, phase_result: Dict, cumulative_nodes: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Create GeoDataFrame for nodes in a specific phase (cumulative).

    :param phase: Phase dictionary
    :param phase_result: Phase result dictionary
    :param cumulative_nodes: GeoDataFrame of nodes from previous phases
    :return: GeoDataFrame with node geometries and attributes
    """
    # Get original nodes from this phase
    original_nodes = phase['nodes_gdf'].copy()

    # Determine which nodes are new in this phase
    if len(cumulative_nodes) == 0:
        # First phase - all nodes are new
        original_nodes['phase_intro'] = phase['index']
        original_nodes['year_intro'] = phase['year']
        original_nodes['is_new'] = True
    else:
        # Find nodes that didn't exist before
        existing_node_names = set(cumulative_nodes['name'].values) if 'name' in cumulative_nodes.columns else set()
        original_nodes['is_new'] = ~original_nodes['name'].isin(existing_node_names)
        original_nodes['phase_intro'] = phase['index']
        original_nodes['year_intro'] = phase['year']

        # Merge with previous nodes (keep historical phase_intro for old nodes)
        for idx, row in original_nodes.iterrows():
            if not row['is_new']:
                old_node = cumulative_nodes[cumulative_nodes['name'] == row['name']]
                if len(old_node) > 0:
                    original_nodes.at[idx, 'phase_intro'] = old_node.iloc[0]['phase_intro']
                    original_nodes.at[idx, 'year_intro'] = old_node.iloc[0]['year_intro']

    return original_nodes


def save_edges_timeline_csv(folder: str, phases: List[Dict], phase_results: List[Dict], sizing_decisions: Dict):
    """
    Save complete temporal evolution of edges as CSV.

    :param folder: Output folder
    :param phases: List of phase dictionaries
    :param phase_results: List of phase result dictionaries
    :param sizing_decisions: Sizing decisions dictionary
    """
    timeline_data = []

    for phase, phase_result in zip(phases, phase_results):
        phase_key = f"phase{phase['index']}"

        for edge_id in phase_result['edge_diameters'].keys():
            decision = sizing_decisions.get(edge_id, {})
            phase_decision = decision.get(phase_key, {})

            timeline_data.append({
                'edge_id': edge_id,
                'phase': phase['index'],
                'year': phase['year'],
                'action': phase_decision.get('action', 'existing'),
                'DN': phase_decision.get('DN', phase_result['edge_diameters'][edge_id]),
                'length_m': phase_result['edge_lengths'][edge_id],
                'cost_USD2015': phase_decision.get('cost', 0),
                'cost_npv_USD2015': phase_decision.get('cost_npv', 0),
                'strategy': decision.get('strategy', 'n/a')
            })

    df = pd.DataFrame(timeline_data)
    df.to_csv(os.path.join(folder, 'edges_timeline.csv'), index=False)


def save_nodes_timeline_csv(folder: str, phases: List[Dict]):
    """
    Save complete temporal evolution of nodes as CSV.

    :param folder: Output folder
    :param phases: List of phase dictionaries
    """
    timeline_data = []
    seen_nodes = set()

    for phase in phases:
        nodes_gdf = phase['nodes_gdf']

        for _, node in nodes_gdf.iterrows():
            node_id = node['name']

            # Only record when node is first introduced
            if node_id not in seen_nodes:
                timeline_data.append({
                    'node_id': node_id,
                    'building': node.get('building', 'NONE'),
                    'type': node.get('type', 'NONE'),
                    'phase_introduced': phase['index'],
                    'year_introduced': phase['year'],
                    'geometry_wkt': node.geometry.wkt
                })
                seen_nodes.add(node_id)

    df = pd.DataFrame(timeline_data)
    df.to_csv(os.path.join(folder, 'nodes_timeline.csv'), index=False)


def save_final_network_shapefiles(locator, phases: List[Dict], phase_results: List[Dict],
                                   sizing_decisions: Dict, network_type: str, phasing_plan_name: str):
    """
    Save final network state as shapefiles (edges_final.shp, nodes_final.shp).

    :param locator: InputLocator object
    :param phases: List of phase dictionaries
    :param phase_results: List of phase result dictionaries
    :param sizing_decisions: Sizing decisions dictionary
    :param network_type: DH or DC
    :param phasing_plan_name: Name of phasing plan
    """
    layout_folder = os.path.join(
        locator.get_thermal_network_phasing_folder(network_type, phasing_plan_name),
        'layout'
    )

    # Final phase is last phase
    final_phase = phases[-1]
    final_result = phase_results[-1]

    # Create edges_final.shp
    edges_data = []
    final_edges_gdf = final_phase['edges_gdf'].copy()

    for edge_id in final_result['edge_diameters'].keys():
        decision = sizing_decisions.get(edge_id, {})

        # Find when edge was introduced
        phase_intro = None
        year_intro = None
        for p in phases:
            if edge_id in p['edges_gdf']['name'].values:
                phase_intro = p['index']
                year_intro = p['year']
                break

        # Count replacements
        num_replacements = sum(
            1 for key in decision.keys()
            if isinstance(decision.get(key), dict) and decision[key].get('action') == 'replace'
        )

        # Calculate total cost
        total_cost = sum(
            decision[f"phase{p['index']}"].get('cost', 0)
            for p in phases
            if f"phase{p['index']}" in decision
        )

        # Get geometry
        edge_row = final_edges_gdf[final_edges_gdf['name'] == edge_id]
        if len(edge_row) == 0:
            continue

        geometry = edge_row.iloc[0].geometry
        type_mat = edge_row.iloc[0].get('type_mat', '')

        edges_data.append({
            'name': edge_id,
            'type_mat': type_mat,
            'length_m': final_result['edge_lengths'][edge_id],
            'DN_final': final_result['edge_diameters'][edge_id],
            'phase_intro': phase_intro,
            'year_intro': year_intro,
            'num_repl': num_replacements,
            'cost_USD': total_cost,
            'strategy': decision.get('strategy', 'n/a'),
            'geometry': geometry
        })

    edges_final_gdf = gpd.GeoDataFrame(edges_data, crs=final_edges_gdf.crs)
    edges_final_gdf.to_file(os.path.join(layout_folder, 'edges_final.shp'))

    # Create nodes_final.shp (all nodes from final phase)
    nodes_final_gdf = final_phase['nodes_gdf'].copy()

    # Add phase_introduced info
    nodes_final_gdf['phase_intro'] = 0
    nodes_final_gdf['year_intro'] = 0

    for _, node in nodes_final_gdf.iterrows():
        node_id = node['name']
        # Find when node was introduced
        for p in phases:
            if node_id in p['nodes_gdf']['name'].values:
                nodes_final_gdf.loc[nodes_final_gdf['name'] == node_id, 'phase_intro'] = p['index']
                nodes_final_gdf.loc[nodes_final_gdf['name'] == node_id, 'year_intro'] = p['year']
                break

    nodes_final_gdf.to_file(os.path.join(layout_folder, 'nodes_final.shp'))


def save_phase_substation_results(locator, phases: List[Dict], phase_results: List[Dict],
                                   network_type: str, phasing_plan_name: str):
    """
    Save substation results for each phase.

    Creates folder structure:
    phasing-plans/{plan-name}/{network-type}/substation/
        ├── phase1_2030/
        │   ├── {network-type}_{network-name}_substation_{building}.csv
        │   └── ...
        ├── phase2_2050/
        │   └── ...
        └── ...

    :param locator: InputLocator object
    :param phases: List of phase dictionaries
    :param phase_results: List of phase result dictionaries
    :param network_type: DH or DC
    :param phasing_plan_name: Name of phasing plan
    """
    base_substation_folder = os.path.join(
        locator.get_thermal_network_phasing_folder(network_type, phasing_plan_name),
        'substation'
    )
    os.makedirs(base_substation_folder, exist_ok=True)

    for phase, phase_result in zip(phases, phase_results):
        phase_num = phase['index']
        year = phase['year']
        network_name = phase['network_name']

        # Create substation folder for this phase
        phase_substation_folder = os.path.join(
            base_substation_folder,
            f"phase{phase_num}_{year}"
        )
        os.makedirs(phase_substation_folder, exist_ok=True)

        # Get substation results from phase_result
        # TODO: When actual thermal network simulation is integrated,
        # this will contain real hourly data from ThermalNetwork class
        substation_results = phase_result.get('substation_results', {})

        if substation_results:
            # Save per-building substation results
            for building, data in substation_results.items():
                filename = f"{network_type}_{network_name}_substation_{building}.csv"
                filepath = os.path.join(phase_substation_folder, filename)
                data.to_csv(filepath, index=False)
        else:
            # Create placeholder CSV files with expected structure
            # When thermal simulation is integrated, these will be replaced with real data
            for building in phase['buildings']:
                filename = f"{network_type}_{network_name}_substation_{building}.csv"
                filepath = os.path.join(phase_substation_folder, filename)

                # Create empty DataFrame with expected columns (matching single-phase output)
                placeholder_df = pd.DataFrame({
                    'date': [],
                    'mdot_DH_result_kgpers': [],
                    'T_return_DH_result_C': [],
                    'T_supply_DH_result_C': [],
                    'HEX_hs_area_m2': [],
                    'HEX_ww_area_m2': [],
                    'Qhs_dh_W': [],
                    'Qww_dh_W': [],
                    'Qhs_booster_W': [],
                    'Qww_booster_W': []
                })
                placeholder_df.to_csv(filepath, index=False)

    print(f"    - substation/ ({len(phases)} phase folders)")
