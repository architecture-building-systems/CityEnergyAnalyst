"""
Run a workflow.yml file - this is like a cea-aware "batch" file for running multiple cea scripts including parameters.
``cea workflow`` can also pick up from previous (failed?) runs, which can help in debugging.
"""

import os
import sys
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
    # print('Running {script} with args {args}'.format(script=script, args=kwargs))
    f = getattr(cea.api, script)
    f(config=config, **kwargs)
    config.restricted_to = None
    print('-' * 80)


def run_with_trace(config, script, **kwargs):
    """Same as run, but use the trace-inputlocator functionality to capture InputLocator calls"""
    from cea.utilities.trace_inputlocator.trace_inputlocator import create_trace_function, update_trace_data, meta_to_yaml

    if "multiprocessing" in kwargs:
        # we can only trace single processes
        kwargs["multiprocessing"] = False

    # stuff needed for trace-inputlocator
    script_start = datetime.datetime.now()
    results_set = set()
    orig_trace = sys.gettrace()
    sys.settrace(create_trace_function(results_set))

    run(config, script, **kwargs)  # <------------------------------ this is where we run the script!

    sys.settrace(orig_trace)

    # update the trace data
    trace_data = set()
    update_trace_data(config, cea.inputlocator.InputLocator(config.scenario), results_set, script,
                      script_start, trace_data)
    meta_to_yaml(config, trace_data, config.trace_inputlocator.meta_output_file)


def main(config: cea.config.Configuration):
    workflow_yml = config.workflow.workflow
    resume_yml = config.workflow.resume_file
    resume_mode_on = config.workflow.resume
    trace_input = config.workflow.trace_input

    set_up_environment_variables(config)

    resume_dict = read_resume_info(resume_yml, workflow_yml)
    resume_step = resume_dict[workflow_yml]

    if not os.path.exists(workflow_yml):
        raise cea.ConfigError("Workflow YAML file not found: {workflow}".format(workflow=workflow_yml))

    with open(workflow_yml, 'r') as workflow_fp:
        workflow = yaml.safe_load(workflow_fp)

    for i, step in enumerate(workflow):
        if "script" in step:
            if resume_mode_on and i <= resume_step:
                # skip steps already completed while resuming
                print("Skipping workflow step {i}: script={script}".format(i=i, script=step["script"]))
                write_resume_info(resume_yml, resume_dict, workflow_yml, i)
                continue
            do_script_step(config, i, step, trace_input)
        elif "config" in step:
            config = do_config_step(config, step)
        else:
            raise ValueError("Invalid step configuration: {i} - {step}".format(i=i, step=step))
        write_resume_info(resume_yml, resume_dict, workflow_yml, i)


def write_resume_info(resume_yml, resume_dict, workflow_yml, i):
    # write out information for resuming
    resume_dict[workflow_yml] = i
    with open(resume_yml, 'w') as resume_fp:
        yaml.dump(resume_dict, resume_fp, indent=4)


def read_resume_info(resume_yml, workflow_yml):
    try:
        with open(resume_yml, 'r') as resume_fp:
            resume_dict = yaml.safe_load(resume_fp)
            if not resume_dict:
                resume_dict = {workflow_yml: 0}
    except IOError:
        # no resume file found?
        resume_dict = {workflow_yml: 0}
    if workflow_yml not in resume_dict:
        resume_dict[workflow_yml] = 0
    return resume_dict


def set_up_environment_variables(config):
    """
    create some environment variables to be used when configuring stuff. this includes the variable NOW, plus
    one variable for each config parameter, named "CEA_{SECTION}_{PARAMETER}".

    This is useful for referring to the "user" config, when basing a workflow off the default config.
    """
    os.environ["NOW"] = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    for section in config.sections.values():
        for parameter in section.parameters.values():
            variable = "CEA_{section}_{parameter}".format(section=section.name, parameter=parameter.name)
            os.environ[variable] = str(parameter.get_raw())


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
    with config.ignore_restrictions():
        print("Setting {parameter}={value}".format(parameter=parameter.fqname, value=value))
        if not isinstance(value, str):
            value = str(value)
        expanded_value = os.path.expandvars(value)
        parameter.set(parameter.decode(expanded_value))


def do_script_step(config, i, step, trace_input):
    """Run a script based on the step's "script" and "parameters" (optional) keys."""
    script = cea.scripts.by_name(step["script"], plugins=config.plugins)
    print("")
    print("=" * 80)
    print("Workflow step {i}: script={script}".format(i=i, script=script.name))
    print("=" * 80)
    # with config.ignore_restrictions():
    #     parameters = {p.name: p.get() for s, p in config.matching_parameters(script.parameters)}

    parameters = {}
    if "parameters" in step:
        parameters.update(step["parameters"])
    py_script = script.name.replace("-", "_")
    py_parameters = {k.replace("-", "_"): v for k, v in parameters.items()}

    if trace_input:
        run_with_trace(config, py_script, **py_parameters)
    else:
        run(config, py_script, **py_parameters)


if __name__ == '__main__':
    main(cea.config.Configuration())
