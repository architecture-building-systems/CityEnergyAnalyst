"""
Tests for baseline-costs script
"""

import os
import pandas as pd
import pytest

import cea.config
import cea.inputlocator
from cea.analysis.costs.main import main as baseline_costs_main

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


@pytest.mark.skip(reason="Requires reference case to be extracted and demand to be run")
def test_baseline_costs_reference_case(config):
    """
    Test baseline-costs on reference case.

    Note: This test requires:
    1. Reference case to be extracted
    2. Demand to be calculated first
    """
    # Set up configuration
    config.scenario = os.path.join(os.path.dirname(__file__), '..', 'examples', 'reference-case-open', 'baseline')
    config.system_costs.network_types = ['DH', 'DC']

    # Run baseline-costs
    baseline_costs_main(config)

    # Check outputs exist
    locator = cea.inputlocator.InputLocator(config.scenario)
    assert os.path.exists(locator.get_baseline_costs()), "Baseline costs output file not created"
    assert os.path.exists(locator.get_baseline_costs_detailed()), "Baseline costs detailed output file not created"

    # Read and validate results
    results = pd.read_csv(locator.get_baseline_costs())

    # Check structure
    assert 'name' in results.columns, "Missing 'name' column"
    assert 'GFA_m2' in results.columns, "Missing 'GFA_m2' column"
    assert 'TAC_sys_USD' in results.columns, "Missing 'TAC_sys_USD' column"
    assert 'Capex_a_sys_USD' in results.columns, "Missing 'Capex_a_sys_USD' column"
    assert 'Opex_a_sys_USD' in results.columns, "Missing 'Opex_a_sys_USD' column"

    # Check all buildings present
    assert len(results) > 0, "No buildings in results"

    # Check no negative costs
    assert (results['TAC_sys_USD'] >= 0).all(), "Negative TAC values found"
    assert (results['Capex_a_sys_USD'] >= 0).all(), "Negative CAPEX values found"
    assert (results['Opex_a_sys_USD'] >= 0).all(), "Negative OPEX values found"

    # Check detailed output
    detailed = pd.read_csv(locator.get_baseline_costs_detailed())
    assert len(detailed) > 0, "No components in detailed output"
    assert 'component_code' in detailed.columns, "Missing 'component_code' column in detailed output"
    assert 'capacity_kW' in detailed.columns, "Missing 'capacity_kW' column in detailed output"


@pytest.mark.skip(reason="Requires reference case to be extracted and demand to be run")
def test_baseline_costs_dh_only(config):
    """Test baseline-costs with DH only"""
    config.scenario = os.path.join(os.path.dirname(__file__), '..', 'examples', 'reference-case-open', 'baseline')
    config.system_costs.network_types = ['DH']

    baseline_costs_main(config)

    locator = cea.inputlocator.InputLocator(config.scenario)
    results = pd.read_csv(locator.get_baseline_costs())

    # Should have heating costs
    heating_services = ['NG_hs', 'OIL_hs', 'GRID_hs', 'DH_hs']
    heating_cost_cols = [f'{s}_TAC_USD' for s in heating_services]
    assert any(col in results.columns for col in heating_cost_cols), "No heating cost columns found"


@pytest.mark.skip(reason="Requires reference case to be extracted and demand to be run")
def test_baseline_costs_dc_only(config):
    """Test baseline-costs with DC only"""
    config.scenario = os.path.join(os.path.dirname(__file__), '..', 'examples', 'reference-case-open', 'baseline')
    config.system_costs.network_types = ['DC']

    baseline_costs_main(config)

    locator = cea.inputlocator.InputLocator(config.scenario)
    results = pd.read_csv(locator.get_baseline_costs())

    # Should have cooling costs
    cooling_services = ['GRID_cs', 'DC_cs']
    cooling_cost_cols = [f'{s}_TAC_USD' for s in cooling_services]
    assert any(col in results.columns for col in cooling_cost_cols), "No cooling cost columns found"


def test_baseline_costs_empty_network_types():
    """Test that empty network_types raises error"""
    config = cea.config.Configuration()
    config.system_costs.network_types = []

    with pytest.raises(ValueError, match="No network types selected"):
        from cea.analysis.costs.main import baseline_costs_main
        locator = cea.inputlocator.InputLocator(config.scenario)
        baseline_costs_main(locator, config)


if __name__ == '__main__':
    # For manual testing
    config = cea.config.Configuration()
    test_baseline_costs_reference_case(config)
