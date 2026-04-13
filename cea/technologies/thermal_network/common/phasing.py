"""
Multi-phase thermal network expansion planning and optimisation.

Orchestrates thermal network simulation across multiple phases and optimises
pipe sizing decisions to minimise total NPV of capital and replacement costs.
"""

import os
import json
import pandas as pd
import geopandas as gpd
from typing import TYPE_CHECKING, List, Dict, Optional, Tuple

from cea.technologies.thermal_network.common.geometry import load_network_shapefiles


# Precision for canonical edge identity. mm (3 decimals) is fine enough to
# distinguish real adjacent pipes but coarse enough to absorb shapefile round-
# trip float drift. Tighter than this risks false-missing matches on
# re-loaded geometries; coarser would collapse nearby distinct pipes.
CANONICAL_EDGE_PRECISION = 3

# A canonical edge id is a frozen sorted pair of (x, y) rounded coords.
# Using a tuple lets it serve as a dict key; sorting enforces direction-
# insensitivity (A→B and B→A are the same physical pipe).
CanonicalEdgeId = Tuple[Tuple[float, float], Tuple[float, float]]


def _canonical_edge_id(geometry, precision: int = CANONICAL_EDGE_PRECISION) -> CanonicalEdgeId:
    """
    Return a stable identity key for a pipe geometry based on its endpoints,
    so the same physical pipe can be matched across phase layouts even when
    each phase's Part 1 run gave it a different `name` (e.g. sub1's PIPE1 is
    sub2's PIPE2 for the same geometry).
    """
    coords = list(geometry.coords)
    a = (round(coords[0][0], precision), round(coords[0][1], precision))
    b = (round(coords[-1][0], precision), round(coords[-1][1], precision))
    return tuple(sorted((a, b)))


def _build_edge_maps(edges_gdf: gpd.GeoDataFrame) -> Tuple[Dict[str, CanonicalEdgeId],
                                                           Dict[CanonicalEdgeId, str]]:
    """
    Build (name → canonical, canonical → name) lookups for one phase's
    edges_gdf. If two edges in the same phase map to the same canonical id
    (shouldn't happen — that would be a duplicate pipe), the first one wins.
    """
    name_to_cid: Dict[str, CanonicalEdgeId] = {}
    cid_to_name: Dict[CanonicalEdgeId, str] = {}
    for _, row in edges_gdf.iterrows():
        cid = _canonical_edge_id(row.geometry)
        name = row['name']
        name_to_cid[name] = cid
        cid_to_name.setdefault(cid, name)
    return name_to_cid, cid_to_name

if TYPE_CHECKING:
    from cea.config import Configuration
    from cea.inputlocator import InputLocator


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2024, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def run_multi_phase(config: "Configuration", locator: "InputLocator", network_names: List[str],
                    model_type: str = 'simplified'):
    """
    Main entry point for multi-phase thermal network simulation and optimisation.

    Steps:
    1. Load and validate phases
    2. Simulate each phase independently (thermal-hydraulic + sizing)
    3. Optimise pipe sizing across phases (NPV minimisation)
    4. Save phasing results (timeline, schedules, sized networks)

    :param config: Configuration object
    :param locator: InputLocator object
    :param network_names: List of network layout names (one per phase)
    :param model_type: 'simplified' or 'detailed'
    """
    print("\n" + "="*80)
    print("MULTI-PHASE THERMAL NETWORK OPTIMISATION")
    print("="*80)

    # Step 1: Load and validate phases
    print("\nStep 1: Loading phases...")
    phases = load_phases(config, locator, network_names)
    validate_phases(phases)

    # Step 2: Simulate each phase
    print("\nStep 2: Simulating thermal-hydraulic performance for each phase...")
    phase_results = simulate_all_phases(config, locator, phases, model_type=model_type)

    # Step 3: Optimise pipe sizing
    print("\nStep 3: Optimising pipe sizing across phases...")
    sizing_strategy = config.thermal_network_phasing.sizing_strategy
    sizing_decisions = optimize_pipe_sizing(
        config, locator, phases, phase_results, sizing_strategy
    )

    # Step 3.5: Re-run simulation with optimized DN to get accurate pressure drops and pumping energy
    print("\nStep 3.5: Re-running simulation with optimised pipe sizes...")
    phase_results_optimized = resimulate_with_optimized_dn(
        config, locator, phases, phase_results, sizing_decisions, model_type=model_type
    )

    # Step 4: Save results
    print("\nStep 4: Saving phasing results...")
    save_phasing_results(config, locator, phases, phase_results_optimized, sizing_decisions)

    # Get phasing plan name for final message
    phasing_plan_name = config.thermal_network_phasing.phasing_plan_name
    if not phasing_plan_name:
        phasing_plan_name = network_names[0]

    network_type = config.thermal_network.network_type
    if len(network_type):
        network_type = network_type[0]
    else:
        raise ValueError("Network type must be specified.")

    print("\n" + "="*80)
    print("MULTI-PHASE OPTIMISATION COMPLETE")
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
        nodes_gdf, edges_gdf = load_network_shapefiles(locator, network_type, network_name)

        # Extract building list from nodes
        building_nodes = nodes_gdf[
            nodes_gdf['building'].notna() &
            (nodes_gdf['building'].fillna('').str.upper() != 'NONE')
        ]
        buildings = building_nodes['building'].unique().tolist()

        name_to_cid, cid_to_name = _build_edge_maps(edges_gdf)

        phases.append({
            'index': i + 1,
            'name': f"phase{i+1}",
            'year': year,
            'network_name': network_name,
            'network_type': network_type,
            'buildings': sorted(buildings),
            'nodes_gdf': nodes_gdf,
            'edges_gdf': edges_gdf,
            'edge_name_to_cid': name_to_cid,
            'edge_cid_to_name': cid_to_name,
        })

        print(f"    {len(buildings)} buildings, {len(edges_gdf)} edges")

    return phases


