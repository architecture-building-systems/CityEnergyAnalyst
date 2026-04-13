"""
Unit tests for multi-phase thermal network reductions (decommissioning).

Covers the 'idle' action added when a building connected in an earlier phase
is dropped in a later phase. Verifies:
- validate_phases accepts reductions (previously raised ValueError)
- calculate_size_per_phase_cost / calculate_pre_size_cost emit 'idle' with
  preserved DN and zero cost for installed-then-decommissioned edges
- save_edges_timeline_csv, save_nodes_timeline_csv, save_phasing_summary,
  save_final_network_shapefiles emit the expected columns and values
- _validate_phase_graph catches orphaned consumers
"""

import os
import tempfile
from unittest.mock import MagicMock

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import LineString, Point

from cea.technologies.thermal_network.common.phasing import (
    _build_edge_maps,
    _canonical_edge_id,
    _validate_phase_graph,
    calculate_pre_size_cost,
    calculate_size_per_phase_cost,
    get_pipe_cost,
    load_pipe_costs,
    save_edges_timeline_csv,
    save_final_network_shapefiles,
    save_nodes_timeline_csv,
    save_phasing_summary,
    validate_phases,
)


CRS = 'EPSG:32632'


def _make_linear_phase(idx, year, name, buildings, edge_names):
    """Build a trivial linear network: PLANT -- B1 -- B2 -- B3 etc.

    Uses integer coordinates along the x axis, so each edge's canonical id
    is deterministic and stable across phases. Also populates the
    edge_name_to_cid / edge_cid_to_name maps that the real load_phases sets.
    """
    nodes = [{'name': 'PLANT', 'building': 'NONE', 'type': 'PLANT', 'geometry': Point(0, 0)}]
    for i, b in enumerate(buildings):
        nodes.append({
            'name': b, 'building': b, 'type': 'CONSUMER',
            'geometry': Point((i + 1) * 10, 0),
        })
    nodes_gdf = gpd.GeoDataFrame(nodes, crs=CRS)

    edges = []
    for i, en in enumerate(edge_names):
        edges.append({
            'name': en, 'type_mat': 'steel',
            'geometry': LineString([(i * 10, 0), ((i + 1) * 10, 0)]),
        })
    edges_gdf = gpd.GeoDataFrame(edges, crs=CRS)
    name_to_cid, cid_to_name = _build_edge_maps(edges_gdf)

    return {
        'index': idx,
        'name': f'phase{idx}',
        'year': year,
        'network_name': name,
        'network_type': 'DH',
        'buildings': sorted(buildings),
        'nodes_gdf': nodes_gdf,
        'edges_gdf': edges_gdf,
        'edge_name_to_cid': name_to_cid,
        'edge_cid_to_name': cid_to_name,
    }


def _cid_for(linear_phase_idx):
    """Canonical id for the edge at segment index i (0-based) in a linear phase."""
    start = (float(linear_phase_idx * 10), 0.0)
    end = (float((linear_phase_idx + 1) * 10), 0.0)
    # Match _canonical_edge_id's rounding precision exactly
    from cea.technologies.thermal_network.common.phasing import CANONICAL_EDGE_PRECISION
    a = (round(start[0], CANONICAL_EDGE_PRECISION), round(start[1], CANONICAL_EDGE_PRECISION))
    b = (round(end[0], CANONICAL_EDGE_PRECISION), round(end[1], CANONICAL_EDGE_PRECISION))
    return tuple(sorted((a, b)))


