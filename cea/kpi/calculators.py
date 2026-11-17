"""
Recursive evaluator for the formula tree carried in a KPI yml entry.

Every yml leaf produces a ``pandas.Series`` (one value per row of
the source CSV); inner nodes consume children and return either a
Series or a scalar. The root must produce a scalar — that's the
KPI value the resolver reports back to the API.

Adding a new node kind is a four-step change:

1. add a ``Literal["my_kind"]``-typed pydantic model in
   ``schema.py`` and include it in the ``FormulaNode`` union;
2. add a branch in :func:`evaluate` here;
3. add the column-validation hook in :func:`columns_referenced` so
   the registry catches typos at load;
4. document the new shape in ``schema.py``'s module docstring.

Keep the set small — every new kind is forever, every yml author
has to learn it. v1 ships with ``column``, ``sum_columns``,
``aggregate``, ``divide``, ``share_of`` and ``pv_analytics`` (the
summary's annual PV analytics, computed by the summary's code).
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from cea.analysis.final_energy.pv_analytics import calc_pv_analytics_by_period, district_pv_series
from cea.kpi.exceptions import KPIDefinitionError, KPINotAvailable

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def evaluate(node, df: pd.DataFrame, *, kpi_id: str):
    """Walk a formula node, returning a Series or a scalar.

    ``kpi_id`` is only used to enrich error messages — the
    evaluator itself is stateless across KPIs.
    """
    kind = node.kind
    if kind == "column":
        return _read_column(df, node.name, kpi_id=kpi_id)

    if kind == "sum_columns":
        cols = [_read_column(df, c, kpi_id=kpi_id) for c in node.columns]
        # Concat → row-wise sum keeps NaN handling consistent with
        # ``pandas.DataFrame[columns].sum(axis=1)`` (NaN treated as 0).
        return pd.concat(cols, axis=1).sum(axis=1)

    if kind == "aggregate":
        series = evaluate(node.of, df, kpi_id=kpi_id)
        if not isinstance(series, pd.Series):
            raise KPIDefinitionError(
                f"{kpi_id}: 'aggregate' expects a Series, got {type(series).__name__}"
            )
        op = node.op
        if op == "sum":
            scalar = float(series.sum())
        elif op == "max":
            scalar = float(series.max())
        elif op == "min":
            scalar = float(series.min())
        elif op == "mean":
            scalar = float(series.mean())
        else:
            raise KPIDefinitionError(f"{kpi_id}: unknown aggregate op '{op}'")
        # `scale` is an optional unit-conversion factor (defaults
        # to 1.0). Lets a yml entry express "tons → kg" or
        # "MWh → kWh" without forcing an artificial denominator
        # via `divide`.
        return scalar * float(getattr(node, "scale", 1.0))

    if kind == "divide":
        num = evaluate(node.numerator, df, kpi_id=kpi_id)
        den = evaluate(node.denominator, df, kpi_id=kpi_id)
        num_s = _as_scalar(num, kpi_id, "divide.numerator")
        den_s = _as_scalar(den, kpi_id, "divide.denominator")
        if den_s == 0:
            # Genuine zero denominator (e.g. zero GFA in an empty
            # scenario) — surface as not-available rather than
            # returning inf / NaN.
            raise KPINotAvailable(
                kpi_id, reason="zero denominator in divide"
            )
        return float(num_s / den_s) * float(node.scale)

    if kind == "share_of":
        part = _as_scalar(
            evaluate(node.part, df, kpi_id=kpi_id), kpi_id, "share_of.part"
        )
        whole = _as_scalar(
            evaluate(node.whole, df, kpi_id=kpi_id), kpi_id, "share_of.whole"
        )
        if whole == 0:
            raise KPINotAvailable(kpi_id, reason="zero whole in share_of")
        return float(part / whole) * 100.0

    if kind == "pv_analytics":
        return _pv_analytics(node.metric, df, kpi_id=kpi_id)

    raise KPIDefinitionError(f"{kpi_id}: unknown formula kind '{kind}'")


def columns_referenced(node) -> Iterable[str]:
    """Yield every column name the formula reads — registry uses
    this to validate against ``schemas.yml`` at load time so typos
    fail fast instead of at request time."""
    kind = node.kind
    if kind == "column":
        yield node.name
    elif kind == "sum_columns":
        yield from node.columns
    elif kind == "aggregate":
        yield from columns_referenced(node.of)
    elif kind == "divide":
        yield from columns_referenced(node.numerator)
        yield from columns_referenced(node.denominator)
    elif kind == "share_of":
        yield from columns_referenced(node.part)
        yield from columns_referenced(node.whole)
    elif kind == "pv_analytics":
        yield from _PV_ANALYTICS_COLUMNS
    else:
        raise KPIDefinitionError(f"unknown formula kind '{kind}'")


# ── Helpers ─────────────────────────────────────────────────────────


_PV_ANALYTICS_COLUMNS = ("date", "PV_kWh", "GRID_kWh")
# metric -> (summary column, the series whose total is its denominator)
_PV_ANALYTICS_METRICS = {
    "generation_to_load": ("PV_generation_to_load[-]", "load_kWh"),
    "self_consumption": ("PV_self_consumption[-]", "generation_kWh"),
    "self_sufficiency": ("PV_self_sufficiency[-]", "load_kWh"),
}


def _pv_analytics(metric: str, df: pd.DataFrame, *, kpi_id: str) -> float:
    series = district_pv_series(df)
    column, denominator = _PV_ANALYTICS_METRICS[metric]
    if series[denominator].sum() == 0:
        what = "PV generation" if denominator == "generation_kWh" else "grid electricity"
        raise KPINotAvailable(kpi_id, reason=f"no {what} in this what-if")
    annual = calc_pv_analytics_by_period(series, "annually")
    # A what-if covers one weather year, so "annually" is a single row.
    return float(annual[column].iloc[0]) * 100.0


def _read_column(df: pd.DataFrame, name: str, *, kpi_id: str) -> pd.Series:
    if name not in df.columns:
        # `compute_kpi` checks every referenced column first (and
        # names the tool to re-run); this is the backstop for
        # callers of `evaluate` that skip that check.
        raise KPINotAvailable(
            kpi_id,
            reason=f"source CSV is missing column '{name}'",
        )
    return df[name]


def _as_scalar(value, kpi_id: str, where: str) -> float:
    if isinstance(value, pd.Series):
        # A Series reaching a scalar slot means the formula author
        # forgot an aggregate node — degrade to sum so the
        # behaviour is deterministic, but flag it loudly so
        # registry tests can catch it.
        raise KPIDefinitionError(
            f"{kpi_id}: {where} resolved to a Series; wrap it in an "
            f"`aggregate` node so the result is a scalar"
        )
    return float(value)
