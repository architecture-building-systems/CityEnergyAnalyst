"""Final-energy summaries read carriers from a building's hourly columns.

Solar generation must land in PV / SOLAR (not in carriers named after facades or units), raw
irradiation and booster heat demand are never carriers, and TOTAL counts consumption only.
The district TOTAL counts heat / cold a plant supplies once, at the plant.
"""
import os

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

import cea.technologies.energy_carriers as energy_carriers
from cea.inputlocator import InputLocator
from cea.kpi.resolver import compute_kpi
from cea.analysis.final_energy.calculation import (
    aggregate_buildings_summary,
    classify_carrier_column,
    create_hourly_timeseries_aggregation,
)


@pytest.mark.parametrize("col,expected", [
    ("Qhs_sys_NATURALGAS_kWh", ("NATURALGAS", True)),
    ("Qww_booster_GRID_kWh", ("GRID", True)),
    ("Qww_sys_SOLAR_kWh", ("SOLAR", True)),
    ("Qhs_sys_Biogas2_kWh", ("Biogas2", True)),  # a user database's own carrier code
    ("PV_roof_kWh", ("PV", False)),
    ("PV_wall_south_kWh", ("PV", False)),
    ("PVT_ET_roof_E_kWh", ("PV", False)),
    ("PVT_ET_roof_Q_kWh", ("SOLAR", False)),
    ("SC_FP_wall_east_kWh", ("SOLAR", False)),
    ("PV_PV1_radiation_kWh", None),
    ("SC_FP_radiation_kWh", None),
    ("Qww_sys_SOLAR_dumped_kWh", None),
    ("Qhs_booster_kWh", None),
    ("Qhs_sys_kWh", None),
    ("E_sys_kWh", None),
])
def test_classify_carrier_column(col, expected):
    assert classify_carrier_column(col) == expected


HOURS = 3
DATES = pd.date_range("2022-01-01", periods=HOURS, freq="h").astype(str)


def _building_df():
    """One building: grid + oil consumption, a booster, PV on two facades."""
    return pd.DataFrame({
        "date": pd.date_range("2022-01-01", periods=HOURS, freq="h").astype(str),
        "Qhs_sys_kWh": [10.0] * HOURS,
        "Qww_sys_kWh": [5.0] * HOURS,
        "Qcs_sys_kWh": [0.0] * HOURS,
        "E_sys_kWh": [20.0] * HOURS,
        "Qhs_sys_OIL_kWh": [12.0] * HOURS,
        "E_sys_GRID_kWh": [20.0] * HOURS,
        "Qhs_booster_kWh": [3.0] * HOURS,  # booster heat demand, not a carrier
        "Qhs_booster_GRID_kWh": [3.0] * HOURS,
        "PV_roof_kWh": [7.0] * HOURS,
        "PV_wall_south_kWh": [1.0] * HOURS,
        "PV_PV1_radiation_kWh": [100.0] * HOURS,  # incident sunlight, not energy delivered
        "scale": ["BUILDING"] * HOURS,
        "case": [1] * HOURS,
        "case_description": ["Standalone (all services)"] * HOURS,
    })


def test_district_hourly_counts_pv_as_generation_not_consumption():
    out = create_hourly_timeseries_aggregation({"B1000": _building_df()}, {})

    assert out["PV_kWh"].tolist() == [8.0] * HOURS
    assert out["GRID_kWh"].tolist() == [23.0] * HOURS  # E_sys + booster
    assert out["OIL_kWh"].tolist() == [12.0] * HOURS
    assert out["TOTAL_kWh"].tolist() == [35.0] * HOURS  # consumption only
    assert "kWh_kWh" not in out.columns


class _Locator:
    def __init__(self, tmp_path):
        self.tmp_path = tmp_path

    def get_zone_geometry(self):
        return str(self.tmp_path / "zone.shp")

    def get_total_demand(self):
        return str(self.tmp_path / "Total_demand.csv")


def test_building_summary_reports_pv_and_totals_consumption(tmp_path, monkeypatch):
    gpd.GeoDataFrame(
        {"name": ["B1000"]}, geometry=[Point(0, 0)], crs="EPSG:2056"
    ).to_file(tmp_path / "zone.shp")
    pd.DataFrame({"name": ["B1000"], "GFA_m2": [100.0]}).to_csv(
        tmp_path / "Total_demand.csv", index=False
    )
    monkeypatch.setattr(energy_carriers, "available_carriers", lambda locator: {"GRID", "OIL"})

    summary = aggregate_buildings_summary({"B1000": _building_df()}, {}, _Locator(tmp_path))
    row = summary.set_index("name").loc["B1000"]

    assert row["PV_MWh"] == pytest.approx(8.0 * HOURS / 1000)
    assert row["GRID_MWh"] == pytest.approx(23.0 * HOURS / 1000)
    assert row["OIL_MWh"] == pytest.approx(12.0 * HOURS / 1000)
    assert row["TOTAL_MWh"] == pytest.approx(35.0 * HOURS / 1000)
    assert not {"kWh_MWh", "south_MWh", "radiation_MWh"} & set(summary.columns)


# ── District heating / cooling counted once ─────────────────────────────────


