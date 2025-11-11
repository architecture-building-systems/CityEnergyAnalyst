import os
from copy import deepcopy
from typing import Any

import pandas as pd
import yaml

from cea.config import Configuration
from cea.inputlocator import InputLocator
from cea.workflows.workflow import do_script_step, do_config_step

default_workflow = [
    {"config": "."}, # use state-in-time scenario as base config
    {"script": "radiation"},
    {"script": "occupancy-helper"},
    {"script": "demand"},
    {"script": "photovoltaic"},
    {"script": "emissions"},
]


def generate_state_config(
    config: Configuration, year_of_state: int
) -> Configuration:
    """Modify the given configuration to point to the state-in-time scenario for the specified year.

    Args:
        config (Configuration): The original configuration.
        year_of_state (int): The year of the state-in-time scenario.

    Returns:
        Configuration: The modified configuration pointing to the state-in-time scenario.
    """
    locator = InputLocator(config.scenario)
    event_scenario_folder = locator.get_state_in_time_scenario_folder(year_of_state)
    modified_config = deepcopy(config)
    modified_config.scenario = event_scenario_folder
    return modified_config


def run_workflow(
    workflow: list[dict[str, Any]], scenario_config: Configuration
) -> None:
    """execute the workflow step for creating a state-in-time scenario for the specified year.
    Args:
        config (Configuration): The original configuration.
        year_of_state (int): The year of the state-in-time scenario.
    """
    for i, step in enumerate(workflow):
        if "script" in step:
            do_script_step(scenario_config, i, step, trace_input=False)
        elif "config" in step:
            do_config_step(scenario_config, step)
        else:
            raise ValueError(
                "Invalid step configuration: {i} - {step}".format(i=i, step=step)
            )


def load_log_yaml(locator: InputLocator) -> dict[int, dict[str, Any]]:
    yml_path = locator.get_district_timeline_log_file()
    if not os.path.exists(yml_path):
        raise FileNotFoundError(
            f"District timeline log file '{yml_path}' does not exist."
        )
    with open(yml_path, "r") as f:
        existing_data_in_yml: dict[int, dict[str, Any]] = yaml.safe_load(f) or {}
    if not existing_data_in_yml:
        raise ValueError(f"District timeline log file '{yml_path}' is empty.")
    return existing_data_in_yml


def simulate_all_states(config: Configuration) -> None:
    """Simulate all state-in-time scenarios as per the district timeline log YAML file.

    Args:
        config (Configuration): The original configuration.
    """
    locator = InputLocator(config.scenario)
    timeline_folder = locator.get_district_timeline_states_folder()
    state_years = [
        int(f.replace("state_", ""))
        for f in os.listdir(timeline_folder)
        if f.startswith("state_")
    ]
    state_years.sort()
    log_data = load_log_yaml(locator)
    workflow = deepcopy(default_workflow)
    for year in state_years:
        print(f"Simulating state-in-time scenario for year {year}...")
        state_config = generate_state_config(config, year)
        if type(state_config.emissions.year_end) is int and year > state_config.emissions.year_end:
            state_config.emissions.year_end = year
        run_workflow(workflow, state_config)
        log_data[year]["simulation_workflow"] = workflow
        log_data[year]["latest_simulated_at"] = str(pd.Timestamp.now())
        print(f"Simulation for state-in-time scenario year {year} completed.")


def main(config: Configuration) -> None:
    simulate_all_states(config)


if __name__ == "__main__":
    main(Configuration())
