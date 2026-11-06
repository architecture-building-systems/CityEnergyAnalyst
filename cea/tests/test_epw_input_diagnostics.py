"""Missing EPW hours are reported by timestamp."""
import pandas as pd
import pytest

from cea.utilities import epwreader


def test_missing_epw_hour_reports_only_missing_date(monkeypatch, capsys):
    dates = pd.date_range('2017-01-01', periods=8760, freq='h').delete(12)
    data = pd.DataFrame({'year': dates.year, 'month': dates.month, 'day': dates.day, 'hour': dates.hour + 1})
    monkeypatch.setattr(epwreader, 'epw_to_dataframe', lambda _: data)
    with pytest.raises(ValueError, match='Expected 8760, got 8759'):
        epwreader.epw_reader('unused.epw')
    output = capsys.readouterr().out
    assert '2017-01-01 12:00:00' in output
    assert '2017-01-01 00:00:00' not in output
    assert 'length=8760' not in output
