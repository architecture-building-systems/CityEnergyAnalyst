"""
Shared helpers for plot-side error rendering.

The Canvas Builder's `FeatureCardPlot` embeds the rendered HTML
inline, so error states are surfaced as small styled cards rather
than HTTP errors. The two main shapes:

- ``no_data_html`` — the upstream tool hasn't run for the scenario
  at all (no relevant input/output files exist). One-line message
  pointing at the tool to run.

- ``whatif_mismatch_html`` — the scenario *does* have data, just not
  for the requested what-if-name. Lists the column's available
  what-if-names so the user can pick one, plus run / remove
  options. Mirrors the front-end ``FeatureCardMap`` mismatch
  overlay so plot and map cards read consistently in compare
  mode.

`list_available_whatif_names` enumerates the folders the mismatch
overlay needs as alternatives. Each plot script supplies its own
predicate (which output file it considers "valid") rather than
duplicating the listdir/filter loop in every module.

All snippets share the calmer CEA card chrome — white surface, 1 px
subtle border, 3 px red left accent, no bold. Colours are
duplicated here rather than imported because Python's standard
library doesn't expose ``constants/theme.js``; keep these in sync
with the frontend palette in ``src/constants/theme.js``.
"""
import os
from html import escape
from typing import Callable, Iterable, Optional

from cea.visualisation.format.plot_colours import COLOURS_TO_RGB

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# All colours come from CEA's canonical palette so the overlay
# stays in family with bar charts, sankey colors, and map layer
# gradients. Each binding picks the closest existing entry — no
# new shades introduced.
CEA_PURPLE = COLOURS_TO_RGB['purple']
ERROR_RED = COLOURS_TO_RGB['red']
WARNING_AMBER = COLOURS_TO_RGB['yellow']
BORDER_SUBTLE = COLOURS_TO_RGB['background_grey']
TEXT_PRIMARY = COLOURS_TO_RGB['black']
TEXT_SECONDARY = COLOURS_TO_RGB['grey']
SYSTEM_FONT_STACK = (
    '-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif'
)


def _wrap_style() -> str:
    # Mirrors `errorStyle` in `src/features/canvas/components/CanvasPlot.jsx`
    # so backend-rendered error cards (this module) sit in the same
    # flex-centered position as frontend-rendered ones (`PlotError`,
    # `FeatureCardMap` mismatch overlay). Without this wrapper the
    # backend cards drop into default top-left flow and read very
    # differently from the map cards alongside them.
    return (
        'display:flex;align-items:center;justify-content:center;'
        'min-height:200px;padding:24px;box-sizing:border-box'
    )


def _card_style(accent: str = ERROR_RED) -> str:
    # `max-width:320px` matches the frontend `FeatureCardMap` /
    # `PlotError` cards so all error overlays share the same width.
    # `accent` is the left-edge accent stripe — `ERROR_RED` for
    # errors, `WARNING_AMBER` for soft warnings.
    return (
        f'max-width:320px;padding:12px 14px;border:1px solid {BORDER_SUBTLE};'
        f'border-left:3px solid {accent};border-radius:8px;'
        f'background:#fff;font-family:{SYSTEM_FONT_STACK}'
    )


def _title_style() -> str:
    return (
        f'font-size:13px;font-weight:500;color:{TEXT_PRIMARY};margin-bottom:4px'
    )


def _body_style() -> str:
    return f'font-size:12px;color:{TEXT_SECONDARY}'


def _accent(value: str, color: str = CEA_PURPLE) -> str:
    return f'<span style="color:{color}">{escape(str(value))}</span>'


def generic_error_html(*, title: str) -> str:
    """One-line error card for unexpected exceptions.

    Same chrome as the other helpers — kept generic so callers
    don't leak script-internal traceback details into the UI. Used
    when a plot script catches a non-data exception (data files
    exist but parsing / plotting blew up) and needs a calmer card
    than the dispatcher's raw 500.
    """
    return (
        f'<div style="{_wrap_style()}">'
        f'<div style="{_card_style()}">'
        f'<div style="{_title_style()}">{escape(title)}</div>'
        f'</div>'
        f'</div>'
    )


def warning_html(*, title: str, body: Optional[str] = None) -> str:
    """Soft-warning card (amber left accent) for cases where the
    plot can't render but the issue is *user input*, not missing
    data — e.g. "no what-if-name selected", "filter produced no
    rows". Distinct chrome from the red `generic_error_html` so the
    user can tell at a glance which class of problem they're
    looking at.
    """
    body_html = (
        f'<div style="{_body_style()}">{escape(body)}</div>' if body else ''
    )
    return (
        f'<div style="{_wrap_style()}">'
        f'<div style="{_card_style(WARNING_AMBER)}">'
        f'<div style="{_title_style()}">{escape(title)}</div>'
        f'{body_html}'
        f'</div>'
        f'</div>'
    )


