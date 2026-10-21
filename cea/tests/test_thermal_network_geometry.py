"""Tests for thermal-network geometry helpers."""

import pandas as pd

from cea.technologies.thermal_network.common.geometry import remove_idle_branches


def _network(nodes, edges):
    """``nodes`` as {name: type}, ``edges`` as {name: (start, end)}."""
    node_df = pd.DataFrame({'type': nodes}).rename_axis('name')
    edge_df = pd.DataFrame(
        [(name, start, end) for name, (start, end) in edges.items()],
        columns=['name', 'start node', 'end node'],
    ).set_index('name')
    return node_df, edge_df


def test_idle_branches_are_removed_up_to_the_live_network():
    """A pipe chain ending at a junction (a demolished building's service line) carries no flow."""
    node_df, edge_df = _network(
        {'NODE0': 'PLANT', 'NODE1': 'NONE', 'NODE2': 'CONSUMER',
         'NODE3': 'NONE', 'NODE4': 'NONE'},
        {'PIPE0': ('NODE0', 'NODE1'), 'PIPE1': ('NODE1', 'NODE2'),
         'PIPE2': ('NODE1', 'NODE3'), 'PIPE3': ('NODE3', 'NODE4')},
    )

    nodes, edges, idle = remove_idle_branches(node_df, edge_df)

    assert sorted(idle) == ['PIPE2', 'PIPE3']
    assert list(edges.index) == ['PIPE0', 'PIPE1']
    assert sorted(nodes.index) == ['NODE0', 'NODE1', 'NODE2']


def test_networks_without_idle_branches_are_unchanged():
    node_df, edge_df = _network(
        {'NODE0': 'PLANT_hs_ww', 'NODE1': 'NONE', 'NODE2': 'CONSUMER', 'NODE3': 'CONSUMER'},
        {'PIPE0': ('NODE0', 'NODE1'), 'PIPE1': ('NODE1', 'NODE2'), 'PIPE2': ('NODE1', 'NODE3')},
    )

    nodes, edges, idle = remove_idle_branches(node_df, edge_df)

    assert idle == []
    pd.testing.assert_frame_equal(nodes, node_df)
    pd.testing.assert_frame_equal(edges, edge_df)


def test_idle_loop_with_one_connection_is_removed_but_a_bridge_between_live_nodes_stays():
    """A loop of junctions hanging off the network by one pipe serves nothing; junctions
    that join two live nodes may carry flow and stay."""
    node_df, edge_df = _network(
        {'NODE0': 'PLANT', 'NODE1': 'CONSUMER', 'NODE2': 'CONSUMER',
         'NODE3': 'NONE', 'NODE4': 'NONE', 'NODE5': 'NONE', 'NODE6': 'NONE'},
        {'PIPE0': ('NODE0', 'NODE1'), 'PIPE1': ('NODE0', 'NODE3'), 'PIPE2': ('NODE3', 'NODE4'),
         'PIPE3': ('NODE4', 'NODE5'), 'PIPE4': ('NODE5', 'NODE3'),
         'PIPE5': ('NODE0', 'NODE6'), 'PIPE6': ('NODE6', 'NODE2')},
    )

    nodes, edges, idle = remove_idle_branches(node_df, edge_df)

    assert set(idle) == {'PIPE1', 'PIPE2', 'PIPE3', 'PIPE4'}
    assert set(edges.index) == {'PIPE0', 'PIPE5', 'PIPE6'}
    assert set(nodes.index) == {'NODE0', 'NODE1', 'NODE2', 'NODE6'}


def test_idle_loop_joined_twice_to_the_same_live_node_is_removed():
    node_df, edge_df = _network(
        {'NODE0': 'PLANT', 'NODE1': 'CONSUMER', 'NODE2': 'NONE', 'NODE3': 'NONE'},
        {'PIPE0': ('NODE0', 'NODE1'), 'PIPE1': ('NODE0', 'NODE2'),
         'PIPE2': ('NODE2', 'NODE3'), 'PIPE3': ('NODE3', 'NODE0')},
    )

    _, edges, idle = remove_idle_branches(node_df, edge_df)

    assert set(idle) == {'PIPE1', 'PIPE2', 'PIPE3'}
    assert set(edges.index) == {'PIPE0'}
