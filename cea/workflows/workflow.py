"""
Run a workflow.yml file - this is like a cea-are "batch" file for running multiple cea scripts including parameters.
``cea workflow`` can also pick up from previous (failed?) runs, which can help in debugging.
"""
from __future__ import division
from __future__ import print_function

import os
import datetime
import cea.config
import cea.inputlocator
import cea.api
import cea.scripts
import yaml

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def run(config, script, **kwargs):
    print('Running {script} with args {args}'.format(script=script, args=kwargs))
    f = getattr(cea.api, script)
    f(config=config, **kwargs)
    print('-' * 80)


def main(config):
    set_up_environment_variables(config)

    workflow_yml = config.workflow.workflow
    if not os.path.exists(workflow_yml):
        raise cea.ConfigError("Workflow YAML file not found: {workflow}".format(workflow=workflow_yml))

    with open(workflow_yml, 'r') as workflow_fp:
        workflow = yaml.load(workflow_fp)

    for step in workflow:
        if "script" in step:
            do_script_step(config, step)
        elif "config" in step:
            config = do_config_step(config, step)
        else:
            raise ValueError("Invalid step configuration: {step}".format(step=step))


def set_up_environment_variables(config):
    """
    create some environment variables to be used when configuring stuff. this includes the variable NOW, plus
    one variable for each config parameter, named "CEA_{SECTION}_{PARAMETER}".

    This is useful for referring to the "user" config, when basing a workflow of the default config.
    """
    os.environ["NOW"] = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    for section in config.sections.values():
        for parameter in section.parameters.values():
            variable = "CEA_{section}_{parameter}".format(section=section.name, parameter=parameter.name)
            os.environ[variable] = parameter.get_raw()


def do_config_step(config, step):
    """update the :py:class:cea.config.Configuration object, returning the new value for the config"""
    base_config = step["config"]
    if base_config == "default":
        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    elif base_config == "user":
        config = cea.config.Configuration()
    elif base_config == ".":
        # keep the current config, we're just going to update some parameters
        config = config
    else:
        # load the config from a file
        config = cea.config.Configuration(base_config)

    for fqn in step.keys():
        if fqn == "config":
            continue
        parameter = config.get_parameter(fqname=fqn)
        value = step[fqn]
        set_parameter(config, parameter, value)
    return config


def set_parameter(config, parameter, value):
    """Set a parameter to a value (expand with environment vars) without tripping the restricted_to part of config"""
    original_restricted_to = config.restricted_to
    try:
        config.restricted_to = None
        print("Setting {parameter}={value}".format(parameter=parameter.fqname, value=value))
        if not isinstance(value, basestring):
            value = str(value)
        expanded_value = os.path.expandvars(value)
        parameter.set(parameter.decode(expanded_value))
    finally:
        config.restricted_to = original_restricted_to


def do_script_step(config, step):
    """Run a script based on the step's "script" and "parameters" (optional) keys."""
    script = cea.scripts.by_name(step["script"])
    print("Workflow step: script={script}".format(script=script.name))
    parameters = {p.name: p.get() for s, p in config.matching_parameters(script.parameters)}
    if "parameters" in step:
        parameters.update(step["parameters"])
    py_script = script.name.replace("-", "_")
    py_parameters = {k.replace("-", "_"): v for k, v in parameters.items()}
    run(config, py_script, **py_parameters)


if __name__ == '__main__':
    main(cea.config.Configuration())