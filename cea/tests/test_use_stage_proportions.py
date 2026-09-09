"""Maintenance (B2) and repair (B3) are proportions of production, not modelled activities.

EN 15978 asks for both; modelling them needs maintenance schedules CEA does not have. RICS
(2017) sanctions estimating them as fractions of the product stage, and Green Mark Version 7's
Cn Technical Guide (Table 16, GWP Base Formulae) adopts that. Neither formula carries a
frequency term -- unlike B4 replacement -- so the allowance is charged once per installed
generation, on the component's own replacement cycle.
"""

import pandas as pd
import pytest

from cea.analysis.lca.emission_timeline import (
    DEFAULT_MAINTENANCE_FRACTION,
    DEFAULT_REPAIR_FRACTION,
    BuildingYearlyEmissionTimeline,
)

AREA = 100.0
PRODUCTION_PER_AREA = 10.0
LIFETIME = 25
START_YEAR = 2000
END_YEAR = 2100
KEY = "wall_ag"


class _Timeline:
    """Exercises `log_emissions` on a bare timeline frame, without BuildingProperties."""

    def __init__(self, maintenance=DEFAULT_MAINTENANCE_FRACTION, repair=DEFAULT_REPAIR_FRACTION):
        years = [f"Y_{year}" for year in range(START_YEAR, END_YEAR + 1)]
        columns = [
            f"{phase}_{KEY}_kgCO2e"
            for phase in BuildingYearlyEmissionTimeline._EMISSION_TYPES
        ]
        self.timeline = pd.DataFrame(0.0, index=years, columns=columns)
        self.typology = {"year": START_YEAR}
        self.maintenance_fraction = maintenance
        self.repair_fraction = repair
        self.notes: list[str] = []

    def _append_note(self, **_kwargs):
        pass

    log_emissions = BuildingYearlyEmissionTimeline.log_emissions
    _log_emission_with_lifetime = BuildingYearlyEmissionTimeline._log_emission_with_lifetime
    log = BuildingYearlyEmissionTimeline.log

    def totals(self) -> dict[str, float]:
        return {
            phase: float(self.timeline[f"{phase}_{KEY}_kgCO2e"].sum())
            for phase in BuildingYearlyEmissionTimeline._EMISSION_TYPES
        }


def _run(**kwargs) -> dict[str, float]:
    timeline = _Timeline(**kwargs)
    timeline.log_emissions(AREA, PRODUCTION_PER_AREA, 0.0, 0.0, LIFETIME, KEY)
    return timeline.totals()


def test_the_reported_phases_cover_the_modules_cea_accounts_for():
    assert BuildingYearlyEmissionTimeline._EMISSION_TYPES == [
        "production", "biogenic", "demolition", "maintenance", "repair",
    ]


def test_maintenance_is_the_configured_fraction_of_production():
    totals = _run()

    assert totals["maintenance"] == pytest.approx(
        totals["production"] * DEFAULT_MAINTENANCE_FRACTION
    )


def test_repair_is_the_configured_fraction_of_production():
    totals = _run()

    assert totals["repair"] == pytest.approx(totals["production"] * DEFAULT_REPAIR_FRACTION)


def test_the_rics_defaults_are_one_and_ten_percent():
    """The published figures: B2 at 1%, B3 at 10%. A silent drift here would change every
    reported result, so the constants are asserted rather than assumed."""
    assert DEFAULT_MAINTENANCE_FRACTION == 0.01
    assert DEFAULT_REPAIR_FRACTION == 0.10


def test_they_follow_the_replacement_cycle_not_the_calendar():
    """Charged once per installed generation, so the count matches production's."""
    timeline = _Timeline()
    timeline.log_emissions(AREA, PRODUCTION_PER_AREA, 0.0, 0.0, LIFETIME, KEY)

    production_years = (timeline.timeline[f"production_{KEY}_kgCO2e"] > 0).sum()
    for phase in ("maintenance", "repair"):
        assert (timeline.timeline[f"{phase}_{KEY}_kgCO2e"] > 0).sum() == production_years


def test_setting_a_fraction_to_zero_excludes_the_module():
    """A user who does not want an estimated module must be able to switch it off."""
    totals = _run(maintenance=0.0, repair=0.0)

    assert totals["maintenance"] == 0.0
    assert totals["repair"] == 0.0
    assert totals["production"] > 0.0


def test_they_do_not_alter_production_or_end_of_life():
    """Additive modules: adding B2/B3 must not move the phases that were already reported."""
    with_estimates = _run()
    without = _run(maintenance=0.0, repair=0.0)

    assert with_estimates["production"] == pytest.approx(without["production"])
    assert with_estimates["demolition"] == pytest.approx(without["demolition"])


def test_the_plot_layer_has_a_colour_for_each_new_phase():
    """An uncoloured phase silently renders grey, indistinguishable from biogenic."""
    from cea.analysis.lca.emission_timeline import TIMELINE_COMPONENTS
    from cea.visualisation.format.plot_colours import get_column_color

    uncoloured = [
        f"{phase}_{component}"
        for phase in ("maintenance", "repair")
        for component in TIMELINE_COMPONENTS
        if get_column_color(f"{phase}_{component}_kgCO2e") == "grey"
    ]
    assert uncoloured == [], uncoloured
