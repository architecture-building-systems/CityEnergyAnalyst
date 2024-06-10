import glob
import multiprocessing.pool
import os
import unittest
from typing import List

import cea.config
from cea.workflows.workflow import main


class TestWorkflows(unittest.TestCase):
    @staticmethod
    def get_test_workflows() -> List[str]:
        dirname = os.path.join(os.path.realpath(os.path.dirname(__file__)), "workflows")
        workflows = [workflow for workflow in glob.glob(os.path.join(dirname, "*.yml"))]

        return [os.path.join(dirname, workflow) for workflow in workflows]

    @staticmethod
    def get_workflow_config(workflow: str) -> cea.config.Configuration:
        config = cea.config.Configuration()
        config.workflow.workflow = workflow

        return config

    def _test_workflows(self):
        with multiprocessing.pool.Pool() as p:
            p.map(main, [self.get_workflow_config(workflow) for workflow in self.get_test_workflows()])


if __name__ == '__main__':
    unittest.main()