def validate_phases(phases: List[Dict]):
    """
    Validate phase compatibility:
    - Years must be in chronological order
    - Connected buildings may be added OR removed between phases. Reductions
      are treated as decommissioning under a sunk-infrastructure model: pipes
      stay in the trench (zero CAPEX, zero salvage), only the per-phase
      operational simulation changes.

    :param phases: List of phase dictionaries
    :raises ValueError: If validation fails (years non-monotonic)
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

        # Connected building changes are informational — decommissioning is allowed
        prev_buildings = set(prev_phase['buildings'])
        curr_buildings = set(curr_phase['buildings'])
        added = curr_buildings - prev_buildings
        removed = prev_buildings - curr_buildings
        if added:
            print(f"  Phase {i+1} ({curr_phase['network_name']}) adds {len(added)} building(s): {sorted(added)}")
        if removed:
            print(
                f"  Phase {i+1} ({curr_phase['network_name']}) decommissions {len(removed)} building(s): "
                f"{sorted(removed)}"
            )
            print(
                "    (pipes remain installed — sunk infrastructure; no CAPEX, no salvage, no per-phase OPEX for decommissioned buildings)"
            )

    # Per-phase graph health check: each phase must be a connected graph with
    # at least one plant reachable from every surviving consumer. This catches
    # the footgun where decommissioning a trunk-middle building (via Part 1
    # filter/subtract/replan) leaves a downstream branch orphaned from the plant.
    for phase in phases:
        _validate_phase_graph(phase)

    print(f"  Phase validation passed: {len(phases)} phases in chronological order")


def _validate_phase_graph(phase: Dict) -> None:
    """
    Check that a phase's network is a single connected graph linking every
    consumer to at least one plant. Raises ValueError with a targeted message
    if the check fails.
    """
    import networkx as nx

    nodes_gdf = phase['nodes_gdf']
    edges_gdf = phase['edges_gdf']

    if nodes_gdf is None or nodes_gdf.empty or edges_gdf is None or edges_gdf.empty:
        raise ValueError(
            f"Phase {phase['index']} ({phase['network_name']}) has an empty network. "
            "A phase must have at least one pipe and one consumer node."
        )

    def _coord(geom):
        return (round(geom.x, 6), round(geom.y, 6))

    def _edge_coords(line):
        coords = list(line.coords)
        return (
            (round(coords[0][0], 6), round(coords[0][1], 6)),
            (round(coords[-1][0], 6), round(coords[-1][1], 6)),
        )

    g = nx.Graph()
    name_by_coord = {}
    for _, row in nodes_gdf.iterrows():
        c = _coord(row.geometry)
        g.add_node(c)
        name_by_coord[c] = row['name']
    for _, row in edges_gdf.iterrows():
        a, b = _edge_coords(row.geometry)
        if a != b:
            g.add_edge(a, b)

    type_col = nodes_gdf['type'].fillna('').str.upper() if 'type' in nodes_gdf.columns else None
    is_plant = type_col.str.startswith('PLANT') if type_col is not None else pd.Series([False] * len(nodes_gdf))
    is_consumer = nodes_gdf['building'].notna() & (nodes_gdf['building'].fillna('').str.upper() != 'NONE')
    if type_col is not None:
        is_consumer = is_consumer & ~is_plant

    plant_coords = {_coord(g_) for g_, plant in zip(nodes_gdf.geometry, is_plant) if plant}
    consumer_coords = {_coord(g_): name_by_coord[_coord(g_)]
                       for g_, cons in zip(nodes_gdf.geometry, is_consumer) if cons}

    if not plant_coords:
        raise ValueError(
            f"Phase {phase['index']} ({phase['network_name']}) has no plant node. "
            "Every phase must have at least one plant to supply the consumers."
        )
    if not consumer_coords:
        raise ValueError(
            f"Phase {phase['index']} ({phase['network_name']}) has no consumer nodes. "
            "A phase with no connected buildings is not a valid thermal network."
        )

    orphaned = []
    for component in nx.connected_components(g):
        component_consumers = [consumer_coords[c] for c in component if c in consumer_coords]
        component_plants = [c for c in component if c in plant_coords]
        if component_consumers and not component_plants:
            orphaned.extend(component_consumers)

    if orphaned:
        preview = sorted(orphaned)[:10]
        more = f" ... and {len(orphaned) - 10} more" if len(orphaned) > 10 else ""
        raise ValueError(
            f"Phase {phase['index']} ({phase['network_name']}) has consumer nodes that are not "
            f"connected to any plant:\n  {', '.join(preview)}{more}\n"
            "This usually happens when a phase drops a trunk-middle building and the "
            "downstream branch is left orphaned. Re-run network-layout for this phase "
            "so the remaining consumers stay connected to a plant, or add the trunk "
            "building back to the phase."
        )


def simulate_all_phases(config, locator, phases: List[Dict], model_type: str = 'simplified') -> List[Dict]:
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

        phase_result = simulate_single_phase(config, locator, phase, model_type=model_type)
        phase_results.append(phase_result)

        print(f"  Phase {phase['index']} simulation complete")
        print(f"    Edges: {len(phase_result['edge_diameters'])}")
        print(f"    Peak demand: {phase_result['total_demand_kw']:.0f} kW")

    return phase_results


def resimulate_with_optimized_dn(config, locator, phases: List[Dict],
                                  phase_results: List[Dict], sizing_decisions: Dict,
                                  model_type: str = 'simplified') -> List[Dict]:
    """
    Re-run thermal network simulation for each phase using optimised pipe diameters.

    This updates pressure drops and pumping energy based on optimised DN values,
    ensuring that CSV outputs reflect the actual optimised network performance.

    :param config: Configuration object
    :param locator: InputLocator object
    :param phases: List of phase dictionaries
    :param phase_results: Original simulation results (will be updated)
    :param sizing_decisions: Optimisation decisions with DN per phase
    :return: Updated phase_results with accurate pressure drops and pumping energy
    """
    optimized_phase_results = []

    for phase, phase_result in zip(phases, phase_results):
        print(f"\n  Re-simulating Phase {phase['index']}: {phase['name']}...")

        # Update edges shapefile with optimised DN values
        network_name = phase['network_name']
        network_type = config.thermal_network.network_type
        if isinstance(network_type, list):
            network_type = network_type[0] if len(network_type) > 0 else 'DH'

        # Create temporary shapefile with optimised DN
        edges_path = locator.get_network_layout_edges_shapefile(network_type, network_name)
        if not os.path.exists(edges_path):
            print(
                f"    Warning: Edges shapefile not found for phase {phase['index']} "
                f"({network_name}). Skipping re-simulation; using original results."
            )
            optimized_phase_results.append(phase_result)
            continue
        edges_gdf = gpd.read_file(edges_path)

        # Apply optimised DN from sizing decisions. sizing_decisions is keyed
        # by canonical edge id; this phase's edges_gdf uses local names, so
        # route every write through the name → canonical lookup on the phase.
        phase_key = f"phase{phase['index']}"
        name_to_cid = phase['edge_name_to_cid']
        for edge_name in edges_gdf['name']:
            cid = name_to_cid.get(edge_name)
            if cid is None:
                continue
            decision = sizing_decisions.get(cid, {})
            phase_decision = decision.get(phase_key, {})
            optimized_dn = phase_decision.get('DN')

            if optimized_dn is not None:
                edges_gdf.loc[edges_gdf['name'] == edge_name, 'pipe_DN'] = optimized_dn

        # Save updated shapefile (overwrite original temporarily)
        edges_gdf.to_file(edges_path)

        # Re-run simulation with optimised DN
        try:
            optimized_result = simulate_single_phase(config, locator, phase, model_type=model_type)
            optimized_phase_results.append(optimized_result)

            print("    Re-simulation complete with optimised DN")
            print(f"      Peak pumping: {optimized_result.get('plant_peak_pumping_kw', 0):.1f} kW")

        except Exception as e:
            print(f"    Warning: Re-simulation failed: {e}")
            print("      Using original simulation results")
            optimized_phase_results.append(phase_result)

    return optimized_phase_results


def simulate_single_phase(config, locator, phase: Dict, model_type: str = 'simplified') -> Dict:
    """
    Simulate a single phase network by calling actual thermal network simulation.

    :param config: Configuration object
    :param locator: InputLocator object
    :param phase: Phase dictionary
    :param model_type: 'simplified' or 'detailed'
    :return: Phase result dictionary with actual simulation results
    """
    from cea.technologies.thermal_network.simplified.model import thermal_network_simplified
    from cea.technologies.thermal_network.detailed.model import (
        check_heating_cooling_demand, ThermalNetwork, thermal_network_main
    )

    network_name = phase['network_name']
    network_types = config.thermal_network.network_type
    if isinstance(network_types, list):
        network_type = network_types[0] if len(network_types) > 0 else 'DH'
    else:
        network_type = network_types or 'DH'

    print(f"\n  Running {model_type} model simulation...")

    # Run the actual thermal network simulation
    try:
        if model_type == 'simplified':
            # Read per-building service configuration from unified network_connectivity.json
            connectivity_json_path = locator.get_network_connectivity_file(network_name)
            per_building_services = None

            if os.path.exists(connectivity_json_path):
                # Read from unified network_connectivity.json
                with open(connectivity_json_path, 'r') as f:
                    connectivity_data = json.load(f)

                # Extract per-building services for this network type
                if network_type in connectivity_data.get('networks', {}):
                    network_data = connectivity_data['networks'][network_type]
                    per_building_services_dict = network_data.get('per_building_services', {})

                    if per_building_services_dict:
                        # Convert lists back to sets
                        per_building_services = {
                            building: set(services)
                            for building, services in per_building_services_dict.items()
                        }
            else:
                # Fallback: Try legacy building_services.json location
                nodes_path = locator.get_network_layout_nodes_shapefile(network_type, network_name)
                legacy_metadata_path = os.path.join(os.path.dirname(nodes_path), 'building_services.json')

                if os.path.exists(legacy_metadata_path):
                    with open(legacy_metadata_path, 'r') as f:
                        metadata = json.load(f)

                    # Convert lists back to sets
                    per_building_services = {
                        building: set(services)
                        for building, services in metadata['per_building_services'].items()
                    }

            thermal_network_simplified(locator, config, network_type, network_name,
                                      per_building_services=per_building_services)

        elif model_type == 'detailed':
            check_heating_cooling_demand(locator, config)

            # Create a per-network config section with the correct network_type
            class NetworkConfig:
                def __init__(self, base_config, network_type_override):
                    self.network_type = network_type_override
                    # Copy all other attributes from base config
                    for attr in ['network_names', 'file_type',
                               'load_max_edge_flowrate_from_previous_run', 'start_t', 'stop_t',
                               'use_representative_week_per_month', 'minimum_mass_flow_iteration_limit',
                               'minimum_edge_mass_flow', 'diameter_iteration_limit',
                               'substation_cooling_systems', 'substation_heating_systems',
                               'network_temperature_dh', 'network_temperature_dc',
                               'dh_temperature_mode',
                               'temperature_control', 'plant_supply_temperature', 'equivalent_length_factor']:
                        if hasattr(base_config, attr):
                            setattr(self, attr, getattr(base_config, attr))

            per_network_config = NetworkConfig(config.thermal_network, network_type)
            thermal_network = ThermalNetwork(locator, network_name, per_network_config)
            thermal_network_main(locator, thermal_network, processes=config.get_number_of_processes())
        else:
            raise RuntimeError(f"Unknown model type: {model_type}")

    except Exception as e:
        # Do NOT silently substitute placeholder data — that would feed fake
        # DN=100 values into the cost optimiser and the final CSV reports
        # would look plausible while being wrong. Re-raise with phase context
        # so the user knows which sub-network failed.
        raise RuntimeError(
            f"Thermal-network simulation failed for phase {phase['index']} "
            f"({phase['network_name']}): {e}"
        ) from e

    # Read simulation results from output files
    return read_phase_simulation_results(locator, phase, network_type, network_name)


def read_phase_simulation_results(locator, phase: Dict, network_type: str, network_name: str) -> Dict:
    """
    Read simulation results from output files.

    :param locator: InputLocator object
    :param phase: Phase dictionary
    :param network_type: DH or DC
    :param network_name: Network layout name
    :return: Dictionary with simulation results
    """
    # Read metadata edges to get DN values
    metadata_edges_path = locator.get_thermal_network_edge_list_file(network_type, network_name)
    metadata_edges = pd.read_csv(metadata_edges_path)

    # Read plant thermal load
    plant_thermal_path = locator.get_thermal_network_plant_heat_requirement_file(network_type, network_name)
    plant_thermal = pd.read_csv(plant_thermal_path, index_col=0)  # First column is index

    # Read plant pumping load
    plant_pumping_path = locator.get_network_energy_pumping_requirements_file(network_type, network_name)
    plant_pumping = pd.read_csv(plant_pumping_path)

    # Extract edge data, keyed by canonical edge id so phases with different
    # per-phase naming (sub1's PIPE1 ≠ sub2's PIPE1 for the same geometry)
    # still align correctly across the multi-phase sizing engine.
    name_to_cid = phase['edge_name_to_cid']
    edge_diameters = {}
    edge_lengths = {}
    missing_names = []
    for _, edge in metadata_edges.iterrows():
        edge_name = edge['name']
        cid = name_to_cid.get(edge_name)
        if cid is None:
            missing_names.append(edge_name)
            continue
        edge_diameters[cid] = edge['pipe_DN']
        edge_lengths[cid] = edge['length_m']
    if missing_names:
        print(
            f"    Warning: {len(missing_names)} pipe name(s) from simulation output not found "
            f"in phase {phase['index']} layout: {missing_names[:5]}"
            + (f" ... and {len(missing_names) - 5} more" if len(missing_names) > 5 else "")
        )

    # Calculate plant metrics - drop date columns if they exist
    # Handle both 'date' and 'DATE' column names
    thermal_cols_to_drop = [col for col in plant_thermal.columns if col.lower() in ['date', 'time']]
    thermal_data = plant_thermal.drop(columns=thermal_cols_to_drop) if thermal_cols_to_drop else plant_thermal

    plant_peak_thermal_kw = thermal_data.max().max()
    plant_annual_thermal_mwh = thermal_data.sum().sum() / 1000.0

    pumping_cols_to_drop = [col for col in plant_pumping.columns if col.lower() in ['date', 'time']]
    pumping_data = plant_pumping.drop(columns=pumping_cols_to_drop) if pumping_cols_to_drop else plant_pumping

    plant_peak_pumping_kw = pumping_data.max().max()
    plant_annual_pumping_mwh = pumping_data.sum().sum() / 1000.0

    # Calculate total demand from plant thermal load
    total_demand_kw = plant_peak_thermal_kw

    return {
        'phase_index': phase['index'],
        'phase_name': phase['name'],
        'network_name': phase['network_name'],
        'year': phase['year'],
        'edge_mass_flows': {},  # Not used in optimization
        'edge_diameters': edge_diameters,
        'edge_lengths': edge_lengths,
        'total_demand_kw': total_demand_kw,
        'plant_peak_thermal_kw': plant_peak_thermal_kw,
        'plant_peak_pumping_kw': plant_peak_pumping_kw,
        'plant_annual_thermal_mwh': plant_annual_thermal_mwh,
        'plant_annual_pumping_mwh': plant_annual_pumping_mwh
    }


def optimize_pipe_sizing(config, locator, phases: List[Dict],
                        phase_results: List[Dict], strategy: str) -> Dict:
    """
    Optimise pipe sizing decisions across all phases.

    For each edge, decide optimal DN for each phase based on strategy:
    - 'optimise': Minimise NPV (per-edge decision: size now vs replace later)
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
                edge_id, dn_per_phase, phases, length, pipe_costs, replacement_multiplier
            )
        elif strategy == 'size-per-phase':
            decision = size_per_phase_strategy(
                edge_id, dn_per_phase, phases, length, pipe_costs, replacement_multiplier
            )
        elif strategy == 'pre-size-all':
            decision = pre_size_all_strategy(
                edge_id, dn_per_phase, phases, length, pipe_costs
            )
        else:
            raise ValueError(f"Unknown sizing strategy: {strategy}")

        sizing_decisions[edge_id] = decision

    # Calculate summary statistics
    total_cost = sum(d['total_cost'] for d in sizing_decisions.values())
    total_replacements = sum(
        sum(1 for phase_key in d.keys()
            if phase_key.startswith('phase') and d[phase_key].get('action') == 'replace')
        for d in sizing_decisions.values()
    )

    print("\n  Optimisation complete:")
    print(f"    Total Cost: ${total_cost:,.0f} USD2015")
    print(f"    Pipes requiring replacement: {total_replacements}")

    return sizing_decisions


