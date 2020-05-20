"""
Run the CEA scripts and unit tests as part of our CI efforts (cf. The Jenkins)
"""

from __future__ import division
from __future__ import print_function

import os
import shutil
import tempfile
import coverage

import cea.config
import cea.inputlocator
import cea.workflows.workflow

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main(config):
    workflow_yml = os.path.join(os.path.dirname(__file__), "workflow_{workflow}.yml".format(workflow=config.test.workflow))

    default_config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    default_config.project = os.path.expandvars("${TEMP}/reference-case-open")
    default_config.workflow.workflow = workflow_yml
    default_config.workflow.resume = False
    default_config.workflow.resume_file = tempfile.mktemp("resume.yml")  # force resume file to be temporary

    if os.path.exists(default_config.project):
        # make sure we're working on a clean slate
        shutil.rmtree(default_config.project)

    cov = coverage.Coverage()
    cov.start()
    cea.workflows.workflow.main(default_config)
    cov.stop()

    print("=" * 80)
    print("Coverage Summary:")
    print("=" * 80)
    cov.report()

    coverage_report_path = os.path.join(default_config.project, 'coverage_report')
    cov.html_report(directory=coverage_report_path)
    print("\nCoverage report saved in '{coverage_report_path}'".format(coverage_report_path=coverage_report_path))


if __name__ == '__main__':
    main(cea.config.Configuration())