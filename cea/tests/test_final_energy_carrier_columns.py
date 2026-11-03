"""Final-energy summaries read carriers from a building's hourly columns.

Solar generation must land in PV / SOLAR (not in carriers named after facades or units), raw
irradiation and booster heat demand are never carriers, and TOTAL counts consumption only.
"""
import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

import cea.technologies.energy_carriers as energy_carriers
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