@pytest.fixture
def three_phase_reduction():
    """
    Three-phase scenario with progressive decommissioning:
      sub1: B1,B2,B3 (edges e1,e2,e3)
      sub2: B1,B2    (edges e1,e2)    — B3 decommissioned
      sub3: B1       (edges e1)       — B2 also decommissioned

    phase_results dicts are keyed by canonical edge id to mirror what
    read_phase_simulation_results produces in production.
    """
    phases = [
        _make_linear_phase(1, 2025, 'sub1', ['B1', 'B2', 'B3'], ['e1', 'e2', 'e3']),
        _make_linear_phase(2, 2050, 'sub2', ['B1', 'B2'], ['e1', 'e2']),
        _make_linear_phase(3, 2075, 'sub3', ['B1'], ['e1']),
    ]
    cid_e1, cid_e2, cid_e3 = _cid_for(0), _cid_for(1), _cid_for(2)
    phase_results = [
        {
            'edge_diameters': {cid_e1: 150, cid_e2: 100, cid_e3: 80},
            'edge_lengths':   {cid_e1: 100.0, cid_e2: 100.0, cid_e3: 100.0},
            'total_demand_kw': 1000,
        },
        {
            'edge_diameters': {cid_e1: 100, cid_e2: 80},
            'edge_lengths':   {cid_e1: 100.0, cid_e2: 100.0},
            'total_demand_kw': 700,
        },
        {
            'edge_diameters': {cid_e1: 80},
            'edge_lengths':   {cid_e1: 100.0},
            'total_demand_kw': 400,
        },
    ]
    return phases, phase_results


@pytest.fixture
def pipe_costs():
    return pd.DataFrame({
        'DN': [50, 80, 100, 150, 200, 250],
        'cost_per_m_eur': [100, 120, 150, 220, 280, 350],
    })


class TestPipeCostDatabase:
    """
    Pipe cost lookup must come from the scenario THERMAL_GRID.csv — no
    silent hardcoded fallbacks, no snapping to "largest available" when
    the simulation needs a bigger pipe.
    """

    def test_load_pipe_costs_missing_file_raises(self, tmp_path):
        class _Locator:
            def get_database_components_distribution_thermal_grid(self):
                return str(tmp_path / 'does_not_exist.csv')

        with pytest.raises(ValueError, match='THERMAL_GRID.csv not found'):
            load_pipe_costs(_Locator())

    def test_load_pipe_costs_missing_columns_raises(self, tmp_path):
        bad_path = tmp_path / 'THERMAL_GRID.csv'
        bad_path.write_text('some_col,other_col\n1,2\n')

        class _Locator:
            def get_database_components_distribution_thermal_grid(self):
                return str(bad_path)

        with pytest.raises(ValueError, match='missing required column'):
            load_pipe_costs(_Locator())

    def test_load_pipe_costs_happy_path(self, tmp_path):
        # Canonical schema in CEA's shipped databases:
        # pipe_DN (int mm) + Inv_USD2015perm (float USD2015 / m)
        good_path = tmp_path / 'THERMAL_GRID.csv'
        good_path.write_text(
            'pipe_DN,Inv_USD2015perm\n'
            '40,90\n'
            '65,140\n'
            '100,200\n'
        )

        class _Locator:
            def get_database_components_distribution_thermal_grid(self):
                return str(good_path)

        df = load_pipe_costs(_Locator())
        assert list(df['DN']) == [40, 65, 100]
        assert list(df['cost_per_m_eur']) == [90, 140, 200]

    def test_get_pipe_cost_rounds_up_to_next_available(self):
        df = pd.DataFrame({'DN': [40, 65, 100], 'cost_per_m_eur': [90, 140, 200]})
        # requested DN=50 → round up to 65
        assert get_pipe_cost(50, 100.0, df) == 140 * 100.0
        # exact match
        assert get_pipe_cost(100, 100.0, df) == 200 * 100.0
        # below smallest → round up to smallest
        assert get_pipe_cost(30, 100.0, df) == 90 * 100.0

    def test_get_pipe_cost_raises_on_oversize(self):
        df = pd.DataFrame({'DN': [40, 65, 100], 'cost_per_m_eur': [90, 140, 200]})
        with pytest.raises(ValueError, match='largest DN in the cost database is 100'):
            get_pipe_cost(150, 100.0, df)

    def test_shipped_databases_load(self):
        """
        Sanity: the THERMAL_GRID.csv shipped with every CEA region database
        must load without touching the fallback. Regression guard against
        schema drift (e.g. someone renaming Inv_USD2015perm).
        """
        import os as _os
        from cea.technologies.thermal_network.common.phasing import (
            THERMAL_GRID_DN_COL,
            THERMAL_GRID_COST_COL,
        )

        repo_root = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
        for region in ('CH', 'DE', 'SG'):
            path = _os.path.join(
                repo_root, 'databases', region, 'COMPONENTS', 'DISTRIBUTION', 'THERMAL_GRID.csv'
            )
            if not _os.path.exists(path):
                continue
            df = pd.read_csv(path)
            assert THERMAL_GRID_DN_COL in df.columns, (
                f'{region} THERMAL_GRID.csv is missing {THERMAL_GRID_DN_COL}. '
                f'Present: {list(df.columns)}'
            )
            assert THERMAL_GRID_COST_COL in df.columns, (
                f'{region} THERMAL_GRID.csv is missing {THERMAL_GRID_COST_COL}. '
                f'Present: {list(df.columns)}'
            )


