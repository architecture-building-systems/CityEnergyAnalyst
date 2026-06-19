from __future__ import annotations

import pandas as pd

from cea.visualisation.special.pathway_emission_timeline import (
    _apply_cutoff_year,
    _resolve_effective_year_bounds,
)


def test_apply_cutoff_year_filters_earlier_periods():
    timeline_df = pd.DataFrame(
        {
            "period": ["Y_2020", "Y_2025", "Y_2030"],
            "production_kgCO2e": [10.0, 20.0, 30.0],
        }
    )

    filtered = _apply_cutoff_year(timeline_df, 2025)

    assert filtered["period"].tolist() == ["Y_2025", "Y_2030"]


def test_resolve_effective_year_bounds_uses_later_cutoff_year():
    period_start, period_end = _resolve_effective_year_bounds(
        {"period_start": 2020, "period_end": 2035},
        2027,
    )

    assert period_start == 2027
    assert period_end == 2035
