"""Envelope rows may describe their construction with material layers or with direct properties.

The rule under test: U and the two GHG columns may be left empty when the row defines at least
one material layer -- a material name paired with a thickness greater than zero. A row with no
usable layer must carry the direct properties instead. Service life is always required and
always positive.
"""

import pandas as pd
import pytest

from cea.datamanagement.database.assemblies import Envelope
from cea.datamanagement.format_helper.cea4_verify_db import verify_file_against_schema_4_db

MATERIAL = {
    "name": "brick",
    "thermal_conductivity": 0.6,
    "density": 1000.0,
    "unit": "kg",
    "GHG_emission_total": 0.5,
    "GHG_emission_production": 0.4,
    "GHG_emission_disposal": 0.1,
    "biogenic_carbon_in_product": -0.05,
}

# brick at 0.20 m plus surface resistances; the value the layers derive on their own.
DERIVED_U = 2.006688963210702


@pytest.fixture
def wall(envelope_scenario):
    """Yields ``write(**row)``, replacing ENVELOPE_WALL with one row and returning the locator."""
    def write(**row):
        return envelope_scenario([MATERIAL], wall=[{"code": "WALL_A", **row}])

    return write


def _wall_row(locator):
    df = Envelope.from_locator(locator).wall
    return df.loc["WALL_A"] if df.index.name == "code" else df.set_index("code").loc["WALL_A"]


def _wall_errors(locator):
    _missing, errors = verify_file_against_schema_4_db(
        locator.scenario, "ENVELOPE", sheet_name="ENVELOPE_WALL"
    )
    return [error for error in errors if isinstance(error, str)]


# --- loading --------------------------------------------------------------------------------

def test_one_layer_is_enough_to_leave_u_and_ghg_empty(wall):
    """The reported case: a single layer, the other two slots blank, no U or GHG columns."""
    locator = wall(material_name_1="brick", thickness_1_m=0.20, Service_Life_wall=40)

    row = _wall_row(locator)
    assert float(row["U_wall"]) == pytest.approx(DERIVED_U)
    assert float(row["GHG_wall_kgCO2m2"]) > 0


def test_third_layer_alone_is_enough(wall):
    """Any one of the three slots satisfies the rule, not just the first."""
    locator = wall(material_name_3="brick", thickness_3_m=0.15, Service_Life_wall=40)

    assert float(_wall_row(locator)["U_wall"]) > 0


def test_no_usable_layer_requires_the_direct_properties(wall):
    """A name with zero thickness is an unused slot, so this row has nothing to derive from."""
    locator = wall(material_name_1="brick", thickness_1_m=0.0, Service_Life_wall=40)

    with pytest.raises(ValueError, match="at least one material layer"):
        Envelope.from_locator(locator)


def test_direct_properties_still_carry_a_row_with_no_layers(wall):
    locator = wall(U_wall=0.25, GHG_wall_kgCO2m2=90.0, GHG_biogenic_wall_kgCO2m2=-5.0,
                   Service_Life_wall=40)

    assert float(_wall_row(locator)["U_wall"]) == pytest.approx(0.25)


def test_thickness_without_a_material_is_rejected(wall):
    """Skipping this layer would silently understate the construction, so it must not load."""
    locator = wall(material_name_1="brick", thickness_1_m=0.20, thickness_2_m=0.30,
                   Service_Life_wall=40)

    with pytest.raises(ValueError, match="at least one material layer"):
        Envelope.from_locator(locator)


# --- cross-check ----------------------------------------------------------------------------

def test_a_genuine_zero_is_cross_checked_like_any_other_value(wall):
    """Zero is a real claim about the construction, not a stand-in for "empty"."""
    locator = wall(material_name_1="brick", thickness_1_m=0.20, U_wall=0,
                   GHG_wall_kgCO2m2=0, GHG_biogenic_wall_kgCO2m2=0, Service_Life_wall=40)

    with pytest.raises(ValueError, match="cross-check failed"):
        Envelope.from_locator(locator)


def test_a_partly_filled_direct_set_is_still_cross_checked(wall):
    """Only U is filled in, which is not a complete direct set -- but it is still a claim, so
    it must be compared rather than silently overwritten by the derived value."""
    locator = wall(material_name_1="brick", thickness_1_m=0.20, U_wall=0.25,
                   Service_Life_wall=40)

    with pytest.raises(ValueError, match="U_wall"):
        Envelope.from_locator(locator)