class TestCanonicalEdgeIdentity:
    """Regression tests for the cross-phase name/geometry alignment bug.

    Each Part-1 run numbers its pipes independently from PIPE0. When two
    phases refer to the same physical pipe under different local names, the
    multi-phase engine must still recognise them as identical.
    """

    def _phase_with_renamed_edges(self, idx, year, name, buildings, edge_names, offset=0):
        """
        Build a phase where the nth edge spans x=10n..10(n+1), identical
        geometry across phases, but with a configurable name list so sub1's
        'e1' can become sub2's 'e2' (same pipe, different names).
        """
        return _make_linear_phase(idx, year, name, buildings, edge_names)

    def test_same_pipe_different_names_align_in_sizing(self, pipe_costs):
        """
        Phase 1 names its pipes [p1, p2, p3]. Phase 2 names the SAME first
        two physical pipes [q2, q3] (note the collision — q2 is not p2,
        but its geometry matches p1). The engine must treat p1 and q2 as
        the same edge via canonical id.
        """
        from cea.technologies.thermal_network.common.phasing import (
            get_all_edges_across_phases,
        )

        sub1 = self._phase_with_renamed_edges(1, 2025, 'sub1', ['B1', 'B2', 'B3'], ['p1', 'p2', 'p3'])
        sub2 = self._phase_with_renamed_edges(2, 2050, 'sub2', ['B1', 'B2'], ['q2', 'q3'])

        # Sanity: the literal name sets are disjoint (p1/p2/p3 vs q2/q3)
        assert set(sub1['edges_gdf']['name']).isdisjoint(set(sub2['edges_gdf']['name']))

        # But the canonical IDs for the first two pipes must match
        cid_p1 = sub1['edge_name_to_cid']['p1']
        cid_q2 = sub2['edge_name_to_cid']['q2']
        assert cid_p1 == cid_q2, 'Same geometry must produce the same canonical id across phases'

        # Simulated phase_results, keyed by canonical id (as production does)
        phase_results = [
            {
                'edge_diameters': {
                    sub1['edge_name_to_cid']['p1']: 150,
                    sub1['edge_name_to_cid']['p2']: 100,
                    sub1['edge_name_to_cid']['p3']: 80,
                },
                'edge_lengths':   {
                    sub1['edge_name_to_cid']['p1']: 100.0,
                    sub1['edge_name_to_cid']['p2']: 100.0,
                    sub1['edge_name_to_cid']['p3']: 100.0,
                },
                'total_demand_kw': 1000,
            },
            {
                'edge_diameters': {
                    sub2['edge_name_to_cid']['q2']: 100,
                    sub2['edge_name_to_cid']['q3']: 80,
                },
                'edge_lengths':   {
                    sub2['edge_name_to_cid']['q2']: 100.0,
                    sub2['edge_name_to_cid']['q3']: 100.0,
                },
                'total_demand_kw': 700,
            },
        ]

        all_edges = get_all_edges_across_phases(phase_results)
        # Expected: 3 unique canonical ids (p1/q2 collapse, p2/q3 collapse, p3 alone)
        assert len(all_edges) == 3

        # Build sizing decisions the production way
        phases = [sub1, sub2]
        decisions = {}
        for cid in all_edges:
            dn_per_phase = [pr['edge_diameters'].get(cid) for pr in phase_results]
            decisions[cid] = calculate_size_per_phase_cost(
                cid, dn_per_phase, phases, 100.0, pipe_costs, 1.5
            )

        # The first pipe (p1 / q2) is installed in phase 1 (DN=150) and
        # still flowing in phase 2 (required DN=100, kept at installed 150).
        cid_first = sub1['edge_name_to_cid']['p1']
        assert decisions[cid_first]['phase1']['action'] == 'install'
        assert decisions[cid_first]['phase1']['DN'] == 150
        assert decisions[cid_first]['phase2']['action'] == 'keep'
        assert decisions[cid_first]['phase2']['DN'] == 150  # installed DN preserved

        # The third pipe (p3, no q3 equivalent) is install → idle
        cid_third = sub1['edge_name_to_cid']['p3']
        assert decisions[cid_third]['phase1']['action'] == 'install'
        assert decisions[cid_third]['phase2']['action'] == 'idle'

        # Critically: total install cost should be 3 installs (not 5), because
        # p1/q2 and p2/q3 collapse. With the old name-keyed code, p1 would be
        # "install 150", q2 would be "install 100" (counted as a separate pipe),
        # giving 5 installs total. Canonical keying restores the correct 3.
        install_count = sum(
            1 for d in decisions.values()
            for phase_key in ('phase1', 'phase2')
            if phase_key in d and d[phase_key].get('action') == 'install'
        )
        assert install_count == 3, f'Expected 3 installs (one per canonical pipe), got {install_count}'


