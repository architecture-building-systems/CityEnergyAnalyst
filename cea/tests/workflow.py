"""
Run a workflow.yml file - this is like a cea-are "batch" file for running multiple cea scripts including parameters.
``cea workflow`` can also pick up from previous (failed?) runs, which can help in debugging.
"""
from __future__ import division
from __future__ import print_function

import os
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
    f = getattr(cea.api, script.replace('-', '_'))
    f(config=config, **kwargs)
    print('-' * 80)


def main(config):
    workflow_yml = config.workflow.workflow
    if not os.path.exists(workflow_yml):
        raise cea.ConfigError("Workflow YAML file not found: {workflow}".format(workflow=workflow_yml))

    with open(workflow_yml, 'r') as workflow_fp:
        workflow = yaml.load(workflow_fp)

    for step in workflow:
        script = cea.scripts.by_name(step["script"])
        print("Workflow step: script={script}".format(script=script.name))
        parameters = {p for s, p in config.matching_parameters(script.parameters)}
        if "parameters" in step:
            parameters.update(step["parameters"])


if __name__ == '__main__':
    main(cea.config.Configuration())