#: Canonical column names in the scenario THERMAL_GRID.csv cost table.
#: These match the schema shipped in cea/databases/{CH,DE,SG}/COMPONENTS/
#: DISTRIBUTION/THERMAL_GRID.csv — pipe_DN is the nominal diameter in mm
#: and Inv_USD2015perm is the per-meter install cost in USD2015.
THERMAL_GRID_DN_COL = 'pipe_DN'
THERMAL_GRID_COST_COL = 'Inv_USD2015perm'


def load_pipe_costs(locator) -> pd.DataFrame:
    """
    Load pipe costs from the scenario's THERMAL_GRID.csv distribution database.

    The pipe cost table is authoritative — every pipe diameter the phasing
    engine needs to cost MUST be present in this file. If required columns
    are missing, we raise a clear error pointing at the file and the expected
    schema instead of silently substituting hardcoded defaults (which would
    let wrong numbers propagate all the way to the final cost report).

    :param locator: InputLocator object
    :return: DataFrame with columns [DN, cost_per_m_eur]
    :raises ValueError: If the file is missing required columns
    """
    thermal_grid_path = locator.get_database_components_distribution_thermal_grid()
    if not os.path.exists(thermal_grid_path):
        raise ValueError(
            f"THERMAL_GRID.csv not found at:\n  {thermal_grid_path}\n"
            "Multi-phase pipe sizing requires this file. Check that the "
            "scenario's distribution database is populated."
        )

    df = pd.read_csv(thermal_grid_path)
    required_cols = {THERMAL_GRID_DN_COL, THERMAL_GRID_COST_COL}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"THERMAL_GRID.csv is missing required column(s): {sorted(missing)}\n"
            f"  File: {thermal_grid_path}\n"
            f"  Present columns: {list(df.columns)}\n"
            f"Multi-phase pipe sizing reads costs from {THERMAL_GRID_DN_COL} + {THERMAL_GRID_COST_COL}. "
            "Add these columns to the file or replace it with a version that has them."
        )

    pipe_costs = df[[THERMAL_GRID_DN_COL, THERMAL_GRID_COST_COL]].copy()
    pipe_costs.columns = ['DN', 'cost_per_m_eur']
    pipe_costs = pipe_costs.drop_duplicates(subset=['DN'])
    if pipe_costs.empty:
        raise ValueError(
            f"THERMAL_GRID.csv has the required columns but no rows:\n"
            f"  File: {thermal_grid_path}"
        )
    return pipe_costs


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
                        replacement_multiplier: float) -> Dict:
    """
    Minimise cost for a single edge by choosing optimal sizing path (in constant USD2015).

    Compares:
    - Option A: Size per phase (replace as needed)
    - Option B: Pre-size for final (no replacement)

    :return: Decision dictionary with DN per phase and costs
    """
    # Get final DN (maximum across all phases)
    dn_values = [dn for dn in dn_per_phase if dn is not None]
    if not dn_values:
        # Edge never exists
        return {'strategy': 'n/a', 'total_cost': 0}

    final_dn = max(dn_values)

    # Option A: Size per phase (replace when needed)
    cost_a = calculate_size_per_phase_cost(
        edge_id, dn_per_phase, phases, length, pipe_costs, replacement_multiplier
    )

    # Option B: Pre-size for final
    cost_b = calculate_pre_size_cost(
        edge_id, dn_per_phase, phases, final_dn, length, pipe_costs
    )

    # Choose cheaper option
    if cost_a['total_cost'] < cost_b['total_cost']:
        result = cost_a
        result['strategy'] = 'size-per-phase (optimised)'
    else:
        result = cost_b
        result['strategy'] = 'pre-size (optimised)'

    return result


