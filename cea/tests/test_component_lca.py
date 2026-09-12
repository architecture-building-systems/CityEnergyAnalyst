"""Service life resolution: the component's own data first, then documented fallbacks.

Replacement count scales inversely with service life, so an assumed value changes the
embodied result. Every path therefore reports which source it used.
"""

import glob
import os

import pandas as pd
import pytest

from cea.analysis.lca.component_lca import (
    GM_FALLBACK_SERVICE_LIFE_YR,
    GM_SERVICE_LIFE_YR,
    resolve_service_life,
)
from cea.tests import paths


def test_the_components_own_value_wins():
    result = resolve_service_life("BOILERS", 20)

    assert result == (20, "database")
    assert not result.is_assumed


def test_the_components_own_value_wins_even_when_it_differs_from_the_reference():
    """CEA's LT_yr is data about a specific component; the Green Mark value is a category
    default. UNITARY_AIR_CONDITIONERS is where the two disagree most (25 vs 10)."""
    assert resolve_service_life("UNITARY_AIR_CONDITIONERS", 25).years == 25
    assert GM_SERVICE_LIFE_YR["UNITARY_AIR_CONDITIONERS"] == 10


def test_a_missing_value_falls_back_to_the_green_mark_reference():
    result = resolve_service_life("UNITARY_AIR_CONDITIONERS", None)

    assert result == (10, "green_mark_reference")
    assert result.is_assumed


def test_a_family_with_no_reference_falls_back_further():
    """FUEL_CELLS and BORE_HOLES have no Green Mark counterpart."""
    result = resolve_service_life("FUEL_CELLS", None)

    assert result == (GM_FALLBACK_SERVICE_LIFE_YR, "fallback")
    assert result.is_assumed


@pytest.mark.parametrize("unusable", [None, 0, -5, "", "n/a", float("nan")])
def test_an_unusable_value_is_treated_as_absent(unusable):
    """A zero or negative service life would make replacement scheduling meaningless."""
    result = resolve_service_life("BOILERS", unusable)

    assert result.is_assumed
    assert result.years == GM_SERVICE_LIFE_YR["BOILERS"]


def test_the_family_name_is_matched_case_insensitively():
    assert resolve_service_life("boilers", None).years == GM_SERVICE_LIFE_YR["BOILERS"]


def test_every_shipped_component_resolves_from_its_own_data():
    """No shipped component should need a fallback -- if one does, the database lost a value."""
    pattern = os.path.join(
        str(paths.REPO_ROOT), "cea", "databases", "*", "COMPONENTS", "CONVERSION", "*.csv"
    )
    assumed = []
    checked = 0
    for path in sorted(glob.glob(pattern)):
        family = os.path.splitext(os.path.basename(path))[0]
        frame = pd.read_csv(path)
        if "LT_yr" not in frame.columns:
            assumed.append(f"{family}: no LT_yr column")
            continue
        for code, lt_yr in zip(frame.get("code", frame.index), frame["LT_yr"]):
            checked += 1
            if resolve_service_life(family, lt_yr).is_assumed:
                assumed.append(f"{family}/{code}")

    assert checked > 0, "no conversion components found to check"
    assert assumed == [], assumed


def test_every_reference_value_is_plausible():
    """Guards against a typo in the mapping table (e.g. months instead of years)."""
    for family, years in GM_SERVICE_LIFE_YR.items():
        assert 5 <= years <= 60, f"{family}={years}"


# --- resolving from a component code -------------------------------------------------------

@pytest.fixture
def ch_locator(tmp_path):
    """A scenario holding the shipped CH database, safe to mutate."""
    import shutil
    import cea.config
    from cea.inputlocator import InputLocator

    config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    config.project = str(tmp_path)
    config.scenario_name = "s"
    shutil.copytree(
        os.path.join(str(paths.REPO_ROOT), "cea", "databases", "CH"),
        os.path.join(config.scenario, "inputs", "database"),
        dirs_exist_ok=True,
    )
    return InputLocator(config.scenario)


@pytest.mark.parametrize("code,expected", [("BO1", 20), ("CH1", 25), ("HP1", 20), ("PV1", 25)])
def test_a_real_component_code_resolves_from_the_database(ch_locator, code, expected):
    from cea.analysis.lca.component_lca import service_life_for_component

    result = service_life_for_component(code, ch_locator)

    assert result == (expected, "database")


