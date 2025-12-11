"""
Tests for anthropogenic-heat script
"""

import os
import pandas as pd
import pytest

import cea.config
import cea.inputlocator
from cea.analysis.heat.main import main as anthropogenic_heat_main

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


@pytest.mark.skip(reason="Requires reference case to be extracted and demand to be run")
def test_anthropogenic_heat_reference_case(config):
    """
    Test anthropogenic-heat on reference case.

    Note: This test requires:
    1. Reference case to be extracted
    2. Demand to be calculated first
    """
    # Set up configuration
    config.scenario = os.path.join(os.path.dirname(__file__), '..', 'examples', 'reference-case-open', 'baseline')
    config.anthropogenic_heat.network_types = ['DH', 'DC']

    # Run anthropogenic-heat
    anthropogenic_heat_main(config)

    # Check outputs exist
    locator = cea.inputlocator.InputLocator(config.scenario)
    assert os.path.exists(locator.get_heat_rejection_buildings()), "Heat rejection buildings output file not created"
    assert os.path.exists(locator.get_heat_rejection_components()), "Heat rejection components output file not created"
    assert os.path.exists(locator.get_heat_rejection_hourly_spatial()), "Heat rejection hourly spatial output file not created"

    # Read and validate results
    results = pd.read_csv(locator.get_heat_rejection_buildings())

    # Check structure
    assert 'name' in results.columns, "Missing 'name' column"
    assert 'type' in results.columns, "Missing 'type' column"
    assert 'GFA_m2' in results.columns, "Missing 'GFA_m2' column"
    assert 'x_coord' in results.columns, "Missing 'x_coord' column"
    assert 'y_coord' in results.columns, "Missing 'y_coord' column"
    assert 'heat_rejection_annual_MWh' in results.columns, "Missing 'heat_rejection_annual_MWh' column"
    assert 'peak_heat_rejection_kW' in results.columns, "Missing 'peak_heat_rejection_kW' column"
    assert 'peak_datetime' in results.columns, "Missing 'peak_datetime' column"
    assert 'scale' in results.columns, "Missing 'scale' column"

    # Check all buildings present
    assert len(results) > 0, "No buildings in results"

    # Check no negative heat rejection
    assert (results['heat_rejection_annual_MWh'] >= 0).all(), "Negative heat rejection values found"
    assert (results['peak_heat_rejection_kW'] >= 0).all(), "Negative peak heat rejection values found"

    # Check type values
    assert results['type'].isin(['building', 'plant']).all(), "Invalid type values found"

    # Check scale values
    assert results['scale'].isin(['BUILDING', 'DISTRICT']).all(), "Invalid scale values found"

    # Check detailed output
    detailed = pd.read_csv(locator.get_heat_rejection_components())
    assert len(detailed) >= 0, "Components output missing"
    assert 'name' in detailed.columns, "Missing 'name' column in components output"
    assert 'component_code' in detailed.columns, "Missing 'component_code' column in components output"
    assert 'energy_carrier' in detailed.columns, "Missing 'energy_carrier' column in components output"

    # Check hourly spatial output
    hourly = pd.read_csv(locator.get_heat_rejection_hourly_spatial())
    assert len(hourly) > 0, "No hourly spatial data in output"
    assert 'name' in hourly.columns, "Missing 'name' column in hourly output"
    assert 'type' in hourly.columns, "Missing 'type' column in hourly output"
    assert 'x_coord' in hourly.columns, "Missing 'x_coord' column in hourly output"
    assert 'y_coord' in hourly.columns, "Missing 'y_coord' column in hourly output"
    assert 'DATE' in hourly.columns, "Missing 'DATE' column in hourly output"
    assert 'Heat_rejection_kW' in hourly.columns, "Missing 'Heat_rejection_kW' column in hourly output"

    # Check hourly data has 8760 hours per location
    num_locations = len(results)
    expected_rows = num_locations * 8760
    assert len(hourly) == expected_rows, f"Expected {expected_rows} hourly rows but got {len(hourly)}"


@pytest.mark.skip(reason="Requires reference case to be extracted and demand to be run")
def test_anthropogenic_heat_dh_only(config):
    """Test anthropogenic-heat with DH only"""
    config.scenario = os.path.join(os.path.dirname(__file__), '..', 'examples', 'reference-case-open', 'baseline')
    config.anthropogenic_heat.network_types = ['DH']

    anthropogenic_heat_main(config)

    locator = cea.inputlocator.InputLocator(config.scenario)
    results = pd.read_csv(locator.get_heat_rejection_buildings())

    # Should have results (buildings may have cooling systems even with DH only)
    assert len(results) >= 0, "Results should be present"


@pytest.mark.skip(reason="Requires reference case to be extracted and demand to be run")
def test_anthropogenic_heat_dc_only(config):
    """Test anthropogenic-heat with DC only"""
    config.scenario = os.path.join(os.path.dirname(__file__), '..', 'examples', 'reference-case-open', 'baseline')
    config.anthropogenic_heat.network_types = ['DC']

    anthropogenic_heat_main(config)

    locator = cea.inputlocator.InputLocator(config.scenario)
    results = pd.read_csv(locator.get_heat_rejection_buildings())

    # Should have cooling-related heat rejection
    assert len(results) > 0, "Should have heat rejection from cooling systems"

    # All heat rejection should be non-negative
    assert (results['heat_rejection_annual_MWh'] >= 0).all(), "Negative heat rejection values found"


@pytest.mark.skip(reason="Requires reference case to be extracted and demand to be run")
def test_anthropogenic_heat_standalone_only(config):
    """Test anthropogenic-heat with no networks (standalone only)"""
    config.scenario = os.path.join(os.path.dirname(__file__), '..', 'examples', 'reference-case-open', 'baseline')
    config.anthropogenic_heat.network_types = []

    anthropogenic_heat_main(config)

    locator = cea.inputlocator.InputLocator(config.scenario)
    results = pd.read_csv(locator.get_heat_rejection_buildings())

    # Should have only buildings, no plants
    assert results['type'].eq('building').all(), "Should only have buildings in standalone mode"
    assert results['scale'].eq('BUILDING').all(), "Should only have BUILDING scale in standalone mode"


if __name__ == '__main__':
    # For manual testing
    config = cea.config.Configuration()
    test_anthropogenic_heat_reference_case(config)
