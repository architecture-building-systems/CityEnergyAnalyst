"""
Integration tests for network layout functionality.

Tests the complete workflow: loading street/building data, creating connectivity network,
and verifying coordinate precision handling.
"""

from types import SimpleNamespace

import pytest
import geopandas as gpd
import networkx as nx
from shapely.geometry import Point, LineString

from cea.technologies.network_layout.connectivity_potential import calc_connectivity_network_with_geometry
from cea.technologies.network_layout.graph_utils import gdf_to_nx, nx_to_gdf
from cea.optimization_new.user_network_loader import (
    augment_user_network_with_buildings,
    filter_network_to_buildings,
    _prune_dangling_stubs,
)
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


class TestFilterNetwork:
    """Tests for filter_network_to_buildings and _prune_dangling_stubs.

    Networks are constructed as small synthetic GeoDataFrames so the logic can
    be exercised without a full CEA scenario. Coordinates are chosen on an
    integer grid to keep the topology easy to reason about.
    """

    CRS = 'EPSG:32632'

    def _build_network(self, include_plant=False):
        """Build a small linear trunk network:

            B001 — J1 — J2 — J3 — J4 — B004
                        |    |
                       B002 B003

        Optionally attaches a plant node P1 via its own pipe off J2.

        Returns (nodes_gdf, edges_gdf). Nodes carry the CEA full format
        columns (building, name, type).
        """
        node_records = [
            ('B001',  'N0', 'CONSUMER', Point(0.0, 0.0)),
            ('NONE',  'J1', 'NONE',     Point(10.0, 0.0)),
            ('NONE',  'J2', 'NONE',     Point(20.0, 0.0)),
            ('NONE',  'J3', 'NONE',     Point(30.0, 0.0)),
            ('NONE',  'J4', 'NONE',     Point(40.0, 0.0)),
            ('B004',  'N4', 'CONSUMER', Point(50.0, 0.0)),
            ('B002',  'N2', 'CONSUMER', Point(20.0, 10.0)),
            ('B003',  'N3', 'CONSUMER', Point(30.0, 10.0)),
        ]
        if include_plant:
            node_records.append(('NONE', 'P1', 'PLANT', Point(20.0, -10.0)))

        nodes_gdf = gpd.GeoDataFrame(
            [{'building': b, 'name': n, 'type': t, 'geometry': g}
             for b, n, t, g in node_records],
            crs=self.CRS,
        )

        edge_lines = [
            LineString([(0.0, 0.0), (10.0, 0.0)]),    # B001—J1
            LineString([(10.0, 0.0), (20.0, 0.0)]),   # J1—J2
            LineString([(20.0, 0.0), (30.0, 0.0)]),   # J2—J3
            LineString([(30.0, 0.0), (40.0, 0.0)]),   # J3—J4
            LineString([(40.0, 0.0), (50.0, 0.0)]),   # J4—B004
            LineString([(20.0, 0.0), (20.0, 10.0)]),  # J2—B002
            LineString([(30.0, 0.0), (30.0, 10.0)]),  # J3—B003
        ]
        if include_plant:
            edge_lines.append(LineString([(20.0, 0.0), (20.0, -10.0)]))  # J2—P1

        edges_gdf = gpd.GeoDataFrame(
            [{'name': f'P{i}', 'type_mat': 'steel', 'geometry': g}
             for i, g in enumerate(edge_lines)],
            crs=self.CRS,
        )
        return nodes_gdf, edges_gdf

    def _buildings_in(self, nodes_gdf):
        return set(
            nodes_gdf[nodes_gdf['building'].fillna('NONE') != 'NONE']['building']
        ) - {'NONE'}

    def _junction_names_in(self, nodes_gdf):
        return set(nodes_gdf[nodes_gdf['type'] == 'NONE']['name'])

    def test_filter_removes_leaf_building_and_its_stub(self):
        """Filtering out a leaf building must also drop its terminal pipe."""
        nodes_gdf, edges_gdf = self._build_network()
        original_edges = len(edges_gdf)

        keep = ['B001', 'B002', 'B003', 'B004']  # drop nothing
        out_nodes, out_edges = filter_network_to_buildings(nodes_gdf, edges_gdf, keep)
        assert self._buildings_in(out_nodes) == {'B001', 'B002', 'B003', 'B004'}
        assert len(out_edges) == original_edges

        # Now drop B002 — its terminal pipe J2—B002 should be gone.
        keep = ['B001', 'B003', 'B004']
        out_nodes, out_edges = filter_network_to_buildings(nodes_gdf, edges_gdf, keep)
        assert self._buildings_in(out_nodes) == {'B001', 'B003', 'B004'}
        assert len(out_edges) == original_edges - 1  # only B002's pipe dropped
        # J2 is still a trunk junction, must survive
        assert 'J2' in self._junction_names_in(out_nodes)

    def test_filter_preserves_isolated_plant(self, capsys):
        """Plant nodes and their pipes must survive filtering."""
        nodes_gdf, edges_gdf = self._build_network(include_plant=True)

        # Drop every consumer — the plant should still be there with its pipe.
        keep = ['B001']  # keep one consumer so filter has at least one terminal
        out_nodes, out_edges = filter_network_to_buildings(nodes_gdf, edges_gdf, keep)

        assert 'P1' in out_nodes['name'].values
        # Plant pipe J2—P1 must survive
        plant_coord = (20.0, -10.0)
        j2_coord = (20.0, 0.0)
        has_plant_pipe = any(
            {tuple(g.coords[0]), tuple(g.coords[-1])} == {plant_coord, j2_coord}
            for g in out_edges.geometry
        )
        assert has_plant_pipe, "Plant pipe was pruned by filter"

    def test_filter_removing_middle_building_drops_spur(self):
        """Filtering out B003 must drop its spur pipe J3—B003."""
        nodes_gdf, edges_gdf = self._build_network()
        original_edges = len(edges_gdf)

        keep = ['B001', 'B002', 'B004']
        out_nodes, out_edges = filter_network_to_buildings(nodes_gdf, edges_gdf, keep)
        assert self._buildings_in(out_nodes) == {'B001', 'B002', 'B004'}
        assert len(out_edges) == original_edges - 1
        # Trunk junctions must all survive
        for jn in ('J1', 'J2', 'J3', 'J4'):
            assert jn in self._junction_names_in(out_nodes)

    def test_prune_dangling_stubs_protects_listed_coords(self):
        """Helper should not prune nodes whose coords are in protected_coords."""
        # Build a minimal graph with a single trunk + stub
        nodes = gpd.GeoDataFrame(
            [
                {'building': 'B1', 'name': 'A', 'type': 'CONSUMER',
                 'geometry': Point(0.0, 0.0)},
                {'building': 'NONE', 'name': 'J', 'type': 'NONE',
                 'geometry': Point(5.0, 0.0)},
                {'building': 'NONE', 'name': 'STUB', 'type': 'NONE',
                 'geometry': Point(5.0, 5.0)},
            ],
            crs=self.CRS,
        )
        edges = gpd.GeoDataFrame(
            [
                {'name': 'E1', 'geometry': LineString([(0.0, 0.0), (5.0, 0.0)])},
                {'name': 'E2', 'geometry': LineString([(5.0, 0.0), (5.0, 5.0)])},
            ],
            crs=self.CRS,
        )
        # Protect only the consumer terminal → J and STUB are unprotected,
        # so the degree-1 STUB gets pruned first, then J becomes degree-1
        # and it too gets pruned (leaving only A).
        protected = {(0.0, 0.0)}
        out_nodes, out_edges = _prune_dangling_stubs(nodes, edges, protected)
        assert set(out_nodes['name']) == {'A'}
        assert len(out_edges) == 0


