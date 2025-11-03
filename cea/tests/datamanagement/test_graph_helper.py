"""
Unit tests for the GraphCorrector class.

Tests all graph correction functionality including validation, correction methods,
and edge cases. Uses unittest framework to create various graph scenarios for testing.
"""

import unittest
import networkx as nx
from unittest.mock import patch

from cea.datamanagement.graph_helper import GraphCorrector
from cea.constants import SHAPEFILE_TOLERANCE

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Mathias Niffeler"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"


class TestGraphCorrector(unittest.TestCase):
    """Test suite for GraphCorrector class."""

    # ==================================================================================
    # SETUP HELPERS
    # ==================================================================================

    def create_empty_graph(self):
        """Create an empty graph."""
        return nx.Graph()

    def create_simple_connected_graph(self):
        """Create a simple connected graph with 4 nodes."""
        g = nx.Graph()
        g.add_edges_from([
            ((0, 0), (1, 0), {'weight': 1.0}),
            ((1, 0), (1, 1), {'weight': 1.0}),
            ((1, 1), (0, 1), {'weight': 1.0}),
            ((0, 1), (0, 0), {'weight': 1.0})
        ])
        return g

    def create_graph_with_self_loops(self):
        """Create a graph containing self-loops."""
        g = nx.Graph()
        g.add_edges_from([
            ((0, 0), (1, 0), {'weight': 1.0}),
            ((1, 0), (1, 0), {'weight': 0.0}),  # Self-loop
            ((1, 0), (1, 1), {'weight': 1.0}),
            ((1, 1), (1, 1), {'weight': 0.0})   # Another self-loop
        ])
        return g

    def create_disconnected_graph(self):
        """Create a graph with two disconnected components."""
        g = nx.Graph()
        # Component 1
        g.add_edges_from([
            ((0, 0), (1, 0), {'weight': 1.0}),
            ((1, 0), (1, 1), {'weight': 1.0})
        ])
        # Component 2 (disconnected)
        g.add_edges_from([
            ((5, 5), (6, 5), {'weight': 1.0}),
            ((6, 5), (6, 6), {'weight': 1.0})
        ])
        return g

    def create_graph_with_close_nodes(self):
        """Create a graph with nodes that are very close to each other."""
        g = nx.Graph()
        g.add_edges_from([
            ((0, 0), (1, 0), {'weight': 1.0}),
            ((1, 0), (1.001, 0.001), {'weight': 0.001}),  # Very close nodes
            ((1.001, 0.001), (1, 1), {'weight': 1.0})
        ])
        return g

    def create_graph_with_intersecting_edges(self):
        """Create a graph with edges that should intersect but don't share nodes."""
        g = nx.Graph()
        # First line: horizontal from (0,1) to (2,1)
        g.add_edge((0, 1), (2, 1), weight=2.0)
        # Second line: vertical from (1,0) to (1,2) - should intersect at (1,1)
        g.add_edge((1, 0), (1, 2), weight=2.0)
        return g


    # ==================================================================================
    # INITIALIZATION TESTS
    # ==================================================================================

    def test_init_with_graph(self):
        """Test GraphCorrector initialization with a valid graph."""
        simple_connected_graph = self.create_simple_connected_graph()
        corrector = GraphCorrector(simple_connected_graph)

        self.assertIsNot(corrector.graph, simple_connected_graph)  # Should be a copy
        self.assertIs(corrector.original_graph, simple_connected_graph)
        self.assertEqual(corrector.coord_precision, SHAPEFILE_TOLERANCE)
        self.assertEqual(corrector.corrections_log, [])
        self.assertEqual(corrector.graph.number_of_nodes(), simple_connected_graph.number_of_nodes())
        self.assertEqual(corrector.graph.number_of_edges(), simple_connected_graph.number_of_edges())

    def test_init_with_custom_coord_precision(self):
        """Test GraphCorrector initialization with custom coordinate precision."""
        simple_connected_graph = self.create_simple_connected_graph()
        custom_coord_precision = 4
        corrector = GraphCorrector(simple_connected_graph, coord_precision=custom_coord_precision)

        self.assertEqual(corrector.coord_precision, custom_coord_precision)

    # ==================================================================================
    # VALIDATION TESTS
    # ==================================================================================

    def test_validate_connectivity_empty_graph(self):
        """Test validation of empty graph."""
        empty_graph = self.create_empty_graph()
        corrector = GraphCorrector(empty_graph)
        is_valid, message = corrector.validate_connectivity()

        self.assertFalse(is_valid)
        self.assertEqual(message, "Graph is empty (no nodes)")

    def test_validate_connectivity_connected_graph(self):
        """Test validation of connected graph."""
        simple_connected_graph = self.create_simple_connected_graph()
        corrector = GraphCorrector(simple_connected_graph)
        is_valid, message = corrector.validate_connectivity()

        self.assertTrue(is_valid)
        self.assertEqual(message, "Graph is valid and connected")

    def test_validate_connectivity_disconnected_graph(self):
        """Test validation of disconnected graph."""
        disconnected_graph = self.create_disconnected_graph()
        corrector = GraphCorrector(disconnected_graph)
        is_valid, message = corrector.validate_connectivity()

        self.assertFalse(is_valid)
        self.assertEqual(message, "Graph is not connected: 2 disconnected components found")

    def test_validate_connectivity_graph_with_self_loops(self):
        """Test validation of graph with self-loops."""
        graph_with_self_loops = self.create_graph_with_self_loops()
        corrector = GraphCorrector(graph_with_self_loops)
        is_valid, message = corrector.validate_connectivity()

        self.assertFalse(is_valid)
        self.assertEqual(message, "Graph contains 2 self-loops")

    def test_identify_disconnected_components(self):
        """Test identification of disconnected components."""
        disconnected_graph = self.create_disconnected_graph()
        corrector = GraphCorrector(disconnected_graph)
        components = corrector.identify_disconnected_components()

        self.assertEqual(len(components), 2)
        # Components should be sorted by size (largest first)
        self.assertGreaterEqual(len(components[0]), len(components[1]))

        # Check that all nodes are accounted for
        all_component_nodes = set()
        for component in components:
            all_component_nodes.update(component)
        self.assertEqual(all_component_nodes, set(disconnected_graph.nodes()))

    # ==================================================================================
    # SELF-LOOP REMOVAL TESTS
    # ==================================================================================

    def test_remove_self_loops_with_self_loops(self):
        """Test removal of self-loops from graph."""
        graph_with_self_loops = self.create_graph_with_self_loops()
        corrector = GraphCorrector(graph_with_self_loops)

        # Verify self-loops exist before removal
        self.assertGreater(nx.number_of_selfloops(corrector.graph), 0)

        result_graph = corrector.remove_self_loops()

        # Verify self-loops are removed
        self.assertEqual(nx.number_of_selfloops(result_graph), 0)
        self.assertIs(result_graph, corrector.graph)  # Should return the same graph object

        # Check corrections log
        self.assertEqual(len(corrector.corrections_log), 1)
        self.assertEqual(corrector.corrections_log[0]['type'], 'remove_self_loops')
        self.assertGreater(corrector.corrections_log[0]['details']['self_loops_removed'], 0)

    def test_remove_self_loops_no_self_loops(self):
        """Test removal of self-loops from graph without self-loops."""
        simple_connected_graph = self.create_simple_connected_graph()
        corrector = GraphCorrector(simple_connected_graph)

        with patch('builtins.print') as mock_print:
            result_graph = corrector.remove_self_loops()

        # Should print message about no self-loops
        mock_print.assert_called_with("No self-loops found")
        self.assertIs(result_graph, corrector.graph)

    # ==================================================================================
    # CLOSE NODES MERGING TESTS
    # ==================================================================================

    def test_merge_close_nodes_with_close_nodes(self):
        """Test merging of nodes that are close to each other."""
        graph_with_close_nodes = self.create_graph_with_close_nodes()
        corrector = GraphCorrector(graph_with_close_nodes)
        initial_node_count = corrector.graph.number_of_nodes()

        result_graph = corrector.merge_close_nodes()

        # Should have fewer nodes after merging
        self.assertLess(result_graph.number_of_nodes(), initial_node_count)
        self.assertIs(result_graph, corrector.graph)

        # Check corrections log
        self.assertEqual(len(corrector.corrections_log), 1)
        self.assertEqual(corrector.corrections_log[0]['type'], 'merge_close_nodes')
        self.assertGreater(corrector.corrections_log[0]['details']['nodes_merged'], 0)

    def test_merge_close_nodes_custom_threshold(self):
        """Test merging with custom distance threshold."""
        graph_with_close_nodes = self.create_graph_with_close_nodes()
        corrector = GraphCorrector(graph_with_close_nodes)

        # Use very small threshold - should not merge any nodes
        result_graph = corrector.merge_close_nodes(distance_threshold=0.0001)
        self.assertEqual(result_graph.number_of_nodes(), graph_with_close_nodes.number_of_nodes())

    # ==================================================================================
    # INTERSECTING EDGES TESTS
    # ==================================================================================

    def test_connect_intersecting_edges_already_connected(self):
        """Test intersection detection on already connected graph."""
        simple_connected_graph = self.create_simple_connected_graph()
        corrector = GraphCorrector(simple_connected_graph)

        with patch('builtins.print') as mock_print:
            result_graph = corrector.connect_intersecting_edges()

        # Should skip intersection check for connected graph
        mock_print.assert_called_with("Graph already connected, skipping intersection check")
        self.assertIs(result_graph, corrector.graph)

    def test_calculate_edge_intersection(self):
        """Test edge intersection calculation."""
        corrector = GraphCorrector(nx.Graph())

        # Test intersecting lines
        edge1 = ((0, 0), (2, 2))  # Diagonal line
        edge2 = ((0, 2), (2, 0))  # Reverse diagonal line
        intersection = corrector._calculate_edge_intersection(edge1, edge2)

        self.assertIsNotNone(intersection)
        self.assertLess(abs(intersection[0] - 1.0), 1e-10)
        self.assertLess(abs(intersection[1] - 1.0), 1e-10)

    def test_calculate_edge_intersection_parallel(self):
        """Test edge intersection calculation for parallel lines."""
        corrector = GraphCorrector(nx.Graph())

        # Test parallel lines
        edge1 = ((0, 0), (1, 0))  # Horizontal line
        edge2 = ((0, 1), (1, 1))  # Parallel horizontal line
        intersection = corrector._calculate_edge_intersection(edge1, edge2)

        self.assertIsNone(intersection)

    def test_point_on_segment(self):
        """Test point-on-segment detection."""
        corrector = GraphCorrector(nx.Graph())

        segment = ((0, 0), (2, 0))  # Horizontal line segment

        # Point on segment
        self.assertTrue(corrector._point_on_segment((1, 0), segment))

        # Point on line but outside segment
        self.assertFalse(corrector._point_on_segment((3, 0), segment))

        # Point not on line
        self.assertFalse(corrector._point_on_segment((1, 1), segment))

    def test_connect_intersecting_edges_with_intersections(self):
        """Test connection of disconnected components through intersecting edges."""
        # Create two disconnected components with edges that intersect geometrically
        g = nx.Graph()

        # Component 1: horizontal line from (0,1) to (2,1)
        g.add_edge((0, 1), (2, 1), weight=2.0)

        # Component 2: vertical line from (1,0) to (1,2) - should intersect at (1,1)
        g.add_edge((1, 0), (1, 2), weight=2.0)

        corrector = GraphCorrector(g)

        # Verify graph is initially disconnected
        self.assertFalse(nx.is_connected(corrector.graph))
        self.assertEqual(nx.number_connected_components(corrector.graph), 2)

        result_graph = corrector.connect_intersecting_edges()

        # Should be connected after finding intersection
        self.assertTrue(nx.is_connected(result_graph))
        self.assertIs(result_graph, corrector.graph)

        # Should have added a junction node at the intersection
        initial_nodes = {(0, 1), (2, 1), (1, 0), (1, 2)}
        final_nodes = set(result_graph.nodes())

        # Should have more nodes (junction added)
        self.assertGreater(len(final_nodes), len(initial_nodes))

        # Check corrections log
        self.assertEqual(len(corrector.corrections_log), 1)
        self.assertEqual(corrector.corrections_log[0]['type'], 'connect_intersecting_edges')
        self.assertGreater(corrector.corrections_log[0]['details']['intersections_found'], 0)

    def test_connect_intersecting_edges_multiple_intersections_same_edge(self):
        """Test edge that intersects with multiple other edges from different components."""
        # Create a scenario where one edge intersects with two separate edges from different components
        g = nx.Graph()

        # Component 1: Long horizontal line from (0,2) to (6,2)
        g.add_edge((0, 2), (6, 2), weight=6.0)

        # Component 2: Vertical line from (2,0) to (2,4) - intersects at (2,2)
        g.add_edge((2, 0), (2, 4), weight=4.0)

        # Component 3: Vertical line from (4,0) to (4,4) - also intersects horizontal at (4,2)
        g.add_edge((4, 0), (4, 4), weight=4.0)

        corrector = GraphCorrector(g)

        # Verify graph is initially disconnected with 3 components
        self.assertFalse(nx.is_connected(corrector.graph))
        self.assertEqual(nx.number_connected_components(corrector.graph), 3)

        result_graph = corrector.connect_intersecting_edges()

        # Should be connected after finding all intersections
        self.assertTrue(nx.is_connected(result_graph))

        # The horizontal edge should have been split twice:
        # Original: (0,2)---(6,2)
        # After split 1: (0,2)---(2,2)---(6,2)
        # After split 2: (0,2)---(2,2)---(4,2)---(6,2)
        # So we should have at least 2 junction nodes added

        initial_nodes = {(0, 2), (6, 2), (2, 0), (2, 4), (4, 0), (4, 4)}
        final_nodes = set(result_graph.nodes())

        # Should have at least 2 more nodes (junctions at intersections)
        self.assertGreaterEqual(len(final_nodes), len(initial_nodes) + 2)

        # Check corrections log
        self.assertEqual(len(corrector.corrections_log), 1)
        self.assertEqual(corrector.corrections_log[0]['type'], 'connect_intersecting_edges')
        # Should have found 2 intersections
        self.assertGreaterEqual(corrector.corrections_log[0]['details']['intersections_found'], 2)

    # ==================================================================================
    # COMPONENT CONNECTION TESTS
    # ==================================================================================

    def test_connect_disconnected_components(self):
        """Test connection of disconnected components."""
        disconnected_graph = self.create_disconnected_graph()
        corrector = GraphCorrector(disconnected_graph)

        # Verify graph is initially disconnected
        self.assertFalse(nx.is_connected(corrector.graph))
        initial_components = nx.number_connected_components(corrector.graph)

        result_graph = corrector.connect_disconnected_components()

        # Should be connected after correction
        self.assertTrue(nx.is_connected(result_graph))
        self.assertIs(result_graph, corrector.graph)

        # Check corrections log
        self.assertEqual(len(corrector.corrections_log), 1)
        self.assertEqual(corrector.corrections_log[0]['type'], 'connect_components')
        self.assertEqual(corrector.corrections_log[0]['details']['original_components'], initial_components)
        self.assertEqual(corrector.corrections_log[0]['details']['final_components'], 1)

    def test_connect_disconnected_components_already_connected(self):
        """Test component connection on already connected graph."""
        simple_connected_graph = self.create_simple_connected_graph()
        corrector = GraphCorrector(simple_connected_graph)

        result_graph = corrector.connect_disconnected_components()

        # Should not change the graph
        self.assertIs(result_graph, corrector.graph)
        self.assertTrue(nx.is_connected(result_graph))

        # Check corrections log
        self.assertEqual(len(corrector.corrections_log), 1)
        self.assertEqual(corrector.corrections_log[0]['details']['message'], 'Graph already connected, no action needed')

    # ==================================================================================
    # FULL PIPELINE TESTS
    # ==================================================================================

    def test_apply_corrections_full_pipeline(self):
        """Test the complete correction pipeline."""
        # Create a complex problematic graph
        g = nx.Graph()

        # Add disconnected components with various issues
        g.add_edges_from([
            # Component 1 with self-loop
            ((0, 0), (1, 0), {'weight': 1.0}),
            ((1, 0), (1, 0), {'weight': 0.0}),  # Self-loop

            # Component 2 (disconnected)
            ((5, 5), (6, 5), {'weight': 1.0}),
            ((6, 5), (6.001, 5.001), {'weight': 0.001}),  # Close nodes
        ])

        corrector = GraphCorrector(g)

        with patch('builtins.print'):  # Suppress output for test
            result_graph = corrector.apply_corrections()

        # Should be connected and clean after corrections
        self.assertTrue(nx.is_connected(result_graph))
        self.assertEqual(nx.number_of_selfloops(result_graph), 0)
        self.assertIs(result_graph, corrector.graph)

        # Should have logged multiple corrections
        self.assertGreater(len(corrector.corrections_log), 0)

    def test_get_corrections_log(self):
        """Test retrieval of corrections log."""
        graph_with_self_loops = self.create_graph_with_self_loops()
        corrector = GraphCorrector(graph_with_self_loops)

        # Initially empty
        log = corrector.get_corrections_log()
        self.assertEqual(log, [])
        self.assertIs(log, corrector.corrections_log)

        # After applying corrections
        corrector.remove_self_loops()
        log = corrector.get_corrections_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]['type'], 'remove_self_loops')

    # ==================================================================================
    # STATIC METHOD TESTS
    # ==================================================================================

    def test_validate_steiner_tree_ready_valid_graph(self):
        """Test Steiner tree validation for valid graph and terminals."""
        simple_connected_graph = self.create_simple_connected_graph()
        terminal_nodes = list(simple_connected_graph.nodes())[:2]

        is_ready, message = GraphCorrector.validate_steiner_tree_ready(
            simple_connected_graph, terminal_nodes
        )

        self.assertTrue(is_ready)
        self.assertEqual(message, "Graph is ready for Steiner tree with 2 terminals")

    def test_validate_steiner_tree_ready_empty_graph(self):
        """Test Steiner tree validation for empty graph."""
        empty_graph = self.create_empty_graph()
        is_ready, message = GraphCorrector.validate_steiner_tree_ready(empty_graph, [])

        self.assertFalse(is_ready)
        self.assertIn("empty", message.lower())

    def test_validate_steiner_tree_ready_disconnected_graph(self):
        """Test Steiner tree validation for disconnected graph."""
        disconnected_graph = self.create_disconnected_graph()
        terminal_nodes = list(disconnected_graph.nodes())[:2]

        is_ready, message = GraphCorrector.validate_steiner_tree_ready(
            disconnected_graph, terminal_nodes
        )

        self.assertFalse(is_ready)
        self.assertIn("not connected", message.lower())

    def test_validate_steiner_tree_ready_insufficient_terminals(self):
        """Test Steiner tree validation with insufficient terminal nodes."""
        simple_connected_graph = self.create_simple_connected_graph()
        # Test with only one terminal
        is_ready, message = GraphCorrector.validate_steiner_tree_ready(
            simple_connected_graph, [list(simple_connected_graph.nodes())[0]]
        )

        self.assertFalse(is_ready)
        self.assertIn("at least 2 terminal nodes", message.lower())

    def test_validate_steiner_tree_ready_missing_terminals(self):
        """Test Steiner tree validation with terminals not in graph."""
        simple_connected_graph = self.create_simple_connected_graph()
        missing_terminals = [(999, 999), (888, 888)]

        is_ready, message = GraphCorrector.validate_steiner_tree_ready(
            simple_connected_graph, missing_terminals
        )

        self.assertFalse(is_ready)
        self.assertIn("not found in graph", message.lower())

    # ==================================================================================
    # EDGE CASE TESTS
    # ==================================================================================

    def test_corrections_log_structure(self):
        """Test that corrections log has proper structure."""
        graph_with_self_loops = self.create_graph_with_self_loops()
        corrector = GraphCorrector(graph_with_self_loops)
        corrector.remove_self_loops()

        log_entry = corrector.corrections_log[0]
        self.assertIn('type', log_entry)
        self.assertIn('details', log_entry)
        self.assertIsInstance(log_entry['details'], dict)
        self.assertEqual(log_entry['type'], 'remove_self_loops')

    def test_graph_modification_isolation(self):
        """Test that graph modifications don't affect original graph."""
        simple_connected_graph = self.create_simple_connected_graph()
        original_edges = set(simple_connected_graph.edges())

        corrector = GraphCorrector(simple_connected_graph)

        # Add an edge to the corrector's graph
        new_node = (999, 999)
        corrector.graph.add_node(new_node)
        corrector.graph.add_edge(list(corrector.graph.nodes())[0], new_node)

        # Original graph should be unchanged
        self.assertEqual(set(simple_connected_graph.edges()), original_edges)
        self.assertNotIn(new_node, simple_connected_graph.nodes())


if __name__ == '__main__':
    unittest.main()