import networkx as nx
from geopandas import GeoDataFrame as gdf
from cea.constants import SHAPEFILE_TOLERANCE

def check_network_connectivity(network_gdf: gdf, plot: bool = False, output_path: str | None = None) -> dict:
    """
    Check network connectivity and optionally visualize disconnected components.

    This function analyzes the network topology to identify:
    - Disconnected components (groups of connected lines isolated from main network)
    - Isolated linestrings (single edges with no connections)
    - Distances from isolated linestrings to closest main network component

    :param network_gdf: GeoDataFrame with street LineStrings
    :type network_gdf: gdf
    :param plot: If True, create a visualization of disconnected components
    :type plot: bool
    :param output_path: Optional path to save the plot (e.g., "network_components.png")
    :type output_path: str | None
    :return: Dictionary with connectivity statistics including:
        - is_connected: bool
        - num_components: int
        - num_isolated_linestrings: int
        - isolated_linestrings: list of dicts with index, geometry, length
        - isolated_distances: list of dicts with isolated edge index, closest component, and distance
    :rtype: dict

    Example:
        >>> stats = check_network_connectivity(streets_gdf, plot=True)
        >>> print(f"Found {stats['num_components']} components")
        >>> print(f"Found {stats['num_isolated_linestrings']} isolated linestrings")
    """
    from cea.technologies.network_layout.graph_utils import gdf_to_nx

    # Convert to NetworkX graph
    G = gdf_to_nx(network_gdf, coord_precision=SHAPEFILE_TOLERANCE)

    # Find connected components
    components = list(nx.connected_components(G))
    num_components = len(components)
    is_connected = num_components == 1

    # Calculate component statistics
    component_sizes = [len(comp) for comp in components]
    largest_component_size = max(component_sizes) if component_sizes else 0
    largest_component_pct = (largest_component_size / G.number_of_nodes() * 100) if G.number_of_nodes() > 0 else 0

    # Identify isolated linestrings (components with only 2 nodes = single edge)
    isolated_components = [comp for comp in components if len(comp) == 2]
    num_isolated = len(isolated_components)

    # Get the actual LineString geometries for isolated components
    isolated_lines = []
    if num_isolated > 0:
        # Build node-to-edge mapping
        node_to_edges = {}
        for idx, row in network_gdf.iterrows():
            line = row.geometry
            coords = list(line.coords)
            start = (round(coords[0][0], SHAPEFILE_TOLERANCE), round(coords[0][1], SHAPEFILE_TOLERANCE))
            end = (round(coords[-1][0], SHAPEFILE_TOLERANCE), round(coords[-1][1], SHAPEFILE_TOLERANCE))

            for node in [start, end]:
                if node not in node_to_edges:
                    node_to_edges[node] = []
                node_to_edges[node].append((idx, line))

        # Find isolated linestrings
        for comp in isolated_components:
            comp_nodes = list(comp)
            # Get any edge that has both nodes
            for node in comp_nodes:
                if node in node_to_edges:
                    for idx, line in node_to_edges[node]:
                        line_coords = list(line.coords)
                        line_start = (round(line_coords[0][0], SHAPEFILE_TOLERANCE),
                                     round(line_coords[0][1], SHAPEFILE_TOLERANCE))
                        line_end = (round(line_coords[-1][0], SHAPEFILE_TOLERANCE),
                                   round(line_coords[-1][1], SHAPEFILE_TOLERANCE))
                        if set([line_start, line_end]) == set(comp_nodes):
                            isolated_lines.append({'index': idx, 'geometry': line, 'length': line.length})
                            break
                    break

    # Calculate distances from isolated linestrings to closest main network geometry
    isolated_distances = []
    if num_isolated > 0 and num_components > 1:
        from shapely.geometry import MultiLineString

        # Build geometries for each component (excluding isolated ones)
        component_geometries = []
        for comp_id, comp in enumerate(components):
            if len(comp) > 2:  # Skip isolated components (only 2 nodes)
                # Collect all linestrings that belong to this component
                comp_lines = []
                for idx, row in network_gdf.iterrows():
                    line = row.geometry
                    coords = list(line.coords)
                    start = (round(coords[0][0], SHAPEFILE_TOLERANCE),
                            round(coords[0][1], SHAPEFILE_TOLERANCE))
                    if start in comp:
                        comp_lines.append(line)

                if comp_lines:
                    # Combine into MultiLineString for efficient distance calculation
                    comp_geom = MultiLineString(comp_lines) if len(comp_lines) > 1 else comp_lines[0]
                    component_geometries.append({
                        'component_id': comp_id,
                        'geometry': comp_geom,
                        'size': len(comp)
                    })

        # Calculate distance from each isolated linestring to closest component
        for isolated_info in isolated_lines:
            isolated_geom = isolated_info['geometry']
            min_distance = float('inf')
            closest_component = None
            closest_edge_geom = None

            for comp_info in component_geometries:
                comp_geom = comp_info['geometry']
                distance = isolated_geom.distance(comp_geom)
                if distance < min_distance:
                    min_distance = distance
                    closest_component = comp_info

                    # Find the specific edge in the component that is closest
                    if comp_geom.geom_type == 'MultiLineString':
                        for line in comp_geom.geoms:
                            if isolated_geom.distance(line) == min_distance:
                                closest_edge_geom = line
                                break
                    else:
                        closest_edge_geom = comp_geom

            if closest_component:
                isolated_distances.append({
                    'isolated_index': isolated_info['index'],
                    'isolated_geometry': isolated_geom,
                    'isolated_length': isolated_info['length'],
                    'closest_component': closest_component['component_id'],
                    'component_size': closest_component['size'],
                    'closest_edge_geometry': closest_edge_geom,
                    'distance': min_distance
                })

        # Sort by distance (closest first)
        isolated_distances.sort(key=lambda x: x['distance'])

    stats = {
        'is_connected': is_connected,
        'num_components': num_components,
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges(),
        'largest_component_size': largest_component_size,
        'largest_component_pct': largest_component_pct,
        'component_sizes': component_sizes,
        'num_isolated_linestrings': num_isolated,
        'isolated_linestrings': isolated_lines,
        'isolated_distances': isolated_distances
    }

    # Print summary
    print(f"\n{'='*60}")
    print("Network Connectivity Analysis")
    print(f"{'='*60}")
    print(f"Connected: {is_connected}")
    print(f"Number of components: {num_components}")
    print(f"Total nodes: {G.number_of_nodes()}")
    print(f"Total edges: {G.number_of_edges()}")

    if num_isolated > 0:
        total_isolated_length = sum(line['length'] for line in isolated_lines)
        print(f"\n⚠️  Isolated LineStrings: {num_isolated}")
        print(f"   Total length: {total_isolated_length:.2f} meters")

        # Show distances from isolated linestrings to closest main network
        if isolated_distances:
            print("\n   Distances to closest main network component:")
            for i, dist_info in enumerate(isolated_distances[:10], 1):  # Show top 10
                idx = dist_info['isolated_index']
                length = dist_info['isolated_length']
                comp_id = dist_info['closest_component']
                comp_size = dist_info['component_size']
                distance = dist_info['distance']
                isolated_geom = dist_info['isolated_geometry']
                closest_edge = dist_info['closest_edge_geometry']

                # Get coordinates
                isolated_coords = list(isolated_geom.coords)
                closest_coords = list(closest_edge.coords) if closest_edge else []

                print(f"\n     {i}. Index {idx} ({length:.2f}m) → Component {comp_id} ({comp_size} nodes): {distance:.6f}m away")
                print(f"        Isolated edge coords: {isolated_coords[0]} to {isolated_coords[-1]}")
                if closest_coords:
                    print(f"        Closest edge coords: {closest_coords[0]} to {closest_coords[-1]}")
            if len(isolated_distances) > 10:
                print(f"\n     ... and {len(isolated_distances) - 10} more")

    if not is_connected:
        print(f"\nLargest component: {largest_component_size} nodes ({largest_component_pct:.1f}%)")
        print(f"Component sizes: {sorted(component_sizes, reverse=True)[:10]}")  # Show top 10

    # Optionally plot
    if plot:
        try:
            import matplotlib.pyplot as plt
            import matplotlib.colors as mcolors

            # Create figure
            fig, ax = plt.subplots(figsize=(15, 15))

            # Assign each component a unique color
            colors = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.CSS4_COLORS.values())

            # Map nodes to component IDs
            node_to_component = {}
            for comp_id, component in enumerate(components):
                for node in component:
                    node_to_component[node] = comp_id

            # Plot each edge colored by its component
            for idx, row in network_gdf.iterrows():
                line = row.geometry
                coords = list(line.coords)
                start = (round(coords[0][0], SHAPEFILE_TOLERANCE), round(coords[0][1], SHAPEFILE_TOLERANCE))

                # Find which component this edge belongs to
                comp_id = node_to_component.get(start, 0)
                color = colors[comp_id % len(colors)]

                # Plot line
                xs, ys = line.xy
                ax.plot(xs, ys, color=color, linewidth=2, alpha=0.7)

            ax.set_aspect('equal')
            ax.set_title(f'Network Components (Found {num_components} components)', fontsize=14, fontweight='bold')
            ax.set_xlabel('X coordinate')
            ax.set_ylabel('Y coordinate')
            ax.grid(True, alpha=0.3)

            # Add legend for top components
            if num_components > 1:
                legend_items = []
                for i, size in enumerate(sorted(component_sizes, reverse=True)[:5]):
                    legend_items.append(plt.Line2D([0], [0], color=colors[i % len(colors)],
                                                   linewidth=2, label=f'Component {i+1} ({size} nodes)'))
                ax.legend(handles=legend_items, loc='upper right')

            plt.tight_layout()

            if output_path:
                plt.savefig(output_path, dpi=150, bbox_inches='tight')
                print(f"\nPlot saved to: {output_path}")
            else:
                plt.savefig('network_components.png', dpi=150, bbox_inches='tight')
                print("\nPlot saved to: network_components.png")

            plt.close()

        except ImportError as e:
            print(f"\nWarning: Could not create plot. Missing dependency: {e}")

    print(f"{'='*60}\n")

    return stats
