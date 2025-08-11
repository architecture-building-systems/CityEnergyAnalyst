import os
import shutil
import tempfile
import unittest

import pandas as pd

import cea.config
from cea.inputlocator import InputLocator
from cea.datamanagement.construction_helper import construction_helper


def _seed_envelope_csvs(locator: InputLocator):
    os.makedirs(os.path.dirname(locator.get_database_assemblies_envelope_roof()), exist_ok=True)

    # Minimal headers per schema assumptions
    roof_cols = [
        "description", "code", "U_roof", "a_roof", "e_roof", "r_roof",
        "GHG_roof_kgCO2m2", "GHG_biogenic_roof_kgCO2m2", "Service_Life_roof",
        "Reference Service life", "Reference U-Value",
    ]
    wall_cols = [
        "description", "code", "U_wall", "a_wall", "e_wall", "r_wall",
        "GHG_wall_kgCO2m2", "GHG_biogenic_wall_kgCO2m2", "Service_Life_wall",
        "Reference Service life", "Reference U-Value",
    ]
    floor_cols = [
        "description", "code", "U_base", "GHG_floor_kgCO2m2",
        "GHG_biogenic_floor_kgCO2m2", "Service_Life_floor", "Reference",
    ]

    for path, cols in [
        (locator.get_database_assemblies_envelope_roof(), roof_cols),
        (locator.get_database_assemblies_envelope_wall(), wall_cols),
        (locator.get_database_assemblies_envelope_floor(), floor_cols),
    ]:
        if not os.path.exists(path):
            pd.DataFrame(columns=cols).to_csv(path, index=False)


class TestConstructionHelper(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="cea_test_scn_")
        config = cea.config.Configuration()
        # Point scenario to temp directory
        config.apply_command_line_args(["--scenario", self.tmpdir], ["general"])
        self.config = config
        self.locator = InputLocator(self.config.scenario)
        _seed_envelope_csvs(self.locator)

        # Ensure region is Switzerland and set defaults
        ch = self.config.sections["construction-helper"].parameters
        ch["database-region"].set("Switzerland")
        ch["cladding-type"].set("plaster")
        ch["insulation-type"].set("EPS")
        ch["insulation-thickness"].set("medium (around 10 cm)")
        ch["building-structure-type"].set("concrete")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _read_rows(self):
        roof_df = pd.read_csv(self.locator.get_database_assemblies_envelope_roof())
        wall_df = pd.read_csv(self.locator.get_database_assemblies_envelope_wall())
        floor_df = pd.read_csv(self.locator.get_database_assemblies_envelope_floor())
        return roof_df, wall_df, floor_df

    def test_append_basic_construction(self):
        # first run
        self.config.sections["construction-helper"].parameters["construction-prefix"].set("TST1")
        construction_helper_copilot(self.config, self.locator)

        roof_df, wall_df, floor_df = self._read_rows()
        self.assertTrue((wall_df["code"].str.startswith("TST1_WALL")).any())
        self.assertTrue((roof_df["code"].str.startswith("TST1_ROOF")).any())
        self.assertTrue((floor_df["code"].str.startswith("TST1_FLOOR")).any())

        # Validate GHG numbers present and > 0
        self.assertGreater(wall_df.iloc[-1]["GHG_wall_kgCO2m2"], 0)
        self.assertGreater(roof_df.iloc[-1]["GHG_roof_kgCO2m2"], 0)
        self.assertGreater(floor_df.iloc[-1]["GHG_floor_kgCO2m2"], 0)

    def test_uniqueness_on_multiple_runs(self):
        self.config.sections["construction-helper"].parameters["construction-prefix"].set("TST2")
        construction_helper_copilot(self.config, self.locator)
        construction_helper_copilot(self.config, self.locator)

        roof_df, wall_df, floor_df = self._read_rows()
        # Expect at least 2 entries with distinct codes for each type
        wall_codes = wall_df[wall_df["code"].str.startswith("TST2_WALL")]["code"].tolist()
        roof_codes = roof_df[roof_df["code"].str.startswith("TST2_ROOF")]["code"].tolist()
        floor_codes = floor_df[floor_df["code"].str.startswith("TST2_FLOOR")]["code"].tolist()
        self.assertGreaterEqual(len(set(wall_codes)), 2)
        self.assertGreaterEqual(len(set(roof_codes)), 2)
        self.assertGreaterEqual(len(set(floor_codes)), 2)

    def test_various_combinations(self):
        combos = [
            ("CMB1", "wood", "XPS", "thin (around 5 cm)", "wood"),
            ("CMB2", "masonry", "PUR", "thick (around 20 cm)", "brick"),
            ("CMB3", "concrete", "EPS", "none", "none"),
        ]
        for prefix, structure, ins, ins_t, cladding in combos:
            ch = self.config.sections["construction-helper"].parameters
            ch["construction-prefix"].set(prefix)
            ch["building-structure-type"].set(structure)
            ch["insulation-type"].set(ins)
            ch["insulation-thickness"].set(ins_t)
            ch["cladding-type"].set(cladding)
            construction_helper_copilot(self.config, self.locator)

        roof_df, wall_df, floor_df = self._read_rows()
        for prefix, *_ in combos:
            self.assertTrue((wall_df["code"].str.startswith(f"{prefix}_WALL")).any())
            self.assertTrue((roof_df["code"].str.startswith(f"{prefix}_ROOF")).any())
            self.assertTrue((floor_df["code"].str.startswith(f"{prefix}_FLOOR")).any())


if __name__ == "__main__":
    unittest.main()
