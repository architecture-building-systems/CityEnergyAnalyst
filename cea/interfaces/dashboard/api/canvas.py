"""
Canvas Builder API.

The on-disk shape, schemas, and read/write/lifecycle helpers live
in ``cea.interfaces.dashboard.lib.canvas_storage``; this router is
a thin HTTP-facing wrapper that exposes those primitives.

Endpoints (all scenario-scoped via the standard
``?project=&scenario=`` query params, mirroring ``reports.py``):

  GET    /api/canvas/                    list saved canvas names
  POST   /api/canvas/                    create a new (empty)
                                         canvas; body `{ name }`
                                         → returns `{ name }`
                                         (sanitised); 409 if the
                                         name is taken
  GET    /api/canvas/{name}              read state
  PUT    /api/canvas/{name}              sparse autosave; body any
                                         subset of `{ canvas,
                                         layout, feature_card }`
  DELETE /api/canvas/{name}              delete folder
  GET    /api/canvas/{name}/export       capture-on-share + zip
  POST   /api/canvas/import              upload a canvas zip;
                                         optional `?as=<new>`
                                         escape hatch for renaming

Every edit goes straight to the saved folder — there's no temp /
draft staging area. The previous Save / Auto Save buttons were
retired in favour of "every move autosaves to the saved folder";
plot-data capture (the expensive bit, since it re-renders every
plot card) now happens lazily, when the user clicks Share to
download a zip.
"""

from __future__ import annotations

import os
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import cea.inputlocator
from cea.interfaces.dashboard.dependencies import CEAConfig, CEAProjectRoot
from cea.interfaces.dashboard.lib.canvas_capture import capture_canvas_data
from cea.interfaces.dashboard.lib.canvas_storage import (
    CanvasMeta,
    CanvasState,
    FeatureCardFile,
    LayoutFile,
    create_saved_canvas,
    delete_canvas_folder,
    export_canvas_zip,
    import_canvas_zip,
    list_saved_canvases,
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


class CreateCanvasRequest(BaseModel):
    """Body for ``POST /``. Sanitised server-side; the cleaned name
    is what gets persisted and returned."""
    name: str


class SparseWriteRequest(BaseModel):
    """Body for ``PUT /{name}``. Any subset of the three slices may
    be present; missing slices stay untouched on disk."""
    canvas: Optional[CanvasMeta] = None
    layout: Optional[LayoutFile] = None
    feature_card: Optional[FeatureCardFile] = None


# ── Helpers ─────────────────────────────────────────────────────


def _locator_for(project_root, project: str, scenario: str) -> cea.inputlocator.InputLocator:
    scenario_path = resolve_scenario_path(project_root, project, scenario)
    return cea.inputlocator.InputLocator(scenario_path)


def _require_saved(locator: cea.inputlocator.InputLocator, name: str) -> str:
    """Resolve a saved canvas folder, 404 if missing."""
    folder = locator.get_saved_canvas_folder(name)
    if not os.path.isdir(folder):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved canvas {name!r} not found",
        )
    return folder


# ── List + create ──────────────────────────────────────────────


@router.get('/')
async def get_saved_canvases(
    project_root: CEAProjectRoot,
    project: str,
    scenario: str,
) -> List[str]:
    """Return the display names of every saved canvas in the scenario."""
    locator = _locator_for(project_root, project, scenario)
    return await run_in_threadpool(list_saved_canvases, locator)


@router.post('/')
async def create_canvas(
    project_root: CEAProjectRoot,
    project: str,
    scenario: str,
    body: CreateCanvasRequest,
) -> dict:
    """Create a fresh canvas folder.

    The name is sanitised; the cleaned form is returned. 409 if a
    saved canvas already exists under the same sanitised name; 400
    on illegal name.
    """
    locator = _locator_for(project_root, project, scenario)

    def _do() -> str:
        try:
            safe_name, _folder = create_saved_canvas(locator, body.name)
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
        return safe_name

    return {'name': await run_in_threadpool(_do)}


# ── Read + sparse update ───────────────────────────────────────


@router.get('/{name}')
async def get_saved_canvas(
    project_root: CEAProjectRoot,
    project: str,
    scenario: str,
    name: str,
) -> CanvasState:
    """Read a saved canvas's full state (canvas + layout +
    feature_card YAMLs)."""
    locator = _locator_for(project_root, project, scenario)
    folder = _require_saved(locator, name)
    return await run_in_threadpool(read_canvas, locator, folder)


@router.put('/{name}')
async def update_saved_canvas(
    project_root: CEAProjectRoot,
    project: str,
    scenario: str,
    name: str,
    body: SparseWriteRequest,
) -> dict:
    """Sparse-write any subset of the three YAMLs.

    The autosave path on the frontend posts only what changed:
      - drag/resize lands here as ``{ layout: … }``
      - a card add/edit/delete lands as ``{ feature_card: … }``
      - toggling a navigator switch lands as ``{ canvas: … }``
    """
    locator = _locator_for(project_root, project, scenario)
    folder = _require_saved(locator, name)
    await run_in_threadpool(
        write_canvas,
        locator,
        folder,
        body.canvas,
        body.layout,
        body.feature_card,
    )
    return {'ok': True}


@router.delete('/{name}')
async def delete_saved_canvas(
    project_root: CEAProjectRoot,
    project: str,
    scenario: str,
    name: str,
) -> dict:
    """Permanently remove a saved canvas folder. No-op if missing."""
    locator = _locator_for(project_root, project, scenario)
    folder = locator.get_saved_canvas_folder(name)
    await run_in_threadpool(delete_canvas_folder, folder)
    return {'ok': True}


# ── Zip export / import ─────────────────────────────────────────


@router.get('/{name}/export')
async def export_canvas(
    config: CEAConfig,
    project_root: CEAProjectRoot,
    project: str,
    scenario: str,
    name: str,
) -> StreamingResponse:
    """Capture every plot card to HTML, then stream a zip of the
    canvas folder.

    This is where the expensive plot-rendering pass runs (it was
    previously bundled into Save). Capture writes
    ``data/<cardId>/plot_<i>.html`` files alongside the YAMLs so
    a recipient unzipping the archive can view the canvas without
    the original CEA scenario.
    """
    locator = _locator_for(project_root, project, scenario)
    folder = _require_saved(locator, name)

    original_scenario = config.scenario

    def _do() -> str:
        try:
            canvas_state = read_canvas(locator, folder)
            # Best-effort: capture failures inside individual cards
            # are logged and don't bubble up, so a single broken
            # plot never blocks Share.
            capture_canvas_data(config, locator, folder, canvas_state)
        finally:
            config.project = os.path.dirname(original_scenario)
        return name

    await run_in_threadpool(_do)
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
    folder and sanitised. Pass ``?as=<new name>`` to import under
    a different name (used by the UI to recover from a 409
    conflict by prompting the user for a fresh name and retrying
    the upload).

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