def size_per_phase_strategy(edge_id: str, dn_per_phase: List[Optional[int]],
                            phases: List[Dict], length: float, pipe_costs: pd.DataFrame,
                            replacement_multiplier: float) -> Dict:
    """
    Size-per-phase strategy: Always size for current phase demand (in constant USD2015).

    :return: Decision dictionary with DN per phase and costs
    """
    return calculate_size_per_phase_cost(
        edge_id, dn_per_phase, phases, length, pipe_costs, replacement_multiplier
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
        return {'strategy': 'n/a', 'total_cost': 0}

    final_dn = max(dn_values)

    return calculate_pre_size_cost(
        edge_id, dn_per_phase, phases, final_dn, length, pipe_costs
    )


def calculate_size_per_phase_cost(edge_id: str, dn_per_phase: List[Optional[int]],
                                  phases: List[Dict], length: float, pipe_costs: pd.DataFrame,
                                  replacement_multiplier: float) -> Dict:
    """
    Calculate cost for size-per-phase approach (in constant USD2015).

    Actions on a per-phase basis:
      - 'none':     edge has not been installed in any phase up to this one
      - 'install':  edge is being installed for the first time this phase
      - 'replace':  edge exists but required DN has grown — replace at multiplier
      - 'keep':     edge exists, required DN is ≤ installed DN, still carrying flow
      - 'idle':     edge exists (installed in an earlier phase) but does not
                    carry flow this phase (connected building decommissioned).
                    Pipe stays in the trench under the sunk-infrastructure model:
                    zero CAPEX, zero salvage. Installed DN is preserved so a
                    later reactivation or demand increase sees the real state.

    :return: Dictionary with per-phase decisions and total cost
    """
    result = {'strategy': 'size-per-phase', 'total_cost': 0}

    current_dn = None
    for i, (phase, dn) in enumerate(zip(phases, dn_per_phase)):
        phase_key = f"phase{i+1}"

        if dn is None:
            if current_dn is None:
                # Edge hasn't been installed in any prior phase
                result[phase_key] = {'DN': None, 'action': 'none', 'cost': 0}
            else:
                # Edge was installed earlier but is idle this phase
                # (e.g. downstream building decommissioned). Sunk infra: keep
                # the installed pipe, no CAPEX, no salvage.
                result[phase_key] = {'DN': current_dn, 'action': 'idle', 'cost': 0}
            continue

        if current_dn is None:
            # Initial install
            cost = get_pipe_cost(dn, length, pipe_costs)
            result[phase_key] = {
                'DN': dn,
                'action': 'install',
                'cost': cost
            }
            result['total_cost'] += cost
            current_dn = dn
        elif dn > current_dn:
            # Need to replace with larger pipe
            cost = get_pipe_cost(dn, length, pipe_costs) * replacement_multiplier
            result[phase_key] = {
                'DN': dn,
                'action': 'replace',
                'cost': cost
            }
            result['total_cost'] += cost
            current_dn = dn
        else:
            # Keep existing pipe
            result[phase_key] = {
                'DN': current_dn,
                'action': 'keep',
                'cost': 0
            }

    return result


def calculate_pre_size_cost(edge_id: str, dn_per_phase: List[Optional[int]],
                            phases: List[Dict], final_dn: int, length: float,
                            pipe_costs: pd.DataFrame) -> Dict:
    """
    Calculate cost for pre-size-all approach (in constant USD2015).

    See calculate_size_per_phase_cost for the action vocabulary. The pre-size
    strategy never uses 'replace' — the pipe is installed once at its final
    (maximum-across-phases) DN and kept thereafter. Phases with no flow after
    install are labelled 'idle'.

    :return: Dictionary with per-phase decisions and total cost
    """
    result = {'strategy': 'pre-size-all', 'total_cost': 0}

    installed = False
    for i, (phase, dn) in enumerate(zip(phases, dn_per_phase)):
        phase_key = f"phase{i+1}"

        if dn is None:
            if not installed:
                # Edge hasn't appeared yet in any prior phase
                result[phase_key] = {'DN': None, 'action': 'none', 'cost': 0}
            else:
                # Installed earlier, idle this phase (decommissioned building)
                result[phase_key] = {'DN': final_dn, 'action': 'idle', 'cost': 0}
            continue

        if not installed:
            # Install at final DN when edge first appears
            cost = get_pipe_cost(final_dn, length, pipe_costs)
            result[phase_key] = {
                'DN': final_dn,
                'action': 'install',
                'cost': cost
            }
            result['total_cost'] += cost
            installed = True
        else:
            # Keep existing pre-sized pipe
            result[phase_key] = {
                'DN': final_dn,
                'action': 'keep',
                'cost': 0
            }

    return result


def get_pipe_cost(dn: int, length: float, pipe_costs: pd.DataFrame) -> float:
    """
    Look up the per-meter install cost for a pipe of diameter `dn` in the
    database cost table and return total cost = cost_per_m × length.

    The requested DN must be ≤ the largest DN in the table. If a simulation
    produces a DN larger than the database covers, this raises — silently
    substituting "the largest available" would under-estimate the cost AND
    imply the engineer can install a pipe that physically can't carry the
    required flow.

    For DNs smaller than the database minimum, we round up to the smallest
    available DN (commercially there's no point sizing below the smallest
    stocked pipe). For DNs in the middle that don't exactly match a row, we
    round up to the next available commercial size.

    :param dn: Nominal diameter (mm) — must be a positive integer
    :param length: Pipe length (m)
    :param pipe_costs: DataFrame with DN and cost_per_m_eur columns, non-empty
    :return: Total cost (USD2015)
    :raises ValueError: If required DN exceeds the largest DN in the database
    """
    if pipe_costs.empty:
        raise ValueError("get_pipe_cost called with empty pipe_costs table")

    available_dns = pipe_costs['DN'].astype(int).tolist()
    max_dn = max(available_dns)
    if dn > max_dn:
        raise ValueError(
            f"Pipe sizing needs DN {dn} mm, but the largest DN in the cost "
            f"database is {max_dn} mm. Available DNs: {sorted(set(available_dns))}.\n"
            "Add a larger pipe row to THERMAL_GRID.csv, or check why the "
            "simulation is producing an over-sized diameter."
        )

    # Round up to the smallest available DN ≥ requested.
    candidates = [d for d in available_dns if d >= dn]
    chosen_dn = min(candidates)
    row = pipe_costs[pipe_costs['DN'] == chosen_dn].iloc[0]
    return float(row['cost_per_m_eur']) * length


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
    save_phasing_summary(locator, phases, phase_results, sizing_decisions, config, network_type, phasing_plan_name)

    # Save pipe sizing decisions
    save_pipe_sizing_decisions(locator, phases, sizing_decisions, network_type, phasing_plan_name)

    # Save timeline CSVs
    save_edges_timeline_csv(locator, phases, phase_results, sizing_decisions, network_type, phasing_plan_name)
    save_nodes_timeline_csv(locator, phases, network_type, phasing_plan_name)

    # Save timeline network shapefiles (top-level layout/ with optimisation metadata)
    save_final_network_shapefiles(locator, phases, phase_results, sizing_decisions, network_type, phasing_plan_name)

    # Save individual phase layout shapefiles (matching single-phase structure)
    save_phase_layout_shapefiles(locator, phases, phase_results, sizing_decisions, network_type, phasing_plan_name)

    # Save substation results per phase (inside each phase folder)
    save_phase_substation_results(locator, phases, phase_results, network_type, phasing_plan_name)

    # Copy all simulation results to phase-specific folders
    copy_phase_simulation_results(locator, phases, network_type, phasing_plan_name)

    print(f"\n  Results saved to: {phasing_folder}/")
    print("    - phasing_summary.csv")
    print("    - pipe_sizing_decisions.csv")
    print("    - edges_timeline.csv")
    print("    - nodes_timeline.csv")
    print("    - layout/edges.shp, nodes.shp (timeline with optimisation metadata)")
    print(f"    - {phases[0]['network_name']}/...{phases[-1]['network_name']}/ (single-phase structure)")


def save_phasing_summary(locator, phases: List[Dict],
                        phase_results: List[Dict], sizing_decisions: Dict, config,
                        network_type: str, phasing_plan_name: str):
    """
    Save consolidated phasing summary CSV with metrics, costs, and NPV analysis.
    Combines what was previously in phasing_summary, cost_breakdown, and npv_analysis.
    """
    summary_data = []

    for phase, phase_result in zip(phases, phase_results):
        # Calculate costs broken down by action type
        install_cost = 0
        replace_cost = 0
        num_installs = 0
        num_replacements = 0
        num_idle = 0

        phase_key = f"phase{phase['index']}"
        for edge_id, decision in sizing_decisions.items():
            if phase_key not in decision:
                continue

            phase_decision = decision[phase_key]
            action = phase_decision['action']
            if action == 'install':
                install_cost += phase_decision['cost']
                num_installs += 1
            elif action == 'replace':
                replace_cost += phase_decision['cost']
                num_replacements += 1
            elif action == 'idle':
                num_idle += 1

        summary_data.append({
            'phase': phase['index'],
            'year': phase['year'],
            'network': phase['network_name'],
            'buildings': len(phase['buildings']),
            'edges': len(phase_result['edge_diameters']),
            'peak_demand_kW': phase_result['total_demand_kw'],
            'plant_peak_thermal_kW': phase_result.get('plant_peak_thermal_kw', 0),
            'plant_peak_pumping_kW': phase_result.get('plant_peak_pumping_kw', 0),
            'plant_annual_thermal_MWh': phase_result.get('plant_annual_thermal_mwh', 0),
            'plant_annual_pumping_MWh': phase_result.get('plant_annual_pumping_mwh', 0),
            'install_cost_USD2015': install_cost,
            'replace_cost_USD2015': replace_cost,
            'total_cost_USD2015': install_cost + replace_cost,
            'num_installs': num_installs,
            'num_replacements': num_replacements,
            'num_idle': num_idle,
        })

    df = pd.DataFrame(summary_data)
    # Round numeric columns to 2 decimal places
    numeric_cols = ['peak_demand_kW', 'plant_peak_thermal_kW', 'plant_peak_pumping_kW',
                    'plant_annual_thermal_MWh', 'plant_annual_pumping_MWh',
                    'install_cost_USD2015', 'replace_cost_USD2015', 'total_cost_USD2015']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].round(2)
    df.to_csv(locator.get_thermal_network_phasing_summary_file(network_type, phasing_plan_name), index=False)


