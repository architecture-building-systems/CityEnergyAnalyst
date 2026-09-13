"""
Shared pytest fixtures for CEA tests.
"""

import os
import shutil
import tempfile

import pandas as pd
import pytest

import cea.config
from cea.inputlocator import InputLocator

# Service-life column name per envelope table, which is suffixed rather than uniform.
ENVELOPE_SERVICE_LIFE = {
    "wall": "Service_Life_wall",
    "roof": "Service_Life_roof",
    "floor": "Service_Life_floor",
}


@pytest.fixture
def config():
    """Provide a default CEA Configuration instance for tests."""
    return cea.config.Configuration()


def write_database_csv(path: str, rows: list[dict]) -> None:
    """Write a database CSV, creating the folder the locator expects it in."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


@pytest.fixture
def envelope_scenario():
    """Build a throwaway scenario whose envelope tables load.

    Yields ``build(materials, **rows_by_kind)``, returning the scenario's ``InputLocator``.
    All three of wall/roof/floor are always written -- ``Envelope.from_locator`` reads every
    table, so a test that seeds only the one it cares about fails on a sibling instead of on
    the row under test. Unspecified tables get a single valid one-layer row.
    """
    root = tempfile.mkdtemp()

    def build(materials: list[dict], **rows_by_kind: list[dict]) -> InputLocator:
        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.project = root
        config.scenario_name = "baseline"
        locator = InputLocator(config.scenario)

        write_database_csv(locator.get_database_components_materials(), materials)
        default_layers = {"material_name_1": materials[0]["name"], "thickness_1_m": 0.20}
        for kind, service_life in ENVELOPE_SERVICE_LIFE.items():
            rows = rows_by_kind.get(kind) or [
                {"code": f"{kind.upper()}_A", **default_layers, service_life: 40}
            ]
            write_database_csv(
                getattr(locator, f"get_database_assemblies_envelope_{kind}")(), rows
            )
        return locator

    yield build
    shutil.rmtree(root, ignore_errors=True)