class TestValidatePhases:
    def test_reduction_is_accepted(self, three_phase_reduction):
        phases, _ = three_phase_reduction
        validate_phases(phases)  # must not raise

    def test_chronological_order_still_enforced(self, three_phase_reduction):
        phases, _ = three_phase_reduction
        phases[2]['year'] = 2020  # earlier than phase 1
        with pytest.raises(ValueError, match='chronological order'):
            validate_phases(phases)

    def test_orphaned_consumer_detected(self):
        good = _make_linear_phase(1, 2025, 'sub1', ['B1', 'B2'], ['e1', 'e2'])
        # Craft a phase where B2 is floating (no edges reach it)
        bad_nodes = gpd.GeoDataFrame([
            {'name': 'PLANT', 'building': 'NONE', 'type': 'PLANT', 'geometry': Point(0, 0)},
            {'name': 'B1', 'building': 'B1', 'type': 'CONSUMER', 'geometry': Point(10, 0)},
            {'name': 'B2', 'building': 'B2', 'type': 'CONSUMER', 'geometry': Point(100, 100)},
        ], crs=CRS)
        bad_edges = gpd.GeoDataFrame([
            {'name': 'e1', 'type_mat': 'steel', 'geometry': LineString([(0, 0), (10, 0)])},
        ], crs=CRS)
        bad = {
            'index': 2, 'name': 'phase2', 'year': 2050, 'network_name': 'sub2',
            'network_type': 'DH', 'buildings': ['B1', 'B2'],
            'nodes_gdf': bad_nodes, 'edges_gdf': bad_edges,
        }
        with pytest.raises(ValueError, match='not connected to any plant'):
            validate_phases([good, bad])


