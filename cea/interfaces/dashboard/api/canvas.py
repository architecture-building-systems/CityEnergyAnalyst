"""
Canvas Builder API — saved + in-progress canvases for the Canvas
Builder dashboard.

The on-disk shape, schemas, and read/write/lifecycle helpers live in
``cea.interfaces.dashboard.lib.canvas_storage``; this router is a
thin HTTP-facing wrapper that exposes those primitives.

Endpoints (all scenario-scoped via the standard ``?project=&scenario=``
query params, mirroring ``reports.py``):

  GET    /api/canvas/                    list saved canvas names
  POST   /api/canvas/temp                create draft (or dirty edit
                                         of a saved canvas); body
                                         `{ from?: <saved-name> }`,
                                         returns `{ uuid }`
  GET    /api/canvas/temp/{uuid}         read draft state
  PUT    /api/canvas/temp/{uuid}         sparse autosave; body any
                                         subset of `{ canvas, layout,
                                         feature_card }`
  DELETE /api/canvas/temp/{uuid}         discard draft
  POST   /api/canvas/temp/{uuid}/save    promote to saved; body
                                         `{ name }`, returns `{ name }`
  GET    /api/canvas/{name}              read saved canvas state
  DELETE /api/canvas/{name}              delete saved canvas

The temp / saved split is the dirty / committed boundary — the
frontend's autosave debouncer flushes to ``/temp/{uuid}`` while the
user works, and the explicit Save click promotes the temp into the
display-named root folder.

The per-column auto-clone behaviour (when the user adds a column to
an inter-feature comparison and we want to clone column 0's cards
into the new column with the feature swapped) lives entirely on the
frontend: ``feature_card.yml`` already stores one independent card
map per column index, so the round-trip is just a structural copy.
The schema doesn't need to encode the cloning relationship.
"""

from __future__ import annotations

import os
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

import cea.inputlocator
from cea.interfaces.dashboard.dependencies import CEAConfig, CEAProjectRoot
from cea.interfaces.dashboard.lib.canvas_capture import capture_canvas_data
from cea.interfaces.dashboard.lib.canvas_storage import (
    CanvasMeta,
    CanvasState,
    FeatureCardFile,
    LayoutFile,
    create_temp_canvas,
    delete_canvas_folder,
    export_canvas_zip,
    import_canvas_zip,
    list_saved_canvases,
    promote_temp_to_saved,
    read_canvas,
    sanitize_canvas_name,
    write_canvas,
)
from cea.interfaces.dashboard.utils import resolve_scenario_path

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

router = APIRouter()


# ── Request bodies ──────────────────────────────────────────────


class CreateTempRequest(BaseModel):
    """Body for ``POST /temp``. ``from_name`` (sent as ``from`` over
    the wire) names the saved canvas to seed the draft from. Omit it
    for an untitled draft."""
    from_name: Optional[str] = Field(default=None, alias='from')

    model_config = {'populate_by_name': True}


class SparseWriteRequest(BaseModel):
    """Body for ``PUT /temp/{uuid}``. Any subset of the three slices
    may be present; missing slices stay untouched on disk."""
    canvas: Optional[CanvasMeta] = None
    layout: Optional[LayoutFile] = None
    feature_card: Optional[FeatureCardFile] = None


class SaveRequest(BaseModel):
    """Body for ``POST /temp/{uuid}/save``. ``name`` is sanitised
    server-side; the cleaned form is what gets persisted."""
    name: str


# ── Helpers ─────────────────────────────────────────────────────


def _locator_for(project_root, project: str, scenario: str) -> cea.inputlocator.InputLocator:
    """Build an InputLocator scoped to a `<project, scenario>` pair —
    same path resolution every report-style endpoint uses."""
    scenario_path = resolve_scenario_path(project_root, project, scenario)
    return cea.inputlocator.InputLocator(scenario_path)


def _require_temp(locator: cea.inputlocator.InputLocator, uuid: str) -> str:
    """Resolve a temp folder, 404 if missing."""
    folder = locator.get_temp_canvas_folder(uuid)
    if not _is_dir(folder):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Temp canvas {uuid!r} not found",
        )
    return folder


