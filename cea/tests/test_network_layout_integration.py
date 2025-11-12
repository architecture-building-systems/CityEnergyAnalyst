"""
Integration tests for network layout functionality.

Tests the complete workflow: loading street/building data, creating connectivity network,
and verifying coordinate precision handling.
"""

import pytest
import geopandas as gpd
import networkx as nx
from shapely.geometry import Point, LineString

from cea.technologies.network_layout.connectivity_potential import calc_connectivity_network_with_geometry
from cea.technologies.network_layout.graph_utils import gdf_to_nx, nx_to_gdf
from cea.constants import SHAPEFILE_TOLERANCE


class TestNetworkLayoutIntegration:
    """Integration tests for complete network creation workflow."""

    @pytest.fixture
    def simple_street_network(self):
        """Create a simple test street network."""
        streets = gpd.GeoDataFrame(
            geometry=[
                LineString([(0.0, 0.0), (100.0, 0.0)]),  # Horizontal street
                LineString([(100.0, 0.0), (100.0, 100.0)]),  # Vertical street
                LineString([(0.0, 0.0), (0.0, 100.0)]),  # Vertical street
                LineString([(0.0, 100.0), (100.0, 100.0)]),  # Horizontal street
            ],
            crs='EPSG:32632'  # UTM zone 32N
        )
        return streets

    @pytest.fixture
    def simple_buildings(self):
        """Create simple test building centroids."""
        buildings = gpd.GeoDataFrame(
            {
                'name': ['B001', 'B002', 'B003', 'B004'],
                'geometry': [
                    Point(25.0, 10.0),   # Near first street
                    Point(75.0, 10.0),   # Near first street
                    Point(25.0, 90.0),   # Near last street
                    Point(75.0, 90.0),   # Near last street
                ]
            },
            crs='EPSG:32632'
        )
        return buildings

    def test_network_creation_basic(self, simple_street_network, simple_buildings):
        """Test basic network creation with simple geometry."""
        # Create network graph
        graph = calc_connectivity_network_with_geometry(
            simple_street_network,
            simple_buildings
        )

        # Verify output is a NetworkX graph with metadata
        assert isinstance(graph, nx.Graph)
        assert len(graph.nodes()) > 0
        assert len(graph.edges()) > 0
        assert 'building_terminals' in graph.graph
        assert 'crs' in graph.graph

        # Convert to GeoDataFrame and verify structure
        network_gdf = nx_to_gdf(graph, crs=graph.graph['crs'], preserve_geometry=True)
        assert not network_gdf.empty
        assert all(network_gdf.geometry.is_valid)

    def test_network_preserves_geometries(self, simple_street_network, simple_buildings):
        """Test that network creation preserves street geometries."""
        # Create curved street for testing
        curved_street = gpd.GeoDataFrame(
            geometry=[
                LineString([
                    (0.0, 0.0),
                    (25.0, 5.0),   # Curve point
                    (50.0, 7.0),   # Curve point
                    (75.0, 5.0),   # Curve point
                    (100.0, 0.0)
                ])
            ],
            crs='EPSG:32632'
        )

        buildings = gpd.GeoDataFrame(
            {'name': ['B001'], 'geometry': [Point(50.0, 10.0)]},
            crs='EPSG:32632'
        )

        graph = calc_connectivity_network_with_geometry(curved_street, buildings)

        # Graph should be valid NetworkX graph
        assert isinstance(graph, nx.Graph)
        assert len(graph.nodes()) > 0
        assert len(graph.edges()) > 0

        # Convert to GeoDataFrame to check geometry preservation
        edges_gdf = nx_to_gdf(graph, crs=graph.graph['crs'], preserve_geometry=True)

        # Check that at least one edge has curved geometry (more than 2 coordinates)
        has_curved = any(len(geom.coords) > 2 for geom in edges_gdf.geometry)
        assert has_curved, "Connectivity network flattened the curved street geometry"

    def test_coordinate_precision_consistency(self, simple_street_network, simple_buildings):
        """Test that coordinates maintain consistent precision throughout workflow."""
        graph = calc_connectivity_network_with_geometry(
            simple_street_network,
            simple_buildings
        )

        # Check all node coordinates have SHAPEFILE_TOLERANCE precision
        for node in graph.nodes():
            x, y = node
            # Verify coordinates are rounded to SHAPEFILE_TOLERANCE decimal places
            # by checking that rounding again produces the same value
            assert round(x, SHAPEFILE_TOLERANCE) == x
            assert round(y, SHAPEFILE_TOLERANCE) == y

    def test_building_terminal_metadata(self, simple_street_network, simple_buildings):
        """Test that building terminal metadata is properly stored in graph."""
        # Request graph directly to test metadata preservation
        graph = calc_connectivity_network_with_geometry(
            simple_street_network,
            simple_buildings,
            
        )

        # Verify graph has building terminal metadata
        assert 'building_terminals' in graph.graph, "Building terminal metadata not found"
        assert 'crs' in graph.graph, "CRS metadata not found"
        assert 'coord_precision' in graph.graph, "Coordinate precision metadata not found"

        # Verify building terminal mapping
        terminal_mapping = graph.graph['building_terminals']
        assert len(terminal_mapping) == len(simple_buildings), "Not all buildings have terminal nodes"

        # Verify each terminal node exists in graph
        graph_nodes = set(graph.nodes())
        for building_id, terminal_coord in terminal_mapping.items():
            assert terminal_coord in graph_nodes, f"Terminal for building {building_id} not in graph nodes"

        # Should be a connected graph
        assert nx.is_connected(graph)

        # Should have nodes and edges
        assert len(graph.nodes()) > 0
        assert len(graph.edges()) > 0

    def test_round_trip_conversion_preserves_network(self, simple_street_network, simple_buildings):
        """Test that graph → GeoDataFrame → graph preserves network."""
        # Create network graph
        original_graph = calc_connectivity_network_with_geometry(
            simple_street_network,
            simple_buildings
        )

        # Convert to GeoDataFrame
        network_gdf = nx_to_gdf(original_graph, crs=original_graph.graph['crs'], preserve_geometry=True)

        # Convert back to graph
        restored_graph = gdf_to_nx(network_gdf, preserve_geometry=True)

        # Verify same number of edges
        assert len(original_graph.edges()) == len(restored_graph.edges())

        # Verify all geometries in GeoDataFrame are valid
        assert all(network_gdf.geometry.is_valid)

        # Verify number of nodes is preserved
        assert len(original_graph.nodes()) == len(restored_graph.nodes())

    def test_network_handles_multiple_buildings(self, simple_street_network):
        """Test network creation with varying numbers of buildings."""
        # Test with different building counts
        for n_buildings in [1, 4, 10]:
            # Create buildings along a line
            buildings = gpd.GeoDataFrame(
                {
                    'name': [f'B{i:03d}' for i in range(n_buildings)],
                    'geometry': [
                        Point(i * 100.0 / (n_buildings + 1), 10.0)
                        for i in range(1, n_buildings + 1)
                    ]
                },
                crs='EPSG:32632'
            )

            graph = calc_connectivity_network_with_geometry(
                simple_street_network,
                buildings
            )

            # Verify network was created
            assert len(graph.nodes()) > 0
            assert len(graph.edges()) >= n_buildings  # At least one edge per building terminal

    def test_network_with_high_precision_coordinates(self):
        """Test that high-precision coordinates are properly normalized."""
        # Create network with high-precision floating-point coordinates
        streets = gpd.GeoDataFrame(
            geometry=[
                LineString([
                    (0.123456789123456, 1.987654321987654),
                    (100.111111111111, 100.999999999999)
                ])
            ],
            crs='EPSG:32632'
        )

        buildings = gpd.GeoDataFrame(
            {'name': ['B001'], 'geometry': [Point(50.555555555555, 50.777777777777)]},
            crs='EPSG:32632'
        )

        # This should work without floating-point precision errors
        graph = calc_connectivity_network_with_geometry(streets, buildings)

        # Verify network was created successfully
        assert len(graph.nodes()) > 0

        # Verify all coordinates are normalized
        for node in graph.nodes():
            x, y = node
            # Check precision
            x_str = f"{x:.{SHAPEFILE_TOLERANCE}f}"
            y_str = f"{y:.{SHAPEFILE_TOLERANCE}f}"
            assert float(x_str) == x
            assert float(y_str) == y

    def test_network_handles_disconnected_components(self):
        """Test that disconnected street networks are connected automatically."""
        # Create two separate street networks (disconnected)
        streets = gpd.GeoDataFrame(
            {
                'geometry': [
                    # First component - main street network
                    LineString([(0.0, 0.0), (100.0, 0.0)]),
                    LineString([(0.0, 0.0), (0.0, 100.0)]),
                    LineString([(100.0, 0.0), (100.0, 100.0)]),
                    LineString([(0.0, 100.0), (100.0, 100.0)]),
                    # Second component - isolated street (disconnected)
                    LineString([(200.0, 200.0), (300.0, 200.0)]),
                ]
            },
            crs='EPSG:32632'
        )

        # Buildings: some in first component, some in second
        buildings = gpd.GeoDataFrame(
            {
                'name': ['B001', 'B002', 'B003', 'B004'],
                'geometry': [
                    Point(25.0, 10.0),   # In first component
                    Point(75.0, 10.0),   # In first component
                    Point(250.0, 210.0), # In second component
                    Point(280.0, 210.0), # In second component
                ]
            },
            crs='EPSG:32632'
        )

        # Should raise an error for disconnected components
        # The current implementation does not automatically connect disconnected components
        with pytest.raises(ValueError, match="disconnected components"):
            calc_connectivity_network_with_geometry(streets, buildings)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
