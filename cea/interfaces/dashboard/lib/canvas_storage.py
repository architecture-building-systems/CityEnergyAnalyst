"""
Canvas Builder storage layer.

Owns the on-disk shape of a canvas (one folder per canvas, three YAML
files inside, plus a per-card ``data/<cardId>/`` subtree) and the
read / write primitives used by the FastAPI router.

Layout under ``<scenario>/outputs/canvas`` (paths owned by
``InputLocator.get_canvas_*`` helpers; this module assembles the YAML
shape that lives inside each canvas folder):

    outputs/canvas/
    ├── temp/
    │   └── <uuid>/                  # never-saved drafts AND dirty
    │       ├── canvas.yml           #   edits of saved canvases
    │       ├── layout.yml
    │       ├── feature_card.yml
    │       └── data/<card_id>/...
    └── <Display Name>/              # committed canvases — folder
        └── …same shape              #   name = display name

Why three YAMLs (and not one)?

    - ``canvas.yml`` rarely changes (name, view, scenarios picked,
      navigator toggles, timestamps).
    - ``layout.yml`` is the hot file — drag/resize fires it
      constantly, so an autosave path can flush *just* this file
      without rewriting the rest.
    - ``feature_card.yml`` changes when cards are added / edited /
      removed, on a slower cadence than layout.

Splitting them lets the autosave debouncer be granular and lets the
zip-export / import pass round-trip the full state with no extra
metadata.

Module exports:

- ``CanvasMeta``, ``LayoutFile``, ``FeatureCardFile`` — Pydantic
  schemas with stable ``schema_version`` fields. ``extra='allow'``
  on the inner card / column models so we can grow the shape without
  forcing a YAML migration.
- ``sanitize_canvas_name`` — bounce names that would break a
  filesystem (or collide with the ``temp`` reserved subfolder).
- ``read_canvas`` / ``write_canvas`` — load / dump all three YAMLs
  for a given canvas folder.
- ``list_saved_canvases`` / ``list_temp_canvases`` — directory
  listings keyed by name / uuid.
- ``create_temp_canvas`` / ``promote_temp_to_saved`` /
  ``delete_canvas_folder`` — directory lifecycle helpers.
"""

from __future__ import annotations

import io
import os
import re
import shutil
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import yaml
from pydantic import BaseModel, ConfigDict, Field

import cea.inputlocator

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# ── Schemas ──────────────────────────────────────────────────────


SCHEMA_VERSION = 1


class _Allowed(BaseModel):
    """Base for inner shapes that callers may extend without a
    schema bump (per-card metadata, plot configs, etc.)."""
    model_config = ConfigDict(extra='allow')


class ColumnSpec(_Allowed):
    """One column in a comparison view. Mirrors the canvasStore
    column shape so round-tripping is trivial."""
    type: str  # 'scenario' | 'whatif' | 'feature'
    scenario: Optional[str] = None
    whatif: Optional[str] = None
    feature: Optional[str] = None


class CanvasMeta(BaseModel):
    """Top-level canvas state — what gets written to ``canvas.yml``."""
    schema_version: int = SCHEMA_VERSION

    # Display name. ``None`` while a draft is still untitled.
    name: Optional[str] = None
    # Set on temp canvases that started as a copy of a saved one,
    # so Save knows which root folder to overwrite. ``None`` for
    # drafts and for saved canvases.
    parent_canvas_name: Optional[str] = None

    # 'launch' | 'inter-scenario' | 'inter-whatif' | 'inter-feature'
    view: str = 'launch'
    # Carried for portability — the project this canvas belongs to.
    project: Optional[str] = None
    # For inter-whatif / inter-feature views.
    parent_scenario: Optional[str] = None
    columns: List[ColumnSpec] = Field(default_factory=list)

    # Navigator toggle state.
    maps_linked: bool = True
    fix_layout: bool = False

    # ISO-8601 UTC strings; updated on every write.
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TilePos(BaseModel):
    """A grid tile's position + size in `react-grid-layout` units."""
    x: int = 0
    y: int = 0
    w: int = 1
    h: int = 1


