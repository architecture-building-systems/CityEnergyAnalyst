"""
Helper for removing stale per-script output folders before re-running.

Each CEA simulation script (radiation, occupancy, demand, photovoltaic, etc.) writes
to a known output folder. When the user re-runs the script, stale files from a previous
run with different settings (e.g. monthly vs hourly demand, different building list)
can pollute the output and cause downstream readers to fail or aggregate mixed schemas.

To avoid this, scripts call ``cleanup_output_folder(folder)`` at the very start of their
``main()`` to wipe the folder. This is a deliberate one-line cleanup — not a generic
"delete everything" — and only affects the script's own output.
"""
from __future__ import annotations

import os
import shutil


def cleanup_output_folder(folder: str) -> None:
    """Remove a script's output folder if it exists, to clear stale results."""
    if folder and os.path.isdir(folder):
        shutil.rmtree(folder, ignore_errors=True)


def cleanup_output_files(*paths: str) -> None:
    """Remove a list of specific output files if they exist."""
    for path in paths:
        if path and os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass
