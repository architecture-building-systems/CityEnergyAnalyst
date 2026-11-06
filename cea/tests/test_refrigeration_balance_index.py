"""Refrigeration losses retain one value per hour in the balance dashboard."""
from types import SimpleNamespace

import numpy as np

from cea.demand.hourly_procedure_heating_cooling_system_load import (
    detailed_thermal_balance_to_tsd,
)
from cea.demand.time_series_data import TimeSeriesData


def test_refrigeration_balance_preserves_hourly_array():
    tsd = TimeSeriesData(weather=None)
    tsd.electrical_loads.El[:2] = 0
    tsd.electrical_loads.Ea[:2] = 0
    tsd.electrical_loads.Epro[:2] = 0
    tsd.cooling_loads.Qcdata_sys[:2] = 0
    tsd.cooling_loads.Qcre_sys[:2] = [-100, -400]
    tsd.occupancy.Qs[:2] = 0
    temperatures = dict.fromkeys([
        'h_em', 'h_op_m', 'theta_m', 'theta_em', 'h_ec', 'theta_c',
        'theta_ec', 'h_ea', 'T_int', 'theta_ea'], 0.)
    for hour in range(2):
        detailed_thermal_balance_to_tsd(tsd, SimpleNamespace(), hour, temperatures)
    assert isinstance(tsd.energy_balance_dashboard.Q_loss_sen_ref, np.ndarray)
    np.testing.assert_array_equal(tsd.energy_balance_dashboard.Q_loss_sen_ref[:2], [100, 400])
    assert np.isnan(tsd.energy_balance_dashboard.Q_loss_sen_ref[2])