def _require_saved(locator: cea.inputlocator.InputLocator, name: str) -> str:
    """Resolve a saved canvas folder, 404 if missing."""
    folder = locator.get_saved_canvas_folder(name)
    if not _is_dir(folder):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved canvas {name!r} not found",
        )
    return folder


def _is_dir(path: str) -> bool:
    return os.path.isdir(path)


# ── Saved canvases ──────────────────────────────────────────────


@router.get('/')
async def get_saved_canvases(
    project_root: CEAProjectRoot,
    project: str,
    scenario: str,
) -> List[str]:
    """Return the display names of every saved canvas in the scenario."""
    locator = _locator_for(project_root, project, scenario)
    return await run_in_threadpool(list_saved_canvases, locator)


@router.get('/{name}')
async def get_saved_canvas(
    project_root: CEAProjectRoot,
    project: str,
    scenario: str,
    name: str,
) -> CanvasState:
    """Read a committed canvas's full state (canvas + layout +
    feature_card YAMLs)."""
    locator = _locator_for(project_root, project, scenario)
    folder = _require_saved(locator, name)
    return await run_in_threadpool(read_canvas, locator, folder)


@router.delete('/{name}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_canvas(
    project_root: CEAProjectRoot,
    project: str,
    scenario: str,
    name: str,
) -> None:
    """Permanently remove a saved canvas folder. No-op if missing."""
    locator = _locator_for(project_root, project, scenario)
    folder = locator.get_saved_canvas_folder(name)
    await run_in_threadpool(delete_canvas_folder, folder)


# ── Zip export / import ─────────────────────────────────────────


@router.get('/{name}/export')
async def export_canvas(
    project_root: CEAProjectRoot,
    project: str,
    scenario: str,
    name: str,
) -> StreamingResponse:
    """Stream a zip of the saved canvas folder.

    The zip's top-level directory is the canvas's display name, so
    extracting yields ``<name>/canvas.yml`` etc. The captured per-
    card data folder (``data/<cardId>/``) ships in the zip too —
    that's the whole point of the capture-on-Save pass — so a
    recipient can view the canvas without the original CEA scenario.
    """
    locator = _locator_for(project_root, project, scenario)
    _require_saved(locator, name)
    try:
        buf = await run_in_threadpool(export_canvas_zip, locator, name)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    safe_filename = name.replace('"', '')
    return StreamingResponse(
        buf,
        media_type='application/zip',
        headers={
            'Content-Disposition': f'attachment; filename="{safe_filename}.zip"',
        },
    )


@router.post('/import')
async def import_canvas(
    project_root: CEAProjectRoot,
    project: str,
    scenario: str,
    file: UploadFile = File(...),
    as_name: Optional[str] = Query(None, alias='as'),
) -> dict:
    """Unpack a previously-exported canvas zip into the scenario.

    By default the display name is read from the zip's top-level
    folder and sanitised. Pass ``?as=<new name>`` (mapped to
    ``as_name`` because ``as`` is reserved in Python) to import
    under a different name — the UI uses this to recover from a
    409 conflict by prompting the user for a fresh name and
    retrying the upload.

    Returns ``{ name: <cleaned> }`` on success.

    400 — malformed zip / missing canvas marker / illegal name.
    409 — a saved canvas with the same target name already exists.
    """
    locator = _locator_for(project_root, project, scenario)
    payload = await file.read()

    def _do() -> str:
        try:
            return import_canvas_zip(locator, payload, rename_to=as_name)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )
        except FileExistsError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            )

    return {'name': await run_in_threadpool(_do)}


# ── Temp / draft canvases ───────────────────────────────────────