def save_pipe_sizing_decisions(locator, phases: List[Dict], sizing_decisions: Dict,
                              network_type: str, phasing_plan_name: str):
    """Save pipe sizing decisions CSV with all pipe actions across phases."""
    display_name_by_cid: Dict[CanonicalEdgeId, str] = {}
    for p in phases:
        for cid, name in p['edge_cid_to_name'].items():
            display_name_by_cid.setdefault(cid, name)

    decisions_data = []

    for phase in phases:
        for cid, decision in sizing_decisions.items():
            phase_key = f"phase{phase['index']}"
            if phase_key not in decision:
                continue

            phase_decision = decision[phase_key]
            decisions_data.append({
                'edge': display_name_by_cid.get(cid, ''),
                'phase': phase['index'],
                'year': phase['year'],
                'action': phase_decision['action'],
                'DN': phase_decision['DN'],
                'old_DN': phase_decision.get('old_dn', 'n/a'),
                'cost_USD2015': phase_decision['cost'],
                'strategy': decision.get('strategy', 'n/a')
            })

    df = pd.DataFrame(decisions_data)
    df = df.sort_values(['edge', 'phase'])
    # Round numeric columns to 2 decimal places
    numeric_cols = ['DN', 'cost_USD2015']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].round(2)
    df.to_csv(locator.get_thermal_network_pipe_sizing_decisions_file(network_type, phasing_plan_name), index=False)


