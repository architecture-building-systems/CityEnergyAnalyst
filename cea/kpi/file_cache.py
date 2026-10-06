"""
Stat-keyed read cache for the small lookups KPI requests repeat.

A KPI card re-reads the same scenario files on every fetch (the PV panel
database for labels, the what-if configuration for annotations). Those files
change rarely, so :func:`read_cached` keeps the loaded value until the file's
modification time or size changes -- the next read after an edit reloads it,
with no invalidation hook to wire up.

Cached values are shared between callers (and threads): treat them as
read-only.
"""

from __future__ import annotations

import os
import threading
from collections import OrderedDict
from typing import Any, Callable, Tuple

__author__ = "Reynold Mok"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Reynold Mok"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

_MAX_ENTRIES = 64

_lock = threading.Lock()
_entries: "OrderedDict[Tuple[str, str], Tuple[Tuple[int, int], Any]]" = OrderedDict()


def read_cached(path: str, loader: Callable[[str], Any], *, kind: str) -> Any:
    """``loader(path)``, reused until ``path``'s mtime or size changes.

    ``kind`` names what the loader extracts, so two different readings of the
    same file do not share a slot. Raises ``OSError`` when ``path`` cannot be
    stat-ed; whatever ``loader`` raises propagates and is not cached.
    """
    stat = os.stat(path)
    stamp = (stat.st_mtime_ns, stat.st_size)
    key = (kind, path)
    with _lock:
        hit = _entries.get(key)
        if hit is not None and hit[0] == stamp:
            _entries.move_to_end(key)
            return hit[1]
    # Loaded outside the lock so one slow file does not stall every other
    # reader; two threads racing on a cold entry both load, which is harmless.
    value = loader(path)
    with _lock:
        _entries[key] = (stamp, value)
        _entries.move_to_end(key)
        while len(_entries) > _MAX_ENTRIES:
            _entries.popitem(last=False)
    return value


def clear() -> None:
    """Drop every cached entry. Used by tests."""
    with _lock:
        _entries.clear()
