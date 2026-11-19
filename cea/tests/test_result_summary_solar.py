"""Summary & Analytics: solar potentials and PV analytics.

- Self-consumption and self-sufficiency match generation and load hour by hour, then sum over
  the reported period (not period totals); generation-to-load is the period's net balance.
- PV analytics are for the PV installed in a final-energy what-if, not for potentials.
- The solar potential summary covers only families and panel types that have results.
"""
import os

import pandas as pd
import pytest

import cea.import_export.result_summary as rs
import cea.inputlocator
from cea.analysis.final_energy.pv_analytics import PV_ANALYTICS, calc_pv_analytics_by_period


@pytest.fixture(autouse=True)
def emission_context(monkeypatch):
    # Metric mapping reads the cached emission context; these tests need none of its metrics.
    monkeypatch.setattr(rs, "EMISSION_CONTEXT", {
        "list_metrics_lifecycle_emissions": [],
        "list_metrics_operational_emissions": [],
        "hourly_colnames": [],
        "yearly_colnames": [],
    })


def _hours(generation, load, start="2022-01-01"):
    return pd.DataFrame({
        "date": pd.date_range(start, periods=len(generation), freq="h"),
        "generation_kWh": generation,
        "load_kWh": load,
    })


# ── Formulas ────────────────────────────────────────────────────────────────

def test_self_consumption_matches_each_hour_not_period_totals():
    # Two days: 10 kWh generated at noon, 10 kWh used at night -- nothing is used as it is made.
    day = [0.0] * 24
    generation = day.copy()
    generation[12] = 10.0
    load = day.copy()
    load[22] = 10.0
    df = _hours(generation * 2, load * 2)

    for period in ("daily", "annually"):
        result = calc_pv_analytics_by_period(df, period)
        assert result["PV_generation_to_load[-]"].tolist() == pytest.approx([1.0] * len(result))
        assert result["PV_self_consumption[-]"].tolist() == pytest.approx([0.0] * len(result))
        assert result["PV_self_sufficiency[-]"].tolist() == pytest.approx([0.0] * len(result))


def test_partly_matched_hours():
    # Hour 0: 4 generated, 1 used. Hour 1: 0 generated, 3 used.
    result = calc_pv_analytics_by_period(_hours([4.0, 0.0], [1.0, 3.0]), "annually")
    row = result.iloc[0]
    assert row["period"] == "Y_2022"
    assert row["PV_generation_to_load[-]"] == pytest.approx(4 / 4)
    assert row["PV_self_consumption[-]"] == pytest.approx(1 / 4)  # min(4,1)+min(0,3) over 4 generated
    assert row["PV_self_sufficiency[-]"] == pytest.approx(1 / 4)  # over 4 used
    assert {"hour_start", "hour_end"} <= set(result.columns)


def test_no_generation_or_load_gives_zero():
    result = calc_pv_analytics_by_period(_hours([0.0, 0.0], [0.0, 0.0]), "annually")
    assert result[PV_ANALYTICS].iloc[0].tolist() == [0.0, 0.0, 0.0]


def test_monthly_periods():
    df = _hours([1.0] * (24 * 31 + 24), [2.0] * (24 * 31 + 24))  # all of January + 1 Feb
    result = calc_pv_analytics_by_period(df, "monthly")
    assert result["period"].tolist() == ["Jan", "Feb"]
    assert result["PV_self_sufficiency[-]"].tolist() == pytest.approx([0.5, 0.5])


# ── Sources ─────────────────────────────────────────────────────────────────

class _Locator:
    def __init__(self, folder):
        self.folder = folder

    def get_final_energy_building_file(self, building, whatif_name):
        return os.path.join(self.folder, f"{building}_{whatif_name}.csv")

    def get_final_energy_file(self, whatif_name):
        return os.path.join(self.folder, f"district_{whatif_name}.csv")


DATES = pd.date_range("2022-01-01", periods=3, freq="h").astype(str)


def test_installed_source_reads_pv_and_all_grid_consumption(tmp_path):
    pd.DataFrame({
        "date": DATES,
        "Qhs_sys_kWh": [9.0] * 3,
        "E_sys_kWh": [5.0] * 3,
        "Qhs_sys_OIL_kWh": [9.0] * 3,  # not electricity
        "E_sys_GRID_kWh": [5.0] * 3,
        "Qhs_booster_kWh": [2.0] * 3,  # booster heat demand, not a carrier
        "Qhs_booster_GRID_kWh": [2.0] * 3,
        "PV_roof_kWh": [3.0, 0.0, 1.0],
        "PV_wall_south_kWh": [1.0, 0.0, 0.0],
        "PV_PV1_radiation_kWh": [50.0] * 3,  # sunlight on the panels, not generation
    }).to_csv(tmp_path / "B1000_with_pv.csv", index=False)

    series = rs.read_building_pv_series(_Locator(tmp_path), "with_pv", ["B1000", "B1001"], 0, 3)

    assert list(series) == ["B1000"]  # B1001 has no final-energy file
    assert series["B1000"]["generation_kWh"].tolist() == [4.0, 0.0, 1.0]
    assert series["B1000"]["load_kWh"].tolist() == [7.0, 7.0, 7.0]  # E_sys + booster GRID


