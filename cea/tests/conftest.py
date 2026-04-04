"""
Shared pytest fixtures for CEA tests.
"""

import pytest
import cea.config


@pytest.fixture
def config():
    """Provide a default CEA Configuration instance for tests."""
    return cea.config.Configuration()
