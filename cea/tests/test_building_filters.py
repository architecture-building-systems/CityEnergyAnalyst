"""Building filters shared by the plots and `export-results-csv` (`result_summary.filter_buildings`).

A blank multi-choice filter arrives already expanded to every choice the archetype database
offers, so "blank" and "everything ticked" are the same list. Both must select every building,
including ones whose construction or use type the database does not list at all -- those can
never be ticked, so treating the list as a whitelist silently drops the whole scenario.
"""

import pandas as pd
import pytest

from cea.import_export import result_summary
from cea.import_export.result_summary import filter_buildings

DB_STANDARDS = ['SFH_A', 'SFH_B', 'MFH_A']
DB_USE_TYPES = ['MULTI_RES', 'OFFICE']


class FakeLocator:
    def __init__(self, tmp_path):
        self._construction = str(tmp_path / 'CONSTRUCTION_TYPES.csv')
        self._use = str(tmp_path / 'USE_TYPES.csv')
        pd.DataFrame({'const_type': DB_STANDARDS, 'description': 'x'}).to_csv(self._construction, index=False)
        pd.DataFrame({'use_type': DB_USE_TYPES}).to_csv(self._use, index=False)

    def get_database_archetypes_construction_type(self):
        return self._construction

    def get_database_archetypes_use_type(self):
        return self._use


@pytest.fixture
def locator(tmp_path, monkeypatch):
    buildings = pd.DataFrame({
        'name': ['B1', 'B2', 'B3'],
        'main_use_type': ['MULTI_RES', 'OFFICE', 'WAREHOUSE'],
        'main_use_type_ratio': [1.0, 1.0, 1.0],
        'construction_type': ['STANDARD4', 'STANDARD4', 'SFH_A'],
        'construction_year': [1965, 1980, 1998],
    })
    monkeypatch.setattr(result_summary, 'get_building_year_standard_main_use_type', lambda _: buildings.copy())
    return FakeLocator(tmp_path)


def select(locator, standards, use_types=None, year_start=None, year_end=None):
    return filter_buildings(locator, [], year_start, year_end, standards, use_types or [], 0)[1]


def test_every_database_standard_selected_keeps_buildings_the_database_does_not_list(locator):
    assert select(locator, DB_STANDARDS) == ['B1', 'B2', 'B3']


def test_blank_standard_filter_keeps_every_building(locator):
    assert select(locator, []) == ['B1', 'B2', 'B3']


def test_a_partial_standard_selection_still_filters(locator):
    assert select(locator, ['SFH_A', 'MFH_A']) == ['B3']


def test_every_database_use_type_selected_keeps_buildings_the_database_does_not_list(locator):
    assert select(locator, [], use_types=DB_USE_TYPES) == ['B1', 'B2', 'B3']


def test_a_partial_use_type_selection_still_filters(locator):
    assert select(locator, [], use_types=['OFFICE']) == ['B2']


def test_a_selection_against_an_empty_database_still_filters(locator):
    # nothing to cover is not "everything selected"
    pd.DataFrame({'const_type': []}).to_csv(locator.get_database_archetypes_construction_type(), index=False)
    assert select(locator, ['SFH_A']) == ['B3']


def test_no_match_names_the_construction_types_the_scenario_has(locator):
    with pytest.raises(ValueError, match='SFH_A, STANDARD4'):
        select(locator, ['MFH_A'])


def test_an_empty_year_range_reports_the_years_the_scenario_has(locator):
    with pytest.raises(ValueError, match='between 1965 and 1998'):
        select(locator, [], year_start=2025, year_end=2100)
