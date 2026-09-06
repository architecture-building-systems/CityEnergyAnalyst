"""Envelope row handling when baking a pathway state from an intervention template.

Baking copies an envelope row and patches template fields onto it. The direct-property
``U_*``/``GHG_*`` columns are a cache of the material layers, so they must be dropped when the
layers change or the copy keeps numbers describing the old composition (issue #4059).
"""

import os
import shutil
import tempfile

import pandas as pd
import pytest

import cea.config
import cea.datamanagement.district_pathways.pathway_state as pathway_state
from cea.datamanagement.database.envelope_lookup import EnvelopeLookup
from cea.inputlocator import InputLocator

PATHWAY_NAME = "demo"
YEAR = 2029
ARCHETYPE = "STANDARD1"

# Layers shared by every row in the fixture, and the values assemblies.py derives from them.
# The source row's cache has to agree with its own materials, or the loader rejects the
# fixture before the code under test runs.
LAYERS = {
    "material_name_1": "brick",
    "thickness_1_m": 0.20,
    "material_name_2": "insulation",
    "thickness_2_m": 0.10,
    "material_name_3": "plaster",
    "thickness_3_m": 0.02,
}
DERIVED_U = 0.3335  # 1 / (0.20/0.6 + 0.10/0.04 + 0.02/0.8), to 4 s.f.
DERIVED_GHG = 160.0

ROOF_CACHE_COLS = ("U_roof", "GHG_roof_kgCO2m2", "GHG_biogenic_roof_kgCO2m2")


def _write_csv(path: str, rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


@pytest.fixture
def baked_state(monkeypatch):
    """A minimal pathway state whose roof row carries both layers and a consistent cache.

    Yields ``(state_locator, apply)`` where ``apply(recipe)`` runs
    ``_apply_state_construction_changes`` for the fixture's pathway/year.
    """
    root = tempfile.mkdtemp()
    config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    config.project = root
    config.scenario_name = "baseline"

    main_locator = InputLocator(config.scenario)
    state = InputLocator(
        main_locator.get_state_in_time_scenario_folder(PATHWAY_NAME, YEAR)
    )

    _write_csv(
        state.get_database_archetypes_construction_type(),
        [{
            "const_type": ARCHETYPE,
            "type_wall": "WALL_A",
            "type_roof": "ROOF_A",
            "type_base": "FLOOR_A",
            "type_floor": "FLOOR_A",
        }],
    )
    _write_csv(
        state.get_database_components_materials(),
        [
            {
                "name": name,
                "thermal_conductivity": conductivity,
                "density": 1000.0,
                "unit": "kg",
                "GHG_emission_total": 0.5,
                "GHG_emission_production": 0.4,
                "GHG_emission_recycling": 0.1,
                "biogenic_carbon_in_product": -0.05,
            }
            for name, conductivity in (("brick", 0.6), ("insulation", 0.04), ("plaster", 0.8))
        ],
    )
    _write_csv(
        state.get_database_assemblies_envelope_wall(),
        [{"code": "WALL_A", **LAYERS, "Service_Life_wall": 50}],
    )
    _write_csv(
        state.get_database_assemblies_envelope_floor(),
        [{"code": "FLOOR_A", **LAYERS, "Service_Life_floor": 60}],
    )
    # Only the roof carries a direct-property cache — the shape the issue reporter added to
    # their database, and the one the stock CH database does not ship.
    _write_csv(
        state.get_database_assemblies_envelope_roof(),
        [{
            "code": "ROOF_A",
            **LAYERS,
            "Service_Life_roof": 40,
            "U_roof": DERIVED_U,
            "GHG_roof_kgCO2m2": DERIVED_GHG,
            "GHG_biogenic_roof_kgCO2m2": -16.0,  # 320 kg/m2 x -0.05
        }],
    )

    # Per-building regeneration needs a full scenario and is not what these tests exercise.
    monkeypatch.setattr(
        pathway_state, "_regenerate_building_properties_from_archetypes", lambda *a, **k: None
    )

    def apply(recipe):
        return pathway_state._apply_state_construction_changes(
            config, PATHWAY_NAME, YEAR, recipe
        )

    yield state, apply
    shutil.rmtree(root, ignore_errors=True)


def _baked_roof_row(state: InputLocator) -> pd.Series:
    df = pd.read_csv(state.get_database_assemblies_envelope_roof(), index_col="code")
    baked = [code for code in df.index if "YEAR" in str(code)]
    assert len(baked) == 1, f"expected one baked roof row, found {baked}"
    return df.loc[baked[0]]


def test_editing_layers_clears_the_stale_cache(baked_state):
    """Issue #4059: a layer edit must not leave the source row's U/GHG behind.

    The source row already has a full material set, so this is not a promotion — which is
    exactly the case the original `is_material_promotion` gate skipped.
    """
    state, apply = baked_state

    assert apply({ARCHETYPE: {"roof": {"thickness_1_m": 0.30}}}) is True

    row = _baked_roof_row(state)
    assert row["thickness_1_m"] == pytest.approx(0.30)
    for col in ROOF_CACHE_COLS:
        assert pd.isna(row[col]), f"{col} still holds a value derived from the old layers"

    # Step 7 of the issue: the next load re-derives from the new layers instead of raising
    # "Envelope cross-check failed for roof".
    envelope = EnvelopeLookup.from_locator(state)
    reloaded = envelope._df_for("roof").loc[row.name]
    assert float(reloaded["U_roof"]) != pytest.approx(DERIVED_U, rel=0.01)


def test_explicit_value_in_the_recipe_survives(baked_state):
    """A recipe that sets layers AND a U means that U; only the untouched cache is cleared."""
    state, apply = baked_state

    apply({ARCHETYPE: {"roof": {"thickness_1_m": 0.30, "U": 0.25}}})

    row = _baked_roof_row(state)
    assert float(row["U_roof"]) == pytest.approx(0.25)
    for col in (c for c in ROOF_CACHE_COLS if c != "U_roof"):
        assert pd.isna(row[col])


def test_non_material_edit_keeps_the_cache(baked_state):
    """Editing only a direct property must not blank values the layers still agree with."""
    state, apply = baked_state

    apply({ARCHETYPE: {"roof": {"Service_Life": 55}}})

    row = _baked_roof_row(state)
    assert float(row["U_roof"]) == pytest.approx(DERIVED_U, rel=1e-3)
    assert float(row["GHG_roof_kgCO2m2"]) == pytest.approx(DERIVED_GHG, rel=1e-3)


def test_promotion_still_requires_the_full_material_set(baked_state):
    """The promotion guard is independent of the cache clearing and must be unchanged."""
    state, apply = baked_state

    # Strip the roof's layers so the source is direct-property only.
    roof_path = state.get_database_assemblies_envelope_roof()
    df = pd.read_csv(roof_path).drop(columns=list(LAYERS))
    df.to_csv(roof_path, index=False)

    with pytest.raises(ValueError, match="full material set must be provided"):
        apply({ARCHETYPE: {"roof": {"material_name_1": "brick"}}})
