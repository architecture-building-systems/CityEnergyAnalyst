"""
One vertical scale for a batch of Sankey figures, so the same flow draws at the
same pixel width in every figure of the batch.

Plotly's Sankey (d3-sankey) lays out each column of nodes in the plot area and
picks a single vertical scale per figure::

    ky = min over columns of (H - (n - 1) * pad) / sum(node values)

where ``H`` is the plot-area height, ``n`` the column's node count and a node's
value is the larger of its inflow and outflow; a link is ``value * ky`` pixels
wide. It also caps the padding at ``2/3 * H / (max_n - 1)``. To give a figure a
chosen scale ``px`` (pixels per unit), its plot area must therefore be exactly
the tallest column at that scale, with a padding small enough that the cap does
not bite -- otherwise Plotly shrinks the padding itself and the scale drifts.

The batch scale is the largest one that keeps every figure within
``MAX_FIGURE_HEIGHT``, unless that leaves the smallest figure below
``MIN_FIGURE_HEIGHT`` (illegible); the minimum wins. Heights here are whole
figures: plot area plus the layout's top and bottom margins.

The canvas re-applies the same rule across compare columns from the scale data
:func:`apply_scale` stores in ``layout.meta`` (see the GUI's ``sankeyScale.js``).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Sequence, Tuple

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

MIN_FIGURE_HEIGHT = 250
MAX_FIGURE_HEIGHT = 750
NODE_PAD = 24
# Plotly caps node padding at this share of H / (max_n - 1).
_PLOTLY_PAD_RATIO = 2 / 3

# (sum of node values, node count) per node column.
Extents = List[Tuple[float, int]]


def column_extents(sankey_data: dict) -> Extents:
    """Per-column node totals and counts, grouping nodes by their ``x`` position.

    Every node with flow counts towards its column's padding, including the
    transparent pass-through nodes the Sankey builders add for alignment. Nodes
    without any link are left out, as Plotly leaves them out of its layout.
    """
    inflow: Dict[int, float] = defaultdict(float)
    outflow: Dict[int, float] = defaultdict(float)
    for source, target, value in zip(sankey_data['source'], sankey_data['target'], sankey_data['value']):
        outflow[source] += value
        inflow[target] += value

    columns: Dict[float, List[float]] = defaultdict(list)
    for node, x in enumerate(sankey_data['node_x']):
        node_value = max(inflow[node], outflow[node])
        if node_value > 0:
            columns[round(float(x), 6)].append(node_value)
    return [(sum(values), len(values)) for _, values in sorted(columns.items())]


def column_extents_of(fig) -> Extents:
    """:func:`column_extents` of a built Sankey figure."""
    trace = fig.data[0]
    return column_extents({
        'source': list(trace.link.source),
        'target': list(trace.link.target),
        'value': list(trace.link.value),
        'node_x': list(trace.node.x),
    })


def node_pad(extents: Extents, px_per_unit: float, pad: float = NODE_PAD) -> float:
    """The padding to give the figure so Plotly's padding cap leaves it unchanged."""
    max_n = max((n for _, n in extents), default=1)
    if max_n <= 1:
        return pad
    # The cap is p <= 2/3 * H(p) / (max_n - 1) with H(p) = max_j(a_j + (n_j - 1) p);
    # solved per column j for the largest p that satisfies it.
    k = _PLOTLY_PAD_RATIO / (max_n - 1)
    fits = max(k * total * px_per_unit / (1 - k * (n - 1)) for total, n in extents)
    return min(pad, fits)


def plot_height(extents: Extents, px_per_unit: float, pad: float = NODE_PAD) -> float:
    """Plot-area height that makes Plotly draw the figure at ``px_per_unit``."""
    p = node_pad(extents, px_per_unit, pad)
    return max((total * px_per_unit + (n - 1) * p for total, n in extents), default=0.0)


def _px_for_plot_height(extents: Extents, target: float, pad: float) -> float:
    """Inverse of :func:`plot_height` (which grows monotonically with the scale)."""
    low, high = 0.0, 1.0
    while plot_height(extents, high, pad) < target:
        high *= 2
    for _ in range(60):
        mid = (low + high) / 2
        if plot_height(extents, mid, pad) < target:
            low = mid
        else:
            high = mid
    return high


def shared_px_per_unit(
    figures: Sequence[Tuple[Extents, float]],
    min_height: float = MIN_FIGURE_HEIGHT,
    max_height: float = MAX_FIGURE_HEIGHT,
    pad: float = NODE_PAD,
) -> float:
    """The batch scale: the largest that keeps every figure within ``max_height``,
    raised if needed so the smallest reaches ``min_height`` (the minimum wins).

    :param figures: ``(extents, margins)`` per figure, ``margins`` being the layout's
        top + bottom margin in pixels.
    """
    figures = [(extents, margins) for extents, margins in figures if extents]
    if not figures:
        return 0.0
    largest_within_max = min(_px_for_plot_height(e, max_height - m, pad) for e, m in figures)
    smallest_reaching_min = max(_px_for_plot_height(e, min_height - m, pad) for e, m in figures)
    return max(largest_within_max, smallest_reaching_min)


def vertical_margins(fig) -> float:
    margin = fig.layout.margin
    return (margin.t or 0) + (margin.b or 0)


def apply_scale(fig, extents: Extents, px_per_unit: float, unit: str, pad: float = NODE_PAD) -> None:
    """Size ``fig`` to draw at ``px_per_unit``, and record the scale inputs in
    ``layout.meta`` so the canvas can rescale it against other compare columns."""
    fig.update_traces(node_pad=node_pad(extents, px_per_unit, pad))
    fig.update_layout(
        height=round(plot_height(extents, px_per_unit, pad) + vertical_margins(fig)),
        autosize=False,
        meta={'sankey_scale': {
            'columns': [[total, n] for total, n in extents],
            'pad': pad,
            'unit': unit,
        }},
    )


def scale_figures(figures, unit: str, pad: float = NODE_PAD) -> None:
    """Give every Sankey in ``figures`` (a batch shown together) one shared scale."""
    extents = [column_extents_of(fig) for fig in figures]
    px = shared_px_per_unit([(e, vertical_margins(fig)) for e, fig in zip(extents, figures)], pad=pad)
    for fig, e in zip(figures, extents):
        apply_scale(fig, e, px, unit, pad)