# Removed: save_cost_breakdown, save_npv_analysis, save_phase_sized_network
# These have been consolidated into save_phasing_summary and phase-specific shapefiles


def save_edges_timeline_csv(locator, phases: List[Dict], phase_results: List[Dict], sizing_decisions: Dict,
                           network_type: str, phasing_plan_name: str):
    """
    Save complete temporal evolution of edges as CSV.

    Emits one row per (edge, phase) for every edge that has ever been installed,
    including phases where the edge is 'idle' (installed earlier, no flow this
    phase because the downstream building was decommissioned). Phases before
    the edge's first install are skipped.

    :param phases: List of phase dictionaries
    :param phase_results: List of phase result dictionaries
    :param sizing_decisions: Sizing decisions dictionary (keyed by edge_id,
        containing per-phase decisions with the 'idle' action where applicable)
    """
    # Build a length lookup and a display-name lookup. sizing_decisions and
    # phase_result['edge_lengths'] are both keyed by canonical edge id now;
    # we surface a first-seen per-phase local name in the CSV so the output
    # is human-readable.
    length_lookup: Dict[CanonicalEdgeId, float] = {}
    for phase_result in phase_results:
        for cid, length in phase_result['edge_lengths'].items():
            length_lookup.setdefault(cid, length)

    display_name_by_cid: Dict[CanonicalEdgeId, str] = {}
    for p in phases:
        for cid, name in p['edge_cid_to_name'].items():
            display_name_by_cid.setdefault(cid, name)

    timeline_data = []

    for phase, phase_result in zip(phases, phase_results):
        phase_key = f"phase{phase['index']}"

        for cid, decision in sizing_decisions.items():
            phase_decision = decision.get(phase_key, {})
            action = phase_decision.get('action', 'none')
            if action == 'none':
                continue

            dn = phase_decision.get('DN')
            if dn is None:
                dn = phase_result['edge_diameters'].get(cid)

            timeline_data.append({
                'edge_id': display_name_by_cid.get(cid, ''),
                'phase': phase['index'],
                'year': phase['year'],
                'action': action,
                'DN': dn,
                'length_m': length_lookup.get(cid, 0.0),
                'cost_USD2015': phase_decision.get('cost', 0),
                'strategy': decision.get('strategy', 'n/a')
            })

    df = pd.DataFrame(timeline_data)
    # Round numeric columns to 2 decimal places
    numeric_cols = ['DN', 'length_m', 'cost_USD2015']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].round(2)
    df.to_csv(locator.get_thermal_network_edges_timeline_file(network_type, phasing_plan_name), index=False)


def save_nodes_timeline_csv(locator, phases: List[Dict], network_type: str, phasing_plan_name: str):
    """
    Save complete temporal evolution of nodes as CSV.

    Columns (in addition to node_id / building / type / geometry):
      - phase_introduced, year_introduced: phase where the node first appears
      - phase_last_seen, year_last_seen:   phase where the node last appears.
        For persistent nodes this equals the final phase. For decommissioned
        consumer nodes (a connected building dropped in a later phase) it's
        the last phase in which the node was still listed. Infrastructure
        nodes (plants, junctions) typically persist to the final phase even
        if downstream buildings are decommissioned.

    :param phases: List of phase dictionaries
    """
    # First pass: collect first/last-seen info per node.
    first_seen: Dict[str, int] = {}
    last_seen: Dict[str, int] = {}
    node_meta: Dict[str, Dict] = {}

    for phase in phases:
        nodes_gdf = phase['nodes_gdf']
        phase_idx = phase['index']
        for _, node in nodes_gdf.iterrows():
            node_id = node['name']
            if node_id not in first_seen:
                first_seen[node_id] = phase_idx
                node_meta[node_id] = {
                    'building': node.get('building', 'NONE'),
                    'type': node.get('type', 'NONE'),
                    'geometry_wkt': node.geometry.wkt,
                }
            last_seen[node_id] = phase_idx

    # Build year lookup by phase index for the last-seen year.
    year_by_phase: Dict[int, int] = {p['index']: p['year'] for p in phases}

    timeline_data = []
    for node_id, first_idx in first_seen.items():
        last_idx = last_seen[node_id]
        meta = node_meta[node_id]
        timeline_data.append({
            'node_id': node_id,
            'building': meta['building'],
            'type': meta['type'],
            'phase_introduced': first_idx,
            'year_introduced': year_by_phase[first_idx],
            'phase_last_seen': last_idx,
            'year_last_seen': year_by_phase[last_idx],
            'geometry_wkt': meta['geometry_wkt'],
        })

    df = pd.DataFrame(timeline_data)
    df.to_csv(locator.get_thermal_network_nodes_timeline_file(network_type, phasing_plan_name), index=False)


