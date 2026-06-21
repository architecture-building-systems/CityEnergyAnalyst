"""
Deterministic state fingerprints — short, stable identifiers used to
detect when something has changed since the last time we looked at it.

Three primitives:

* :func:`hash_folder`  — SHA256 over a folder's relative paths and file
  contents. OS-level junk (Finder / Windows / cloud-sync sidecars) is
  filtered out so the hash stays stable when external software
  rewrites those files.

* :func:`hash_files`   — SHA256 over a sorted sequence of files. Same
  shape as ``hash_folder`` but for an explicit list rather than a
  folder walk — handy when only a few specific files matter (e.g. the
  CSVs a single KPI reads).

* :func:`hash_payload` — SHA256 over a JSON-serialisable object using
  canonical encoding (``sort_keys=True``, no whitespace). Identical
  objects produce identical hashes regardless of dict-insertion order
  or pretty-print formatting.

Used by:

* ``cea/datamanagement/district_pathways/pathway_status.py`` for the
  baked / validated / simulated freshness gates.
* ``cea/datamanagement/district_pathways/pathway_state.py`` for the
  ``source_log_hash`` of a year's modification log.
* ``cea/kpi/`` for the three-hash cache gate
  (scenario-inputs / upstream-outputs / KPI-definition).

Anything that asks "did this state change since I last cached
something against it?" should reuse these helpers rather than reach
for ``hashlib`` directly. (``cea/plots/cache.py``'s parameter MD5 is
a different beast — it generates cache *keys*, not freshness
fingerprints — and stays as-is.)
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Iterable, Sequence


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

_DEFAULT_IGNORED_FILES = frozenset({".DS_Store", "Thumbs.db", "desktop.ini", "Icon\r"})


def _is_ignored_hash_file(name: str, *, extra: frozenset[str] = frozenset()) -> bool:
    # AppleDouble sidecars (``._<name>``) plus Finder / Windows /
    # cloud-sync metadata files are written by external software and
    # can drift independently of CEA's own outputs. Skip them so the
    # hash stays stable across reboots / Dropbox syncs / etc.
    if name.startswith("._"):
        return True
    if name in _DEFAULT_IGNORED_FILES:
        return True
    return name in extra


_HASH_CHUNK_BYTES = 1024 * 1024


def hash_folder(
    path: str,
    *,
    ignored_files: Iterable[str] = (),
) -> str:
    """SHA256 fingerprint of a folder's relative paths + file contents.

    Walks ``path`` deterministically (sorted directories, sorted file
    names) so two runs over the same on-disk state produce the same
    hex digest. OS junk files are skipped per
    :func:`_is_ignored_hash_file`.

    Returns a 64-character hex digest. Raises whatever ``os.walk``
    raises if ``path`` doesn't exist.
    """
    extra = frozenset(ignored_files)
    digest = hashlib.sha256()
    for root, dirs, files in os.walk(path):
        dirs.sort()
        rel_root = os.path.relpath(root, path)
        digest.update(rel_root.replace("\\", "/").encode("utf-8"))
        for file_name in sorted(files):
            if _is_ignored_hash_file(file_name, extra=extra):
                continue
            file_path = os.path.join(root, file_name)
            rel_path = os.path.relpath(file_path, path).replace("\\", "/")
            digest.update(rel_path.encode("utf-8"))
            with open(file_path, "rb") as handle:
                while True:
                    chunk = handle.read(_HASH_CHUNK_BYTES)
                    if not chunk:
                        break
                    digest.update(chunk)
    return digest.hexdigest()


def hash_files(paths: Sequence[str]) -> str:
    """SHA256 fingerprint over an explicit list of files.

    The list is sorted so call order doesn't matter. Each file
    contributes its absolute path (as the canonical key) followed by
    its bytes. Missing files contribute an explicit ``<missing>``
    marker rather than raising — callers checking "did anything
    change?" want to see "this file disappeared" as a state change,
    not as an exception.
    """
    digest = hashlib.sha256()
    for file_path in sorted(paths):
        canonical = file_path.replace("\\", "/")
        digest.update(canonical.encode("utf-8"))
        if not os.path.isfile(file_path):
            digest.update(b"<missing>")
            continue
        with open(file_path, "rb") as handle:
            while True:
                chunk = handle.read(_HASH_CHUNK_BYTES)
                if not chunk:
                    break
                digest.update(chunk)
    return digest.hexdigest()


def hash_payload(obj: Any) -> str:
    """SHA256 fingerprint of a JSON-serialisable object.

    Uses canonical encoding (``sort_keys=True``, ``separators=(",", ":")``)
    so dict-insertion order and whitespace don't perturb the hash.
    Anything ``json.dumps`` can serialise is acceptable; tuples become
    lists, NaN / Infinity are rejected.
    """
    encoded = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
