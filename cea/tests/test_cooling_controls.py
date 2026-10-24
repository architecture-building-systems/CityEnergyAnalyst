"""Regression tests for inactive cooling subsystems and zero-load ARU operation."""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from cea.demand.airconditioning_model import C_A, local_air_recirculation_unit_cooling
from cea.demand.building_properties.building_hvac import verify_cooling_supply_temperatures
from cea.demand.control_heating_cooling_systems import cooling_system_is_active
from cea.demand.latent_loads import convert_rh_to_moisture_content


@pytest.fixture
def bpr():
    return SimpleNamespace(
        hvac={'class_cs': 'DECENTRALIZED_AC', 'Tc_sup_air_ahu_C': np.nan,
              'Tc_sup_air_aru_C': 16.0, 'Tscs0_aru_C': 7.5},
        rc_model=SimpleNamespace(Af=100.0), geometry={'floor_height': 3.0},
    )


@pytest.mark.parametrize('system,ahu,temperature,expected', [
    ('DECENTRALIZED_AC', np.nan, 16.0, False),
    ('DECENTRALIZED_AC', np.nan, 15.0, False),
    ('DECENTRALIZED_AC', np.nan, 28.0, True),
    ('DECENTRALIZED_AC', 30.0, 28.0, True),  # Unused AHU must not affect operation.
    ('CENTRAL_AC', 18.0, 17.0, False),
    ('CENTRAL_AC', 18.0, 28.0, True),
    ('HYBRID_AC', 18.0, 17.0, False),
    ('HYBRID_AC', 18.0, 28.0, True),
    ('FLOOR_COOLING', np.nan, 28.0, True),
    ('CEILING_COOLING', np.nan, 28.0, True),
    ('NONE', np.nan, 28.0, False),
])
def test_cooling_activation_uses_installed_subsystems(bpr, system, ahu, temperature, expected):
    bpr.hvac.update(class_cs=system, Tc_sup_air_ahu_C=ahu)
    if system in ('FLOOR_COOLING', 'CEILING_COOLING', 'NONE'):
        bpr.hvac['Tc_sup_air_aru_C'] = np.nan
    tsd = SimpleNamespace(rc_model_temperatures=SimpleNamespace(
        ta_cs_set=np.array([26.0]), T_int=np.array([temperature])))
    assert cooling_system_is_active(bpr, tsd, 0) == expected


def test_cooling_without_setpoint_is_off(bpr):
    tsd = SimpleNamespace(rc_model_temperatures=SimpleNamespace(
        ta_cs_set=np.array([np.nan]), T_int=np.array([28.0])))
    assert not cooling_system_is_active(bpr, tsd, 0)


def _hvac_row(system, **overrides):
    row = {'class_cs': system, 'hvac_type_cs': 'HVAC_COOLING_ASX', 'Tc_sup_air_ahu_C': 16.0,
           'Tscs0_ahu_C': 7.5, 'Tc_sup_air_aru_C': 16.0, 'Tscs0_aru_C': 7.5}
    row.update(overrides)
    return row


@pytest.mark.parametrize('system', ['NONE', 'CEILING_COOLING', 'FLOOR_COOLING'])
def test_radiant_and_no_cooling_need_no_air_parameters(system):
    row = _hvac_row(system, Tc_sup_air_ahu_C=np.nan, Tscs0_ahu_C=np.nan,
                    Tc_sup_air_aru_C=np.nan, Tscs0_aru_C=np.nan)
    verify_cooling_supply_temperatures(pd.DataFrame([row], index=['B001']))


def test_mini_split_does_not_need_ahu_parameters():
    row = _hvac_row('DECENTRALIZED_AC', Tc_sup_air_ahu_C=np.nan, Tscs0_ahu_C=np.nan)
    verify_cooling_supply_temperatures(pd.DataFrame([row], index=['B001']))


@pytest.mark.parametrize('system,field', [
    ('DECENTRALIZED_AC', 'Tc_sup_air_aru_C'),
    ('CENTRAL_AC', 'Tc_sup_air_ahu_C'),
    ('CENTRAL_AC', 'Tc_sup_air_aru_C'),
    ('HYBRID_AC', 'Tscs0_ahu_C'),
    ('HYBRID_AC', 'Tc_sup_air_aru_C'),
])
def test_missing_air_parameter_is_rejected_naming_the_building(system, field):
    row = _hvac_row(system, **{field: np.nan})
    with pytest.raises(ValueError, match=f'B001.*{system}.*{field}'):
        verify_cooling_supply_temperatures(pd.DataFrame([row], index=['B001']))


@pytest.mark.parametrize('t_control,x_control', [(True, False), (False, True), (True, True)])
def test_zero_load_at_zero_temperature_and_moisture_difference(bpr, t_control, x_control):
    humidity = convert_rh_to_moisture_content(100.0, bpr.hvac['Tscs0_aru_C'])
    with np.errstate(divide='raise', invalid='raise'):
        result = local_air_recirculation_unit_cooling(
            0.0, 0.0, np.float64(16.0), humidity, bpr, t_control, x_control)
    assert all(np.isfinite(value) for value in result.values())
    for field in ('ma_sup_cs_aru', 'qc_sen_aru', 'qc_lat_aru', 'g_dhu_aru'):
        assert result[field] == 0.0


def test_sensible_control_does_not_evaluate_unused_latent_division(bpr):
    humidity = convert_rh_to_moisture_content(100.0, bpr.hvac['Tscs0_aru_C'])
    with np.errstate(divide='raise', invalid='raise'):
        result = local_air_recirculation_unit_cooling(
            -1000.0, 0.001, 28.0, humidity, bpr, True, False)
    assert result['qc_sen_aru'] == pytest.approx(-1000.0)
    assert result['ma_sup_cs_aru'] == pytest.approx(1000.0 / (C_A * 12.0))
    assert result['qc_lat_aru'] == 0.0


@pytest.mark.parametrize('t_control', [False, True])
def test_latent_control_still_dehumidifies_without_sensible_demand(bpr, t_control):
    with np.errstate(divide='raise', invalid='raise'):
        result = local_air_recirculation_unit_cooling(
            0.0, 0.0001, np.float64(16.0), 0.012, bpr, t_control, True)
    assert all(np.isfinite(value) for value in result.values())
    assert result['ma_sup_cs_aru'] > 0.0
    assert result['qc_sen_aru'] == 0.0
    assert result['g_dhu_aru'] == pytest.approx(-0.0001)
