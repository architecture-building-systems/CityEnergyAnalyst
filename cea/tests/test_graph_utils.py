"""
Tests for graph utility functions in cea/technologies/network_layout/graph_utils.py

Tests coordinate normalization, GeoDataFrame ↔ NetworkX graph conversion,
and round-trip conversion reliability.
"""

import pytest
import networkx as nx
import geopandas as gpd
from shapely.geometry import Point, LineString, MultiLineString

from cea.technologies.network_layout.graph_utils import (
    normalize_coords,
    normalize_geometry,
    normalize_gdf_geometries,
    gdf_to_nx,
    nx_to_gdf,
)


class TestCoordinateNormalization:
    """Test coordinate normalization utilities."""

    def test_normalize_coords_basic(self):
        """Test basic coordinate normalization."""
        coords = [(1.123456789, 2.987654321), (3.111111111, 4.999999999)]
        normalized = normalize_coords(coords, precision=6)

        assert len(normalized) == 2
        assert normalized[0] == (1.123457, 2.987654)
        assert normalized[1] == (3.111111, 5.0)

    def test_normalize_coords_default_precision(self):
        """Test that default precision uses SHAPEFILE_TOLERANCE."""
        coords = [(1.1234567, 2.9876543)]
        normalized = normalize_coords(coords)

        # Should round to SHAPEFILE_TOLERANCE (6) decimal places
        assert normalized[0] == (1.123457, 2.987654)

    def test_normalize_coords_empty_list(self):
        """Test normalizing empty coordinate list."""
        coords = []
        normalized = normalize_coords(coords)

        assert normalized == []

    def test_normalize_geometry_point(self):
        """Test normalizing Point geometry."""
        point = Point(1.123456789, 2.987654321)
        normalized = normalize_geometry(point, precision=6)

        assert normalized.geom_type == 'Point'
        assert normalized.x == 1.123457
        assert normalized.y == 2.987654

    def test_normalize_geometry_linestring(self):
        """Test normalizing LineString geometry."""
        line = LineString([(0.123456789, 1.987654321), (2.111111111, 3.999999999)])
        normalized = normalize_geometry(line, precision=6)

        assert normalized.geom_type == 'LineString'
        coords = list(normalized.coords)
        assert coords[0] == (0.123457, 1.987654)
        assert coords[1] == (2.111111, 4.0)

    def test_normalize_geometry_multilinestring(self):
        """Test normalizing MultiLineString geometry."""
        line1 = LineString([(0.1234567, 1.9876543), (2.1111111, 3.9999999)])
        line2 = LineString([(4.5555555, 5.6666666), (6.7777777, 7.8888888)])
        multi_line = MultiLineString([line1, line2])

        normalized = normalize_geometry(multi_line, precision=6)

        assert normalized.geom_type == 'MultiLineString'
        assert len(normalized.geoms) == 2

        # Check first line
        coords1 = list(normalized.geoms[0].coords)
        assert coords1[0] == (0.123457, 1.987654)
        assert coords1[1] == (2.111111, 4.0)

        # Check second line
        coords2 = list(normalized.geoms[1].coords)
        assert coords2[0] == (4.555555, 5.666667)  # Python rounds 4.5555555 down to 4.555555
        assert coords2[1] == (6.777778, 7.888889)

    def test_normalize_geometry_unsupported_type(self):
        """Test that unsupported geometry types raise ValueError."""
        from shapely.geometry import Polygon

        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        with pytest.raises(ValueError, match="Unsupported geometry type"):
            normalize_geometry(polygon)

    def test_normalize_gdf_geometries_inplace(self):
        """Test normalizing GeoDataFrame geometries in place."""
        gdf = gpd.GeoDataFrame(
            geometry=[
                LineString([(0.123456789, 1.987654321), (2.111111111, 3.999999999)]),
                LineString([(4.555555555, 5.666666666), (6.777777777, 7.888888888)])
            ],
            crs='EPSG:4326'
        )

        # Normalize in place
        result = normalize_gdf_geometries(gdf, precision=6, inplace=True)

        # Should return None when inplace=True
        assert result is None

        # Check that original GDF was modified
        coords1 = list(gdf.geometry[0].coords)
        assert coords1[0] == (0.123457, 1.987654)

        coords2 = list(gdf.geometry[1].coords)
        assert coords2[0] == (4.555556, 5.666667)

    def test_normalize_gdf_geometries_copy(self):
        """Test normalizing GeoDataFrame geometries with copy."""
        original_gdf = gpd.GeoDataFrame(
            geometry=[
                LineString([(0.123456789, 1.987654321), (2.111111111, 3.999999999)])
            ],
            crs='EPSG:4326'
        )

        # Normalize as copy
        normalized_gdf = normalize_gdf_geometries(original_gdf, precision=6, inplace=False)

        # Original should be unchanged
        original_coords = list(original_gdf.geometry[0].coords)
        assert original_coords[0] == (0.123456789, 1.987654321)

        # Copy should be normalized
        normalized_coords = list(normalized_gdf.geometry[0].coords)
        assert normalized_coords[0] == (0.123457, 1.987654)


