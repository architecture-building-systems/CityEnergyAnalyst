"""Envelope embodied carbon is reported split into production and demolition.

`GHG_*_kgCO2m2` stays the whole-lifecycle figure; `GHG_production_*` and `GHG_recycling_*`
split it and are derived from the material layers. A database without MATERIALS.csv, a
direct-property row, and a window all lack the split, so the split is decided per row -- one
file routinely holds both kinds.
"""

import os

import pandas as pd
import pytest

from cea.datamanagement.database.assemblies import Envelope
from cea.tests.conftest import write_database_csv
from cea.datamanagement.database.envelope_lookup import (
    EnvelopeLookup,
    envelope_emission_intensities,
)

# density 1000 kg/m3 x 0.20 m = 200 kg/m2
BRICK = {
    "name": "brick",
    "thermal_conductivity": 0.6,
    "density": 1000.0,
    "unit": "kg",
    "GHG_emission_total": 0.5,
    "GHG_emission_production": 0.4,
    "GHG_emission_recycling": 0.1,
    "biogenic_carbon_in_product": -0.05,
}
LAYER = {"material_name_1": "brick", "thickness_1_m": 0.20}
EXPECTED_TOTAL = 100.0       # 0.5 x 200
EXPECTED_PRODUCTION = 80.0   # 0.4 x 200
EXPECTED_RECYCLING = 20.0    # 0.1 x 200

DIRECT_ROW = {
    "code": "WALL_DIRECT",
    "U_wall": 0.25,
    "GHG_wall_kgCO2m2": 90.0,
    "GHG_biogenic_wall_kgCO2m2": -5.0,
    "Service_Life_wall": 40,
}


def _wall(locator, code="WALL_A"):
    df = Envelope.from_locator(locator).wall
    df = df if df.index.name == "code" else df.set_index("code")
    return df.loc[code]


def test_a_layered_row_derives_the_split(envelope_scenario):
    locator = envelope_scenario(
        [BRICK], wall=[{"code": "WALL_A", **LAYER, "Service_Life_wall": 40}]
    )

    row = _wall(locator)
    assert float(row["GHG_wall_kgCO2m2"]) == pytest.approx(EXPECTED_TOTAL)
    assert float(row["GHG_production_wall_kgCO2m2"]) == pytest.approx(EXPECTED_PRODUCTION)
    assert float(row["GHG_recycling_wall_kgCO2m2"]) == pytest.approx(EXPECTED_RECYCLING)


def test_the_split_adds_up_to_the_total(envelope_scenario):
    """The split reallocates the total; it must not invent or lose emissions."""
    locator = envelope_scenario(
        [BRICK], wall=[{"code": "WALL_A", **LAYER, "Service_Life_wall": 40}]
    )

    row = _wall(locator)
    parts = float(row["GHG_production_wall_kgCO2m2"]) + float(row["GHG_recycling_wall_kgCO2m2"])
    assert parts == pytest.approx(float(row["GHG_wall_kgCO2m2"]))


def test_one_file_can_hold_split_and_unsplit_rows(envelope_scenario):
    """The reason the decision is per row: once any row derives a split the columns exist for
    every row, so a direct-property row must fall back on its own values, not read NaN."""
    locator = envelope_scenario(
        [BRICK],
        wall=[{"code": "WALL_A", **LAYER, "Service_Life_wall": 40}, DIRECT_ROW],
    )
    lookup = EnvelopeLookup.from_locator(locator)

    production, demolition, biogenic = envelope_emission_intensities(lookup, "WALL_A")
    assert (production, demolition) == pytest.approx(
        (EXPECTED_PRODUCTION, EXPECTED_RECYCLING)
    )

    production, demolition, biogenic = envelope_emission_intensities(lookup, "WALL_DIRECT")
    assert production == pytest.approx(90.0), "must use its own total, not NaN"
    assert demolition == pytest.approx(0.0)
    assert biogenic == pytest.approx(-5.0)


def test_a_database_without_materials_reports_no_demolition(envelope_scenario):
    """The DE/SG shape: no MATERIALS.csv, so nothing to derive. The lifecycle total is still
    right -- it is attributed entirely to production."""
    direct_only = {
        "wall": [DIRECT_ROW],
        "roof": [{"code": "ROOF_A", "U_roof": 0.3, "GHG_roof_kgCO2m2": 50.0,
                  "Service_Life_roof": 40}],
        "floor": [{"code": "FLOOR_A", "U_base": 0.3, "GHG_floor_kgCO2m2": 50.0,
                   "Service_Life_floor": 40}],
    }
    locator = envelope_scenario([BRICK], **direct_only)
    # No MATERIALS.csv at all: the DE/SG shape.
    os.remove(locator.get_database_components_materials())

    lookup = EnvelopeLookup.from_locator(locator)
    production, demolition, _biogenic = envelope_emission_intensities(lookup, "WALL_DIRECT")

    assert production == pytest.approx(90.0)
    assert demolition == pytest.approx(0.0)


def test_a_window_reports_no_demolition(envelope_scenario):
    """Windows have no material layers, so they can never derive a split."""
    locator = envelope_scenario([BRICK], wall=[{"code": "WALL_A", **LAYER,
                                                "Service_Life_wall": 40}])
    write_database_csv(
        locator.get_database_assemblies_envelope_window(),
        [{"code": "WINDOW_A", "U_win": 1.2, "GHG_win_kgCO2m2": 47.0,
          "GHG_biogenic_win_kgCO2m2": 0.0, "Service_Life_win": 30,
          "G_win": 0.6, "e_win": 0.9, "F_F": 0.2}],
    )
    lookup = EnvelopeLookup.from_locator(locator)

    _production, demolition, _biogenic = envelope_emission_intensities(lookup, "WINDOW_A")

    assert demolition == pytest.approx(0.0)


def test_a_hand_written_split_that_does_not_add_up_is_rejected(envelope_scenario):
    """A direct-property row carrying all three gets no arbiter from materials, so the only
    check available is that the parts add up to the whole."""
    locator = envelope_scenario(
        [BRICK],
        wall=[{**DIRECT_ROW,
               "GHG_production_wall_kgCO2m2": 10.0,
               "GHG_recycling_wall_kgCO2m2": 5.0}],   # 15 vs a stated total of 90
    )

    with pytest.raises(ValueError, match="does not add up"):
        Envelope.from_locator(locator)


def test_a_hand_written_split_within_tolerance_is_accepted(envelope_scenario):
    """Published figures are rounded, so the check has the cross-check's 1% tolerance."""
    locator = envelope_scenario(
        [BRICK],
        wall=[{**DIRECT_ROW,
               "GHG_production_wall_kgCO2m2": 72.0,
               "GHG_recycling_wall_kgCO2m2": 18.4}],  # 90.4 vs 90.0: 0.44%
    )

    row = _wall(locator, "WALL_DIRECT")
    assert float(row["GHG_production_wall_kgCO2m2"]) == pytest.approx(72.0)


def test_the_split_is_written_back_to_the_csv(envelope_scenario):
    """Persisted so a reader sees the split without re-deriving it."""
    locator = envelope_scenario(
        [BRICK], wall=[{"code": "WALL_A", **LAYER, "Service_Life_wall": 40}]
    )
    path = locator.get_database_assemblies_envelope_wall()
    assert "GHG_production_wall_kgCO2m2" not in pd.read_csv(path).columns

    Envelope.from_locator(locator).save(locator)

    saved = pd.read_csv(path).set_index("code")
    assert float(saved.loc["WALL_A", "GHG_production_wall_kgCO2m2"]) == pytest.approx(
        EXPECTED_PRODUCTION
    )
