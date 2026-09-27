"""Custom grid-carbon-intensity CSV override: column-name resolution and error messages.

`_load_grid_emission_intensity_override` lets a user supply an external CSV of hourly grid
carbon intensity plus a column name typed by hand -- with no way to see the file's actual
header first (see `cea/analysis/lca/CLAUDE.md` Grid Emission Intensity Override). A wrong or
oddly-formatted column name must fail with a message that names the available columns, not a
raw pandas `usecols` error, and the on-disk temp path must never leak into the message.
"""

import os
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from cea.analysis.lca.emission_time_dependent import (
    _load_grid_emission_intensity_override,
)

HOURS_IN_YEAR = 8760
LEAP_YEAR_HOURS = 8784


def _make_config(csv_path, column_name):
    emissions = SimpleNamespace(
        grid_carbon_intensity_dataset_csv=csv_path,
        csv_carbon_intensity_column_name=column_name,
    )
    return SimpleNamespace(emissions=emissions)


def _write_csv(tmp_path, filename, data: dict) -> str:
    path = os.path.join(str(tmp_path), filename)
    pd.DataFrame(data).to_csv(path, index=False)
    return path


def test_no_csv_provided_returns_no_override():
    config = _make_config(None, None)
    override, values = _load_grid_emission_intensity_override(config)
    assert override is False
    assert values is None


def test_exact_column_match_returns_values(tmp_path):
    values = np.arange(HOURS_IN_YEAR, dtype=float)
    csv_path = _write_csv(tmp_path, "grid.csv", {"Carbon intensity": values})
    config = _make_config(csv_path, "Carbon intensity")

    override, result = _load_grid_emission_intensity_override(config)

    assert override is True
    np.testing.assert_array_equal(result, values)


def test_leap_year_rows_drops_feb_29(tmp_path):
    values = np.arange(LEAP_YEAR_HOURS, dtype=float)
    csv_path = _write_csv(tmp_path, "grid.csv", {"Carbon intensity": values})
    config = _make_config(csv_path, "Carbon intensity")

    with pytest.warns(RuntimeWarning, match="8784 rows"):
        override, result = _load_grid_emission_intensity_override(config)

    assert override is True
    assert len(result) == HOURS_IN_YEAR
    # Feb 29 (hours 1416..1439) were dropped, not just truncated from the end
    expected = np.delete(values, range(1416, 1440))
    np.testing.assert_array_equal(result, expected)


def test_unicode_and_whitespace_tolerant_match(tmp_path):
    # Real-world header uses a Unicode subscript '₂'; user types plain ASCII with trailing space.
    values = np.arange(HOURS_IN_YEAR, dtype=float)
    header = "Carbon intensity gCO₂eq/kWh (direct)"
    csv_path = _write_csv(tmp_path, "grid.csv", {header: values})
    config = _make_config(csv_path, "Carbon intensity gCO2eq/kWh (direct) ")

    override, result = _load_grid_emission_intensity_override(config)

    assert override is True
    np.testing.assert_array_equal(result, values)


def test_missing_column_lists_available_columns_and_hides_temp_path(tmp_path):
    values = np.arange(HOURS_IN_YEAR, dtype=float)
    csv_path = _write_csv(
        tmp_path, "snapshot (1).csv", {"Carbon intensity gCO2eq/kWh (direct)": values, "Zone id": "A"}
    )
    config = _make_config(csv_path, "112")

    with pytest.raises(ValueError) as exc_info:
        _load_grid_emission_intensity_override(config)

    message = str(exc_info.value)
    assert csv_path not in message
    assert "snapshot (1).csv" in message
    assert "Carbon intensity gCO2eq/kWh (direct)" in message
    assert "Zone id" in message


def test_missing_column_suggests_close_match(tmp_path):
    values = np.arange(HOURS_IN_YEAR, dtype=float)
    csv_path = _write_csv(tmp_path, "grid.csv", {"Carbon intensity gCO2eq/kWh (direct)": values})
    config = _make_config(csv_path, "Carbon intensity")

    with pytest.raises(ValueError, match="Did you mean"):
        _load_grid_emission_intensity_override(config)


def test_sparse_column_reports_nan_count_and_column_name(tmp_path):
    values = [np.nan] * (HOURS_IN_YEAR - 25) + list(np.arange(25, dtype=float))
    csv_path = _write_csv(tmp_path, "grid.csv", {"Carbon intensity": values})
    config = _make_config(csv_path, "Carbon intensity")

    with pytest.raises(ValueError) as exc_info:
        _load_grid_emission_intensity_override(config)

    message = str(exc_info.value)
    assert "Carbon intensity" in message
    assert f"{HOURS_IN_YEAR - 25}" in message
    assert f"out of {HOURS_IN_YEAR}" in message


def test_non_numeric_column_reports_clear_message(tmp_path):
    csv_path = _write_csv(
        tmp_path, "grid.csv", {"Carbon intensity": ["A"] * HOURS_IN_YEAR}
    )
    config = _make_config(csv_path, "Carbon intensity")

    with pytest.raises(ValueError, match="non-numeric"):
        _load_grid_emission_intensity_override(config)


def test_missing_file_raises_file_not_found_without_leaking_temp_path(tmp_path):
    csv_path = os.path.join(str(tmp_path), "does_not_exist.csv")
    config = _make_config(csv_path, "Carbon intensity")

    with pytest.raises(FileNotFoundError) as exc_info:
        _load_grid_emission_intensity_override(config)

    assert csv_path not in str(exc_info.value)
    assert "does_not_exist.csv" in str(exc_info.value)


def test_column_name_without_csv_path_is_not_an_error():
    config = _make_config(None, "Carbon intensity")
    override, values = _load_grid_emission_intensity_override(config)
    assert override is False
    assert values is None


def test_csv_path_without_column_name_raises():
    config = _make_config("/some/path.csv", None)
    with pytest.raises(ValueError, match="csv_carbon_intensity_column_name"):
        _load_grid_emission_intensity_override(config)
