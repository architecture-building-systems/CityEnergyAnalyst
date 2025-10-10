from __future__ import annotations

import numpy as np
import pandas as pd
import unittest

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from cea.analysis.lca import emission_timeline


class _DummyFeedstocks:
    def __init__(self) -> None:
        # The actual dataframe contents are irrelevant for this test; only the keys matter.
        self._library = {
            "GRID": pd.DataFrame(),
            "NATURALGAS": pd.DataFrame(),
        }


class _DummyLocator:
    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def get_lca_operational_hourly_building(self, _building: str) -> str:
        return str(self._output_path)


def _build_sample_operational_file(path: Path) -> tuple[float, float, float]:
    hours = 8760
    base_grid = 1.0
    base_natural_gas = 2.0
    df = pd.DataFrame(
        {
            "hour": np.arange(hours),
            "date": pd.date_range("2020-01-01", periods=hours, freq="h").astype(str),
            "heating_kgCO2e": (base_grid + base_natural_gas),
            "cooling_kgCO2e": 0.0,
            "hot_water_kgCO2e": 0.0,
            "electricity_kgCO2e": 0.0,
            "Qhs_sys_GRID_kgCO2e": base_grid,
            "Qhs_sys_NATURALGAS_kgCO2e": base_natural_gas,
        }
    )
    df.to_csv(path, index=False)
    return (base_grid + base_natural_gas) * hours, base_grid * hours, base_natural_gas * hours


class TestOperationalEmissionTimeline(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.operational_path = Path(self._tmpdir.name) / "B1_operational.csv"
        baseline_total, self.grid_total, self.natural_gas_total = _build_sample_operational_file(
            self.operational_path
        )
        self.baseline_total = baseline_total

        self.timeline = object.__new__(emission_timeline.BuildingEmissionTimeline)
        self.timeline.name = "B1"
        self.timeline.locator = _DummyLocator(self.operational_path)  # type: ignore[assignment]
        self.timeline.timeline = pd.DataFrame(
            0.0,
            index=[f"Y_{year}" for year in range(2020, 2024)],
            columns=emission_timeline.BuildingEmissionTimeline._OPERATIONAL_COLS,
        )

        dummy_feedstocks = _DummyFeedstocks()
        patcher = patch(
            "cea.datamanagement.database.components.Feedstocks.from_locator",
            return_value=dummy_feedstocks,
        )
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_discount_multiple_feedstocks(self) -> None:
        self.timeline.fill_operational_emissions(
            feedstock_policies={
                "grid": (2020, 2022, 0.5),
                "naturalgas": (2020, 2022, 0.5),
            }
        )

        self.assertAlmostEqual(
            float(self.timeline.timeline.loc["Y_2020", "operation_heating_kgCO2e"]),
            float(self.baseline_total),
        )
        self.assertAlmostEqual(
            float(self.timeline.timeline.loc["Y_2021", "operation_heating_kgCO2e"]),
            float(self.baseline_total * 0.75),
        )
        self.assertAlmostEqual(
            float(self.timeline.timeline.loc["Y_2022", "operation_heating_kgCO2e"]),
            float(self.baseline_total * 0.5),
        )
        self.assertAlmostEqual(
            float(self.timeline.timeline.loc["Y_2023", "operation_heating_kgCO2e"]),
            float(self.baseline_total * 0.5),
        )
        self.assertEqual(
            self.timeline.timeline.loc["Y_2020", "operation_cooling_kgCO2e"],
            0.0,
        )

    def test_discount_single_feedstock_string_input(self) -> None:
        self.timeline.fill_operational_emissions(
            feedstock_policies={
                "naturalgas": (2020, 2021, 0.0)
            }
        )

        self.assertAlmostEqual(
            float(self.timeline.timeline.loc["Y_2020", "operation_heating_kgCO2e"]),
            float(self.grid_total + self.natural_gas_total),
        )
        self.assertAlmostEqual(
            float(self.timeline.timeline.loc["Y_2021", "operation_heating_kgCO2e"]),
            float(self.grid_total),
        )
        # After 2021 the discounted value should be held constant at 0 for NATURALGAS portion
        self.assertAlmostEqual(
            float(self.timeline.timeline.loc["Y_2022", "operation_heating_kgCO2e"]),
            float(self.grid_total),
        )


if __name__ == "__main__":
    unittest.main()