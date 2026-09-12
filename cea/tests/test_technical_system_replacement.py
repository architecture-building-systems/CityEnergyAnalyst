"""Technical systems are replaced on each supply component's own service life.

The stack used to renew on a single blanket 25-year cycle regardless of what was installed.
It is now scheduled per supply component (`primary_components` -> `LT_yr`), while the total
embodied intensity stays the blanket per-GFA figure, because the per-component factor is
capacity-based and capacities are not known at this point.
"""

import os
import shutil

import pandas as pd
import pytest

import cea.config
from cea.constants import (
    EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS,
    SERVICE_LIFE_OF_TECHNICAL_SYSTEMS,
)
from cea.inputlocator import InputLocator
from cea.tests import paths

GFA = 1000.0
START_YEAR = 2000
END_YEAR = 2100


class _Timeline:
    """Drives `_log_technical_system_emissions` without a full BuildingProperties."""

    def __init__(self, locator, supply_systems):
        from cea.analysis.lca.emission_timeline import BuildingYearlyEmissionTimeline

        self.locator = locator
        self.supply_systems = supply_systems
        self.typology = {"year": START_YEAR}
        self.notes: list[str] = []
        self.logged: list[tuple[float, int, str]] = []
        # Borrow the real implementations rather than reimplementing the logic under test.
        self._log = BuildingYearlyEmissionTimeline._log_technical_system_emissions
        self._supply_components = (
            lambda: BuildingYearlyEmissionTimeline._supply_components(self)
        )
        self._SUPPLY_SERVICES = BuildingYearlyEmissionTimeline._SUPPLY_SERVICES

    # `_log_technical_system_emissions` calls this; capture instead of writing a frame.
    def log_emissions(self, area, production, biogenic, demolition, lifetime, key,
                      note_detail=None):
        self.logged.append((production, lifetime, note_detail or ""))

    def run(self, area=GFA, key="technical_systems"):
        self._log(self, area=area, key=key)
        return self.logged


@pytest.fixture
def ch_locator(tmp_path):
    config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    config.project = str(tmp_path)
    config.scenario_name = "s"
    shutil.copytree(
        os.path.join(str(paths.REPO_ROOT), "cea", "databases", "CH"),
        os.path.join(config.scenario, "inputs", "database"),
        dirs_exist_ok=True,
    )
    return InputLocator(config.scenario)


def test_each_component_gets_its_own_service_life(ch_locator):
    """BO1 is a 20-year boiler and CH1 a 25-year chiller: they must not share a cycle."""
    timeline = _Timeline(ch_locator, {
        "primary_component_hs": "BO1",
        "primary_component_cs": "CH1",
        "primary_component_dhw": "-",
    })

    logged = timeline.run()

    lifetimes = sorted(lifetime for _p, lifetime, _n in logged)
    assert lifetimes == [20, 25], logged
    assert len(logged) == 2


def test_the_building_total_is_unchanged_by_the_split(ch_locator):
    """A reallocation, not an addition: the intensity is shared, never multiplied."""
    timeline = _Timeline(ch_locator, {
        "primary_component_hs": "BO1",
        "primary_component_cs": "CH1",
        "primary_component_dhw": "BO2",
    })

    logged = timeline.run()

    assert sum(production for production, _l, _n in logged) == pytest.approx(
        EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS
    )


def test_a_building_with_no_supply_components_keeps_the_blanket_behaviour(ch_locator):
    """Every service NONE, or a district connection: must not silently become zero."""
    timeline = _Timeline(ch_locator, {
        "primary_component_hs": "-",
        "primary_component_cs": None,
        "primary_component_dhw": "",
    })

    logged = timeline.run()

    assert len(logged) == 1
    production, lifetime, note = logged[0]
    assert production == pytest.approx(EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS)
    assert lifetime == SERVICE_LIFE_OF_TECHNICAL_SYSTEMS
    assert "blanket" in note


def test_an_assumed_service_life_is_reported_in_the_note(ch_locator):
    """An assumed lifetime changes the replacement count, so it must be visible."""
    path = ch_locator.get_db4_components_conversion_conversion_technology_csv("BOILERS")
    frame = pd.read_csv(path)
    frame["LT_yr"] = None
    frame.to_csv(path, index=False)
    timeline = _Timeline(ch_locator, {"primary_component_hs": "BO1"})

    logged = timeline.run()

    _production, _lifetime, note = logged[0]
    assert "assumed" in note, note


def test_electricity_is_not_treated_as_a_replaceable_component(ch_locator):
    """SUPPLY_ELECTRICITY is a grid connection; it names no conversion component."""
    from cea.analysis.lca.emission_timeline import BuildingYearlyEmissionTimeline

    assert "el" not in BuildingYearlyEmissionTimeline._SUPPLY_SERVICES