def test_an_unknown_code_falls_back_rather_than_raising(ch_locator):
    """An unrecognised component must not stop an emissions run; the guess is reported."""
    from cea.analysis.lca.component_lca import service_life_for_component

    result = service_life_for_component("NO_SUCH_COMPONENT", ch_locator)

    assert result == (GM_FALLBACK_SERVICE_LIFE_YR, "fallback")
    assert result.is_assumed


def test_a_blank_lt_yr_in_the_database_uses_the_reference(ch_locator):
    """The tier-2 path, exercised through the real lookup rather than in isolation."""
    from cea.analysis.lca.component_lca import service_life_for_component

    path = ch_locator.get_db4_components_conversion_conversion_technology_csv("BOILERS")
    frame = pd.read_csv(path)
    frame["LT_yr"] = None
    frame.to_csv(path, index=False)

    result = service_life_for_component("BO1", ch_locator)

    assert result == (GM_SERVICE_LIFE_YR["BOILERS"], "green_mark_reference")


# --- embodied-carbon factor (optional column) ----------------------------------------------

def test_the_factor_column_is_optional_everywhere():
    """Declared in every conversion schema, required by none: no shipped database has data
    yet, so demanding it would report every database as incomplete."""
    import cea.schemas
    from cea.analysis.lca.component_lca import EMBODIED_FACTOR_COLUMN

    schemas = cea.schemas.schemas(plugins=[])
    conversion = [k for k in schemas if k.startswith("get_database_components_conversion_")]
    assert conversion, "no conversion schemas found"
    for key in conversion:
        spec = schemas[key]["schema"]["columns"].get(EMBODIED_FACTOR_COLUMN)
        assert spec is not None, f"{key} does not declare it"
        assert spec["nullable"] is True, f"{key} declares it as required"


def test_a_component_with_no_factor_returns_none(ch_locator):
    """None is the normal answer today, and must not be an error: the caller falls back to
    the blanket per-GFA intensity."""
    from cea.analysis.lca.component_lca import embodied_factor_for_component

    assert embodied_factor_for_component("BO1", ch_locator) is None


def test_an_unknown_component_returns_none(ch_locator):
    from cea.analysis.lca.component_lca import embodied_factor_for_component

    assert embodied_factor_for_component("NO_SUCH_COMPONENT", ch_locator) is None


def test_an_authored_factor_is_read_with_the_capacity_unit(ch_locator):
    """The factor is capacity-based like the cost curve, so it travels with its unit --
    callers must not assume watts (transformers are VA, collectors m2, storage m3/kWh)."""
    from cea.analysis.lca.component_lca import (
        EMBODIED_FACTOR_COLUMN,
        embodied_factor_for_component,
    )

    path = ch_locator.get_db4_components_conversion_conversion_technology_csv("BOILERS")
    frame = pd.read_csv(path)
    frame[EMBODIED_FACTOR_COLUMN] = 0.0042
    frame.to_csv(path, index=False)

    factor = embodied_factor_for_component("BO1", ch_locator)

    assert factor is not None
    assert factor.kgCO2e_per_unit == pytest.approx(0.0042)
    assert factor.unit == "W"
    assert factor.family == "BOILERS"


@pytest.mark.parametrize("unusable", [None, 0, -1, "", "n/a"])
def test_an_unusable_factor_is_treated_as_absent(ch_locator, unusable):
    from cea.analysis.lca.component_lca import (
        EMBODIED_FACTOR_COLUMN,
        embodied_factor_for_component,
    )

    path = ch_locator.get_db4_components_conversion_conversion_technology_csv("BOILERS")
    frame = pd.read_csv(path)
    frame[EMBODIED_FACTOR_COLUMN] = unusable
    frame.to_csv(path, index=False)

    assert embodied_factor_for_component("BO1", ch_locator) is None


def test_photovoltaic_panels_are_read_from_their_legacy_column(ch_locator):
    """PV shipped a per-m2 factor before the shared column existed; it should still be found,
    and reported in m2 rather than the table's W capacity unit."""
    from cea.analysis.lca.component_lca import embodied_factor_for_component

    factor = embodied_factor_for_component("PV1", ch_locator)

    assert factor is not None
    assert factor.unit == "m2"
    assert factor.kgCO2e_per_unit > 0