def no_data_html(*, label: str, tool: str) -> str:
    """Generic "tool hasn't been run for this scenario" message.

    ``label`` is the human-facing data domain (e.g. ``'Final energy'``).
    ``tool`` is the human-readable feature label (e.g. ``'Energy by Carrier'``).
    """
    return (
        f'<div style="{_wrap_style()}">'
        f'<div style="{_card_style()}">'
        f'<div style="{_title_style()}">{escape(label)} data not found</div>'
        f'<div style="{_body_style()}">'
        f'Run {escape(tool)} for this scenario first.'
        f'</div>'
        f'</div>'
        f'</div>'
    )


def whatif_mismatch_html(
    *,
    scenario_name: str,
    whatif_name: str,
    label: str,  # noqa: ARG001 — kept for API symmetry with `no_data_html`.
    tool: str,
    available: Optional[Iterable[str]] = None,
) -> str:
    """Render the calmer mismatch error.

    Title is always *"what-if-name X not available in <scenario>"*.
    Bullets adapt to context:

    - "Pick from …" appears only when ``available`` is non-empty.
    - "Run <tool> for <whatif>" and "Remove this row" always appear.

    Falling back to a different shape (e.g. ``no_data_html``) when
    ``available`` is empty was confusing — every column then read
    "Final energy data not found" / "Plot data not found" with no
    obvious connection to the same condition rendered as a mismatch
    overlay in the column next to it. Single template keeps the
    visual story consistent.
    """
    available_list = [a for a in (available or []) if a]
    items = []
    if available_list:
        pick_from = ', '.join(_accent(name) for name in available_list)
        items.append(f'Pick from {pick_from}')
    items.append(f'Run {escape(tool)} for {_accent(whatif_name)}')
    items.append('Remove this row')
    bullets = ''.join(f'<li>{item}</li>' for item in items)
    return (
        f'<div style="{_wrap_style()}">'
        f'<div style="{_card_style()}">'
        f'<div style="{_title_style()}">'
        f'what-if-name {_accent(whatif_name)} not available in '
        f'{_accent(scenario_name)}'
        f'</div>'
        f'<ul style="margin:0;padding-left:18px;font-size:12px;'
        f'color:{TEXT_SECONDARY};line-height:1.5">'
        f'{bullets}'
        f'</ul>'
        f'</div>'
        f'</div>'
    )


# Shared what-if-name predicates. Each plot script picks the one
# matching its data dependency and passes it as
# ``has_data_for`` below. Defining them once here avoids the
# tendency for two scripts that read the same file (cost_sankey +
# cost_breakdown both read `costs/components.csv`) to grow
# divergent copies. Each predicate is a thin wrapper around an
# `InputLocator` accessor — no business logic.

def has_analysis_config(locator, whatif_name: str) -> bool:
    """True when the what-if's analysis configuration exists. Used
    by energy / LCA plot scripts."""
    return locator.find_analysis_configuration_file(whatif_name) is not None


def has_costs_components(locator, whatif_name: str) -> bool:
    """True when the what-if's `costs/components.csv` exists. Used
    by `cost_sankey` and `cost_breakdown`."""
    return os.path.exists(locator.get_costs_whatif_components_file(whatif_name))


def has_emissions_timeline(locator, whatif_name: str) -> bool:
    """True when the what-if's emissions timeline file exists. Used
    by `emission_timeline`."""
    return os.path.exists(locator.get_emissions_whatif_timeline_file(whatif_name))


def list_available_whatif_names(
    locator,
    has_data_for: Optional[Callable[[object, str], bool]] = None,
) -> list:
    """Direct subfolders of ``analysis_parent_folder`` that satisfy
    ``has_data_for(locator, name)``.

    Each plot script owns its own predicate — energy plots check for a
    valid analysis configuration, costs plots check for the costs
    components file, emissions plots check for the timeline file —
    so the differing "is this what-if-name valid" question stays
    out of this helper. When ``has_data_for`` is ``None`` every
    direct subfolder is returned (used by the dispatcher fallback,
    which doesn't know the per-script predicate).

    Best-effort: any filesystem hiccup (missing folder, permission
    error, deleted-mid-listdir entry) returns ``[]``.
    """
    try:
        base = locator.get_analysis_parent_folder()
        if not os.path.isdir(base):
            return []
        out = []
        for name in sorted(os.listdir(base)):
            if name.startswith('.'):
                continue
            if not os.path.isdir(os.path.join(base, name)):
                continue
            if has_data_for is None or has_data_for(locator, name):
                out.append(name)
        return out
    except OSError:
        return []