class TestSizingWithIdle:
    def test_leaf_decommissioning(self, three_phase_reduction, pipe_costs):
        """e3 serves only B3 → install → idle → idle; only phase-1 CAPEX."""
        phases, phase_results = three_phase_reduction
        cid_e3 = _cid_for(2)
        dn_per_phase = [pr['edge_diameters'].get(cid_e3) for pr in phase_results]
        decision = calculate_size_per_phase_cost(cid_e3, dn_per_phase, phases, 100.0, pipe_costs, 1.5)
        assert decision['phase1']['action'] == 'install'
        assert decision['phase2']['action'] == 'idle'
        assert decision['phase3']['action'] == 'idle'
        assert decision['phase2']['DN'] == 80  # installed DN preserved
        assert decision['phase3']['DN'] == 80
        assert decision['phase2']['cost'] == 0
        assert decision['phase3']['cost'] == 0

    def test_never_installed_then_installed_then_idle(self, pipe_costs):
        """Edge first appears mid-timeline, then goes idle."""
        phases = [
            _make_linear_phase(1, 2025, 'sub1', ['B1'], ['e1']),
            _make_linear_phase(2, 2050, 'sub2', ['B1', 'B2'], ['e1', 'e2']),
            _make_linear_phase(3, 2075, 'sub3', ['B1'], ['e1']),
        ]
        dn_per_phase = [None, 100, None]
        decision = calculate_size_per_phase_cost('e2', dn_per_phase, phases, 100.0, pipe_costs, 1.5)
        assert decision['phase1']['action'] == 'none'
        assert decision['phase1']['DN'] is None
        assert decision['phase2']['action'] == 'install'
        assert decision['phase3']['action'] == 'idle'
        assert decision['phase3']['DN'] == 100

    def test_reactivation_with_larger_dn_triggers_replace(self, pipe_costs):
        """install → idle → reactivate at larger DN → replace (not keep)."""
        phases = [_make_linear_phase(i, 2025 + 25 * (i - 1), f'sub{i}', ['B1'], ['e1']) for i in (1, 2, 3)]
        decision = calculate_size_per_phase_cost('e1', [150, None, 200], phases, 100.0, pipe_costs, 1.5)
        assert decision['phase1']['action'] == 'install'
        assert decision['phase2']['action'] == 'idle'
        assert decision['phase2']['DN'] == 150
        assert decision['phase3']['action'] == 'replace'
        assert decision['phase3']['DN'] == 200
        # Total cost = install(150) + replace(200) * 1.5
        assert decision['total_cost'] > decision['phase1']['cost']

    def test_reactivation_with_smaller_dn_keeps_existing(self, pipe_costs):
        """install → idle → reactivate at smaller DN → keep (sunk infra)."""
        phases = [_make_linear_phase(i, 2025 + 25 * (i - 1), f'sub{i}', ['B1'], ['e1']) for i in (1, 2, 3)]
        decision = calculate_size_per_phase_cost('e1', [150, None, 100], phases, 100.0, pipe_costs, 1.5)
        assert decision['phase2']['action'] == 'idle'
        assert decision['phase3']['action'] == 'keep'
        assert decision['phase3']['DN'] == 150  # keep the larger existing pipe
        assert decision['phase3']['cost'] == 0

    def test_pre_size_strategy_handles_idle(self, pipe_costs):
        """Pre-size-all installs at max DN, idle phases cost 0."""
        phases = [_make_linear_phase(i, 2025 + 25 * (i - 1), f'sub{i}', ['B1'], ['e1']) for i in (1, 2, 3)]
        decision = calculate_pre_size_cost('e1', [150, None, 200], phases, 200, 100.0, pipe_costs)
        assert decision['phase1']['action'] == 'install'
        assert decision['phase1']['DN'] == 200  # pre-sized
        assert decision['phase2']['action'] == 'idle'
        assert decision['phase2']['DN'] == 200
        assert decision['phase3']['action'] == 'keep'


