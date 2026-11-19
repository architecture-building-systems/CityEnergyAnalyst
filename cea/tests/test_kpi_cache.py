"""The KPI cache gate: a hit depends on the source file, definition and args, not on `inputs/`."""

import os

import pandas as pd
import pytest

from cea.inputlocator import InputLocator
from cea.kpi import cache, status
from cea.kpi.cache import compute_kpi_cached

PV_GENERATION = "solar.annual_pv_generation_kwh"
ARGS = {"panel_type": "PV1"}


@pytest.fixture
def locator(tmp_path):
    return InputLocator(str(tmp_path))


@pytest.fixture
def computes(monkeypatch):
    """Calls to the resolver made through the cache gate."""
    calls = []
    real = cache.compute_kpi

    def counting(*args, **kwargs):
        calls.append(args)
        return real(*args, **kwargs)

    monkeypatch.setattr(cache, "compute_kpi", counting)
    return calls


def _write_pv_totals(locator, kwh):
    path = locator.PV_total_buildings("PV1")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pd.DataFrame({"name": ["B1", "B2"], "E_PV_gen_kWh": [kwh, kwh]}).to_csv(path, index=False)


def _compute(locator, **kwargs):
    return compute_kpi_cached(
        PV_GENERATION, locator.scenario, locator_args_override=ARGS, **kwargs
    )


def test_an_input_edit_does_not_recompute(locator, computes):
    _write_pv_totals(locator, 100.0)
    first = _compute(locator)

    zone = locator.get_zone_geometry()
    os.makedirs(os.path.dirname(zone), exist_ok=True)
    with open(zone, "w") as handle:
        handle.write("edited")

    assert _compute(locator).value == first.value
    assert len(computes) == 1


def test_a_source_edit_recomputes(locator, computes):
    _write_pv_totals(locator, 100.0)
    first = _compute(locator)

    _write_pv_totals(locator, 250.0)

    assert _compute(locator).value != first.value
    assert len(computes) == 2


def test_a_record_with_the_old_inputs_hash_is_still_a_hit(locator, computes):
    _write_pv_totals(locator, 100.0)
    _compute(locator)

    key = next(iter(status.read_status(locator.scenario)["kpis"]))
    record = status.read_kpi(locator.scenario, key)
    status.write_kpi(locator.scenario, key, {**record, "scenario_inputs_hash": "stale"})

    _compute(locator)
    assert len(computes) == 1


def test_force_recomputes(locator, computes):
    _write_pv_totals(locator, 100.0)
    _compute(locator)
    _compute(locator, force=True)
    assert len(computes) == 2


def _record(definition_hash="d1", computed_at="2026-01-01T00:00:00+00:00"):
    return {"value": 1.0, "kpi_definition_hash": definition_hash, "computed_at": computed_at}


def _keys(locator):
    return set(status.read_status(locator.scenario)["kpis"])


def test_a_write_drops_variants_of_an_older_definition(locator):
    status.write_kpi(locator.scenario, "a.kpi::old", _record("d0"))
    status.write_kpi(locator.scenario, "a.kpi::kept", _record("d1"))
    status.write_kpi(locator.scenario, "b.kpi::other", _record("d0"))

    status.write_kpi(locator.scenario, "a.kpi::new", _record("d1"))

    assert _keys(locator) == {"a.kpi::kept", "a.kpi::new", "b.kpi::other"}


def test_the_oldest_variants_go_past_the_cap(locator, monkeypatch):
    monkeypatch.setattr(status, "MAX_VARIANTS_PER_KPI", 3)
    for day in range(1, 5):
        status.write_kpi(locator.scenario, f"a.kpi::v{day}", _record(computed_at=f"2026-01-0{day}"))

    assert _keys(locator) == {"a.kpi::v2", "a.kpi::v3", "a.kpi::v4"}


def test_the_record_just_written_survives_the_cap(locator, monkeypatch):
    monkeypatch.setattr(status, "MAX_VARIANTS_PER_KPI", 1)
    status.write_kpi(locator.scenario, "a.kpi::new", _record(computed_at="2026-01-01"))
    status.write_kpi(locator.scenario, "a.kpi::older", _record(computed_at="2025-01-01"))

    assert _keys(locator) == {"a.kpi::older"}