class LayoutFile(BaseModel):
    """Per-card grid positions — written to ``layout.yml``.

    Either ``cards`` or ``column_cards`` is populated, depending on
    the canvas's ``view``:
      - ``launch`` / ``inter-scenario`` / ``inter-whatif`` →
        ``cards`` (single shared grid)
      - ``inter-feature`` → ``column_cards`` (one grid per column)

    ``map_positions`` holds the primary map tile's position per
    column (single-entry list for the launch view).
    """
    schema_version: int = SCHEMA_VERSION
    map_positions: List[TilePos] = Field(default_factory=list)
    cards: Dict[str, TilePos] = Field(default_factory=dict)
    column_cards: Dict[str, Dict[str, TilePos]] = Field(default_factory=dict)


class PlotEntry(_Allowed):
    """One plot inside a `plot`-typed card."""
    id: str
    plot_config: Dict[str, Any] = Field(default_factory=dict)


class CardConfig(_Allowed):
    """One card's content — type, feature, plot configs, layer info."""
    type: str  # 'plot' | 'kpi' | 'map'
    feature: Optional[str] = None
    plots: List[PlotEntry] = Field(default_factory=list)
    category: Optional[str] = None
    layer: Optional[str] = None


class FeatureCardFile(BaseModel):
    """Per-card content — written to ``feature_card.yml``.

    Mirrors `LayoutFile`'s shape: ``cards`` for shared grids,
    ``column_cards`` for inter-feature.
    """
    schema_version: int = SCHEMA_VERSION
    cards: Dict[str, CardConfig] = Field(default_factory=dict)
    column_cards: Dict[str, Dict[str, CardConfig]] = Field(default_factory=dict)


class CanvasState(BaseModel):
    """Bundle returned by ``read_canvas`` — all three YAMLs together."""
    canvas: CanvasMeta
    layout: LayoutFile
    feature_card: FeatureCardFile


# ── Name sanitisation ────────────────────────────────────────────


# Reserved subfolder under the canvas root — saving a canvas under
# this exact name would clash with the in-progress staging area.
_RESERVED_NAMES = {'temp'}

# Filesystem hostiles. Replaced with `_` so a typed " / " becomes
# "_ _" rather than failing with "no such directory".
_FS_HOSTILE_CHARS_RE = re.compile(r'[\\/:*?"<>|]')

# Collapse runs of whitespace + strip leading/trailing whitespace
# and dots (leading dots make hidden folders on POSIX).
_WS_COLLAPSE_RE = re.compile(r'\s+')


def sanitize_canvas_name(name: str) -> str:
    """Return a filesystem-safe version of ``name``, or raise
    ``ValueError`` if no reasonable name remains.

    - Replaces ``\\ / : * ? " < > |`` with ``_`` (those are illegal
      on at least one of the major filesystems we ship to).
    - Collapses internal whitespace runs to a single space, trims
      leading/trailing whitespace + dots.
    - Rejects names that collapse to empty.
    - Rejects ``temp`` (case-insensitive) since the canvas root uses
      that for in-progress drafts.
    - Rejects names longer than 200 chars to stay under common
      filesystem limits.
    """
    if not isinstance(name, str):
        raise ValueError('Canvas name must be a string')
    cleaned = _FS_HOSTILE_CHARS_RE.sub('_', name)
    cleaned = _WS_COLLAPSE_RE.sub(' ', cleaned).strip(' .')
    if not cleaned:
        raise ValueError('Canvas name cannot be empty')
    if cleaned.lower() in _RESERVED_NAMES:
        raise ValueError(f"'{cleaned}' is reserved; choose a different name")
    if len(cleaned) > 200:
        raise ValueError('Canvas name must be 200 characters or fewer')
    return cleaned


