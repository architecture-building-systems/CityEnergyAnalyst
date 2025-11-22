"""
Test suite for orphan node merging in thermal network connectivity.

This module validates that isolated street fragments are automatically connected
to the main network component when they're within the merge threshold distance.

Key Issues Addressed:
- Isolated street fragments cause building disconnections
- Buildings connecting to orphan streets create disconnected components
- Automatic merging reconnects small isolated fragments (< 5 nodes)
- Building terminals are preserved and never merged
"""

import unittest
import networkx as nx
from geopandas import GeoDataFrame
from shapely.geometry import Point, LineString
from cea.technologies.network_layout.graph_utils import (
    gdf_to_nx, _merge_orphan_nodes_to_nearest, SHAPEFILE_TOLERANCE
)


class TestOrphanNodeMerging(unittest.TestCase):
    """Test orphan node merging in network connectivity."""

    def test_isolated_fragment_gets_merged(self):
        """
        Test that a small isolated street fragment is merged to main component.
        
        This simulates the B1014 case where a building connects to an isolated
        street fragment that's disconnected from the main network.
        """
        # Main network component (connected streets forming a square)
        main_streets = [
            LineString([(0, 0), (100, 0)]),       # Bottom
            LineString([(100, 0), (100, 100)]),   # Right
            LineString([(100, 100), (0, 100)]),   # Top
            LineString([(0, 100), (0, 0)])        # Left
        ]
        
        # Isolated fragment 40m away from node (100, 50) - wait, (100,50) is NOT a node
        # The main network nodes are: (0,0), (100,0), (100,100), (0,100)
        # Distance from (140, 0) to (100, 0) is exactly 40m
        isolated_fragment = LineString([(140, 0), (170, 0)])
        
        all_streets = main_streets + [isolated_fragment]
        
        network_gdf = GeoDataFrame(
            geometry=all_streets,
            crs='EPSG:2056'
        )
        
        # Convert without merging - should have 2 components
        graph_no_merge = gdf_to_nx(
            network_gdf,
            coord_precision=SHAPEFILE_TOLERANCE
        )
        
        num_components_before = nx.number_connected_components(graph_no_merge.to_undirected())
        self.assertEqual(num_components_before, 2,
            "Network should have 2 disconnected components before merging")
        
        # Convert then merge - should have 1 component
        graph_merged = gdf_to_nx(
            network_gdf,
            coord_precision=SHAPEFILE_TOLERANCE
        )
        graph_merged = _merge_orphan_nodes_to_nearest(
            graph_merged,
            terminal_nodes=set(),  # No terminals to protect
            merge_threshold=50.0
        )
        
        num_components_after = nx.number_connected_components(graph_merged.to_undirected())
        self.assertEqual(num_components_after, 1,
            "Network should have 1 connected component after merging")

    def test_terminal_nodes_not_merged(self):
        """
        Test that building terminal nodes are never merged, even if disconnected.
        
        This ensures we don't accidentally merge building connection points,
        which would create incorrect network topology.
        """
        # Main network
        main_street = LineString([(0, 0), (100, 0)])
        
        # Isolated fragment with a building terminal
        isolated_fragment = LineString([(200, 50), (250, 50)])
        building_terminal = Point(200, 50)  # Endpoint of isolated fragment
        
        network_gdf = GeoDataFrame(
            geometry=[main_street, isolated_fragment, building_terminal],
            crs='EPSG:2056'
        )
        
        # Normalize terminal coordinate (as done in actual code)
        terminal_coord = (round(building_terminal.x, SHAPEFILE_TOLERANCE),
                         round(building_terminal.y, SHAPEFILE_TOLERANCE))
        
        # Convert then merge with terminal protection
        graph = gdf_to_nx(
            network_gdf,
            coord_precision=SHAPEFILE_TOLERANCE
        )
        graph = _merge_orphan_nodes_to_nearest(
            graph,
            terminal_nodes={terminal_coord},
            merge_threshold=100.0  # High threshold to test terminal protection
        )
        
        # Terminal node should still exist
        self.assertIn(terminal_coord, graph.nodes(),
            "Terminal node should be preserved in graph")
        
        # Network should still be disconnected because terminal is protected
        num_components = nx.number_connected_components(graph.to_undirected())
        self.assertEqual(num_components, 2,
            "Network should remain disconnected when terminal protects orphan component")

    def test_large_orphan_component_not_merged(self):
        """
        Test that large disconnected components (>= 5 nodes) are NOT merged.
        
        Large disconnected components indicate real network gaps that should
        be reported as errors rather than silently merged.
        """
        # Main network (large - 10 nodes to ensure it's the main component)
        main_streets = [
            LineString([(0, 0), (10, 0)]),
            LineString([(10, 0), (20, 0)]),
            LineString([(20, 0), (30, 0)]),
            LineString([(30, 0), (40, 0)]),
            LineString([(40, 0), (50, 0)]),
            LineString([(50, 0), (60, 0)]),
            LineString([(60, 0), (70, 0)]),
            LineString([(70, 0), (80, 0)]),
            LineString([(80, 0), (90, 0)])
        ]
        
        # Large isolated network (7 segments = 8 nodes, > 5 node threshold)
        # Even though it's large, it should NOT be merged because len >= 5
        isolated_streets = [
            LineString([(200, 0), (210, 0)]),
            LineString([(210, 0), (220, 0)]),
            LineString([(220, 0), (230, 0)]),
            LineString([(230, 0), (240, 0)]),
            LineString([(240, 0), (250, 0)]),
            LineString([(250, 0), (260, 0)]),
            LineString([(260, 0), (270, 0)])  # 7 segments for 8 nodes total
        ]
        
        all_streets = main_streets + isolated_streets
        
        network_gdf = GeoDataFrame(
            geometry=all_streets,
            crs='EPSG:2056'
        )
        
        # Convert then merge
        graph = gdf_to_nx(
            network_gdf,
            coord_precision=SHAPEFILE_TOLERANCE
        )
        graph = _merge_orphan_nodes_to_nearest(
            graph,
            terminal_nodes=set(),
            merge_threshold=100.0  # High threshold
        )
        
        # Should still have 2 components (large orphan not merged)
        num_components = nx.number_connected_components(graph.to_undirected())
        self.assertEqual(num_components, 2,
            "Large disconnected component should NOT be merged")

    def test_merge_threshold_enforced(self):
        """
        Test that orphan nodes beyond merge_threshold distance are not merged.
        
        This ensures we don't create unrealistically long bridging edges.
        """
        # Main network
        main_street = LineString([(0, 0), (100, 0)])
        
        # Isolated fragment 60m away (beyond default 50m threshold)
        isolated_fragment = LineString([(0, 60), (50, 60)])
        
        network_gdf = GeoDataFrame(
            geometry=[main_street, isolated_fragment],
            crs='EPSG:2056'
        )
        
        # Convert then merge with 50m threshold
        graph = gdf_to_nx(
            network_gdf,
            coord_precision=SHAPEFILE_TOLERANCE
        )
        graph = _merge_orphan_nodes_to_nearest(
            graph,
            terminal_nodes=set(),
            merge_threshold=50.0
        )
        
        # Should still be disconnected (beyond threshold)
        num_components = nx.number_connected_components(graph.to_undirected())
        self.assertEqual(num_components, 2,
            "Orphan beyond merge_threshold should not be merged")
        
        # Now try with higher threshold
        graph_merged = gdf_to_nx(
            network_gdf,
            coord_precision=SHAPEFILE_TOLERANCE
        )
        graph_merged = _merge_orphan_nodes_to_nearest(
            graph_merged,
            terminal_nodes=set(),
            merge_threshold=70.0
        )
        
        # Should now be connected
        num_components_merged = nx.number_connected_components(graph_merged.to_undirected())
        self.assertEqual(num_components_merged, 1,
            "Orphan within higher threshold should be merged")

    def test_building_on_isolated_fragment_gets_connected(self):
        """
        Test the complete scenario: building → isolated fragment → merged to main.
        
        This replicates the B1014 case where a building connects to an isolated
        street fragment that needs to be merged to the main network.
        
        NOTE: This is a simplified test. The real scenario (B1014) works correctly
        because create_terminals() splits streets at connection points, creating
        additional nodes that can serve as bridge points.
        """
        # Main network (square)
        main_streets = [
            LineString([(0, 0), (100, 0)]),
            LineString([(100, 0), (100, 100)]),
            LineString([(0, 100), (100, 100)]),
            LineString([(0, 100), (0, 0)])
        ]
        
        # Isolated fragment 40m from node (100, 0) - close enough to merge
        isolated_street = LineString([(135, 0), (165, 0)])
        
        network_gdf = GeoDataFrame(
            geometry=main_streets + [isolated_street],
            crs='EPSG:2056'
        )
        
        # Convert then merge (no terminals in this simple test)
        graph = gdf_to_nx(
            network_gdf,
            coord_precision=SHAPEFILE_TOLERANCE
        )
        graph = _merge_orphan_nodes_to_nearest(
            graph,
            terminal_nodes=set(),
            merge_threshold=50.0
        )
        
        # Should be fully connected - isolated fragment should merge to main
        num_components = nx.number_connected_components(graph.to_undirected())
        self.assertEqual(num_components, 1,
            "Isolated street fragment should be merged to main network")


if __name__ == '__main__':
    unittest.main()
