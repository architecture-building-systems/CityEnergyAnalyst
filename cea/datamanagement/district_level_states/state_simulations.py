from __future__ import annotations

from typing import Literal
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


def simulate_all_states(config: Configuration, timeline_name: str) -> None:
    """Simulate all state-in-time scenarios as per the district timeline log YAML file.

    Args:
        config (Configuration): The original configuration.
    """
    timeline = DistrictEventTimeline(config, timeline_name=timeline_name)
    # Ensure simulation_mode is one of the supported literals ('pending' or 'all')
    simulation_mode: Literal["pending", "all"]
    if getattr(config.state_simulations, "simulation_mode", "all") == "pending":
        simulation_mode = "pending"
    else:
        simulation_mode = "all"
    timeline.simulate_states(
        simulation_mode=simulation_mode, workflow=list(default_workflow)
    )


def main(config: Configuration) -> None:
    timeline_name = config.state_simulations.existing_timeline_name
    if not timeline_name:
        raise ValueError(
            "No existing timeline name provided. "
            "Please provide an existing timeline name to simulate all states from."
        )
    simulate_all_states(config, timeline_name=timeline_name)


if __name__ == "__main__":
    main(Configuration())
