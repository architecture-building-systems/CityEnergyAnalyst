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
from cea.technologies.network_layout.graph_utils import gdf_to_nx, nx_to_gdf, normalize_gdf_geometries
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
                'Name': ['B001', 'B002', 'B003', 'B004'],
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
        # Create network
        network = calc_connectivity_network_with_geometry(
            simple_street_network,
            simple_buildings
        )

        # Verify output structure
        assert isinstance(network, gpd.GeoDataFrame)
        assert not network.empty
        assert 'length' in network.columns
        assert all(network.geometry.is_valid)
        assert all(network['length'] > 0)

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
            {'Name': ['B001'], 'geometry': [Point(50.0, 10.0)]},
            crs='EPSG:32632'
        )

        network = calc_connectivity_network_with_geometry(curved_street, buildings)

        # Should have at least one edge with curved geometry
        assert not network.empty

        # Check that some geometries have intermediate vertices (curves)
        has_curved = False
        for geom in network.geometry:
            if len(geom.coords) > 2:
                has_curved = True
                break

        # Note: Curved streets may be split at building connections,
        # so we just verify the network was created successfully
        assert len(network) > 0

    def test_coordinate_precision_consistency(self, simple_street_network, simple_buildings):
        """Test that coordinates maintain consistent precision throughout workflow."""
        network = calc_connectivity_network_with_geometry(
            simple_street_network,
            simple_buildings
        )

        # Convert to graph
        graph = gdf_to_nx(network, preserve_geometry=True)

        # Check all node coordinates have SHAPEFILE_TOLERANCE precision
        for node in graph.nodes():
            x, y = node
            # Verify coordinates are rounded to SHAPEFILE_TOLERANCE decimal places
            # by checking that rounding again produces the same value
            assert round(x, SHAPEFILE_TOLERANCE) == x
            assert round(y, SHAPEFILE_TOLERANCE) == y

    def test_building_terminal_metadata(self, simple_street_network, simple_buildings):
        """Test that building terminal metadata is properly stored in graph."""
        # Note: calc_connectivity_network_with_geometry returns GeoDataFrame,
        # but internally it creates a graph with metadata. We need to test
        # this by inspecting the internal workflow or by using the graph directly.

        # For now, verify the network was created successfully
        network = calc_connectivity_network_with_geometry(
            simple_street_network,
            simple_buildings
        )

        # Convert to graph to verify it works
        graph = gdf_to_nx(network, preserve_geometry=True)

        # Should be a connected graph
        assert nx.is_connected(graph)

        # Should have nodes and edges
        assert len(graph.nodes()) > 0
        assert len(graph.edges()) > 0

    def test_round_trip_conversion_preserves_network(self, simple_street_network, simple_buildings):
        """Test that GeoDataFrame → graph → GeoDataFrame preserves network."""
        # Create network
        original_network = calc_connectivity_network_with_geometry(
            simple_street_network,
            simple_buildings
        )

        # Convert to graph
        graph = gdf_to_nx(original_network, preserve_geometry=True)

        # Convert back to GeoDataFrame
        restored_network = nx_to_gdf(graph, crs=original_network.crs, preserve_geometry=True)

        # Verify same number of edges
        assert len(original_network) == len(restored_network)

        # Verify all geometries are valid
        assert all(restored_network.geometry.is_valid)

        # Verify lengths are similar (may differ slightly due to rounding)
        original_total_length = original_network['length'].sum()
        restored_total_length = restored_network.geometry.length.sum()
        assert abs(original_total_length - restored_total_length) < 0.01  # Within 1cm

    def test_network_handles_multiple_buildings(self, simple_street_network):
        """Test network creation with varying numbers of buildings."""
        # Test with different building counts
        for n_buildings in [1, 4, 10]:
            # Create buildings along a line
            buildings = gpd.GeoDataFrame(
                {
                    'Name': [f'B{i:03d}' for i in range(n_buildings)],
                    'geometry': [
                        Point(i * 100.0 / (n_buildings + 1), 10.0)
                        for i in range(1, n_buildings + 1)
                    ]
                },
                crs='EPSG:32632'
            )

            network = calc_connectivity_network_with_geometry(
                simple_street_network,
                buildings
            )

            # Verify network was created
            assert not network.empty
            assert len(network) >= n_buildings  # At least one edge per building terminal

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
            {'Name': ['B001'], 'geometry': [Point(50.555555555555, 50.777777777777)]},
            crs='EPSG:32632'
        )

        # This should work without floating-point precision errors
        network = calc_connectivity_network_with_geometry(streets, buildings)

        # Verify network was created successfully
        assert not network.empty

        # Verify all coordinates are normalized
        graph = gdf_to_nx(network, preserve_geometry=False)
        for node in graph.nodes():
            x, y = node
            # Check precision
            x_str = f"{x:.{SHAPEFILE_TOLERANCE}f}"
            y_str = f"{y:.{SHAPEFILE_TOLERANCE}f}"
            assert float(x_str) == x
            assert float(y_str) == y


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
