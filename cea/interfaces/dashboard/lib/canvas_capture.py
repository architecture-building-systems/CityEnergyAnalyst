"""
Capture-on-Save helper for the Canvas Builder.

When the user promotes a draft canvas (``temp/<uuid>/`` →
``<name>/``), we want the saved folder to carry enough rendered
content for a recipient who imports a zip of it to actually *see*
the canvas — without needing the original CEA scenario directory or
a running backend.

The lazy strategy: walk every plot card in the canvas state, ask
``plot_dispatch.render_plot_html`` for its HTML, and write the
result to ``data/<cardId>/plot_<i>.html``. The folder is materialised
inside the **temp** folder before promote, so the subsequent
``shutil.move`` carries the data along to the saved canvas root.

Phase 6 scope:

- Plot-typed cards only. Map / KPI cards are skipped — capturing
  their state for a self-contained zip needs more thought (a static
  PNG of the map? a JSON dump of the KPI summary?) and isn't blocked
  by anything we ship today.
- One render per card per the canvas's dominant scenario:
    * inter-feature → the column's own scenario
    * inter-whatif  → the parent scenario
    * inter-scenario → first column's scenario
- Failures are logged and swallowed — a single broken card must not
  abort Save.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import cea.inputlocator

from .canvas_storage import CanvasState
from .plot_dispatch import render_plot_html


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


logger = logging.getLogger(__name__)


def capture_canvas_data(
    config,
    locator: cea.inputlocator.InputLocator,
    canvas_folder: str,
    canvas_state: CanvasState,
) -> None:
    """Render every plot card in ``canvas_state`` and write the
    resulting HTML into ``<canvas_folder>/data/<card_id>/``.

    Mutates ``config`` (project / scenario_name / parameters) for
    each card; the caller should snapshot ``config.scenario`` before
    calling and restore afterwards if the surrounding code path
    needs the original.

    Best-effort: per-card failures are logged but never raise.
    """
    project_root = os.path.dirname(locator.scenario)
    columns = canvas_state.canvas.columns
    parent_scenario = canvas_state.canvas.parent_scenario

    # ── Shared cards (launch / inter-scenario / inter-whatif) ──
    # These cards are rendered once per canvas using whichever
    # scenario best represents the dominant view: the parent for
    # inter-whatif, the first column otherwise. Capturing per-column
    # variations would require N renders per card and lives in a
    # later phase if it turns out to matter.
    shared_scenario = _pick_scenario(
        parent_scenario, columns, column_index=None
    )
    for card_id, card in canvas_state.feature_card.cards.items():
        _capture_card(
            config,
            locator,
            project_root,
            canvas_folder,
            card_id,
            card,
            shared_scenario,
        )

    # ── Per-column cards (inter-feature) ──────────────────────
    for col_idx_str, cards in canvas_state.feature_card.column_cards.items():
        column_scenario = _pick_scenario(
            parent_scenario, columns, column_index=col_idx_str
        )
        for card_id, card in cards.items():
            _capture_card(
                config,
                locator,
                project_root,
                canvas_folder,
                card_id,
                card,
                column_scenario,
            )


def _pick_scenario(
    parent_scenario: Optional[str],
    columns,
    column_index,
) -> Optional[str]:
    """Resolve which scenario to use when rendering a card.

    - If ``column_index`` is given (per-column card) and that column
      carries a ``scenario`` field, prefer it. Falls back to
      ``parent_scenario`` if the column has none (e.g. a feature
      column under inter-feature where the scenario is implicit).
    - Otherwise (shared card): ``parent_scenario`` first, then the
      first column's scenario as a last resort.
    """
    if column_index is not None:
        try:
            col = columns[int(column_index)]
            if col.scenario:
                return col.scenario
        except (IndexError, ValueError, TypeError):
            pass
    if parent_scenario:
        return parent_scenario
    if columns:
        first = columns[0]
        if getattr(first, 'scenario', None):
            return first.scenario
    return None


def _capture_card(
    config,
    locator: cea.inputlocator.InputLocator,
    project_root: str,
    canvas_folder: str,
    card_id: str,
    card,
    scenario: Optional[str],
) -> None:
    """Render every plot inside one card and dump the HTML."""
    if card.type != 'plot':
        # Map / KPI capture is a future phase. Skip cleanly so the
        # `data/<cardId>/` folder isn't created with nothing inside.
        return
    if not card.plots or not scenario:
        return

    data_folder = locator.get_canvas_card_data_folder(canvas_folder, card_id)
    os.makedirs(data_folder, exist_ok=True)

    scenario_path = os.path.join(project_root, scenario)
    for i, plot in enumerate(card.plots):
        script = plot.plot_config.get('script') if plot.plot_config else None
        params = plot.plot_config.get('parameters', {}) if plot.plot_config else {}
        if not script:
            continue
        try:
            html = render_plot_html(
                config,
                scenario_path=scenario_path,
                script_name=script,
                parameters=params,
            )
            out_path = os.path.join(data_folder, f'plot_{i}.html')
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(html)
        except Exception as exc:  # noqa: BLE001 — best-effort capture
            logger.warning(
                'Canvas data capture failed for card %s plot %d: %s',
                card_id, i, exc,
            )
