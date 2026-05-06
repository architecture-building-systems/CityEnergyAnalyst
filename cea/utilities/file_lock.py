"""
Cross-process file lock — POSIX ``fcntl.flock`` and Windows
``msvcrt.locking`` under one context manager so callers don't
need a platform branch at every use site.

The lock file itself is a separate sidecar (``<target>.lock`` is
the convention) — never the file being protected. Acquiring
``open(..., 'w')`` on the protected file would truncate it on
crash; the sidecar lets the protected file's atomic-replace
write semantics stay intact.

Usage::

    with FileLock(f"{path}.lock"):
        current = read(path)
        write_atomic(path, mutate(current))

The lock is exclusive (``LOCK_EX`` / ``LK_LOCK``) and blocking —
contenders queue on the kernel's lock table rather than spinning.
Release happens on context-manager exit, including the exception
path; the sidecar file is left in place (cheap, and avoids a
race where one process unlinks while another is mid-acquire).

This is a process-level lock. Within a single process,
``threading.Lock`` is the right primitive — flock semantics on a
single fd are undefined across threads on some platforms.
"""

from __future__ import annotations

import os
import sys

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class FileLock:
    """Cross-process file lock backed by ``fcntl`` / ``msvcrt``.

    Pass the *sidecar* path (e.g. ``f"{target}.lock"``) — never
    the file you're protecting. The sidecar is created on first
    acquire (parent directory must already exist) and reused
    on subsequent ones.
    """

    def __init__(self, lock_file_path: str):
        self.lock_file_path = lock_file_path
        self.lock_file = None

    def __enter__(self) -> "FileLock":
        # 'w' truncates an existing file but the file's contents
        # are irrelevant — only the kernel's lock table on the fd
        # matters. Truncation is the cheapest way to ensure the
        # file exists.
        self.lock_file = open(self.lock_file_path, "w")
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self.lock_file is None:
            return False
        try:
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
        finally:
            self.lock_file.close()
            self.lock_file = None
        return False


def kpi_status_lock_path(scenario: str) -> str:
    """Sidecar lock path for ``kpi_status.json`` writes.

    Lives next to the JSON itself so the lock and the file it
    protects share a directory — administrators auditing the
    cache folder see the relationship at a glance.
    """
    from cea.inputlocator import InputLocator

    status_path = InputLocator(scenario).get_kpi_status_file()
    os.makedirs(os.path.dirname(status_path), exist_ok=True)
    return f"{status_path}.lock"
