"""Shared filesystem anchors for the CEA test suite.

Centralises the repo/examples/workflows locations so individual test modules don't
recompute them from their own ``__file__`` (which breaks when tests move between
subfolders).
"""
from pathlib import Path

import cea.examples

TESTS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TESTS_ROOT.parent.parent  # cea/tests -> cea -> <repo root>
EXAMPLES_DIR = Path(cea.examples.__file__).resolve().parent
WORKFLOWS_DIR = TESTS_ROOT / "workflows"


def reference_case_baseline() -> str:
    """Baseline scenario of the bundled open reference case."""
    return str(EXAMPLES_DIR / "reference-case-open" / "baseline")
