"""PV analytics KPI cards (generation-to-load, self-consumption, self-sufficiency).

- The cards read a what-if's district file `final_energy.csv` and compute with the Summary &
  Analytics code, so a card equals the summary's annual district value.
- The retired "Solar Share of Final Energy" id is an alias of generation-to-load.
"""

import asyncio
import json
import os

import pandas as pd
import pytest

import cea.import_export.result_summary as rs
from cea.analysis.final_energy.pv_analytics import calc_pv_analytics_by_period
from cea.inputlocator import InputLocator
from cea.interfaces.dashboard.api.kpis import get_kpi_registry, get_kpi_value
from cea.kpi import registry
from cea.kpi.exceptions import KPIDefinitionError
from cea.kpi.schema import KPIDefinition

GENERATION_TO_LOAD = "final_energy.pv_generation_to_load_pct"
SELF_CONSUMPTION = "final_energy.pv_self_consumption_pct"
SELF_SUFFICIENCY = "final_energy.pv_self_sufficiency_pct"
RETIRED_SOLAR_SHARE = "final_energy.solar_share_pct"


@pytest.fixture
def locator(tmp_path):
    return InputLocator(str(tmp_path))


def _write_district(locator, pv, grid, whatif="w1"):
    path = locator.get_final_energy_file(whatif)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pd.DataFrame({
        "date": pd.date_range("2022-01-01", periods=len(pv), freq="h").astype(str),
        "GRID_kWh": grid,
        "PV_kWh": pv,
        "OIL_kWh": [5.0] * len(pv),  # not electricity
    }).to_csv(path, index=False)


def _noon_surplus(locator):
    """One day: 30 kWh of PV at noon, 1 kWh of grid electricity every hour."""
    pv = [0.0] * 24
    pv[12] = 30.0
    _write_district(locator, pv, [1.0] * 24)


def _value(locator, kpi_id, whatif_name="w1"):
    return asyncio.run(get_kpi_value(kpi_id, scenario_path=locator.scenario,
                                     locator_args=json.dumps({"whatif_name": whatif_name}), whatif=None))


def test_cards_match_hour_by_hour(locator):
    _noon_surplus(locator)

    # More PV than load over the year, but only 1 of the 30 kWh is used as it is generated.
    assert _value(locator, GENERATION_TO_LOAD)["value"] == pytest.approx(30 / 24 * 100)
    assert _value(locator, SELF_CONSUMPTION)["value"] == pytest.approx(1 / 30 * 100)
    assert _value(locator, SELF_SUFFICIENCY)["value"] == pytest.approx(1 / 24 * 100)


def test_cards_equal_the_summary_district_values(locator):
    _noon_surplus(locator)
    district = rs.read_district_pv_series(locator, "w1", 0, 8760)
    annual = calc_pv_analytics_by_period(district, "annually").iloc[0]

    for kpi_id, column in [(GENERATION_TO_LOAD, "PV_generation_to_load[-]"),
                           (SELF_CONSUMPTION, "PV_self_consumption[-]"),
                           (SELF_SUFFICIENCY, "PV_self_sufficiency[-]")]:
        assert _value(locator, kpi_id)["value"] == pytest.approx(annual[column] * 100)


def test_unavailable_without_the_whatif_or_without_pv(locator):
    assert _value(locator, SELF_SUFFICIENCY, whatif_name="missing")["available"] is False

    _write_district(locator, [0.0] * 24, [1.0] * 24)
    assert _value(locator, GENERATION_TO_LOAD)["value"] == 0.0
    no_pv = _value(locator, SELF_CONSUMPTION)
    assert (no_pv["available"], no_pv["reason"]) == (False, "no PV generation in this what-if")


def test_an_outdated_district_file_asks_to_rerun_the_tool(locator):
    # Written before final-energy zero-filled every declared carrier: no PV_kWh column.
    path = locator.get_final_energy_file("w1")
    os.makedirs(os.path.dirname(path))
    pd.DataFrame({"date": ["2022-01-01 00:00:00"], "GRID_kWh": [1.0]}).to_csv(path, index=False)

    result = _value(locator, SELF_SUFFICIENCY)

    assert result["available"] is False
    assert result["upstream_tool"] == "LCA Part 1: Energy by Carrier"
    assert "missing column 'PV_kWh'" in result["reason"]


def test_registry_checks_the_node_reads_the_district_file():
    raw = registry.load_registry()[SELF_SUFFICIENCY].model_dump(mode="python")
    raw["source"]["locator"] = "get_final_energy_buildings_file"  # annual per-building file
    with pytest.raises(KPIDefinitionError, match="column 'date'"):
        registry._validate_one(KPIDefinition.model_validate(raw), schemas=registry._load_schemas(),
                               locator_methods=registry._locator_method_names())


def test_retired_solar_share_resolves_to_generation_to_load(locator):
    _noon_surplus(locator)

    retired = _value(locator, RETIRED_SOLAR_SHARE)

    assert retired["id"] == GENERATION_TO_LOAD
    assert retired["label"] == "PV Generation-to-Load"
    assert retired["value"] == pytest.approx(_value(locator, GENERATION_TO_LOAD)["value"])
    listed = {kpi["id"] for kpi in asyncio.run(get_kpi_registry())["kpis"]}
    assert GENERATION_TO_LOAD in listed and RETIRED_SOLAR_SHARE not in listed