class TestGdfToNxConversion:
    """Test GeoDataFrame to NetworkX graph conversion."""

    def test_gdf_to_nx_basic(self):
        """Test basic GeoDataFrame to NetworkX conversion."""
        gdf = gpd.GeoDataFrame(
            geometry=[
                LineString([(0.0, 0.0), (1.0, 1.0)]),
                LineString([(1.0, 1.0), (2.0, 2.0)])
            ],
            crs='EPSG:4326'
        )

        graph = gdf_to_nx(gdf, coord_precision=6, preserve_geometry=True)

        assert isinstance(graph, nx.Graph)
        assert len(graph.nodes()) == 3  # (0,0), (1,1), (2,2)
        assert len(graph.edges()) == 2

    def test_gdf_to_nx_coordinate_rounding(self):
        """Test that coordinates are properly rounded during conversion."""
        gdf = gpd.GeoDataFrame(
            geometry=[
                LineString([(0.123456789, 1.987654321), (2.111111111, 3.999999999)])
            ],
            crs='EPSG:4326'
        )

        graph = gdf_to_nx(gdf, coord_precision=6, preserve_geometry=False)

        nodes = list(graph.nodes())
        assert len(nodes) == 2
        assert (0.123457, 1.987654) in nodes
        assert (2.111111, 4.0) in nodes

    def test_gdf_to_nx_preserve_geometry(self):
        """Test that geometry preservation stores LineString in edge attributes."""
        gdf = gpd.GeoDataFrame(
            geometry=[
                LineString([(0.0, 0.0), (1.0, 1.0)])
            ],
            crs='EPSG:4326'
        )

        graph = gdf_to_nx(gdf, coord_precision=6, preserve_geometry=True)

        edges = list(graph.edges(data=True))
        assert len(edges) == 1

        u, v, data = edges[0]
        assert 'geometry' in data
        assert isinstance(data['geometry'], LineString)
        assert 'weight' in data

    def test_gdf_to_nx_without_geometry_preservation(self):
        """Test conversion without geometry preservation."""
        gdf = gpd.GeoDataFrame(
            geometry=[
                LineString([(0.0, 0.0), (1.0, 1.0)])
            ],
            crs='EPSG:4326'
        )

        graph = gdf_to_nx(gdf, coord_precision=6, preserve_geometry=False)

        edges = list(graph.edges(data=True))
        assert len(edges) == 1

        u, v, data = edges[0]
        assert 'geometry' not in data  # Should not preserve geometry
        assert 'weight' in data

    def test_gdf_to_nx_multilinestring(self):
        """Test conversion of MultiLineString geometries."""
        line1 = LineString([(0.0, 0.0), (1.0, 1.0)])
        line2 = LineString([(1.0, 1.0), (2.0, 2.0)])
        multi_line = MultiLineString([line1, line2])

        gdf = gpd.GeoDataFrame(geometry=[multi_line], crs='EPSG:4326')

        graph = gdf_to_nx(gdf, coord_precision=6, preserve_geometry=True)

        # MultiLineString should be split into separate edges
        assert len(graph.edges()) == 2


class TestNxToGdfConversion:
    """Test NetworkX graph to GeoDataFrame conversion."""

    def test_nx_to_gdf_basic(self):
        """Test basic NetworkX to GeoDataFrame conversion."""
        graph = nx.Graph()
        graph.add_edge((0.0, 0.0), (1.0, 1.0), weight=1.414)
        graph.add_edge((1.0, 1.0), (2.0, 2.0), weight=1.414)

        gdf = nx_to_gdf(graph, crs='EPSG:4326', preserve_geometry=False)

        assert isinstance(gdf, gpd.GeoDataFrame)
        assert len(gdf) == 2
        assert all(gdf.geometry.geom_type == 'LineString')

    def test_nx_to_gdf_preserve_geometry(self):
        """Test GeoDataFrame conversion with geometry preservation."""
        # Create graph with geometry attribute
        graph = nx.Graph()
        curved_line = LineString([(0.0, 0.0), (0.5, 0.5), (1.0, 1.0)])
        graph.add_edge((0.0, 0.0), (1.0, 1.0), geometry=curved_line, weight=1.414)

        gdf = nx_to_gdf(graph, crs='EPSG:4326', preserve_geometry=True)

        # Should use preserved curved geometry
        assert len(gdf) == 1
        geom = gdf.geometry[0]
        coords = list(geom.coords)
        assert len(coords) == 3  # Curved line has intermediate point
        assert coords[1] == (0.5, 0.5)

    def test_nx_to_gdf_without_geometry_preservation(self):
        """Test GeoDataFrame conversion creating straight lines."""
        graph = nx.Graph()
        curved_line = LineString([(0.0, 0.0), (0.5, 0.5), (1.0, 1.0)])
        graph.add_edge((0.0, 0.0), (1.0, 1.0), geometry=curved_line, weight=1.414)

        gdf = nx_to_gdf(graph, crs='EPSG:4326', preserve_geometry=False)

        # Should create straight line from node coordinates
        assert len(gdf) == 1
        geom = gdf.geometry[0]
        coords = list(geom.coords)
        assert len(coords) == 2  # Straight line, no intermediate points
        assert coords[0] == (0.0, 0.0)
        assert coords[1] == (1.0, 1.0)

    def test_nx_to_gdf_preserves_edge_attributes(self):
        """Test that edge attributes are preserved in conversion."""
        graph = nx.Graph()
        graph.add_edge((0.0, 0.0), (1.0, 1.0), weight=1.414, pipe_DN=150, type_mat='steel')

        gdf = nx_to_gdf(graph, crs='EPSG:4326', preserve_geometry=False)

        assert len(gdf) == 1
        assert 'weight' in gdf.columns
        assert 'pipe_DN' in gdf.columns
        assert 'type_mat' in gdf.columns
        assert gdf['weight'][0] == 1.414
        assert gdf['pipe_DN'][0] == 150
        assert gdf['type_mat'][0] == 'steel'


