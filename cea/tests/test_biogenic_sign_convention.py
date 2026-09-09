"""Biogenic carbon is stored as a negative number at every level of the database.

Stored carbon reduces the CO2 balance, so it is negative in MATERIALS.csv
(`biogenic_carbon_in_product`), negative in the envelope assemblies derived from it
(`GHG_biogenic_*_kgCO2m2`), and negative where the timelines report it. Nothing in the chain
flips the sign -- a compensating negation anywhere would silently turn storage into emission,
which no other check would catch.
"""

import glob
import os

import pandas as pd
import pytest

from cea.datamanagement.database.assemblies import Envelope
from cea.tests import paths

# A material that genuinely stores carbon, so every step below has a non-zero sign to get wrong.
TIMBER = {
    "name": "timber",
    "thermal_conductivity": 0.13,
    "density": 500.0,
    "unit": "kg",
    "GHG_emission_total": 0.4,
    "GHG_emission_production": 0.3,
    "GHG_emission_disposal": 0.1,
    "biogenic_carbon_in_product": -0.5,
}


@pytest.mark.parametrize("path", sorted(glob.glob(
    os.path.join(str(paths.REPO_ROOT), "cea", "databases", "*", "COMPONENTS", "MATERIALS", "MATERIALS.csv"))))
def test_shipped_materials_never_store_a_positive_biogenic_value(path):
    values = pd.to_numeric(pd.read_csv(path)["biogenic_carbon_in_product"], errors="coerce")
    positive = values[values > 0]
    assert positive.empty, f"{path} has {len(positive)} positive biogenic value(s)"


@pytest.mark.parametrize("path", sorted(glob.glob(
    os.path.join(str(paths.REPO_ROOT), "cea", "databases", "*", "ASSEMBLIES", "ENVELOPE", "*.csv"))))
def test_shipped_assemblies_never_store_a_positive_biogenic_value(path):
    df = pd.read_csv(path)
    for column in (c for c in df.columns if "GHG_biogenic" in c):
        values = pd.to_numeric(df[column], errors="coerce")
        positive = values[values > 0]
        assert positive.empty, f"{path}:{column} has {len(positive)} positive value(s)"


def test_a_derived_assembly_value_keeps_the_material_sign(envelope_scenario):
    """The derivation must not reintroduce a positive magnitude."""
    locator = envelope_scenario(
        [TIMBER], wall=[{"code": "WALL_A", "material_name_1": "timber",
                         "thickness_1_m": 0.10, "Service_Life_wall": 40}]
    )

    wall = Envelope.from_locator(locator).wall
    row = wall.loc["WALL_A"] if wall.index.name == "code" else wall.set_index("code").loc["WALL_A"]

    # 500 kg/m3 x 0.10 m = 50 kg/m2, x -0.5 kgCO2eq/kg = -25 kgCO2eq/m2
    assert float(row["GHG_biogenic_wall_kgCO2m2"]) == pytest.approx(-25.0)
    # Production emissions stay positive: only the biogenic term is negative.
    assert float(row["GHG_wall_kgCO2m2"]) > 0


def test_no_consumer_negates_a_biogenic_value():
    """A compensating negation would invert the sign with no error to reveal it.

    Guards the seven sites removed when the convention was unified; the timelines now pass
    the stored value straight through.
    """
    offenders = []
    for path in glob.glob(os.path.join(str(paths.REPO_ROOT), "cea", "**", "*.py"), recursive=True):
        if os.sep + "tests" + os.sep in path:
            continue
        with open(path, encoding="utf-8") as handle:
            for number, line in enumerate(handle, start=1):
                stripped = line.split("#", 1)[0]
                if "biogenic" not in stripped.lower() and "bio" not in stripped:
                    continue
                if "(-bio" in stripped or "=-bio" in stripped or "-biogenic_per_area" in stripped:
                    offenders.append(f"{os.path.relpath(path, str(paths.REPO_ROOT))}:{number}")
    assert offenders == [], f"biogenic value negated at: {offenders}"
