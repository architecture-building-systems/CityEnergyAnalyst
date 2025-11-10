from cea.workflows.workflow import do_script_step
from cea.config import Configuration
from cea.inputlocator import InputLocator
from copy import deepcopy
import os
import yaml
from typing import Any

default_workflow = [
    {"script": "radiation"},
    {"script": "occupancy-helper"},
    {"script": "demand"},
    {
        "script": "photovoltaic",
        "parameters": {},
    },
    {
        "script": "solar-thermal",
        "parameters": {},
    },
]

def modify_config_for_state_scenario(config: Configuration, year_of_state: int) -> Configuration:
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

def do_state_scenario_step(workflow: dict[str, Any], scenario_config: Configuration) -> None:
    """execute the workflow step for creating a state-in-time scenario for the specified year.
    Args:
        config (Configuration): The original configuration.
        year_of_state (int): The year of the state-in-time scenario.
    """
    for i, step in enumerate(workflow):
        if "script" in step:
            do_script_step(scenario_config, i, step, trace_input=False)
        elif "config" in step:
            raise NotImplementedError("Config steps are not supported in state scenario workflow.")
        else:
            raise ValueError("Invalid step configuration: {i} - {step}".format(i=i, step=step))
        

        

        