class TestAugmentNetwork:
    """Tests for augment_user_network_with_buildings (extending an existing network,
    e.g. a pathway state reusing the previous state's layout)."""

    CRS = 'EPSG:32632'
    # A 100 m square block of streets
    SQUARE_STREETS = [
        [(0.0, 0.0), (100.0, 0.0)],
        [(100.0, 0.0), (100.0, 100.0)],
        [(0.0, 0.0), (0.0, 100.0)],
        [(0.0, 100.0), (100.0, 100.0)],
    ]

    def _augment(self, streets, nodes, pipes, buildings):
        """Add every building missing from the existing network (``nodes`` as
        ``(building, type, xy)``, ``pipes`` as coordinate lists) to it.

        :param buildings: ``{name: centroid xy}`` of the zone
        :return: ``(user_edges, augmented_nodes, augmented_edges, edge graph)``
        """
        user_nodes = gpd.GeoDataFrame(
            [{'building': b, 'name': f'NODE{i}', 'type': t, 'geometry': Point(xy)}
             for i, (b, t, xy) in enumerate(nodes)],
            crs=self.CRS,
        )
        user_edges = gpd.GeoDataFrame(
            [{'name': f'PIPE{i}', 'type_mat': 'T1', 'geometry': LineString(coords)}
             for i, coords in enumerate(pipes)],
            crs=self.CRS,
        )
        zone = gpd.GeoDataFrame(
            {'name': list(buildings), 'geometry': [Point(xy).buffer(4) for xy in buildings.values()]},
            crs=self.CRS,
        )
        nodes_out, edges_out = augment_user_network_with_buildings(
            user_nodes_gdf=user_nodes,
            user_edges_gdf=user_edges,
            zone_gdf=zone,
            missing_building_names=[b for b in buildings if b not in set(user_nodes['building'])],
            street_network_gdf=gpd.GeoDataFrame(geometry=[LineString(c) for c in streets], crs=self.CRS),
            locator=SimpleNamespace(get_total_demand=lambda: 'missing-total-demand.csv'),
            snap_tolerance=0.1,
            connection_candidates=1,
            existing_max_pipe_number=len(pipes) - 1,
        )
        graph = nx.Graph()
        for line in edges_out.geometry:
            graph.add_edge(line.coords[0], line.coords[-1])
        return user_edges, nodes_out, edges_out, graph

    def test_stray_street_fragments_do_not_block_augmentation(self):
        """Street data with isolated fragments must not make augmentation fail.

        A fresh layout bridges or discards such fragments; augmentation used to pass the
        raw streets to the Steiner tree, which rejects any disconnected graph.
        """
        streets = self.SQUARE_STREETS + [
            [(120.0, 50.0), (130.0, 50.0)],    # near fragment: bridged
            [(500.0, 500.0), (520.0, 500.0)],  # far fragment: discarded
        ]
        # Existing network: B001 and a plant, both hanging off the bottom street.
        user_edges, nodes, edges, graph = self._augment(
            streets,
            nodes=[('B001', 'CONSUMER', (0.0, -10.0)), ('NONE', 'NONE', (0.0, 0.0)),
                   ('NONE', 'NONE', (100.0, 0.0)), ('NONE', 'PLANT', (100.0, -10.0))],
            pipes=[[(0.0, -10.0), (0.0, 0.0)], [(0.0, 0.0), (100.0, 0.0)], [(100.0, 0.0), (100.0, -10.0)]],
            buildings={'B001': (0.0, -10.0), 'B002': (50.0, 110.0)},
        )

        assert {'B001', 'B002'} <= set(nodes['building'])
        assert {g.wkb for g in user_edges.geometry} <= {g.wkb for g in edges.geometry}
        assert nx.is_connected(graph)
        assert not any(500.0 <= x for x, _ in graph.nodes)  # far fragment not routed through

    def test_new_pipes_do_not_duplicate_existing_pipes(self):
        """New pipes join the existing network at its nodes, never alongside its pipes.

        The layout invites every duplicate: B002 is nearest to B001's service pipe (a
        connection onto it would split it); the trunk runs along a street from a node
        partway along it, and B003 sits beside it (a new pipe could follow the street from
        B003's street connection, beside the trunk); and the plant hangs off a node with
        nothing branching (the trunk and plant pipe could be merged into one new pipe).
        """
        user_edges, nodes, edges, graph = self._augment(
            self.SQUARE_STREETS,
            nodes=[('B001', 'CONSUMER', (50.0, -30.0)), ('NONE', 'NONE', (50.0, 0.0)),
                   ('NONE', 'NONE', (100.0, 0.0)), ('NONE', 'PLANT', (100.0, -10.0))],
            pipes=[[(50.0, -30.0), (50.0, 0.0)], [(50.0, 0.0), (100.0, 0.0)], [(100.0, 0.0), (100.0, -10.0)]],
            buildings={'B001': (50.0, -30.0), 'B002': (40.0, -20.0), 'B003': (70.0, -10.0)},
        )

        assert {'B001', 'B002', 'B003'} <= set(nodes['building'])
        existing = {g.wkb for g in user_edges.geometry}
        assert existing <= {g.wkb for g in edges.geometry}
        new_edges = [g for g in edges.geometry if g.wkb not in existing]
        assert all(user_edges.geometry.intersection(g).length.max() < 1e-6 for g in new_edges)
        assert nx.is_tree(graph)
        # B002 → street → NODE1 (30 m); B003 straight to NODE1, the trunk's nearer end
        assert sum(g.length for g in new_edges) == pytest.approx(30.0 + (20.0 ** 2 + 10.0 ** 2) ** 0.5)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
