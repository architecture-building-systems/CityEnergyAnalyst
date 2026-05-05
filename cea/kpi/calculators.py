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
has to learn it. v1 ships with five (``column``, ``sum_columns``,
``aggregate``, ``divide``, ``share_of``).
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd

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
            return float(series.sum())
        if op == "max":
            return float(series.max())
        if op == "min":
            return float(series.min())
        if op == "mean":
            return float(series.mean())
        raise KPIDefinitionError(f"{kpi_id}: unknown aggregate op '{op}'")

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
    else:
        raise KPIDefinitionError(f"unknown formula kind '{kind}'")


# ── Helpers ─────────────────────────────────────────────────────────


def _read_column(df: pd.DataFrame, name: str, *, kpi_id: str) -> pd.Series:
    if name not in df.columns:
        # The registry validates column references against
        # schemas.yml at load time; the only way a missing column
        # reaches the evaluator is if the upstream tool emitted a
        # CSV that doesn't match its declared schema (rare, but
        # worth surfacing as KPINotAvailable rather than 500).
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
