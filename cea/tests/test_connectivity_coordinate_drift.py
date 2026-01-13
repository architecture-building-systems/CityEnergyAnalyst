"""
Test suite for coordinate drift prevention in thermal network connectivity.

This module validates that coordinate normalization throughout the connectivity workflow
prevents floating-point drift that could cause graph disconnections. The tests focus on
the critical path: building centroids → street network → terminal creation → graph conversion.

Key Issues Addressed:
- substring() operations on curved streets introduce micro-drift at intermediate vertices
- Even normalized geometries can have drift in preserved edge geometry attributes
- Terminal connections at intermediate vertices must match exactly for graph connectivity
- Final normalization pass in create_terminals() ensures consistency
"""

import unittest
from geopandas import GeoDataFrame
from shapely.geometry import Point, LineString
from cea.technologies.network_layout.connectivity_potential import create_terminals
from cea.technologies.network_layout.graph_utils import (
    gdf_to_nx, normalize_coords, SHAPEFILE_TOLERANCE
)


class TestConnectivityCoordinateDrift(unittest.TestCase):
    """Test coordinate drift prevention in network connectivity."""

    def setUp(self):
        """Set up test fixtures with curved street and building."""
        # Create a curved street with many intermediate vertices (simulates real GIS data)
        # Using a bezier-like curve to ensure substring() will interpolate
        street_coords = [
            (0.0, 0.0),
            (10.123456789, 5.987654321),
            (20.111111111, 8.222222222),
            (30.333333333, 7.444444444),
            (40.0, 5.0),
            (50.0, 0.0)
        ]
        self.street_line = LineString(street_coords)
        
        # Create street network GDF
        self.street_network = GeoDataFrame(
            geometry=[self.street_line],
            crs='EPSG:2056'
        )
        
        # Building centroid that will connect to an intermediate point on the curve
        # Choose a point that's close to the curve but not at an exact vertex
        self.building_point = Point(25.0, 10.0)
        
        self.building_centroids = GeoDataFrame(
            {'name': ['B001']},
            geometry=[self.building_point],
            crs='EPSG:2056'
        )

    def test_substring_preserves_normalized_endpoints(self):
        """
        Test that substring operations followed by normalization produce
        consistent endpoint coordinates that survive graph conversion.
        
        This validates the core fix: normalize_gdf_geometries() after
        create_terminals() ensures all coordinates are consistent.
        """
        # Create terminals with k=1 (single nearest connection)
        combined_network = create_terminals(
            self.building_centroids,
            self.street_network,
            connection_candidates=1
        )
        
        # Convert to graph with geometry preservation
        graph = gdf_to_nx(combined_network, coord_precision=SHAPEFILE_TOLERANCE, preserve_geometry=True)
        
        # Check that all nodes have exactly normalized coordinates
        for node in graph.nodes():
            x, y = node
            x_normalized = round(x, SHAPEFILE_TOLERANCE)
            y_normalized = round(y, SHAPEFILE_TOLERANCE)
            
            self.assertEqual(x, x_normalized, 
                f"Node x-coordinate {x} not normalized to {x_normalized}")
            self.assertEqual(y, y_normalized,
                f"Node y-coordinate {y} not normalized to {y_normalized}")
        
        # Check that all edge geometries have normalized coordinates
        for u, v, data in graph.edges(data=True):
            if 'geometry' in data:
                geom = data['geometry']
                coords = list(geom.coords)
                for i, (x, y) in enumerate(coords):
                    x_normalized = round(x, SHAPEFILE_TOLERANCE)
                    y_normalized = round(y, SHAPEFILE_TOLERANCE)
                    
                    self.assertEqual(x, x_normalized,
                        f"Edge {u}->{v} vertex {i} x-coordinate {x} not normalized")
                    self.assertEqual(y, y_normalized,
                        f"Edge {u}->{v} vertex {i} y-coordinate {y} not normalized")

    def test_terminal_connection_survives_graph_conversion(self):
        """
        Test that terminal→street connections remain connected after gdf_to_nx conversion.
        
        This is the critical validation: if coordinate drift exists, the terminal edge
        endpoint won't match the street segment endpoint, creating disconnected nodes.
        """
        combined_network = create_terminals(
            self.building_centroids,
            self.street_network,
            connection_candidates=1
        )
        
        graph = gdf_to_nx(combined_network, coord_precision=SHAPEFILE_TOLERANCE, preserve_geometry=True)
        
        # Find the building node (should be the building centroid, normalized)
        building_coord = normalize_coords(
            [self.building_point.coords[0]],
            precision=SHAPEFILE_TOLERANCE
        )[0]
        
        self.assertIn(building_coord, graph.nodes(),
            f"Building centroid {building_coord} not found in graph nodes")
        
        # Building should have exactly 1 neighbor (the terminal connection point)
        neighbors = list(graph.neighbors(building_coord))
        self.assertEqual(len(neighbors), 1,
            f"Building should have 1 neighbor (terminal connection), found {len(neighbors)}")
        
        # The terminal connection point should have >= 2 neighbors:
        # 1. The building (terminal edge)
        # 2. Street segment(s) - may be 2 if terminal splits a street, or 1 if at endpoint
        terminal_node = neighbors[0]
        terminal_neighbors = list(graph.neighbors(terminal_node))
        self.assertGreaterEqual(len(terminal_neighbors), 2,
            f"Terminal node {terminal_node} should have >=2 neighbors, found {len(terminal_neighbors)}")
        
        # Verify building is in terminal's neighbors (bidirectional edge)
        self.assertIn(building_coord, terminal_neighbors,
            "Terminal connection should be bidirectional")

    def test_multiple_buildings_on_same_curved_street(self):
        """
        Test that multiple buildings connecting to the same curved street
        don't create disconnected components due to coordinate drift.
        
        This tests the most challenging case: multiple substring operations
        on the same curved street with different split points.
        """
        # Add two more buildings at different positions along the curve
        building_points = [
            self.building_point,  # B001 from setUp
            Point(15.0, 12.0),    # B002 - earlier on curve
            Point(35.0, 8.0)      # B003 - later on curve
        ]
        
        multi_building_centroids = GeoDataFrame(
            {'name': ['B001', 'B002', 'B003']},
            geometry=building_points,
            crs='EPSG:2056'
        )
        
        combined_network = create_terminals(
            multi_building_centroids,
            self.street_network,
            connection_candidates=1
        )
        
        graph = gdf_to_nx(combined_network, coord_precision=SHAPEFILE_TOLERANCE, preserve_geometry=True)
        
        # Verify all 3 buildings are in the graph
        for i, bldg_pt in enumerate(building_points):
            bldg_coord = normalize_coords([bldg_pt.coords[0]], precision=SHAPEFILE_TOLERANCE)[0]
            self.assertIn(bldg_coord, graph.nodes(),
                f"Building B{i+1:03d} not found in graph")
        
        # Verify graph is fully connected (single component)
        import networkx as nx
        num_components = nx.number_connected_components(graph.to_undirected())
        self.assertEqual(num_components, 1,
            f"Graph should have 1 connected component, found {num_components}")

    def test_gdf_to_nx_coordinate_consistency(self):
        """
        Test that gdf_to_nx() maintains coordinate consistency between
        node keys and preserved edge geometries.
        
        This validates that the fix prevents the specific bug: when preserve_geometry=True,
        intermediate vertices in stored LineStrings must match node coordinates exactly.
        """
        combined_network = create_terminals(
            self.building_centroids,
            self.street_network,
            connection_candidates=1
        )
        
        graph = gdf_to_nx(combined_network, coord_precision=SHAPEFILE_TOLERANCE, preserve_geometry=True)
        
        # For each edge with preserved geometry, verify start/end coords match node keys
        # Note: NetworkX may store edges in either direction (u->v or v->u)
        for u, v, data in graph.edges(data=True):
            if 'geometry' in data:
                geom = data['geometry']
                coords = list(geom.coords)
                
                start_coord = tuple(coords[0])
                end_coord = tuple(coords[-1])
                
                # Edge geometry should match node pair (in either direction)
                forward_match = (start_coord == u and end_coord == v)
                reverse_match = (start_coord == v and end_coord == u)
                
                self.assertTrue(forward_match or reverse_match,
                    f"Edge geometry ({start_coord} -> {end_coord}) doesn't match nodes ({u}, {v})")

    def test_create_terminals_final_normalization(self):
        """
        Test that create_terminals() applies final normalization pass
        to eliminate any remaining coordinate drift from substring operations.
        
        This directly validates the fix: normalize_gdf_geometries() before return.
        """
        # Create a street with intentionally high-precision coordinates
        high_precision_coords = [
            (0.123456789123456, 0.987654321987654),
            (10.111111111111111, 5.222222222222222),
            (20.333333333333333, 8.444444444444444),
            (30.555555555555555, 7.666666666666666),
            (40.777777777777777, 5.888888888888888),
            (50.999999999999999, 0.111111111111111)
        ]
        high_precision_street = LineString(high_precision_coords)
        
        street_network = GeoDataFrame(
            geometry=[high_precision_street],
            crs='EPSG:2056'
        )
        
        combined_network = create_terminals(
            self.building_centroids,
            street_network,
            connection_candidates=1
        )
        
        # Check that ALL coordinates in the result are normalized to SHAPEFILE_TOLERANCE
        for geom in combined_network.geometry:
            coords = list(geom.coords)
            for x, y in coords:
                # Count decimal places
                x_decimals = len(str(x).split('.')[-1]) if '.' in str(x) else 0
                y_decimals = len(str(y).split('.')[-1]) if '.' in str(y) else 0
                
                # Should be <= SHAPEFILE_TOLERANCE (6 decimal places)
                # Note: May be less due to trailing zeros being dropped
                self.assertLessEqual(x_decimals, SHAPEFILE_TOLERANCE,
                    f"X-coordinate {x} has {x_decimals} decimals, expected <={SHAPEFILE_TOLERANCE}")
                self.assertLessEqual(y_decimals, SHAPEFILE_TOLERANCE,
                    f"Y-coordinate {y} has {y_decimals} decimals, expected <={SHAPEFILE_TOLERANCE}")


if __name__ == '__main__':
    unittest.main()
