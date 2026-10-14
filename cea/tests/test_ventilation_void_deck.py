"""Dynamic infiltration must size the zone from the enclosed part of the building (issue #4115)."""
from types import SimpleNamespace

import numpy as np
import pytest

from cea.demand import ventilation_air_flows_detailed as vent

FOOTPRINT = 500.0
PERIMETER = 90.0


def _geometry(**extra):
    return {'footprint': FOOTPRINT, 'perimeter': PERIMETER, 'height_ag': 20.0, 'floors_ag': 1, **extra}


def _bpr(geometry):
    return SimpleNamespace(geometry=geometry, envelope=SimpleNamespace(n50=3.0))


def test_height_vd_excludes_void_deck_from_zone():
    facade, roof, height, _, base = vent.get_building_geometry_ventilation(_geometry(height_vd=17.0))
    assert height == pytest.approx(3.0)
    assert base == pytest.approx(17.0)
    assert facade == pytest.approx(PERIMETER * 3.0)
    assert roof == FOOTPRINT


def test_legacy_void_deck_floors_are_converted():
    # 4 storeys over 20 m, the lowest storey open -> 5 m void deck
    geometry = _geometry(void_deck=1)
    geometry['floors_ag'] = 4
    _, _, height, _, base = vent.get_building_geometry_ventilation(geometry)
    assert base == pytest.approx(5.0)
    assert height == pytest.approx(15.0)


def test_no_void_deck_is_unchanged():
    facade, _, height, _, base = vent.get_building_geometry_ventilation(_geometry())
    assert (height, base) == (20.0, 0.0)
    assert facade == pytest.approx(PERIMETER * 20.0)


def test_leakage_scales_with_enclosed_volume_and_sits_at_real_elevation():
    with_void = vent.get_properties_natural_ventilation(_bpr(_geometry(height_vd=17.0)))
    without = vent.get_properties_natural_ventilation(_bpr(_geometry()))

    assert np.all(with_void['height_lea_path'] >= 17.0)
    assert np.all(with_void['height_lea_path'] <= 20.0)
    assert np.all(with_void['height_vent_path'] >= 17.0)
    # 1500 m3 enclosed vs 10000 m3: far less leakage than the full-height building
    assert with_void['coeff_lea_path'].sum() < without['coeff_lea_path'].sum() / 3
