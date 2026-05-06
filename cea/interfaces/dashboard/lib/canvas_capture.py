"""
Capture-on-Share helper for the Canvas Builder.

When the user clicks Share, we want the exported zip to carry
enough rendered content for a recipient who imports it to actually
*see* the canvas — without needing the original CEA scenario
directory or a running backend.

The lazy strategy: walk every plot card in the canvas state, ask
``plot_dispatch.render_plot_html`` for its HTML, and write the
result to ``<canvas_folder>/data/<cardId>/plot_<i>.html`` directly
under the saved canvas root. The zip-export pass picks up that
directory tree as-is.

Coverage today:

- **Plot cards** → ``data/<cardId>/plot_<i>.html`` per embedded plot.
  This is what gets rendered in the recipient's browser — a fully
  self-contained Plotly figure that doesn't need the CEA backend to
  view (Plotly's CDN handles the JS).
- **Map / KPI cards** → ``data/<cardId>/card.json`` with the card's
  config snapshot (type, feature, category, layer, scenario). A
  proper server-side render for these (deck.gl PNG for maps, KPI
  summary JSON for KPIs) is a future pass; the metadata at least
  documents what was on the canvas so a viewer-without-backend can
  show a labelled placeholder rather than a blank slot.

Scenario resolution per card:
    * inter-feature → the column's own scenario
    * inter-whatif  → the parent scenario
    * inter-scenario → first column's scenario

Failures are logged and swallowed — a single broken card must not
abort the export.
"""

from __future__ import annotations

import html as html_lib
import json
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
    """Materialise a card's data folder.

    - Plot cards: render every embedded plot to its own HTML file.
    - Map / KPI cards: write a small ``card.json`` capturing the
      card's config + the scenario context so a future viewer that
      doesn't have a CEA backend handy can at least describe what
      was on the canvas. Server-side rendering of these card types
      (a deck.gl PNG snapshot for maps, a JSON dump of the KPI
      summary) is a follow-up; this gives the recipient something
      structured to chew on instead of an empty folder.
    """
    if card.type == 'plot':
        _capture_plot_card(
            config, locator, project_root, canvas_folder,
            card_id, card, scenario,
        )
        return

    if card.type == 'kpi':
        # KPI cards: write the metadata stub AND a value snapshot
        # (kpi.json) + standalone HTML viewer (kpi.html) so a
        # recipient unzipping the archive sees the value the user
        # saw at export time, even without a backend handy.
        _capture_card_metadata(
            locator, canvas_folder, card_id, card, scenario,
        )
        _capture_kpi_card(
            project_root, locator, canvas_folder, card_id, card, scenario,
        )
        return

    if card.type == 'map':
        _capture_card_metadata(
            locator, canvas_folder, card_id, card, scenario,
        )
        return

    # Unknown card type — log and skip rather than crash the export.
    logger.debug('Skipping data capture for card %s (type=%r)',
                 card_id, card.type)


def _capture_plot_card(
    config,
    locator: cea.inputlocator.InputLocator,
    project_root: str,
    canvas_folder: str,
    card_id: str,
    card,
    scenario: Optional[str],
) -> None:
    """Render every plot inside one plot card and dump the HTML."""
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


def _capture_card_metadata(
    locator: cea.inputlocator.InputLocator,
    canvas_folder: str,
    card_id: str,
    card,
    scenario: Optional[str],
) -> None:
    """Write a JSON snapshot of a non-plot card's config.

    The schema mirrors the card's ``feature_card.yml`` entry plus a
    ``scenario`` field so a viewer (now or later) has everything
    needed to look up the right backend resources without having
    to re-resolve the column → scenario mapping itself.
    """
    data_folder = locator.get_canvas_card_data_folder(canvas_folder, card_id)
    os.makedirs(data_folder, exist_ok=True)
    payload = {
        'type': card.type,
        'feature': card.feature,
        'category': card.category,
        'layer': card.layer,
        'scenario': scenario,
        # `kpi_id` is `None` for non-KPI cards. Including it
        # unconditionally keeps the schema uniform across card
        # types so recipients can read `card.json` without
        # branching on `type` first.
        'kpi_id': getattr(card, 'kpi_id', None),
    }
    out_path = os.path.join(data_folder, 'card.json')
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, sort_keys=True)
    except OSError as exc:
        logger.warning(
            'Failed to write metadata for card %s: %s', card_id, exc,
        )


