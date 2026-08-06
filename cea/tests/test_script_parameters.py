"""Test for duplicate parameters in script definitions"""

import unittest

import pytest
from fastapi import HTTPException

import cea
import cea.scripts
import cea.config
from cea.interfaces.dashboard.api.utils import script_takes_scenario_path
from cea.interfaces.dashboard.server.jobs import resolve_job_scenario


class TestScriptParameters(unittest.TestCase):
    """Test that script parameters are correctly defined in scripts.yml"""

    def test_no_duplicate_parameters_in_scripts(self):
        """
        Check that each script doesn't have duplicate parameters in its parameter list.
        This test goes through each script defined in scripts.yml and verifies that
        no parameter is listed more than once, by expanding each section and checking for duplicates.
        """
        config = cea.config.Configuration()
        scripts_with_duplicates = {} # script name -> dict of duplicate param -> section names

        for script in cea.scripts.list_scripts(config.plugins):
            # Parse and check all parameters for duplicates
            seen_params = dict() # param name -> section name
            duplicate_params = dict()
            for section, parameter in config.matching_parameters(script.parameters):
                if parameter.name in seen_params:
                    if parameter.name in duplicate_params:
                        duplicate_params[parameter.name].append(section.name)
                    else:
                        duplicate_params[parameter.name] = [seen_params[parameter.name], section.name]
                else:
                    seen_params[parameter.name] = section.name

            if duplicate_params:
                scripts_with_duplicates[script.name] = duplicate_params

        # Build error message if there are duplicates
        if scripts_with_duplicates:
            error_msg = "\nFound scripts with duplicate parameters:\n"
            for script_name, info in scripts_with_duplicates.items():
                error_msg += f"\nScript: {script_name}\n"
                for param, sections in info.items():
                    error_msg += f"  - '{param}' appears in sections: {' '.join(sections)}\n"
            self.fail(error_msg)


def test_only_general_scenario_is_named_scenario(config):
    """`scenario` is a reserved parameter name across the entire config schema,
    `general:scenario` (a ScenarioParameter -- the current active scenario path)
    is the only parameter anywhere allowed to be named `scenario`.
    """
    offenders = []
    for section in config.sections.values():
        parameter = section.parameters.get('scenario')
        if parameter is None:
            continue
        if section.name != 'general' or not isinstance(parameter, cea.config.ScenarioParameter):
            offenders.append(f"{section.name}:scenario is {type(parameter).__name__}")

    if offenders:
        error_msg = "\nFound non-reserved 'scenario' parameters outside [general]:\n"
        for entry in offenders:
            error_msg += f"  - {entry}\n"
        pytest.fail(error_msg)


def test_script_takes_scenario_path(config):
    # general:scenario -- the reserved active-scenario path
    assert script_takes_scenario_path('demand', config) is True
    # a script with no 'scenario' parameter at all
    assert script_takes_scenario_path('extract-reference-case', config) is False

    with pytest.raises(cea.ScriptNotFoundException):
        script_takes_scenario_path('no-such-script', config)


def test_resolve_job_scenario(config):
    # scenario-taking script + resolved context -> the resolved path is forced in
    assert resolve_job_scenario('demand', config, '/root/proj/baseline') == '/root/proj/baseline'

    # scenario-taking script + no context -> 400, fail fast
    with pytest.raises(HTTPException) as exc_info:
        resolve_job_scenario('demand', config, None)
    assert exc_info.value.status_code == 400

    # extract-reference-case doesn't take a ScenarioParameter -- no override, and no 400
    # even when there is no scenario context (this is the guarantee that scenario-less
    # scripts keep working after this change)
    assert resolve_job_scenario('extract-reference-case', config, '/root/proj/baseline') is None
    assert resolve_job_scenario('extract-reference-case', config, None) is None

    # unknown script -> 422
    with pytest.raises(HTTPException) as exc_info:
        resolve_job_scenario('no-such-script', config, None)
    assert exc_info.value.status_code == 422


if __name__ == "__main__":
    unittest.main()
