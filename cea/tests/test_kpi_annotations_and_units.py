"""KPI card annotations (which PV panel type a value is for), display units, and the
`panel_type` default that resolves to a panel the scenario actually has results for."""

import asyncio
import json
import os

import pandas as pd
import pytest

from cea.inputlocator import InputLocator
from cea.interfaces.dashboard.api.kpis import get_kpi_parameters, get_kpi_value, get_kpis
from cea.kpi import pv_panels, registry
from cea.kpi.annotations import annotate
from cea.kpi.exceptions import KPIDefinitionError, KPINotAvailable
from cea.kpi.resolver import effective_locator_args
from cea.kpi.schema import KPIDefinition
from cea.kpi.units import convert, unit_choices

PV_GENERATION = "solar.annual_pv_generation_kwh"
FE_PV_GENERATION = "final_energy.pv_generation_mwh"


@pytest.fixture
def locator(tmp_path):
    locator = InputLocator(str(tmp_path))
    panels = locator.get_db4_components_conversion_conversion_technology_csv("PHOTOVOLTAIC_PANELS")
    os.makedirs(os.path.dirname(panels))
    # Two rows for PV1, as the real database has one row per capacity range.
    pd.DataFrame({"code": ["PV1", "PV1", "PV3"],
                  "description": ["typical csi 2024 (BIPV)"] * 2 + ["typical cdte 2024 (BIPV)"]}
                 ).to_csv(panels, index=False)
    return locator


