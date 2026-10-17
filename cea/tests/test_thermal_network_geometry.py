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
