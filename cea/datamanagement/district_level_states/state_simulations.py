from __future__ import annotations

from typing import Any

from cea.config import Configuration
from cea.datamanagement.district_level_states.state_scenario import DistrictEventTimeline

default_workflow = [
    {"config": "."},  # use state-in-time scenario as base config
    {"script": "radiation"},
    {"script": "occupancy"},
    {"script": "demand"},
    {"script": "photovoltaic"},
    {"script": "emissions"},
]


def simulate_all_states(config: Configuration) -> None:
    """Simulate all state-in-time scenarios as per the district timeline log YAML file.

    Args:
        config (Configuration): The original configuration.
    """
    timeline = DistrictEventTimeline(config)
    try:
        simulation_mode = str(config.state_simulations.simulation_mode)
    except Exception:
        simulation_mode = "all"
    timeline.simulate_states(
        simulation_mode=simulation_mode, workflow=list(default_workflow)
    )


def main(config: Configuration) -> None:
    simulate_all_states(config)


if __name__ == "__main__":
    main(Configuration())
