"""`calc_surface_azimuth` is called with whole sensor columns, including a column of one sensor."""

import numpy as np
import pandas as pd
import pytest

from cea.utilities.solar_equations import calc_surface_azimuth


def test_scalar_input_returns_a_float():
    azimuth = calc_surface_azimuth(0.5, 0.5, 45.0)
    assert isinstance(azimuth, float)


@pytest.mark.parametrize('as_column', [np.array, pd.Series], ids=['array', 'series'])
def test_a_single_sensor_column_stays_a_column(as_column):
    # a building with one sensor: numpy refuses float() on a one-element 1-D array
    azimuth = calc_surface_azimuth(as_column([0.5]), as_column([0.5]), as_column([45.0]))
    assert np.shape(azimuth) == (1,)
    assert azimuth[0] == pytest.approx(calc_surface_azimuth(0.5, 0.5, 45.0))


def test_a_column_of_sensors_is_evaluated_elementwise():
    xdir, ydir, tilt = np.array([0.5, -0.5, 0.2]), np.array([0.5, -0.5, -0.3]), np.array([45.0, 45.0, 30.0])
    azimuth = calc_surface_azimuth(xdir, ydir, tilt)
    expected = [calc_surface_azimuth(x, y, b) for x, y, b in zip(xdir, ydir, tilt)]
    assert azimuth == pytest.approx(expected)