class TestReporting:
    @pytest.fixture
    def tmp_dir(self, tmp_path):
        return str(tmp_path)

    @pytest.fixture
    def mock_locator(self, tmp_dir):
        class _Locator:
            def get_thermal_network_phasing_summary_file(self, nt, plan): return os.path.join(tmp_dir, 'summary.csv')
            def get_thermal_network_edges_timeline_file(self, nt, plan): return os.path.join(tmp_dir, 'edges_timeline.csv')
            def get_thermal_network_nodes_timeline_file(self, nt, plan): return os.path.join(tmp_dir, 'nodes_timeline.csv')
            def get_thermal_network_phasing_plan_layout_folder(self, nt, plan): return tmp_dir
            def get_thermal_network_phase_edges_shapefile(self, nt, plan, phase): return os.path.join(tmp_dir, f'edges_{phase}.shp')
            def get_thermal_network_phase_nodes_shapefile(self, nt, plan, phase): return os.path.join(tmp_dir, f'nodes_{phase}.shp')
        return _Locator()

    @pytest.fixture
    def sizing_decisions(self, three_phase_reduction, pipe_costs):
        phases, phase_results = three_phase_reduction
        decisions = {}
        for i, local_name in enumerate(('e1', 'e2', 'e3')):
            cid = _cid_for(i)
            dn_per_phase = [pr['edge_diameters'].get(cid) for pr in phase_results]
            decisions[cid] = calculate_size_per_phase_cost(
                cid, dn_per_phase, phases, 100.0, pipe_costs, 1.5
            )
        return decisions

    def test_phasing_summary_has_num_idle(self, three_phase_reduction, mock_locator, sizing_decisions, tmp_dir):
        phases, phase_results = three_phase_reduction
        save_phasing_summary(mock_locator, phases, phase_results, sizing_decisions, MagicMock(), 'DH', 'plan')
        df = pd.read_csv(os.path.join(tmp_dir, 'summary.csv'))
        assert list(df['num_idle']) == [0, 1, 2]
        assert list(df['num_installs']) == [3, 0, 0]
        assert df['total_cost_USD2015'].iloc[0] > 0
        assert df['total_cost_USD2015'].iloc[1] == 0
        assert df['total_cost_USD2015'].iloc[2] == 0

    def test_edges_timeline_emits_idle_rows(self, three_phase_reduction, mock_locator, sizing_decisions, tmp_dir):
        phases, phase_results = three_phase_reduction
        save_edges_timeline_csv(mock_locator, phases, phase_results, sizing_decisions, 'DH', 'plan')
        df = pd.read_csv(os.path.join(tmp_dir, 'edges_timeline.csv'))
        # e3 should have rows for all three phases
        e3 = df[df['edge_id'] == 'e3'].sort_values('phase')
        assert list(e3['action']) == ['install', 'idle', 'idle']
        assert list(e3['DN']) == [80.0, 80.0, 80.0]  # DN preserved during idle
        assert list(e3['cost_USD2015'])[1:] == [0.0, 0.0]

    def test_nodes_timeline_records_phase_last_seen(self, three_phase_reduction, mock_locator, tmp_dir):
        phases, _ = three_phase_reduction
        save_nodes_timeline_csv(mock_locator, phases, 'DH', 'plan')
        df = pd.read_csv(os.path.join(tmp_dir, 'nodes_timeline.csv'))
        assert df[df['building'] == 'B1']['phase_last_seen'].iloc[0] == 3
        assert df[df['building'] == 'B2']['phase_last_seen'].iloc[0] == 2
        assert df[df['building'] == 'B3']['phase_last_seen'].iloc[0] == 1

    def test_final_network_shapefile_includes_idle_edges(self, three_phase_reduction, mock_locator, sizing_decisions, tmp_dir):
        phases, phase_results = three_phase_reduction
        save_final_network_shapefiles(mock_locator, phases, phase_results, sizing_decisions, 'DH', 'plan')
        edges = gpd.read_file(os.path.join(tmp_dir, 'edges_timeline.shp'))
        assert len(edges) == 3  # Union, not just final-phase edges
        e3 = edges[edges['name'] == 'e3'].iloc[0]
        assert e3['idle_final'] == 1
        assert e3['ph_last'] == 1
        e1 = edges[edges['name'] == 'e1'].iloc[0]
        assert e1['idle_final'] == 0
        assert e1['ph_last'] == 3
