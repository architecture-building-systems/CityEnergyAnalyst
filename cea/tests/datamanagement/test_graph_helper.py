"""
Unit tests for the GraphCorrector class.

Tests all graph correction functionality including validation, correction methods,
and edge cases. Uses pytest fixtures to create various graph scenarios for testing.
"""

import pytest
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


class TestGraphCorrector:
    """Test suite for GraphCorrector class."""

    # ==================================================================================
    # FIXTURES
    # ==================================================================================

    @pytest.fixture
    def empty_graph(self):
        """Create an empty graph."""
        return nx.Graph()

    @pytest.fixture
    def simple_connected_graph(self):
        """Create a simple connected graph with 4 nodes."""
        g = nx.Graph()
        g.add_edges_from([
            ((0, 0), (1, 0), {'weight': 1.0}),
            ((1, 0), (1, 1), {'weight': 1.0}),
            ((1, 1), (0, 1), {'weight': 1.0}),
            ((0, 1), (0, 0), {'weight': 1.0})
        ])
        return g

    @pytest.fixture
    def graph_with_self_loops(self):
        """Create a graph containing self-loops."""
        g = nx.Graph()
        g.add_edges_from([
            ((0, 0), (1, 0), {'weight': 1.0}),
            ((1, 0), (1, 0), {'weight': 0.0}),  # Self-loop
            ((1, 0), (1, 1), {'weight': 1.0}),
            ((1, 1), (1, 1), {'weight': 0.0})   # Another self-loop
        ])
        return g

    @pytest.fixture
    def disconnected_graph(self):
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

    @pytest.fixture
    def graph_with_close_nodes(self):
        """Create a graph with nodes that are very close to each other."""
        g = nx.Graph()
        g.add_edges_from([
            ((0, 0), (1, 0), {'weight': 1.0}),
            ((1, 0), (1.001, 0.001), {'weight': 0.001}),  # Very close nodes
            ((1.001, 0.001), (1, 1), {'weight': 1.0})
        ])
        return g

    @pytest.fixture
    def graph_with_intersecting_edges(self):
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

    def test_init_with_graph(self, simple_connected_graph):
        """Test GraphCorrector initialization with a valid graph."""
        corrector = GraphCorrector(simple_connected_graph)
        
        assert corrector.graph is not simple_connected_graph  # Should be a copy
        assert corrector.original_graph is simple_connected_graph
        assert corrector.tolerance == SHAPEFILE_TOLERANCE
        assert corrector.corrections_log == []
        assert corrector.graph.number_of_nodes() == simple_connected_graph.number_of_nodes()
        assert corrector.graph.number_of_edges() == simple_connected_graph.number_of_edges()

    def test_init_with_custom_tolerance(self, simple_connected_graph):
        """Test GraphCorrector initialization with custom tolerance."""
        custom_tolerance = 0.5
        corrector = GraphCorrector(simple_connected_graph, tolerance=custom_tolerance)
        
        assert corrector.tolerance == custom_tolerance

    # ==================================================================================
    # VALIDATION TESTS
    # ==================================================================================

    def test_validate_connectivity_empty_graph(self, empty_graph):
        """Test validation of empty graph."""
        corrector = GraphCorrector(empty_graph)
        is_valid, message = corrector.validate_connectivity()
        
        assert not is_valid
        assert message == "Graph is empty (no nodes)"

    def test_validate_connectivity_connected_graph(self, simple_connected_graph):
        """Test validation of connected graph."""
        corrector = GraphCorrector(simple_connected_graph)
        is_valid, message = corrector.validate_connectivity()
        
        assert is_valid
        assert message == "Graph is valid and connected"

    def test_validate_connectivity_disconnected_graph(self, disconnected_graph):
        """Test validation of disconnected graph."""
        corrector = GraphCorrector(disconnected_graph)
        is_valid, message = corrector.validate_connectivity()
        
        assert not is_valid
        assert message == "Graph is not connected: 2 disconnected components found"

    def test_validate_connectivity_graph_with_self_loops(self, graph_with_self_loops):
        """Test validation of graph with self-loops."""
        corrector = GraphCorrector(graph_with_self_loops)
        is_valid, message = corrector.validate_connectivity()
        
        assert not is_valid
        assert message == "Graph contains 2 self-loops"

    def test_identify_disconnected_components(self, disconnected_graph):
        """Test identification of disconnected components."""
        corrector = GraphCorrector(disconnected_graph)
        components = corrector.identify_disconnected_components()
        
        assert len(components) == 2
        # Components should be sorted by size (largest first)
        assert len(components[0]) >= len(components[1])
        
        # Check that all nodes are accounted for
        all_component_nodes = set()
        for component in components:
            all_component_nodes.update(component)
        assert all_component_nodes == set(disconnected_graph.nodes())

    # ==================================================================================
    # SELF-LOOP REMOVAL TESTS
    # ==================================================================================

    def test_remove_self_loops_with_self_loops(self, graph_with_self_loops):
        """Test removal of self-loops from graph."""
        corrector = GraphCorrector(graph_with_self_loops)
        
        # Verify self-loops exist before removal
        assert nx.number_of_selfloops(corrector.graph) > 0
        
        result_graph = corrector.remove_self_loops()
        
        # Verify self-loops are removed
        assert nx.number_of_selfloops(result_graph) == 0
        assert result_graph is corrector.graph  # Should return the same graph object
        
        # Check corrections log
        assert len(corrector.corrections_log) == 1
        assert corrector.corrections_log[0]['type'] == 'remove_self_loops'
        assert corrector.corrections_log[0]['details']['self_loops_removed'] > 0

    def test_remove_self_loops_no_self_loops(self, simple_connected_graph):
        """Test removal of self-loops from graph without self-loops."""
        corrector = GraphCorrector(simple_connected_graph)
        
        with patch('builtins.print') as mock_print:
            result_graph = corrector.remove_self_loops()
        
        # Should print message about no self-loops
        mock_print.assert_called_with("No self-loops found")
        assert result_graph is corrector.graph

    # ==================================================================================
    # CLOSE NODES MERGING TESTS
    # ==================================================================================

    def test_merge_close_nodes_with_close_nodes(self, graph_with_close_nodes):
        """Test merging of nodes that are close to each other."""
        corrector = GraphCorrector(graph_with_close_nodes)
        initial_node_count = corrector.graph.number_of_nodes()
        
        result_graph = corrector.merge_close_nodes()
        
        # Should have fewer nodes after merging
        assert result_graph.number_of_nodes() < initial_node_count
        assert result_graph is corrector.graph
        
        # Check corrections log
        assert len(corrector.corrections_log) == 1
        assert corrector.corrections_log[0]['type'] == 'merge_close_nodes'
        assert corrector.corrections_log[0]['details']['nodes_merged'] > 0

    def test_merge_close_nodes_custom_threshold(self, graph_with_close_nodes):
        """Test merging with custom distance threshold."""
        corrector = GraphCorrector(graph_with_close_nodes)
        
        # Use very small threshold - should not merge any nodes
        result_graph = corrector.merge_close_nodes(distance_threshold=0.0001)
        assert result_graph.number_of_nodes() == graph_with_close_nodes.number_of_nodes()

    # ==================================================================================
    # INTERSECTING EDGES TESTS
    # ==================================================================================

    def test_connect_intersecting_edges_already_connected(self, simple_connected_graph):
        """Test intersection detection on already connected graph."""
        corrector = GraphCorrector(simple_connected_graph)
        
        with patch('builtins.print') as mock_print:
            result_graph = corrector.connect_intersecting_edges()
        
        # Should skip intersection check for connected graph
        mock_print.assert_called_with("Graph already connected, skipping intersection check")
        assert result_graph is corrector.graph

    def test_calculate_edge_intersection(self):
        """Test edge intersection calculation."""
        corrector = GraphCorrector(nx.Graph())
        
        # Test intersecting lines
        edge1 = ((0, 0), (2, 2))  # Diagonal line
        edge2 = ((0, 2), (2, 0))  # Reverse diagonal line
        intersection = corrector._calculate_edge_intersection(edge1, edge2)
        
        assert intersection is not None
        assert abs(intersection[0] - 1.0) < 1e-10
        assert abs(intersection[1] - 1.0) < 1e-10

    def test_calculate_edge_intersection_parallel(self):
        """Test edge intersection calculation for parallel lines."""
        corrector = GraphCorrector(nx.Graph())
        
        # Test parallel lines
        edge1 = ((0, 0), (1, 0))  # Horizontal line
        edge2 = ((0, 1), (1, 1))  # Parallel horizontal line
        intersection = corrector._calculate_edge_intersection(edge1, edge2)
        
        assert intersection is None

    def test_point_on_segment(self):
        """Test point-on-segment detection."""
        corrector = GraphCorrector(nx.Graph())
        
        segment = ((0, 0), (2, 0))  # Horizontal line segment
        
        # Point on segment
        assert corrector._point_on_segment((1, 0), segment)
        
        # Point on line but outside segment
        assert not corrector._point_on_segment((3, 0), segment)
        
        # Point not on line
        assert not corrector._point_on_segment((1, 1), segment)

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
        assert not nx.is_connected(corrector.graph)
        assert nx.number_connected_components(corrector.graph) == 2
        
        result_graph = corrector.connect_intersecting_edges()
        
        # Should be connected after finding intersection
        assert nx.is_connected(result_graph)
        assert result_graph is corrector.graph
        
        # Should have added a junction node at the intersection
        initial_nodes = {(0, 1), (2, 1), (1, 0), (1, 2)}
        final_nodes = set(result_graph.nodes())
        
        # Should have more nodes (junction added)
        assert len(final_nodes) > len(initial_nodes)
        
        # Check corrections log
        assert len(corrector.corrections_log) == 1
        assert corrector.corrections_log[0]['type'] == 'connect_intersecting_edges'
        assert corrector.corrections_log[0]['details']['intersections_found'] > 0

    # ==================================================================================
    # COMPONENT CONNECTION TESTS
    # ==================================================================================

    def test_connect_disconnected_components(self, disconnected_graph):
        """Test connection of disconnected components."""
        corrector = GraphCorrector(disconnected_graph)
        
        # Verify graph is initially disconnected
        assert not nx.is_connected(corrector.graph)
        initial_components = nx.number_connected_components(corrector.graph)
        
        result_graph = corrector.connect_disconnected_components()
        
        # Should be connected after correction
        assert nx.is_connected(result_graph)
        assert result_graph is corrector.graph
        
        # Check corrections log
        assert len(corrector.corrections_log) == 1
        assert corrector.corrections_log[0]['type'] == 'connect_components'
        assert corrector.corrections_log[0]['details']['original_components'] == initial_components
        assert corrector.corrections_log[0]['details']['final_components'] == 1

    def test_connect_disconnected_components_already_connected(self, simple_connected_graph):
        """Test component connection on already connected graph."""
        corrector = GraphCorrector(simple_connected_graph)
        
        result_graph = corrector.connect_disconnected_components()
        
        # Should not change the graph
        assert result_graph is corrector.graph
        assert nx.is_connected(result_graph)
        
        # Check corrections log
        assert len(corrector.corrections_log) == 1
        assert corrector.corrections_log[0]['details']['message'] == 'Graph already connected, no action needed'

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
        assert nx.is_connected(result_graph)
        assert nx.number_of_selfloops(result_graph) == 0
        assert result_graph is corrector.graph
        
        # Should have logged multiple corrections
        assert len(corrector.corrections_log) > 0

    def test_get_corrections_log(self, graph_with_self_loops):
        """Test retrieval of corrections log."""
        corrector = GraphCorrector(graph_with_self_loops)
        
        # Initially empty
        log = corrector.get_corrections_log()
        assert log == []
        assert log is corrector.corrections_log
        
        # After applying corrections
        corrector.remove_self_loops()
        log = corrector.get_corrections_log()
        assert len(log) == 1
        assert log[0]['type'] == 'remove_self_loops'

    # ==================================================================================
    # STATIC METHOD TESTS
    # ==================================================================================

    def test_validate_steiner_tree_ready_valid_graph(self, simple_connected_graph):
        """Test Steiner tree validation for valid graph and terminals."""
        terminal_nodes = list(simple_connected_graph.nodes())[:2]
        
        is_ready, message = GraphCorrector.validate_steiner_tree_ready(
            simple_connected_graph, terminal_nodes
        )
        
        assert is_ready
        assert message == "Graph is ready for Steiner tree with 2 terminals"

    def test_validate_steiner_tree_ready_empty_graph(self, empty_graph):
        """Test Steiner tree validation for empty graph."""
        is_ready, message = GraphCorrector.validate_steiner_tree_ready(empty_graph, [])
        
        assert not is_ready
        assert "empty" in message.lower()

    def test_validate_steiner_tree_ready_disconnected_graph(self, disconnected_graph):
        """Test Steiner tree validation for disconnected graph."""
        terminal_nodes = list(disconnected_graph.nodes())[:2]
        
        is_ready, message = GraphCorrector.validate_steiner_tree_ready(
            disconnected_graph, terminal_nodes
        )
        
        assert not is_ready
        assert "not connected" in message.lower()

    def test_validate_steiner_tree_ready_insufficient_terminals(self, simple_connected_graph):
        """Test Steiner tree validation with insufficient terminal nodes."""
        # Test with only one terminal
        is_ready, message = GraphCorrector.validate_steiner_tree_ready(
            simple_connected_graph, [list(simple_connected_graph.nodes())[0]]
        )
        
        assert not is_ready
        assert "at least 2 terminal nodes" in message.lower()

    def test_validate_steiner_tree_ready_missing_terminals(self, simple_connected_graph):
        """Test Steiner tree validation with terminals not in graph."""
        missing_terminals = [(999, 999), (888, 888)]
        
        is_ready, message = GraphCorrector.validate_steiner_tree_ready(
            simple_connected_graph, missing_terminals
        )
        
        assert not is_ready
        assert "not found in graph" in message.lower()

    # ==================================================================================
    # EDGE CASE TESTS
    # ==================================================================================

    def test_corrections_log_structure(self, graph_with_self_loops):
        """Test that corrections log has proper structure."""
        corrector = GraphCorrector(graph_with_self_loops)
        corrector.remove_self_loops()
        
        log_entry = corrector.corrections_log[0]
        assert 'type' in log_entry
        assert 'details' in log_entry
        assert isinstance(log_entry['details'], dict)
        assert log_entry['type'] == 'remove_self_loops'

    def test_graph_modification_isolation(self, simple_connected_graph):
        """Test that graph modifications don't affect original graph."""
        original_edges = set(simple_connected_graph.edges())
        
        corrector = GraphCorrector(simple_connected_graph)
        
        # Add an edge to the corrector's graph
        new_node = (999, 999)
        corrector.graph.add_node(new_node)
        corrector.graph.add_edge(list(corrector.graph.nodes())[0], new_node)
        
        # Original graph should be unchanged
        assert set(simple_connected_graph.edges()) == original_edges
        assert new_node not in simple_connected_graph.nodes()


if __name__ == '__main__':
    pytest.main([__file__])