def _network_building_df(dh=10.0, dc=0.0):
    """A building on a network: grid electricity, district heat and cold bought."""
    return pd.DataFrame({
        "date": pd.date_range("2022-01-01", periods=HOURS, freq="h").astype(str),
        "Qhs_sys_kWh": [dh] * HOURS,
        "Qww_sys_kWh": [0.0] * HOURS,
        "Qcs_sys_kWh": [dc] * HOURS,
        "E_sys_kWh": [2.0] * HOURS,
        "E_sys_GRID_kWh": [2.0] * HOURS,
        "Qhs_sys_DH_kWh": [dh] * HOURS,
        "Qcs_sys_DC_kWh": [dc] * HOURS,
    })


def _dh_plant_df():
    """A DH plant burning 12 kWh of gas and pumping with 1 kWh of grid electricity per hour."""
    return pd.DataFrame({
        "plant_primary_DH_NATURALGAS_kWh": [12.0] * HOURS,
        "plant_pumping_DH_GRID_kWh": [1.0] * HOURS,
    })


def test_district_total_counts_plant_supplied_heat_once():
    out = create_hourly_timeseries_aggregation({"B1000": _network_building_df()}, {"DH_P1": _dh_plant_df()})

    assert out["TOTAL_kWh"].tolist() == [15.0] * HOURS  # building grid 2 + plant gas 12 + pumping 1
    assert out["DH_kWh"].tolist() == [10.0] * HOURS  # heat delivered, still reported
    assert out["NATURALGAS_kWh"].tolist() == [12.0] * HOURS
    assert out["GRID_kWh"].tolist() == [3.0] * HOURS  # plant pumping is grid electricity, not DH


def test_district_heat_without_plant_results_stays_in_the_total():
    out = create_hourly_timeseries_aggregation({"B1000": _network_building_df()}, {})
    assert out["TOTAL_kWh"].tolist() == [12.0] * HOURS


def test_a_dh_plant_does_not_drop_district_cooling():
    out = create_hourly_timeseries_aggregation({"B1000": _network_building_df(dc=4.0)}, {"DH_P1": _dh_plant_df()})
    assert out["TOTAL_kWh"].tolist() == [19.0] * HOURS  # DC has no plant results: kept


def test_district_file_writes_every_declared_carrier():
    out = create_hourly_timeseries_aggregation({"B1000": _network_building_df()}, {})
    assert out["COAL_kWh"].tolist() == [0.0] * HOURS


def test_building_total_still_includes_district_heat_bought(tmp_path, monkeypatch):
    gpd.GeoDataFrame(
        {"name": ["B1000"]}, geometry=[Point(0, 0)], crs="EPSG:2056"
    ).to_file(tmp_path / "zone.shp")
    pd.DataFrame({"name": ["B1000"], "GFA_m2": [100.0]}).to_csv(
        tmp_path / "Total_demand.csv", index=False
    )
    monkeypatch.setattr(energy_carriers, "available_carriers", lambda locator: {"GRID", "NATURALGAS"})

    summary = aggregate_buildings_summary({"B1000": _network_building_df()}, {}, _Locator(tmp_path))

    assert summary.set_index("name").loc["B1000", "TOTAL_MWh"] == pytest.approx(12.0 * HOURS / 1000)


def test_total_and_fossil_share_cards_read_the_district_total(tmp_path):
    locator = InputLocator(str(tmp_path))
    out = create_hourly_timeseries_aggregation({"B1000": _network_building_df()}, {"DH_P1": _dh_plant_df()})
    path = locator.get_final_energy_file("w1")
    os.makedirs(os.path.dirname(path))
    out.to_csv(path, index=False)

    def kpi(kpi_id):
        return compute_kpi(kpi_id, locator.scenario, locator_args_override={"whatif_name": "w1"}).value

    assert kpi("final_energy.total_final_mwh") == pytest.approx(15.0 * HOURS / 1000)
    assert kpi("final_energy.fossil_share_pct") == pytest.approx(12 / 15 * 100)


def test_reports_total_counts_plant_supplied_heat_once(tmp_path):
    from cea.interfaces.dashboard.api.reports import _final_energy_summary

    locator = InputLocator(str(tmp_path))
    # One DH building (30 MWh of DH, 6 MWh grid) and its plant (36 MWh gas, 3 MWh pumping)
    summary = locator.get_final_energy_buildings_file("w1")
    os.makedirs(os.path.dirname(summary))
    pd.DataFrame({
        "name": ["B1000", "P1"], "type": ["building", "plant"],
        "Qhs_sys_MWh": [30.0, 30.0], "DH_MWh": [30.0, 0.0], "GRID_MWh": [6.0, 3.0],
        "NATURALGAS_MWh": [0.0, 36.0], "COAL_MWh": [0.0, 0.0], "TOTAL_MWh": [36.0, 39.0],
    }).to_csv(summary, index=False)
    pd.DataFrame({"date": DATES, "TOTAL_kWh": [15000.0] * HOURS}).to_csv(
        locator.get_final_energy_file("w1"), index=False)

    kpis = {k["key"]: k["value"] for k in _final_energy_summary(locator, "w1")["kpis"]}

    assert kpis["TOTAL_MWh"] == pytest.approx(45.0)  # the district file, not 36 + 39 = 75
    assert (kpis["DH_MWh"], kpis["NATURALGAS_MWh"], kpis["GRID_MWh"]) == (30.0, 36.0, 9.0)
    assert "Qhs_sys_MWh" not in kpis and "COAL_MWh" not in kpis