def save_final_network_shapefiles(locator, phases: List[Dict], phase_results: List[Dict],
                                   sizing_decisions: Dict, network_type: str, phasing_plan_name: str):
    """
    Save timeline network shapefiles with multi-phase optimisation metadata.

    Creates layout/edges.shp and layout/nodes.shp covering the union of every
    edge/node that was ever installed across all phases (so idle pipes for
    decommissioned buildings are still drawn). Attributes:

    - phase_intro, year_intro: when each edge/node was first installed
    - phase_last, year_last:   last phase each edge/node was active / present
    - num_repl: number of replacements over the full timeline
    - cost_USD: total cost across all phases
    - strategy: optimisation strategy (pre-size vs size-per-phase)
    - is_idle_final: 1 if the edge's action in the final phase is 'idle'
      (installed but no flow) / 0 otherwise

    :param locator: InputLocator object
    :param phases: List of phase dictionaries
    :param phase_results: List of phase result dictionaries
    :param sizing_decisions: Sizing decisions dictionary
    :param network_type: DH or DC
    :param phasing_plan_name: Name of phasing plan
    """
    layout_folder = locator.get_thermal_network_phasing_plan_layout_folder(network_type, phasing_plan_name)
    os.makedirs(layout_folder, exist_ok=True)

    final_phase = phases[-1]
    final_phase_key = f"phase{final_phase['index']}"

    # Build a geometry + metadata lookup covering the UNION of edges across
    # all phases, keyed by CANONICAL edge id (not per-phase name). Edge names
    # are per-phase local and can collide across phases for different pipes
    # — only the geometry hash is stable.
    edge_geom_lookup: Dict[CanonicalEdgeId, Dict] = {}
    display_name_by_cid: Dict[CanonicalEdgeId, str] = {}
    for p in phases:
        for _, row in p['edges_gdf'].iterrows():
            cid = _canonical_edge_id(row.geometry)
            edge_geom_lookup.setdefault(
                cid,
                {'geometry': row.geometry, 'type_mat': row.get('type_mat', '')},
            )
            display_name_by_cid.setdefault(cid, row['name'])

    length_lookup: Dict[CanonicalEdgeId, float] = {}
    for phase_result in phase_results:
        for cid, length in phase_result['edge_lengths'].items():
            length_lookup.setdefault(cid, length)

    # NOTE: ESRI shapefile column names are limited to 10 characters.
    # All attribute keys below must be ≤ 10 chars or they will be silently
    # truncated on write, causing downstream KeyErrors when reading back.
    edges_data = []
    for cid, decision in sizing_decisions.items():
        geom_info = edge_geom_lookup.get(cid)
        if geom_info is None:
            # No geometry means we can't draw the edge. Skip defensively.
            continue

        # Find the first phase the edge was installed/flowing
        ph_intro = None
        yr_intro = None
        for p in phases:
            pk = f"phase{p['index']}"
            action = decision.get(pk, {}).get('action', 'none')
            if action == 'install':
                ph_intro = p['index']
                yr_intro = p['year']
                break

        # Find the last phase the edge was active (install/replace/keep flowing)
        ph_last = None
        yr_last = None
        for p in phases:
            pk = f"phase{p['index']}"
            action = decision.get(pk, {}).get('action', 'none')
            if action in ('install', 'replace', 'keep'):
                ph_last = p['index']
                yr_last = p['year']

        num_repl = sum(
            1 for key in decision.keys()
            if isinstance(decision.get(key), dict) and decision[key].get('action') == 'replace'
        )

        total_cost = sum(
            decision[f"phase{p['index']}"].get('cost', 0)
            for p in phases
            if f"phase{p['index']}" in decision
        )

        final_decision = decision.get(final_phase_key, {})
        final_dn_optimised = final_decision.get('DN')
        idle_final = 1 if final_decision.get('action') == 'idle' else 0

        edges_data.append({
            'name': display_name_by_cid.get(cid, ''),
            'type_mat': geom_info['type_mat'],
            'length_m': length_lookup.get(cid, 0.0),
            'DN_final': final_dn_optimised,
            'ph_intro': ph_intro,
            'yr_intro': yr_intro,
            'ph_last': ph_last,
            'yr_last': yr_last,
            'idle_final': idle_final,
            'num_repl': num_repl,
            'cost_USD': total_cost,
            'strategy': decision.get('strategy', 'n/a'),
            'geometry': geom_info['geometry'],
        })

    edges_timeline_gdf = gpd.GeoDataFrame(edges_data, crs=final_phase['edges_gdf'].crs)
    edges_timeline_gdf.to_file(locator.get_thermal_network_phase_edges_shapefile(network_type, phasing_plan_name, 'timeline'))

    # Nodes: union across all phases so decommissioned consumers are drawn
    # with their phase_intro / phase_last attributes. Plant and junction
    # nodes typically persist to the final phase.
    node_first: Dict[str, int] = {}
    node_last: Dict[str, int] = {}
    node_row: Dict[str, pd.Series] = {}
    for p in phases:
        phase_idx = p['index']
        for _, node in p['nodes_gdf'].iterrows():
            node_id = node['name']
            if node_id not in node_first:
                node_first[node_id] = phase_idx
                node_row[node_id] = node
            node_last[node_id] = phase_idx

    year_by_phase: Dict[int, int] = {p['index']: p['year'] for p in phases}

    nodes_timeline_records = []
    for node_id, first_idx in node_first.items():
        last_idx = node_last[node_id]
        row = node_row[node_id]
        # Short attribute names to avoid ESRI shapefile 10-char truncation.
        nodes_timeline_records.append({
            **{col: row[col] for col in row.index if col != 'geometry'},
            'ph_intro': first_idx,
            'yr_intro': year_by_phase[first_idx],
            'ph_last': last_idx,
            'yr_last': year_by_phase[last_idx],
            'geometry': row.geometry,
        })

    nodes_timeline_gdf = gpd.GeoDataFrame(nodes_timeline_records, crs=final_phase['nodes_gdf'].crs)
    nodes_timeline_gdf.to_file(locator.get_thermal_network_phase_nodes_shapefile(network_type, phasing_plan_name, 'timeline'))


def save_phase_layout_shapefiles(locator, phases: List[Dict], phase_results: List[Dict],
                                  sizing_decisions: Dict, network_type: str, phasing_plan_name: str):
    """
    Save layout shapefiles for each individual phase with optimised DN values.

    Creates folder structure matching single-phase layout:
    phasing-plans/{plan-name}/{network-type}/
        ├── {network-name-1}/
        │   └── layout/
        │       ├── edges.shp (with optimised pipe_DN, action, cost)
        │       └── nodes.shp
        └── ...

    :param locator: InputLocator object
    :param phases: List of phase dictionaries
    :param phase_results: List of phase result dictionaries
    :param sizing_decisions: Optimisation decisions dictionary
    :param network_type: DH or DC
    :param phasing_plan_name: Name of phasing plan
    """
    # Build a union geometry lookup keyed by canonical edge id across all
    # phases, so idle pipes (installed earlier, not redrawn in a later phase
    # by Part 1) can still be written into that phase's output shapefile.
    # Crucially, keying by canonical id — not by per-phase local name —
    # avoids silently dropping sub2's geometry when sub2 reuses a name like
    # 'PIPE1' that happened to refer to a different physical pipe in sub1.
    edge_base_by_cid: Dict[CanonicalEdgeId, Dict] = {}
    for p in phases:
        for _, row in p['edges_gdf'].iterrows():
            cid = _canonical_edge_id(row.geometry)
            if cid in edge_base_by_cid:
                continue
            base = {col: row[col] for col in p['edges_gdf'].columns}
            edge_base_by_cid[cid] = base

    for phase, phase_result in zip(phases, phase_results):
        phase_num = phase['index']
        year = phase['year']
        network_name = phase['network_name']

        phase_folder_name = network_name
        phase_layout_folder = locator.get_thermal_network_phasing_plan_phase_layout_folder(
            network_type, phasing_plan_name, phase_folder_name
        )
        os.makedirs(phase_layout_folder, exist_ok=True)

        phase_key = f"phase{phase_num}"
        local_cid_to_name = phase['edge_cid_to_name']

        # Iterate over the canonical union. For each installed edge, prefer
        # the current phase's local name / geometry (so the output matches
        # what Part 1 drew for this phase); fall back to the first phase
        # that contained the edge for idle edges not in this phase's layout.
        edge_rows = []
        for cid, decision in sizing_decisions.items():
            phase_decision = decision.get(phase_key, {})
            action = phase_decision.get('action', 'none')
            if action == 'none':
                continue

            if cid in local_cid_to_name:
                local_name = local_cid_to_name[cid]
                local_row = phase['edges_gdf'][phase['edges_gdf']['name'] == local_name].iloc[0]
                row = {col: local_row[col] for col in phase['edges_gdf'].columns}
            else:
                base = edge_base_by_cid.get(cid)
                if base is None:
                    continue
                row = dict(base)

            row['pipe_DN'] = phase_decision.get('DN', phase_result['edge_diameters'].get(cid))
            row['action'] = action
            row['cost_USD'] = phase_decision.get('cost', 0)
            edge_rows.append(row)

        edges_gdf = gpd.GeoDataFrame(edge_rows, crs=phase['edges_gdf'].crs)
        edges_gdf.to_file(locator.get_thermal_network_phase_edges_shapefile(network_type, phasing_plan_name, phase_folder_name))

        # Save nodes.shp for this phase
        nodes_gdf = phase['nodes_gdf'].copy()

        # Add phase introduction metadata
        def get_node_phase_intro(node_name):
            """Find which phase this node was first introduced"""
            for p in phases:
                if node_name in p['nodes_gdf']['name'].values:
                    return p['index']
            return phase_num

        def get_node_year_intro(node_name):
            """Find which year this node was first introduced"""
            for p in phases:
                if node_name in p['nodes_gdf']['name'].values:
                    return p['year']
            return year

        def get_node_status(node_name):
            """Determine if node is new in this phase or existing"""
            for p in phases:
                if p['index'] >= phase_num:
                    continue
                if node_name in p['nodes_gdf']['name'].values:
                    return 'existing'
            return 'new'

        # Short attribute names to avoid ESRI shapefile 10-char truncation.
        nodes_gdf['ph_intro'] = nodes_gdf['name'].map(get_node_phase_intro)
        nodes_gdf['yr_intro'] = nodes_gdf['name'].map(get_node_year_intro)
        nodes_gdf['status'] = nodes_gdf['name'].map(get_node_status)

        nodes_gdf.to_file(locator.get_thermal_network_phase_nodes_shapefile(network_type, phasing_plan_name, phase_folder_name))

    print(f"    - {phases[0]['network_name']}/layout/...{phases[-1]['network_name']}/layout/ (edges.shp with optimised DN)")


