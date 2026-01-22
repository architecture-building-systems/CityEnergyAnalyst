import glob
import multiprocessing.pool
import os
import sys
import unittest
from typing import List

import cea.config
from cea.workflows.workflow import main


def _ensure_utf8_streams():
    """Ensure stdout/stderr use UTF-8 encoding on Windows."""
    import io
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except (AttributeError, TypeError):
        pass
    try:
        if sys.stderr.encoding != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except (AttributeError, TypeError):
        pass


class PrefixedWriter:
    """Wraps a stream and prefixes each line with a label."""

    def __init__(self, stream, prefix: str):
        self._stream = stream
        self._prefix = prefix
        self._at_line_start = True

    def write(self, text: str):
        if not text:
            return

        lines = text.split('\n')
        for i, line in enumerate(lines):
            # Add prefix at the start of each new line
            if self._at_line_start and line:
                self._stream.write(f"{self._prefix} ")

            self._stream.write(line)

            # Add newline between lines (but not after the last segment)
            if i < len(lines) - 1:
                self._stream.write('\n')
                self._at_line_start = True
            else:
                # If the text ended with content (no trailing newline), we're mid-line
                self._at_line_start = text.endswith('\n')

    def flush(self):
        self._stream.flush()


def _run_workflow_with_prefix(config: cea.config.Configuration):
    """Run a workflow with prefixed stdout/stderr output."""
    # Ensure UTF-8 encoding before wrapping streams (fixes Windows cp1252 issues)
    _ensure_utf8_streams()

    workflow_path = config.workflow.workflow
    workflow_name = os.path.splitext(os.path.basename(workflow_path))[0]
    prefix = f"{workflow_name[:12]:<12} | "

    original_stdout = sys.stdout
    original_stderr = sys.stderr

    try:
        sys.stdout = PrefixedWriter(original_stdout, prefix)
        sys.stderr = PrefixedWriter(original_stderr, prefix)
        main(config)
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr


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
            p.map(_run_workflow_with_prefix, [self.get_workflow_config(workflow) for workflow in self.get_test_workflows()])


if __name__ == '__main__':
    unittest.main()