def test_district_source_reads_the_whatif_district_file(tmp_path):
    # final_energy.csv: PV against all grid consumption, plants included.
    pd.DataFrame({"date": DATES, "GRID_kWh": [5.0, 6.0, 7.0], "PV_kWh": [1.0, 0.0, 2.0],
                  "OIL_kWh": [9.0] * 3}).to_csv(tmp_path / "district_with_pv.csv", index=False)

    district = rs.read_district_pv_series(_Locator(tmp_path), "with_pv", 0, 3)

    assert district["generation_kWh"].tolist() == [1.0, 0.0, 2.0]
    assert district["load_kWh"].tolist() == [5.0, 6.0, 7.0]
    assert rs.read_district_pv_series(_Locator(tmp_path), "no_such_whatif", 0, 3) is None


def test_analytics_written_for_district_and_buildings(tmp_path):
    locator = cea.inputlocator.InputLocator(str(tmp_path / "scenario"))
    summary = str(tmp_path / "summary")
    series = {"B1000": _hours([4.0, 0.0], [1.0, 3.0]), "B1001": _hours([0.0, 0.0], [1.0, 1.0])}
    # The district file sums the buildings hour by hour, so buildings share surplus.
    district = _hours([4.0, 0.0], [2.0, 4.0])

    rs.calc_pv_analytics(locator, 0, 8760, summary, district, series, "pv_installed_with_pv", ["annually"],
                         bool_aggregate_by_building=True, bool_use_acronym=False)

    analytics = os.path.join(summary, "pv", "analytics")
    district = pd.read_csv(os.path.join(analytics, "pv_installed_with_pv_analytics_annually.csv"))
    # Hour 0 has 4 generated for 2 used, so B1001 uses B1000's surplus -- 2 matched out of 6 used.
    assert district["PV_self_sufficiency[-]"].iloc[0] == pytest.approx(2 / 6, abs=0.01)
    assert "coverage_ratio" in district.columns
    buildings = pd.read_csv(os.path.join(analytics, "pv_installed_with_pv_analytics_annually_buildings.csv"))
    assert buildings["name"].tolist() == ["B1000", "B1001"]
    # Each building on its own: B1000 uses 1 of its 4 generated.
    assert buildings.set_index("name").loc["B1000", "PV_self_consumption[-]"] == pytest.approx(0.25, abs=0.01)


def test_no_analytics_without_generation(tmp_path):
    locator = cea.inputlocator.InputLocator(str(tmp_path / "scenario"))
    summary = str(tmp_path / "summary")
    series = {"B1000": _hours([0.0], [1.0])}
    rs.calc_pv_analytics(locator, 0, 8760, summary, series["B1000"], series, "pv_installed_no_pv",
                         ["annually"], bool_aggregate_by_building=True, bool_use_acronym=False)
    assert not os.path.exists(os.path.join(summary, "pv"))


# ── Solar potential families ────────────────────────────────────────────────

def test_potential_summary_lists_only_types_with_results(tmp_path):
    locator = cea.inputlocator.InputLocator(str(tmp_path / "scenario"))
    db = locator.get_db4_components_conversion_conversion_technology_csv("PHOTOVOLTAIC_PANELS")
    os.makedirs(os.path.dirname(db), exist_ok=True)
    pd.DataFrame({"code": ["PV1", "PV2"]}).to_csv(db, index=False)
    pv1 = locator.PV_results("B1000", "PV1")
    os.makedirs(os.path.dirname(pv1), exist_ok=True)
    pd.DataFrame({"date": DATES, "E_PV_gen_kWh": [1.0] * 3}).to_csv(pv1, index=False)

    _, appendix = rs.get_results_path(locator, "pv", ["B1000"])
    assert appendix == ["pv_PV1"]  # PV2 has no results
    assert rs._get_solar_potential_metric_lists(locator, ["B1000"]) == [rs.list_metrics_photovoltaic_panels]


def test_potential_area_metric_names():
    columns = rs.map_metrics_and_cea_columns(["PV_potential_area_roof[m2]", "SC_ET_potential_area_total[m2]"])
    assert columns == ["PV_roofs_top_m2", "area_SC_m2"]
    assert rs.map_metrics_and_cea_columns(["PV_roofs_top_m2"], direction="columns_to_metrics") == \
        ["PV_potential_area_roof[m2]"]
