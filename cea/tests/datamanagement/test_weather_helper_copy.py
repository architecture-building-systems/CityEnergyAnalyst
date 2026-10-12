"""`copy_weather_file` must work on a scenario that has no `inputs/weather` folder yet.

A scenario being created from scratch has none, so copying used to fail with FileNotFoundError.
"""
import pytest

from cea.datamanagement.weather_helper.weather_helper import copy_weather_file
from cea.inputlocator import InputLocator


def test_copies_into_a_scenario_without_a_weather_folder(tmp_path):
    source = tmp_path / "source.epw"
    source.write_text("weather")
    locator = InputLocator(str(tmp_path / "scenario"))

    copy_weather_file(str(source), locator)

    assert open(locator.get_weather_file()).read() == "weather"


def test_a_missing_source_is_still_reported(tmp_path):
    locator = InputLocator(str(tmp_path / "scenario"))

    with pytest.raises(ValueError, match="Could not find weather file"):
        copy_weather_file(str(tmp_path / "missing.epw"), locator)
