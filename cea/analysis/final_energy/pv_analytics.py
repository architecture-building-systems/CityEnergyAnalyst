"""
PV analytics for the PV installed in a final-energy what-if: how much of the load the PV covers
and how much of the PV the load uses.

Shared by the Summary & Analytics tool and the Canvas KPI cards so the two cannot disagree.
Depends on pandas and numpy only.
"""
from typing import Optional

import numpy as np
import pandas as pd

from cea.utilities.date import month_names, season_mapping, season_names

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


PV_ANALYTICS = ['PV_generation_to_load[-]', 'PV_self_consumption[-]', 'PV_self_sufficiency[-]']
# Hourly analytics are just the hourly ratios; they are reported per period.
PV_ANALYTICS_PERIODS = ('daily', 'monthly', 'seasonally', 'annually')


def district_pv_series(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hourly ``generation_kWh`` / ``load_kWh`` from a what-if's district file (``final_energy.csv``):
    PV and PVT electricity against all grid consumption, plants included.
    """
    return pd.DataFrame({
        'date': df['date'],
        'generation_kWh': df['PV_kWh'].fillna(0.0),
        'load_kWh': df['GRID_kWh'].fillna(0.0),
    })


def _period_labels(dates: pd.Series, period: str) -> pd.Series:
    """Label each hour with its reporting period (same labels as the other summary outputs)."""
    if period == 'daily':
        days = dates.dt.date
        day_index = {day: f"D_{i:03d}" for i, day in enumerate(sorted(days.unique()))}
        return days.map(day_index)
    if period == 'monthly':
        return pd.Categorical(dates.dt.month.map(lambda m: month_names[m - 1]), categories=month_names, ordered=True)
    if period == 'seasonally':
        return pd.Categorical(dates.dt.month.map(season_mapping), categories=season_names, ordered=True)
    if period == 'annually':
        return 'Y_' + dates.dt.year.astype(str)
    raise ValueError(f"Invalid period: '{period}'. Must be one of {list(PV_ANALYTICS_PERIODS)}.")


def _ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """numerator / denominator, 0 where the denominator is 0."""
    return (numerator / denominator.where(denominator != 0)).fillna(0.0)


def calc_pv_analytics_by_period(df: pd.DataFrame, period: str) -> Optional[pd.DataFrame]:
    """
    The three PV analytics per reporting period, from hourly ``generation_kWh`` and ``load_kWh``.

    Generation and load are matched hour by hour, then summed over the period:
    self-consumption = Σ min(generation, load) / Σ generation, self-sufficiency =
    Σ min(generation, load) / Σ load. Generation-to-load = Σ generation / Σ load is the period's
    net balance.

    :param df: hourly rows: ``date``, ``generation_kWh``, ``load_kWh``
    :param period: one of ``PV_ANALYTICS_PERIODS``
    :return: one row per period, with ``hour_start`` / ``hour_end`` (positions in ``df``);
        ``None`` for no rows
    """
    if df is None or df.empty:
        return None
    hours = pd.DataFrame({
        'period': _period_labels(pd.to_datetime(df['date']).reset_index(drop=True), period),
        'generation': df['generation_kWh'].to_numpy(),
        'load': df['load_kWh'].to_numpy(),
        'hour': np.arange(len(df)),
    })
    hours['matched'] = np.minimum(hours['generation'], hours['load'])
    grouped = hours.groupby('period', observed=True, sort=True)
    totals = grouped[['generation', 'load', 'matched']].sum()

    result = pd.DataFrame({
        'period': totals.index.astype(str),
        'PV_generation_to_load[-]': _ratio(totals['generation'], totals['load']).to_numpy(),
        'PV_self_consumption[-]': _ratio(totals['matched'], totals['generation']).to_numpy(),
        'PV_self_sufficiency[-]': _ratio(totals['matched'], totals['load']).to_numpy(),
        'hour_start': grouped['hour'].first().to_numpy(),
        'hour_end': grouped['hour'].last().to_numpy(),
    })
    # A winter that wraps the year end (Jan-Feb + Dec) starts in December and ends in February.
    if period == 'seasonally':
        winter_hours = hours.loc[hours['period'] == 'Winter', 'hour'].to_numpy()
        gaps = np.flatnonzero(np.diff(winter_hours) > 1)
        if len(gaps):
            winter = result['period'] == 'Winter'
            result.loc[winter, 'hour_start'] = winter_hours[gaps[0] + 1]
            result.loc[winter, 'hour_end'] = winter_hours[gaps[0]]
    return result