def create_placeholder_substation_files(phase: Dict, phase_substation_folder: str,
                                        network_type: str, network_name: str):
    """
    Create placeholder substation CSV files when actual simulation results are not available.

    Creates one CSV per building with the standard substation output structure.

    :param phase: Phase dictionary with building info
    :param phase_substation_folder: Output folder for this phase's substation files
    :param network_type: DH or DC
    :param network_name: Name of network
    """
    import pandas as pd

    # Create a placeholder CSV for each building in the phase
    for building in phase['buildings']:
        filename = f"{network_type}_{network_name}_substation_{building}.csv"
        filepath = os.path.join(phase_substation_folder, filename)

        # Create empty DataFrame with standard substation columns
        # These are the typical columns from thermal network substation output
        placeholder_df = pd.DataFrame({
            'DATE': pd.date_range('2010-01-01', periods=8760, freq='H'),
            'mdot_DH_kgpers': 0.0,
            'T_sup_DH_C': 0.0,
            'T_ret_DH_C': 0.0,
            'Q_heating_W': 0.0,
            'Q_dhw_W': 0.0
        })

        placeholder_df.to_csv(filepath, index=False)

    # Create README to indicate placeholders
    readme_path = os.path.join(phase_substation_folder, 'README.txt')
    with open(readme_path, 'w') as f:
        f.write("Placeholder substation files - actual simulation results not available.\n")
        f.write("These files contain zero values and should be replaced with actual simulation outputs.\n")


def save_phase_substation_results(locator, phases: List[Dict], phase_results: List[Dict],
                                   network_type: str, phasing_plan_name: str):
    """
    Save substation results for each phase.

    Creates folder structure matching single-phase layout:
    phasing-plans/{plan-name}/{network-type}/
        ├── {network-name-1}/
        │   └── substation/
        │       ├── {network-type}_{network-name}_substation_{building}.csv
        │       └── ...
        ├── {network-name-2}/
        │   └── substation/
        └── ...

    :param locator: InputLocator object
    :param phases: List of phase dictionaries
    :param phase_results: List of phase result dictionaries
    :param network_type: DH or DC
    :param phasing_plan_name: Name of phasing plan
    """
    for phase, phase_result in zip(phases, phase_results):
        network_name = phase['network_name']

        # Create substation folder inside phase folder (matching single-phase structure)
        phase_folder_name = network_name
        phase_substation_folder = locator.get_thermal_network_phasing_plan_phase_substation_folder(
            network_type, phasing_plan_name, phase_folder_name
        )
        os.makedirs(phase_substation_folder, exist_ok=True)

        # Copy actual substation results from simulation output
        source_substation_folder = os.path.join(
            locator.get_output_thermal_network_type_folder(network_type, network_name),
            'substation'
        )

        if os.path.exists(source_substation_folder):
            # Copy all substation files
            import shutil
            import glob

            substation_files = glob.glob(f"{source_substation_folder}/{network_type}_{network_name}_substation_*.csv")

            if substation_files:
                for source_file in substation_files:
                    filename = os.path.basename(source_file)
                    dest_file = os.path.join(phase_substation_folder, filename)
                    shutil.copy2(source_file, dest_file)
            else:
                # No substation files found - create placeholders
                print(f"    Warning: No substation results for {network_name}")
                create_placeholder_substation_files(phase, phase_substation_folder, network_type, network_name)
        else:
            # Simulation output doesn't have substation folder - create placeholders
            print(f"    Warning: Substation folder not found for {network_name}")
            create_placeholder_substation_files(phase, phase_substation_folder, network_type, network_name)


def copy_phase_simulation_results(locator, phases: List[Dict], network_type: str, phasing_plan_name: str):
    """
    Copy all simulation result files from single-phase outputs to phase-specific folders.

    Creates folder structure matching single-phase outputs:
    phasing-plans/{plan-name}/{network-type}/{network-name}/*.csv

    :param locator: InputLocator object
    :param phases: List of phase dictionaries
    :param network_type: DH or DC
    :param phasing_plan_name: Name of phasing plan
    """
    import shutil
    import glob

    for phase in phases:
        network_name = phase['network_name']

        # Create phase results folder
        phase_folder_name = network_name
        phase_results_folder = locator.get_thermal_network_phasing_plan_phase_folder(
            network_type, phasing_plan_name, phase_folder_name
        )
        os.makedirs(phase_results_folder, exist_ok=True)

        # Source folder: where single-phase simulation wrote results
        source_folder = locator.get_output_thermal_network_type_folder(network_type, network_name)

        if not os.path.exists(source_folder):
            print(f"    Warning: Results not found for {network_name}, skipping copy")
            continue

        # Copy all CSV files (except substation files - those are handled separately)
        csv_files = glob.glob(f"{source_folder}/{network_type}_{network_name}_*.csv")

        for source_file in csv_files:
            filename = os.path.basename(source_file)
            # Skip substation files (handled by save_phase_substation_results)
            if 'substation' not in filename:
                dest_file = f"{phase_results_folder}/{filename}"
                shutil.copy2(source_file, dest_file)

        # Also copy EPANET files if they exist
        for ext in ['.inp', '.rpt', '.bin']:
            source_file = f"{source_folder}/temp{ext}"
            if os.path.exists(source_file):
                dest_file = f"{phase_results_folder}/{network_name}{ext}"
                shutil.copy2(source_file, dest_file)
