"""
Shared plot-rendering primitive used by both `/api/reports/plot-custom`
(live render for the Canvas Builder) and `/api/canvas/.../save`
(snapshot the rendered HTML alongside the saved canvas so the zip
export is self-contained).

Without sharing this code path, the Save endpoint would have to
re-spawn the FastAPI request lifecycle internally to reuse the
existing dispatcher — clumsy and brittle. Pulling the script lookup
+ config mutation + module import into a plain function keeps both
call sites symmetrical and lets us evolve the dispatch in one place.
"""

from __future__ import annotations

import importlib
import os
import re
import sys
from contextlib import contextmanager
from typing import Any, Dict, Optional

import cea.scripts


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class _NonTtyStdout:
    """Wrap `sys.stdout` so `.isatty()` returns False — several plot
    modules auto-launch a browser via `fig.show(renderer="browser")`
    when stdout is a tty, which is fine from the CLI but disruptive
    when the dashboard server runs in a terminal. Only `isatty` is
    overridden; everything else forwards so logs / prints survive.
    """

    def __init__(self, stream):
        self._stream = stream

    def __getattr__(self, name):
        return getattr(self._stream, name)

    def isatty(self) -> bool:
        return False


@contextmanager
def suppress_browser_autopopup():
    original = sys.stdout
    sys.stdout = _NonTtyStdout(original)
    try:
        yield
    finally:
        sys.stdout = original


_BODY_RE = re.compile(r"<body[^>]*>(.*)</body>", re.DOTALL | re.IGNORECASE)


def render_plot_html(
    config,
    *,
    scenario_path: str,
    script_name: str,
    parameters: Optional[Dict[str, Any]] = None,
) -> str:
    """Run a CEA plot script and return its HTML body.

    The function mutates ``config`` in-place to point at
    ``scenario_path`` and applies the script's parameter set; the
    caller is responsible for restoring ``config.project`` /
    ``config.scenario_name`` afterwards if the surrounding scope
    needs to.

    Pareto-front returns a 2-tuple of partial HTMLs; this helper
    flattens that to a single string so callers don't need to
    special-case it.

    The outer ``<html>/<head>/<body>`` chrome is stripped if present
    — both the live render path (Reports) and the snapshot capture
    path (Canvas Save) embed the body fragment inside their own
    container.
    """
    parameters = parameters or {}

    script = cea.scripts.by_name(script_name, plugins=config.plugins)

    config.project = os.path.dirname(scenario_path)
    config.scenario_name = os.path.basename(scenario_path)

    for _, parameter in config.matching_parameters(script.parameters):
        if parameter.name in parameters:
            value = parameters[parameter.name]
            if isinstance(value, list):
                parameter.set(parameter.decode(",".join(str(v) for v in value)))
            else:
                parameter.set(parameter.decode(str(value)))

    config.restrict_to(script.parameters)
    script_module = importlib.import_module(script.module)
    with suppress_browser_autopopup():
        result = script_module.main(config)

    if isinstance(result, tuple):
        html = "\n".join(part for part in result if part)
    else:
        html = result

    match = _BODY_RE.search(html or "")
    return match.group(1) if match else (html or "")
