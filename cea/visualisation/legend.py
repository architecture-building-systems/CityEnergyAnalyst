"""
Canonical legend layout used across CEA plots.

A horizontal legend below the plot area, so legend entries never overlap the
data when the plot is resized in the dashboard (Reports cards, react-grid
tiles) or stretched into a narrow column.

Use ``apply_legend_below(fig)`` from anywhere a Plotly figure is finalised
before being serialised to HTML. The new visualisation framework
(``cea/visualisation/*``) is the canonical home; the legacy
``cea/plots/base.py`` still imports from here while it is being phased out.
"""


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# Anchor the legend to the chart **container** (the full canvas) rather
# than the plot area. With ``yref='container'`` the legend's pixel
# position is stable when the plot area shrinks on dashboard resize —
# x-axis tick labels live in the bottom margin above the legend, and
# they can't be pushed onto the legend by a short plot area.
# Requires Plotly ≥ 5.10 (CEA ships Plotly 6).
LEGEND_BELOW = dict(
    orientation='h',
    yanchor='bottom',
    y=0.0,
    yref='container',
    xanchor='left',
    x=0,
    xref='container',
)


# Bottom margin = legend strip (~35 px) + just enough room for x-axis
# tick labels above it (~45 px). Plots with long angled tick labels
# (long building names, etc.) should set ``xaxis.automargin = True``
# so Plotly grows the margin as needed; this floor is the visual
# minimum, not a guarantee.
_MIN_BOTTOM_MARGIN_PX = 60


def apply_legend_below(fig):
    """Position the legend horizontally below the plot area.

    Anchored to the canvas via ``yref='container'`` so the legend's
    pixel position survives any subsequent ``Plotly.relayout`` call
    that resizes the plot area (the dashboard's ResizeObserver does
    exactly that).

    Idempotent — call after other ``update_layout`` calls that touch
    the legend; it overwrites the ``legend`` entry only. Bumps
    ``margin.b`` up to ``_MIN_BOTTOM_MARGIN_PX`` to leave room for both
    x-axis labels and the legend strip, but never shrinks a margin a
    caller has already set larger. No-op for figures without a legend
    (e.g. Sankey).
    """
    fig.update_layout(legend=dict(**LEGEND_BELOW))

    current_b = (fig.layout.margin.b if fig.layout.margin is not None else None)
    if current_b is None or current_b < _MIN_BOTTOM_MARGIN_PX:
        fig.update_layout(margin=dict(b=_MIN_BOTTOM_MARGIN_PX))

    return fig