@router.post('/temp')
async def create_temp(
    project_root: CEAProjectRoot,
    project: str,
    scenario: str,
    body: Optional[CreateTempRequest] = None,
) -> dict:
    """Create a fresh ``temp/<uuid>/`` folder.

    Pass ``{ "from": "<saved-name>" }`` to seed the draft from a
    saved canvas (the "first edit on a saved canvas" flow); omit it
    for an untitled draft. UUID is allocated server-side so the
    frontend can rely on it being globally unique.
    """
    import uuid as _uuid

    parent = body.from_name if body else None
    locator = _locator_for(project_root, project, scenario)

    if parent is not None:
        # Validate the parent up front so we can surface a clean 404
        # before allocating a UUID + creating disk state.
        _require_saved(locator, parent)

    new_uuid = _uuid.uuid4().hex

    def _do() -> str:
        create_temp_canvas(locator, new_uuid, parent_canvas_name=parent)
        return new_uuid

    return {'uuid': await run_in_threadpool(_do)}


@router.get('/temp/{uuid}')
async def get_temp(
    project_root: CEAProjectRoot,
    project: str,
    scenario: str,
    uuid: str,
) -> CanvasState:
    """Read a draft canvas's full state."""
    locator = _locator_for(project_root, project, scenario)
    folder = _require_temp(locator, uuid)
    return await run_in_threadpool(read_canvas, locator, folder)


@router.put('/temp/{uuid}', status_code=status.HTTP_204_NO_CONTENT)
async def update_temp(
    project_root: CEAProjectRoot,
    project: str,
    scenario: str,
    uuid: str,
    body: SparseWriteRequest,
) -> None:
    """Sparse-write any subset of the three YAMLs.

    The autosave path on the frontend posts only what changed:
      - drag/resize lands here as ``{ layout: … }``
      - a card add/edit/delete lands as ``{ feature_card: … }``
      - renaming or toggling a navigator switch lands as
        ``{ canvas: … }``
    """
    locator = _locator_for(project_root, project, scenario)
    folder = _require_temp(locator, uuid)
    await run_in_threadpool(
        write_canvas,
        locator,
        folder,
        body.canvas,
        body.layout,
        body.feature_card,
    )


@router.delete('/temp/{uuid}', status_code=status.HTTP_204_NO_CONTENT)
async def discard_temp(
    project_root: CEAProjectRoot,
    project: str,
    scenario: str,
    uuid: str,
) -> None:
    """Discard a draft. Idempotent — missing temps are 204."""
    locator = _locator_for(project_root, project, scenario)
    folder = locator.get_temp_canvas_folder(uuid)
    await run_in_threadpool(delete_canvas_folder, folder)


@router.post('/temp/{uuid}/save')
async def save_temp(
    config: CEAConfig,
    project_root: CEAProjectRoot,
    project: str,
    scenario: str,
    uuid: str,
    body: SaveRequest,
) -> dict:
    """Promote a draft to a saved canvas.

    The user-supplied name is sanitised; the cleaned form is what
    ends up on disk and is returned to the caller. Conflicts (an
    existing root folder under the same sanitised name that isn't
    this draft's parent) raise 409 so the UI can prompt the user
    to rename.

    Before the move, every plot card in the canvas is re-rendered
    and its HTML written to ``<canvas_folder>/data/<card_id>/`` so
    a future zip export carries everything a recipient needs to
    view the canvas without the original CEA scenario data.
    """
    try:
        clean_name = sanitize_canvas_name(body.name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    locator = _locator_for(project_root, project, scenario)
    temp_folder = _require_temp(locator, uuid)

    # `config` is the request-scoped CEAConfig and gets mutated by
    # `render_plot_html` (one mutation per card during capture).
    # Snapshot the bits we need to restore so the user's session
    # survives unchanged.
    original_scenario = config.scenario

    def _do() -> str:
        try:
            canvas_state = read_canvas(locator, temp_folder)
            # Best-effort: capture failures inside individual cards
            # are logged in `capture_canvas_data` and don't bubble
            # up, so a single broken plot never blocks Save.
            capture_canvas_data(config, locator, temp_folder, canvas_state)
            promote_temp_to_saved(locator, uuid, clean_name)
        except FileExistsError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            )
        finally:
            config.project = os.path.dirname(original_scenario)
        return clean_name

    return {'name': await run_in_threadpool(_do)}