# ── YAML I/O ─────────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_yaml(path: str) -> Dict[str, Any]:
    if not os.path.isfile(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        loaded = yaml.safe_load(f)
    return loaded or {}


def _write_yaml(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=True)


def read_canvas(locator: cea.inputlocator.InputLocator,
                canvas_folder: str) -> CanvasState:
    """Load all three YAMLs from a canvas folder into typed models.

    Missing files are allowed (a freshly-created folder may have only
    `canvas.yml` for example) — they fall back to default-empty
    instances. Validation errors propagate so a malformed file is
    surfaced loudly rather than silently ignored.
    """
    canvas_meta = CanvasMeta.model_validate(
        _read_yaml(locator.get_canvas_yml(canvas_folder))
    )
    layout = LayoutFile.model_validate(
        _read_yaml(locator.get_canvas_layout_yml(canvas_folder))
    )
    feature_card = FeatureCardFile.model_validate(
        _read_yaml(locator.get_canvas_feature_card_yml(canvas_folder))
    )
    return CanvasState(canvas=canvas_meta, layout=layout, feature_card=feature_card)


def write_canvas(locator: cea.inputlocator.InputLocator,
                 canvas_folder: str,
                 canvas: Optional[CanvasMeta] = None,
                 layout: Optional[LayoutFile] = None,
                 feature_card: Optional[FeatureCardFile] = None) -> None:
    """Sparse-write the three YAMLs.

    Pass any subset of ``canvas`` / ``layout`` / ``feature_card`` —
    the others stay untouched. Always stamps ``updated_at`` (and
    ``created_at`` on first write) on the canvas meta when it's
    being written.
    """
    if canvas is not None:
        now = _now_iso()
        if canvas.created_at is None:
            canvas.created_at = now
        canvas.updated_at = now
        _write_yaml(locator.get_canvas_yml(canvas_folder),
                    canvas.model_dump(mode='json'))
    if layout is not None:
        _write_yaml(locator.get_canvas_layout_yml(canvas_folder),
                    layout.model_dump(mode='json'))
    if feature_card is not None:
        _write_yaml(locator.get_canvas_feature_card_yml(canvas_folder),
                    feature_card.model_dump(mode='json'))


# ── Directory listings ──────────────────────────────────────────


def list_saved_canvases(locator: cea.inputlocator.InputLocator) -> List[str]:
    """Names of every committed canvas under the scenario.

    Skips the ``temp`` subfolder, files (non-directories), and
    hidden ``.``-prefixed entries (``.DS_Store`` etc.).
    """
    root = locator.get_canvas_folder()
    if not os.path.isdir(root):
        return []
    out = []
    for entry in sorted(os.listdir(root)):
        if entry.startswith('.') or entry == 'temp':
            continue
        if os.path.isdir(os.path.join(root, entry)):
            out.append(entry)
    return out


def list_temp_canvases(locator: cea.inputlocator.InputLocator) -> List[str]:
    """UUIDs of every in-progress canvas."""
    root = locator.get_canvas_temp_folder()
    if not os.path.isdir(root):
        return []
    return sorted(
        entry for entry in os.listdir(root)
        if not entry.startswith('.')
        and os.path.isdir(os.path.join(root, entry))
    )


# ── Lifecycle helpers ───────────────────────────────────────────


def create_temp_canvas(locator: cea.inputlocator.InputLocator,
                       uuid: str,
                       parent_canvas_name: Optional[str] = None) -> str:
    """Materialise a fresh ``temp/<uuid>/`` folder.

    If ``parent_canvas_name`` is given, the saved canvas's contents
    are copied in (this is the "first edit on a saved canvas"
    flow). Otherwise the temp starts empty (untitled draft).

    Returns the temp folder path.
    """
    temp_folder = locator.get_temp_canvas_folder(uuid)
    if os.path.exists(temp_folder):
        raise FileExistsError(f'Temp canvas {uuid!r} already exists')
    if parent_canvas_name:
        src = locator.get_saved_canvas_folder(parent_canvas_name)
        if not os.path.isdir(src):
            raise FileNotFoundError(
                f"Saved canvas {parent_canvas_name!r} not found")
        shutil.copytree(src, temp_folder)
        # Record the edit relationship on the temp's canvas.yml so
        # Save knows where to commit back.
        state = read_canvas(locator, temp_folder)
        state.canvas.parent_canvas_name = parent_canvas_name
        write_canvas(locator, temp_folder, canvas=state.canvas)
    else:
        os.makedirs(temp_folder, exist_ok=True)
        write_canvas(
            locator,
            temp_folder,
            canvas=CanvasMeta(),
            layout=LayoutFile(),
            feature_card=FeatureCardFile(),
        )
    return temp_folder


def promote_temp_to_saved(locator: cea.inputlocator.InputLocator,
                          uuid: str,
                          name: str) -> str:
    """Move ``temp/<uuid>/`` to ``<name>/`` (sanitised).

    Behaviour:
      - If ``<name>/`` already exists AND it matches the temp's
        ``parent_canvas_name``, it's overwritten (re-saving an
        existing canvas).
      - Otherwise an existing ``<name>/`` is treated as a duplicate
        and ``FileExistsError`` is raised so the caller can prompt
        the user (overwrite / rename).
      - The canvas.yml's ``name`` is updated to the sanitised name
        and ``parent_canvas_name`` cleared (no longer a draft).

    Returns the saved canvas folder path.
    """
    safe_name = sanitize_canvas_name(name)
    temp_folder = locator.get_temp_canvas_folder(uuid)
    if not os.path.isdir(temp_folder):
        raise FileNotFoundError(f'Temp canvas {uuid!r} not found')

    state = read_canvas(locator, temp_folder)
    saved_folder = locator.get_saved_canvas_folder(safe_name)

    parent = state.canvas.parent_canvas_name
    if os.path.isdir(saved_folder) and parent != safe_name:
        raise FileExistsError(
            f'A saved canvas named {safe_name!r} already exists')

    # Update canvas.yml with the committed name + clear parent link
    # before the move, so the file on disk is consistent the moment
    # it lands at its final path.
    state.canvas.name = safe_name
    state.canvas.parent_canvas_name = None
    write_canvas(locator, temp_folder, canvas=state.canvas)

    if os.path.isdir(saved_folder):
        shutil.rmtree(saved_folder)
    shutil.move(temp_folder, saved_folder)
    return saved_folder


def delete_canvas_folder(folder: str) -> None:
    """Remove a canvas folder (saved or temp). No-op if absent."""
    if os.path.isdir(folder):
        shutil.rmtree(folder)


# ── Zip export / import ────────────────────────────────────────


# canvas.yml is the load-bearing presence test — a zip without it
# isn't a canvas. layout / feature_card are technically optional
# (an empty draft might lack them) so we don't enforce them here.
_CANVAS_MARKER = 'canvas.yml'


def export_canvas_zip(
    locator: cea.inputlocator.InputLocator,
    name: str,
) -> io.BytesIO:
    """Build an in-memory zip of the saved canvas folder.

    The zip's top-level directory is the canvas's display name, so a
    recipient who unzips gets ``<name>/canvas.yml`` etc. Returns a
    rewound ``BytesIO`` ready for ``StreamingResponse`` to consume.

    Raises ``FileNotFoundError`` if the canvas doesn't exist.
    """
    folder = locator.get_saved_canvas_folder(name)
    if not os.path.isdir(folder):
        raise FileNotFoundError(f'Saved canvas {name!r} not found')

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(folder):
            for filename in files:
                if filename.startswith('.'):
                    # Skip filesystem cruft (`.DS_Store` on macOS, etc.)
                    continue
                full = os.path.join(root, filename)
                rel = os.path.relpath(full, folder)
                # Top-level directory in the zip = canvas name.
                zf.write(full, os.path.join(name, rel))
    buf.seek(0)
    return buf


def _zip_top_level(zf: zipfile.ZipFile) -> Tuple[str, List[zipfile.ZipInfo]]:
    """Walk a canvas zip and return ``(top_dir_name, member_infos)``.

    Validates that:
      - There's exactly one top-level directory (the canvas name).
      - It contains a ``canvas.yml`` marker.

    Raises ``ValueError`` on any structural problem so the caller can
    surface a clean 400 rather than crashing on a bad upload.
    """
    members = [m for m in zf.infolist() if not m.is_dir()]
    if not members:
        raise ValueError('Zip is empty')

    top_levels = set()
    for m in members:
        # Reject absolute paths and parent-traversal segments.
        if m.filename.startswith('/') or '..' in m.filename.split('/'):
            raise ValueError(f'Unsafe path inside zip: {m.filename!r}')
        head = m.filename.split('/', 1)[0]
        if not head:
            raise ValueError('Files at the zip root are not allowed')
        top_levels.add(head)

    if len(top_levels) != 1:
        raise ValueError(
            'Zip must contain exactly one top-level canvas folder'
        )
    top = next(iter(top_levels))

    has_marker = any(
        m.filename == f'{top}/{_CANVAS_MARKER}' for m in members
    )
    if not has_marker:
        raise ValueError(
            f"Zip is not a canvas — missing {_CANVAS_MARKER!r}"
        )

    return top, members


def import_canvas_zip(
    locator: cea.inputlocator.InputLocator,
    zip_bytes: bytes,
    rename_to: Optional[str] = None,
) -> str:
    """Unpack a canvas zip into ``outputs/canvas/<sanitised name>/``.

    The display name is taken from the zip's top-level directory and
    sanitised (same rules as Save). Pass ``rename_to`` to import
    under a different display name — used by the UI's "import as"
    prompt when the original name collides with an existing saved
    canvas. The override is sanitised the same way.

    Returns the cleaned name on success.

    Raises:
      ValueError: malformed zip / missing canvas marker / illegal
        name (caller maps to 400).
      FileExistsError: a saved canvas with the same target name
        already lives on disk (caller maps to 409 so the UI can
        prompt the user to rename or overwrite).
    """
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile as exc:
        raise ValueError(f'Invalid zip file: {exc}') from exc

    with zf:
        top, members = _zip_top_level(zf)
        clean_name = sanitize_canvas_name(rename_to or top)
        target = locator.get_saved_canvas_folder(clean_name)
        if os.path.exists(target):
            raise FileExistsError(
                f'A saved canvas named {clean_name!r} already exists'
            )

        os.makedirs(target, exist_ok=True)
        try:
            for m in members:
                # Strip the top-level prefix; everything else is the
                # path relative to the canvas folder.
                rel = m.filename.split('/', 1)[1]
                if not rel:
                    continue
                out_path = os.path.join(target, rel)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                with zf.open(m) as src, open(out_path, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
        except Exception:
            # Roll back a partial extract so the user retries against
            # a clean target (rather than a half-imported folder
            # that would now collide with the same name).
            shutil.rmtree(target, ignore_errors=True)
            raise

        # When importing under a renamed target, update the canvas's
        # own metadata so the on-disk `name` field matches the
        # folder name — otherwise opening the imported canvas would
        # display its original name in the dashboard switcher even
        # though it now lives at a different path.
        if rename_to is not None:
            try:
                state = read_canvas(locator, target)
                state.canvas.name = clean_name
                state.canvas.parent_canvas_name = None
                write_canvas(locator, target, canvas=state.canvas)
            except Exception:
                # Don't undo a successful extract over a metadata
                # patch failure — the canvas is still importable,
                # just with a stale display name in canvas.yml.
                pass

    return clean_name
