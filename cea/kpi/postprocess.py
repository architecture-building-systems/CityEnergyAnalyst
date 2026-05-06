"""
Eager post-processing chain — fired by the dashboard's job runner
after a CEA tool finishes successfully.

The chain has three conceptual steps:

1. **result_summary**: re-run the per-feature aggregation when a
   KPI's source locator points at a result_summary-produced CSV.
   v1 KPIs all read from *raw* tool outputs (e.g.
   ``Total_demand.csv`` straight from ``cea demand``), so this
   step is a no-op for now and lives behind
   :func:`_features_needing_summary` — wire it in when a KPI's yml
   references a ``get_export_results_summary_*`` locator.
2. **invalidate**: drop the affected feature's rows from
   ``kpi_status.json`` so the next canvas read recomputes against
   the fresh upstream CSVs.
3. **pre-warm**: eagerly call :func:`compute_kpi_cached` for every
   KPI in the affected feature(s) so canvas reads are
   sub-millisecond on the common path. Best-effort —
   :class:`KPINotAvailable` and any other exception is caught and
   logged.

The lazy fallback in ``cache.py`` stays intact: even if this chain
is bypassed (CLI / batch / tests), the next canvas read still
self-heals via the three-hash gate. Eager just makes the common
path faster.

Tool → features mapping is intentionally narrow — only tools whose
outputs feed v1 KPIs are listed. Add entries as new features land.
"""

from __future__ import annotations

import logging
from typing import Iterable

from cea.kpi.cache import compute_kpi_cached
from cea.kpi.exceptions import KPIError
from cea.kpi.registry import kpis_for_feature, load_registry
from cea.kpi.status import clear_kpi

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

logger = logging.getLogger(__name__)

# Maps a CEA tool's script name (the value carried on
# ``JobInfo.script``) to the KPI features whose values become
# stale when that tool finishes. Multiple features per tool is
# fine — e.g. ``optimization-new`` re-runs both the optimisation
# costs and the optimisation emissions Pareto fronts.
#
# Add an entry when a new feature lands; missing tools fall
# through silently (no chain action), so this map is the single
# place to keep the wiring up-to-date.
TOOL_TO_FEATURES: dict[str, list[str]] = {
    # `cea demand` produces Total_demand.csv, which feeds both the
    # demand KPIs (EUI / peak / share) and the architecture KPIs
    # (GFA / conditioned share / roof area) — the floor-area
    # columns ride along on the same totals output.
    "demand": ["demand", "architecture"],
    "emissions": ["emissions"],
    "system-costs": ["costs"],
    "photovoltaic": ["solar"],
    "thermal-network-matrix": ["networks"],
    "optimization-new": ["optimisation"],
    "final-energy": ["final_energy"],
    # KPI feature name aligns with `result_summary.dict_plot_metrics_cea_feature`
    # (`heat_rejection`), so a future Phase 3b dispatcher can call
    # `result_summary --feature heat_rejection` without a translation
    # table.
    "anthropogenic-heat": ["heat_rejection"],
    # Stubs for additional solar-collector tools — uncomment when
    # their yml lands. Optimisation's "costs" linkage from the
    # original v1 plan was dropped because the Pareto outputs are
    # in their own folder, not the `get_baseline_costs` CSV that
    # `costs.yml` reads.
    # "photovoltaic-thermal": ["solar"],
    # "solar-collector": ["solar"],
}


def features_for_tool(tool_script: str) -> list[str]:
    """Return the KPI features affected by a tool finishing, or
    an empty list if the tool isn't mapped."""
    return list(TOOL_TO_FEATURES.get(tool_script, ()))


def run_post_tool_chain(
    scenario: str,
    tool_script: str,
    *,
    pre_warm: bool = True,
) -> None:
    """Fire the post-processing chain for a finished tool.

    Best-effort: any failure is logged and swallowed so the
    dashboard's job-completion path is never blocked. Callers do
    NOT need to wrap this in their own try/except.

    ``pre_warm=False`` skips step 3 — useful in tests where the
    eager cache fill would mask the on-demand recompute being
    exercised.
    """
    try:
        features = features_for_tool(tool_script)
        if not features:
            return

        for feature in features:
            try:
                clear_kpi(scenario, feature=feature)
            except Exception:
                logger.warning(
                    "kpi.invalidate failed for feature=%s scenario=%s",
                    feature,
                    scenario,
                    exc_info=True,
                )

        if pre_warm:
            for feature in features:
                _pre_warm_feature(scenario, feature)
    except Exception:
        # Catch-all so a bug here can never break job-success
        # reporting. The lazy fallback in cache.py still works.
        logger.warning(
            "kpi.run_post_tool_chain failed for tool=%s scenario=%s",
            tool_script,
            scenario,
            exc_info=True,
        )


def _pre_warm_feature(scenario: str, feature: str) -> None:
    """Eagerly compute every KPI in ``feature`` so the cache is
    populated before the next canvas read. Per-KPI failures are
    swallowed — :class:`KPINotAvailable` is the common case (the
    upstream tool ran but didn't produce every CSV the feature
    needs)."""
    for kpi in kpis_for_feature(feature):
        try:
            compute_kpi_cached(kpi.id, scenario)
        except KPIError:
            # Definition errors / not-available — both expected;
            # not-available will be reported to the frontend on
            # the next read.
            logger.debug(
                "pre-warm skipped %s (KPI error)", kpi.id, exc_info=True
            )
        except Exception:
            logger.warning(
                "pre-warm failed for %s on %s",
                kpi.id,
                scenario,
                exc_info=True,
            )


def _features_needing_summary(features: Iterable[str]) -> list[str]:
    """Reserved for the result_summary integration step. Returns
    the subset of ``features`` whose KPIs reference a
    result_summary-produced locator (``get_export_results_summary_*``).

    v1 returns ``[]`` because every demand KPI reads from
    ``get_total_demand`` directly. When a yml entry first cites a
    summary locator, this helper picks it up automatically and the
    caller can dispatch ``result_summary --feature <feature>``
    accordingly.
    """
    registry = load_registry()
    summary_features = []
    for feature in features:
        for kpi in registry.values():
            if kpi.category != feature:
                continue
            if kpi.source.locator.startswith("get_export_results_summary"):
                summary_features.append(feature)
                break
    return summary_features
