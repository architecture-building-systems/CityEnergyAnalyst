"""Shared Sankey scale: the same flow draws at the same pixel width in every figure of a batch.

`_plotly_px_per_unit` restates Plotly's own Sankey layout (d3-sankey, as shipped in plotly.js):
the scale is min over columns of (H - (n - 1) * pad) / column total, with the padding capped at
2/3 * H / (max_n - 1). Checked against Plotly in headless Chrome when this module was written.
"""

import plotly.graph_objects as go
import pytest

from cea.visualisation.special.sankey_scale import (
    MAX_FIGURE_HEIGHT,
    MIN_FIGURE_HEIGHT,
    NODE_PAD,
    apply_scale,
    column_extents,
    node_pad,
    plot_height,
    scale_figures,
    shared_px_per_unit,
)


def _plotly_px_per_unit(extents, plot_h, pad):
    max_n = max(n for _, n in extents)
    if max_n > 1:
        pad = min(pad, 2 / 3 * plot_h / (max_n - 1))
    return min((plot_h - (n - 1) * pad) / total for total, n in extents)


def _sankey(values, node_x):
    """Two-column Sankey: one source node per value, all flowing into a single sink."""
    sink = len(values)
    return {"source": list(range(len(values))), "target": [sink] * len(values),
            "value": list(values), "node_x": list(node_x)}


def _figure(values, margins=(80, 60)):
    data = _sankey(values, [0.01] * len(values) + [0.99])
    fig = go.Figure(go.Sankey(node=dict(x=data["node_x"], pad=NODE_PAD),
                              link=dict(source=data["source"], target=data["target"], value=data["value"])))
    fig.update_layout(margin=dict(t=margins[0], b=margins[1]))
    return fig


def test_column_extents_take_each_nodes_larger_side_and_count_pass_throughs():
    # 0 -> 1 (pass-through) -> 2, plus 0 -> 2 directly: node 1 sits alone in the middle column.
    data = {"source": [0, 1, 0], "target": [1, 2, 2], "value": [5, 5, 3], "node_x": [0.0, 0.5, 1.0]}
    assert column_extents(data) == [(8, 1), (5, 1), (8, 1)]


def test_column_extents_leave_out_nodes_without_links_as_plotly_does():
    data = {"source": [0], "target": [1], "value": [5], "node_x": [0.0, 1.0, 0.0]}
    assert column_extents(data) == [(5, 1), (5, 1)]


@pytest.mark.parametrize("values", [[10, 20, 5], [1, 1, 1, 1, 1, 1], [100]])
@pytest.mark.parametrize("px", [0.05, 1.0, 12.0])
def test_plot_height_makes_plotly_draw_at_the_requested_scale(values, px):
    extents = column_extents(_sankey(values, [0.01] * len(values) + [0.99]))
    h = plot_height(extents, px)
    assert _plotly_px_per_unit(extents, h, node_pad(extents, px)) == pytest.approx(px)


def test_short_figures_lower_the_padding_so_plotlys_cap_does_not_change_the_scale():
    # Many tiny nodes: at 24 px padding Plotly would cap the padding and redraw at a larger scale.
    extents = [(6.0, 6), (6.0, 1)]
    pad = node_pad(extents, 0.5)
    assert pad < NODE_PAD
    assert _plotly_px_per_unit(extents, plot_height(extents, 0.5), pad) == pytest.approx(0.5)


def _heights(figures, px):
    return [plot_height(e, px) + m for e, m in figures]


def test_the_tallest_figure_is_capped_when_the_smallest_stays_legible():
    figures = [(column_extents(_sankey([100, 50], [0, 0, 1])), 140),
               (column_extents(_sankey([60, 30], [0, 0, 1])), 140)]
    heights = _heights(figures, shared_px_per_unit(figures))
    assert max(heights) == pytest.approx(MAX_FIGURE_HEIGHT)
    assert min(heights) >= MIN_FIGURE_HEIGHT


def test_the_minimum_height_wins_over_the_maximum():
    figures = [(column_extents(_sankey([1000], [0, 1])), 140),
               (column_extents(_sankey([1], [0, 1])), 140)]
    heights = _heights(figures, shared_px_per_unit(figures))
    assert min(heights) == pytest.approx(MIN_FIGURE_HEIGHT)
    assert max(heights) > MAX_FIGURE_HEIGHT


def test_scale_figures_gives_a_batch_one_scale_and_records_it():
    figs = [_figure([300, 100]), _figure([40, 10, 10])]

    scale_figures(figs, "MWh")

    scales = []
    for fig in figs:
        extents = [tuple(c) for c in fig.layout.meta["sankey_scale"]["columns"]]
        plot_h = fig.layout.height - fig.layout.margin.t - fig.layout.margin.b
        scales.append(_plotly_px_per_unit(extents, plot_h, fig.data[0].node.pad))
        assert fig.layout.meta["sankey_scale"]["unit"] == "MWh"
        assert fig.layout.height >= MIN_FIGURE_HEIGHT
    # Heights are whole pixels, so the scales agree to within rounding.
    assert scales[0] == pytest.approx(scales[1], rel=0.01)


def test_apply_scale_sets_an_exact_height_and_the_meta():
    fig = _figure([10, 20])
    extents = column_extents(_sankey([10, 20], [0.01, 0.01, 0.99]))

    apply_scale(fig, extents, 4.0, "kUSD")

    assert fig.layout.height == round(plot_height(extents, 4.0) + 140)
    assert fig.layout.meta["sankey_scale"] == {"columns": [[30, 2], [30, 1]], "pad": NODE_PAD, "unit": "kUSD"}