class TestRoundTripConversion:
    """Test round-trip conversion: GeoDataFrame → graph → GeoDataFrame."""

    def test_round_trip_basic(self):
        """Test that basic round-trip conversion preserves structure."""
        original_gdf = gpd.GeoDataFrame(
            geometry=[
                LineString([(0.0, 0.0), (1.0, 1.0)]),
                LineString([(1.0, 1.0), (2.0, 2.0)])
            ],
            crs='EPSG:4326'
        )

        # Convert to graph and back
        graph = gdf_to_nx(original_gdf, preserve_geometry=True)
        restored_gdf = nx_to_gdf(graph, crs='EPSG:4326', preserve_geometry=True)

        # Should have same number of edges
        assert len(original_gdf) == len(restored_gdf)
        assert all(restored_gdf.geometry.geom_type == 'LineString')

    def test_round_trip_with_coordinate_normalization(self):
        """Test round-trip with coordinate normalization."""
        # Create GDF with high-precision coordinates
        original_gdf = gpd.GeoDataFrame(
            geometry=[
                LineString([(0.123456789, 1.987654321), (2.111111111, 3.999999999)])
            ],
            crs='EPSG:4326'
        )

        # Normalize first
        normalize_gdf_geometries(original_gdf, precision=6, inplace=True)

        # Convert to graph and back
        graph = gdf_to_nx(original_gdf, coord_precision=6, preserve_geometry=True)
        restored_gdf = nx_to_gdf(graph, crs='EPSG:4326', preserve_geometry=True)

        # Coordinates should match (after normalization)
        original_coords = list(original_gdf.geometry[0].coords)
        restored_coords = list(restored_gdf.geometry[0].coords)

        assert len(original_coords) == len(restored_coords)
        for orig, rest in zip(original_coords, restored_coords):
            assert orig == rest

    def test_round_trip_preserves_curved_geometry(self):
        """Test that curved street geometries are preserved through round-trip."""
        # Create curved street geometry
        curved_street = LineString([
            (0.0, 0.0),
            (0.25, 0.1),   # Curve point 1
            (0.5, 0.15),   # Curve point 2
            (0.75, 0.1),   # Curve point 3
            (1.0, 0.0)
        ])

        original_gdf = gpd.GeoDataFrame(geometry=[curved_street], crs='EPSG:4326')

        # Convert to graph and back with geometry preservation
        graph = gdf_to_nx(original_gdf, preserve_geometry=True)
        restored_gdf = nx_to_gdf(graph, crs='EPSG:4326', preserve_geometry=True)

        # Should preserve all intermediate curve points
        original_coords = list(original_gdf.geometry[0].coords)
        restored_coords = list(restored_gdf.geometry[0].coords)

        assert len(restored_coords) == 5  # All curve points preserved
        assert len(restored_coords) == len(original_coords)

    def test_round_trip_without_geometry_preservation(self):
        """Test round-trip without geometry preservation creates straight lines."""
        curved_street = LineString([
            (0.0, 0.0),
            (0.25, 0.1),
            (0.5, 0.15),
            (0.75, 0.1),
            (1.0, 0.0)
        ])

        original_gdf = gpd.GeoDataFrame(geometry=[curved_street], crs='EPSG:4326')

        # Convert without geometry preservation
        graph = gdf_to_nx(original_gdf, preserve_geometry=False)
        restored_gdf = nx_to_gdf(graph, crs='EPSG:4326', preserve_geometry=False)

        # Should create straight line (only start and end points)
        restored_coords = list(restored_gdf.geometry[0].coords)
        assert len(restored_coords) == 2
        assert restored_coords[0] == (0.0, 0.0)
        assert restored_coords[1] == (1.0, 0.0)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