def _capture_kpi_card(
    project_root: str,
    locator: cea.inputlocator.InputLocator,
    canvas_folder: str,
    card_id: str,
    card,
    scenario: Optional[str],
) -> None:
    """Snapshot a KPI card's current value to ``kpi.json`` + a
    standalone ``kpi.html`` viewer.

    Goes through ``cea.kpi.cache.compute_kpi_cached`` so the
    snapshot reads the same hash-gated value the canvas just
    rendered (cache hit on the typical "share immediately after
    viewing" path; lazy recompute fallback on the rare miss).
    Best-effort: a failure to compute leaves the metadata
    ``card.json`` in place — the recipient still sees what KPI
    was on the canvas, just without the value.
    """
    kpi_id = getattr(card, 'kpi_id', None)
    if not kpi_id or not scenario:
        return

    scenario_path = os.path.join(project_root, scenario)
    data_folder = locator.get_canvas_card_data_folder(canvas_folder, card_id)
    os.makedirs(data_folder, exist_ok=True)

    # Lazy import — keeps `canvas_capture` importable in test envs
    # that haven't pulled in the KPI registry yet.
    try:
        from cea.kpi.cache import compute_kpi_cached
        from cea.kpi.exceptions import KPIError
    except ImportError as exc:  # pragma: no cover — defensive
        logger.warning(
            'KPI module unavailable for card %s: %s', card_id, exc,
        )
        return

    try:
        result = compute_kpi_cached(kpi_id, scenario_path)
    except KPIError as exc:
        logger.info(
            'KPI %s not available at export time for card %s: %s',
            kpi_id, card_id, exc,
        )
        return
    except Exception as exc:  # noqa: BLE001 — best-effort capture
        logger.warning(
            'KPI capture failed for card %s (%s): %s',
            card_id, kpi_id, exc,
        )
        return

    payload = {
        'kpi_id': kpi_id,
        'value': result.value,
        'unit': result.unit,
        'computed_at': result.computed_at,
        'scenario': scenario,
    }
    json_path = os.path.join(data_folder, 'kpi.json')
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, sort_keys=True)
    except OSError as exc:
        logger.warning(
            'Failed to write kpi.json for card %s: %s', card_id, exc,
        )

    html_path = os.path.join(data_folder, 'kpi.html')
    try:
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(_render_kpi_html(payload))
    except OSError as exc:
        logger.warning(
            'Failed to write kpi.html for card %s: %s', card_id, exc,
        )


def _render_kpi_html(payload: dict) -> str:
    """Render a KPI snapshot as a small standalone HTML page.

    Intentionally chrome-less and self-contained — no external CSS
    or fonts so the recipient can open the file directly from the
    unzipped archive without a server. Mirrors the on-canvas
    `FeatureCardKpi` shape (label / big value / unit / footer).
    """
    kpi_id = html_lib.escape(str(payload.get('kpi_id') or ''))
    value = payload.get('value')
    value_str = (
        format(value, '.4g') if isinstance(value, (int, float)) else '—'
    )
    unit = html_lib.escape(str(payload.get('unit') or ''))
    computed_at = html_lib.escape(str(payload.get('computed_at') or ''))
    feature, _, short = kpi_id.partition('.')
    feature_display = feature.title() if feature else ''
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>KPI · {kpi_id}</title>
<style>
  body {{ margin: 0; padding: 24px; font: 14px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f7f7f7; color: #222; }}
  .card {{ background: #fff; border: 1px solid #e8e8e8; border-radius: 12px; padding: 16px 20px; max-width: 320px; }}
  .label {{ font-size: 11px; color: #666; font-weight: 500; }}
  .feature {{ color: #888; }}
  .dot {{ color: #bbb; margin: 0 4px; }}
  .value {{ font-size: 32px; font-weight: 700; line-height: 1.1; margin-top: 6px; font-variant-numeric: tabular-nums; }}
  .unit {{ font-size: 12px; color: #666; margin-top: 2px; }}
  .footer {{ font-size: 10px; color: #999; margin-top: 12px; }}
</style>
</head>
<body>
  <div class="card">
    <div class="label">
      <span class="feature">{feature_display}</span>
      <span class="dot">·</span>
      <span>{short}</span>
    </div>
    <div class="value">{value_str}</div>
    <div class="unit">{unit}</div>
    <div class="footer">Captured {computed_at}</div>
  </div>
</body>
</html>
"""