def _write_pv_totals(locator, panel, kwh):
    path = locator.PV_total_buildings(panel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pd.DataFrame({"name": ["B1", "B2"], "E_PV_gen_kWh": [kwh, kwh]}).to_csv(path, index=False)


def _write_whatif(locator, solar_by_building, whatif="w1"):
    locator.write_analysis_configuration(
        whatif, {"buildings": {name: {"solar": solar} for name, solar in solar_by_building.items()}})


# --------------------------------------------------------------------------- units


def test_unit_choices_and_conversion():
    assert unit_choices("MWh/yr") == ["kWh/yr", "MWh/yr", "GWh/yr"]
    assert unit_choices("%") == []
    assert convert(2500.0, "kWh/yr", "MWh/yr") == pytest.approx(2.5)
    assert convert(3.0, "MW", "kW") == pytest.approx(3000.0)
    with pytest.raises(ValueError):
        convert(1.0, "kW", "MWh/yr")


# --------------------------------------------------------------------------- annotations


def test_pv_panel_type_carries_the_database_description(locator):
    assert annotate("pv_panel_type", locator, {"panel_type": "PV1"}) == [
        {"label": "Panel", "value": "PV1 · typical csi 2024 (BIPV)"}]
    assert annotate("pv_panel_type", locator, {"panel_type": "PV9"}) == [
        {"label": "Panel", "value": "PV9 (not in database)"}]


def test_installed_pv_groups_orientations_with_the_same_panel(locator):
    _write_whatif(locator, {
        "B1": {"roof": "PV_PV1", "wall_north": "PV_PV3", "wall_south": "PVT_PV3_FP",
               "wall_east": "SC_ET", "wall_west": None},
        "B2": {"roof": "PV_PV1", "wall_north": "PV_PV3", "wall_south": "PV_PV3"},
    })

    assert annotate("installed_pv_by_orientation", locator, {"whatif_name": "w1"}) == [
        {"label": "Roof", "value": "PV1 · typical csi 2024 (BIPV)"},
        # PVT's electrical half counts as PV3; the solar collector on the east wall does not.
        {"label": "Walls N/S", "value": "PV3 · typical cdte 2024 (BIPV)"},
    ]


def test_installed_pv_counts_buildings_when_they_differ(locator):
    _write_whatif(locator, {f"B{i}": {"roof": "PV_PV1" if i < 3 else "PV_PV3"} for i in range(4)})

    [row] = annotate("installed_pv_by_orientation", locator, {"whatif_name": "w1"})
    assert row["label"] == "Roof"
    assert row["value"] == ("PV1 · typical csi 2024 (BIPV) (3 of 4 buildings), "
                            "PV3 · typical cdte 2024 (BIPV) (1 of 4 buildings)")


def test_installed_pv_counts_buildings_when_only_some_carry_it(locator):
    # final-energy attaches `solar` only to the buildings selected for it.
    _write_whatif(locator, {"B1": {"roof": "PV_PV1", "wall_south": "PV_PV1"}, "B2": {"roof": "PV_PV1"}, "B3": {}})

    assert annotate("installed_pv_by_orientation", locator, {"whatif_name": "w1"}) == [
        {"label": "Roof", "value": "PV1 · typical csi 2024 (BIPV) (2 of 3 buildings)"},
        {"label": "Walls S", "value": "PV1 · typical csi 2024 (BIPV) (1 of 3 buildings)"},
    ]


def test_installed_pv_follows_a_rewritten_configuration(locator):
    _write_whatif(locator, {"B1": {"roof": "PV_PV1"}})
    assert annotate("installed_pv_by_orientation", locator, {"whatif_name": "w1"}) == [
        {"label": "Roof", "value": "PV1 · typical csi 2024 (BIPV)"}]

    _write_whatif(locator, {"B1": {"roof": "PV_PV3"}, "B2": {"wall_north": "PV_PV3"}})
    assert annotate("installed_pv_by_orientation", locator, {"whatif_name": "w1"}) == [
        {"label": "Roof, walls N", "value": "PV3 · typical cdte 2024 (BIPV) (1 of 2 buildings)"}]


def test_installed_pv_is_empty_without_pv_or_configuration(locator):
    assert annotate("installed_pv_by_orientation", locator, {"whatif_name": "w1"}) == []
    _write_whatif(locator, {"B1": {"roof": "SC_FP"}})
    assert annotate("installed_pv_by_orientation", locator, {"whatif_name": "w1"}) == []


# --------------------------------------------------------------------------- panel database


def _write_panels(locator, **columns):
    path = locator.get_db4_components_conversion_conversion_technology_csv("PHOTOVOLTAIC_PANELS")
    pd.DataFrame(columns).to_csv(path, index=False)


def test_panels_without_a_description_show_their_code(locator):
    _write_panels(locator, code=["PV1", "PV3"], description=[None, "  "])
    assert annotate("pv_panel_type", locator, {"panel_type": "PV1"}) == [{"label": "Panel", "value": "PV1"}]
    assert annotate("pv_panel_type", locator, {"panel_type": "PV3"}) == [{"label": "Panel", "value": "PV3"}]
    assert annotate("pv_panel_type", locator, {"panel_type": "PV9"}) == [
        {"label": "Panel", "value": "PV9 (not in database)"}]


@pytest.mark.parametrize("columns", [
    {"code": ["PV1"]},                      # no `description` column
    {"name": ["PV1"], "description": ["x"]},  # no `code` column
])
def test_a_database_missing_columns_does_not_break_the_kpi(locator, columns):
    """The labels are cosmetic: the value, the bulk listing and the dropdown all still work."""
    _write_panels(locator, **columns)
    _write_pv_totals(locator, "PV1", 1500.0)

    value = _value(locator, PV_GENERATION)
    assert (value["available"], value["value"]) == (True, 3000.0)
    assert value["annotations"] == [{"label": "Panel", "value": "PV1"}]

    bulk = asyncio.run(get_kpis(scenario_path=locator.scenario, feature="solar", whatif=None))
    assert {k["id"]: k["available"] for k in bulk["kpis"]}[PV_GENERATION] is True

    params = asyncio.run(get_kpi_parameters(PV_GENERATION, scenario_path=locator.scenario))["parameters"]
    assert params["panel_type"]["choices"] == [{"value": "PV1", "label": "PV1"}]


def test_an_unparseable_database_does_not_break_the_kpi(locator):
    path = locator.get_db4_components_conversion_conversion_technology_csv("PHOTOVOLTAIC_PANELS")
    with open(path, "wb") as f:
        f.write(b"code,description\n\xff\xfe\x00broken")
    _write_pv_totals(locator, "PV1", 1500.0)

    value = _value(locator, PV_GENERATION)
    assert (value["available"], value["annotations"]) == (True, [{"label": "Panel", "value": "PV1"}])


def test_the_database_is_read_once_until_it_changes(locator, monkeypatch):
    _write_pv_totals(locator, "PV1", 1500.0)
    reads = []
    real_read_csv = pd.read_csv
    monkeypatch.setattr(pv_panels.pd, "read_csv", lambda *a, **kw: reads.append(a) or real_read_csv(*a, **kw))

    def panel_reads():
        return [call for call in reads if os.path.basename(call[0]) == "PHOTOVOLTAIC_PANELS.csv"]

    # Four solar KPIs each resolve their default panel, then one card fetches its value.
    asyncio.run(get_kpis(scenario_path=locator.scenario, feature="solar", whatif=None))
    _value(locator, PV_GENERATION)
    assert len(panel_reads()) == 1

    _write_panels(locator, code=["PV1"], description=["a renamed panel"])
    assert _value(locator, PV_GENERATION)["annotations"] == [{"label": "Panel", "value": "PV1 · a renamed panel"}]
    assert len(panel_reads()) == 2


# --------------------------------------------------------------------------- panel_type default


def test_panel_type_defaults_to_the_first_panel_with_results(locator):
    _write_pv_totals(locator, "PV3", 10.0)
    _write_pv_totals(locator, "PV1", 10.0)
    kpi = registry.load_registry()[PV_GENERATION]

    assert effective_locator_args(kpi, locator) == {"panel_type": "PV1"}
    assert effective_locator_args(kpi, locator, {"panel_type": "PV3"}) == {"panel_type": "PV3"}


def test_a_declared_default_wins_over_the_first_choice(locator):
    # `current_DES` is declared; the generator would otherwise offer a Pareto-front id first.
    kpi = registry.load_registry()["optimisation.pareto_best_lcc_usd"]
    assert effective_locator_args(kpi, locator) == {"district_energy_system_id": "current_DES"}


def test_no_pv_results_is_unavailable_not_an_error(locator):
    kpi = registry.load_registry()[PV_GENERATION]
    with pytest.raises(KPINotAvailable, match="no panel type"):
        effective_locator_args(kpi, locator)


# --------------------------------------------------------------------------- registry


def _validate(raw):
    registry._validate_one(KPIDefinition.model_validate(raw), schemas=registry._load_schemas(),
                           locator_methods=registry._locator_method_names())


def test_registry_rejects_an_unknown_annotation_and_a_unit_parameter():
    raw = registry.load_registry()[PV_GENERATION].model_dump(mode="python")
    with pytest.raises(KPIDefinitionError, match="annotation"):
        _validate({**raw, "annotation": "nope"})

    raw["source"]["parameters"]["unit"] = {"label": "Unit"}
    with pytest.raises(KPIDefinitionError, match="reserved"):
        _validate(raw)


# --------------------------------------------------------------------------- API


def _value(locator, kpi_id, **args):
    return asyncio.run(get_kpi_value(kpi_id, scenario_path=locator.scenario,
                                     locator_args=json.dumps(args) if args else None, whatif=None))


def test_value_converts_the_unit_and_carries_annotations(locator):
    _write_pv_totals(locator, "PV1", 1500.0)

    base = _value(locator, PV_GENERATION)
    converted = _value(locator, PV_GENERATION, unit="MWh/yr")

    assert (base["value"], base["unit"]) == (3000.0, "kWh/yr")
    assert (converted["value"], converted["unit"]) == (pytest.approx(3.0), "MWh/yr")
    assert (base["unit_scale"], converted["unit_scale"]) == (1.0, pytest.approx(1e-3))
    assert converted["annotations"] == [{"label": "Panel", "value": "PV1 · typical csi 2024 (BIPV)"}]
    # The unit is applied to the cached base value, not cached separately.
    assert converted["computed_at"] == base["computed_at"]


def test_energy_by_carrier_value_lists_installed_panels(locator):
    summary = locator.get_final_energy_buildings_file("w1")
    os.makedirs(os.path.dirname(summary))
    pd.DataFrame({"name": ["B1"], "PV_MWh": [2.0]}).to_csv(summary, index=False)
    _write_whatif(locator, {"B1": {"roof": "PV_PV1"}})

    result = _value(locator, FE_PV_GENERATION, whatif_name="w1", unit="kWh/yr")

    assert (result["value"], result["unit"]) == (pytest.approx(2000.0), "kWh/yr")
    assert result["annotations"] == [{"label": "Roof", "value": "PV1 · typical csi 2024 (BIPV)"}]


def test_a_broken_configuration_drops_the_annotation_not_the_value(locator):
    summary = locator.get_final_energy_buildings_file("w1")
    os.makedirs(os.path.dirname(summary))
    pd.DataFrame({"name": ["B1"], "PV_MWh": [2.0]}).to_csv(summary, index=False)
    with open(locator.get_analysis_configuration_file("w1"), "w") as f:
        f.write("buildings: [unclosed\n")

    result = _value(locator, FE_PV_GENERATION, whatif_name="w1")

    assert (result["available"], result["value"], result["annotations"]) == (True, 2.0, [])


def test_parameters_offer_described_panels_and_units(locator):
    _write_pv_totals(locator, "PV1", 1.0)

    params = asyncio.run(get_kpi_parameters(PV_GENERATION, scenario_path=locator.scenario))["parameters"]

    assert params["panel_type"]["default"] == "PV1"
    assert params["panel_type"]["choices"] == [{"value": "PV1", "label": "PV1 · typical csi 2024 (BIPV)"}]
    assert params["unit"]["default"] == "kWh/yr"
    assert [c["value"] for c in params["unit"]["choices"]] == ["kWh/yr", "MWh/yr", "GWh/yr"]