def test_a_partly_filled_direct_set_that_agrees_still_loads(wall):
    """The partial comparison must not reject a value that matches the materials."""
    locator = wall(material_name_1="brick", thickness_1_m=0.20, U_wall=DERIVED_U,
                   Service_Life_wall=40)

    assert float(_wall_row(locator)["U_wall"]) == pytest.approx(DERIVED_U)


# --- database verifier ----------------------------------------------------------------------

def test_verifier_accepts_a_single_layer(wall):
    locator = wall(material_name_1="brick", thickness_1_m=0.20, Service_Life_wall=40)

    assert _wall_errors(locator) == []


def test_verifier_rejects_a_row_with_neither_layers_nor_direct_properties(wall):
    locator = wall(material_name_1="brick", thickness_1_m=0.0, Service_Life_wall=40)

    assert any("required column sets" in error for error in _wall_errors(locator))


@pytest.mark.parametrize("service_life", [0, -5, None])
def test_verifier_rejects_non_positive_service_life(wall, service_life):
    locator = wall(material_name_1="brick", thickness_1_m=0.20, Service_Life_wall=service_life)

    assert any("greater than 0" in error for error in _wall_errors(locator))


def test_verifier_accepts_a_positive_service_life(wall):
    locator = wall(material_name_1="brick", thickness_1_m=0.20, Service_Life_wall=25)

    assert _wall_errors(locator) == []



# --- derivation on save ---------------------------------------------------------------------

def test_saving_re_derives_from_edited_layers(envelope_scenario):
    """Editing a layer used to keep the U/GHG describing the previous composition, producing
    a file that no longer loads. Saving must recompute them."""
    locator = envelope_scenario(
        [MATERIAL],
        wall=[{"code": "WALL_A", "material_name_1": "brick", "thickness_1_m": 0.20,
               "U_wall": DERIVED_U, "Service_Life_wall": 40}],
    )
    envelope = Envelope.from_locator(locator, strict=False)
    envelope.wall.loc["WALL_A", "thickness_1_m"] = 0.30

    materials = pd.read_csv(locator.get_database_components_materials())
    envelope.apply_material_derivation(materials)
    envelope.save(locator)

    # The written file must load under the strict rules the simulation uses.
    reloaded = _wall_row(locator)
    assert float(reloaded["thickness_1_m"]) == pytest.approx(0.30)
    assert float(reloaded["U_wall"]) != pytest.approx(DERIVED_U)


def test_a_contradicting_stored_value_is_reported(envelope_scenario):
    """A stored value that disagrees with the layers is returned so the caller can confirm."""
    locator = envelope_scenario(
        [MATERIAL],
        wall=[{"code": "WALL_A", "material_name_1": "brick", "thickness_1_m": 0.20,
               "U_wall": 0.25, "Service_Life_wall": 40}],
    )
    envelope = Envelope.from_locator(locator, strict=False)
    materials = pd.read_csv(locator.get_database_components_materials())

    conflicts = envelope.apply_material_derivation(materials)

    assert [(c["code"], c["column"]) for c in conflicts] == [("WALL_A", "U_wall")]
    assert conflicts[0]["stored"] == pytest.approx(0.25)
    assert conflicts[0]["derived"] == pytest.approx(DERIVED_U)


def test_filling_an_empty_value_is_not_a_conflict(envelope_scenario):
    """Deriving into a blank cell needs no confirmation -- nothing is being overwritten."""
    locator = envelope_scenario(
        [MATERIAL],
        wall=[{"code": "WALL_A", "material_name_1": "brick", "thickness_1_m": 0.20,
               "Service_Life_wall": 40}],
    )
    envelope = Envelope.from_locator(locator, strict=False)
    materials = pd.read_csv(locator.get_database_components_materials())

    assert envelope.apply_material_derivation(materials) == []
    assert float(envelope.wall.loc["WALL_A", "U_wall"]) == pytest.approx(DERIVED_U)


def test_rows_without_layers_are_left_alone(envelope_scenario):
    """A direct-property row has nothing to derive from and must not be touched."""
    locator = envelope_scenario(
        [MATERIAL],
        wall=[{"code": "WALL_A", "U_wall": 0.25, "GHG_wall_kgCO2m2": 90.0,
               "GHG_biogenic_wall_kgCO2m2": -5.0, "Service_Life_wall": 40}],
    )
    envelope = Envelope.from_locator(locator, strict=False)
    materials = pd.read_csv(locator.get_database_components_materials())

    assert envelope.apply_material_derivation(materials) == []
    assert float(envelope.wall.loc["WALL_A", "U_wall"]) == pytest.approx(0.25)
