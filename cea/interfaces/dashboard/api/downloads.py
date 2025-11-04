"""
API endpoints for scenario download management.
"""
import os
import asyncio
from typing import List

import aiofiles
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from sqlmodel import select
from starlette.responses import StreamingResponse

from cea.interfaces.dashboard.dependencies import (
    CEAProjectID,
    CEAProjectRoot,
    CEAUserID
)
from cea.interfaces.dashboard.lib.database.session import SessionDep as CEASession
from cea.interfaces.dashboard.lib.database.models import Download, DownloadState, Project
from cea.interfaces.dashboard.lib.logs import logger
from cea.interfaces.dashboard.lib.socketio import emit_with_retry
from cea.interfaces.dashboard.server.downloads import (
    create_download,
    cleanup_download,
    mark_download_downloaded,
    prepare_download_background,
    DownloadStartedEvent,
    OutputFileType
)
from cea.interfaces.dashboard.utils import secure_path

router = APIRouter()

# Chunk size for streaming downloads (1MB)
DOWNLOAD_CHUNK_SIZE = 1024 * 1024


class PrepareDownloadRequest(BaseModel):
    """Request model for preparing a download."""
    project: str
    scenarios: List[str]
    input_files: bool = False
    output_files: List[OutputFileType] = []


class DownloadResponse(BaseModel):
    """Response model for download information."""
    id: str
    project_id: str
    scenarios: List[str]
    input_files: bool
    output_files: List[str]
    state: str
    file_size_mb: float | None
    progress_message: str | None
    error_message: str | None
    created_at: str
    downloaded_at: str | None

    @classmethod
    def from_download(cls, download: Download) -> "DownloadResponse":
        """Create response from Download model."""
        return cls(
            id=download.id,
            project_id=download.project_id,
            scenarios=download.scenarios,
            input_files=download.input_files,
            output_files=download.output_files,
            state=download.state.name,
            file_size_mb=download.file_size_mb,
            progress_message=download.progress_message,
            error_message=download.error_message,
            created_at=download.created_at.isoformat(),
            downloaded_at=download.downloaded_at.isoformat() if download.downloaded_at else None
        )


@router.post("/prepare", response_model=DownloadResponse)
async def prepare_download(
    request: PrepareDownloadRequest,
    project_root: CEAProjectRoot,
    user_id: CEAUserID,
    session: CEASession
):
    """
    Create and start a download preparation job.

    Args:
        request: Download request parameters
        project_id: Current project ID
        project_root: Project root directory
        user_id: Current user ID
        session: Database session

    Returns:
        Download information
    """
    # Validate inputs
    if not request.scenarios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one scenario must be selected"
        )

    if not request.input_files and not request.output_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files selected for download"
        )

    # Ensure project root
    if project_root is None or project_root == "":
        logger.error("Unable to determine project path")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project root not defined",
        )

    project_path = secure_path(os.path.join(project_root, request.project), root=project_root)

    if not os.path.exists(project_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project path does not exist"
        )

    # Get project id (verify ownership)
    result = await session.execute(
        select(Project).where(Project.uri == project_path, Project.owner == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Create download record
    download = await create_download(
        session=session,
        project_id=project.id,
        scenarios=request.scenarios,
        input_files=request.input_files,
        output_files=request.output_files,
        user_id=user_id
    )

    # Start background preparation (fire-and-forget)
    # Convert stored strings back to enum for type safety
    asyncio.create_task(
        prepare_download_background(
            download_id=download.id,
            project_path=project_path,
            scenarios=download.scenarios,
            input_files=download.input_files,
            output_files=[OutputFileType(f) for f in download.output_files]
        )
    )

    # Emit creation event
    await emit_with_retry(
        'download-created',
        DownloadResponse.from_download(download).model_dump(),
        room=f'user-{user_id}'
    )

    logger.info(f"Download {download.id} created and preparation started for user {user_id}")

    return DownloadResponse.from_download(download)


@router.get("/", response_model=List[DownloadResponse])
async def list_downloads(
    user_id: CEAUserID,
    project_id: CEAProjectID,
    session: CEASession,
    limit: int = 50
):
    """
    List all downloads for the current user and project.

    Args:
        user_id: Current user ID
        project_id: Current project ID
        session: Database session
        limit: Maximum number of downloads to return

    Returns:
        List of downloads
    """
    result = await session.execute(
        select(Download)
        .where(
            Download.created_by == user_id,
            Download.project_id == project_id
        )
        .order_by(Download.created_at.desc())
        .limit(limit)
    )
    downloads = result.scalars().all()

    return [DownloadResponse.from_download(d) for d in downloads]


@router.get("/{download_id}/status", response_model=DownloadResponse)
async def get_download_status(
    download_id: str,
    user_id: CEAUserID,
    session: CEASession
):
    """
    Get the status of a download.

    Args:
        download_id: Download ID
        user_id: Current user ID
        session: Database session

    Returns:
        Download information
    """
    result = await session.execute(
        select(Download).where(Download.id == download_id)
    )
    download = result.scalar_one_or_none()

    if not download:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download not found"
        )

    # Check authorization
    if download.created_by != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this download"
        )

    return DownloadResponse.from_download(download)


@router.get("/{download_id}")
async def download_file(
    download_id: str,
    user_id: CEAUserID,
    session: CEASession,
    background_tasks: BackgroundTasks
):
    """
    Download the prepared zip file.
    File is deleted immediately after download (single-use policy).

    Args:
        download_id: Download ID
        user_id: Current user ID
        session: Database session
        background_tasks: FastAPI background tasks for cleanup

    Returns:
        Streaming response with zip file
    """
    # Lock row for update to prevent concurrent downloads
    result = await session.execute(
        select(Download)
        .where(Download.id == download_id)
        .with_for_update()
    )
    download = result.scalar_one_or_none()

    if not download:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download not found"
        )

    # Check authorization
    if download.created_by != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this download"
        )

    # Check download state
    if download.state == DownloadState.DOWNLOADING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Download already in progress. Please wait for the current download to complete."
        )

    if download.state == DownloadState.DOWNLOADED:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This download has already been completed and the file has been deleted. "
                   "Please create a new download request."
        )

    if download.state == DownloadState.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Download has not started yet"
        )

    if download.state == DownloadState.PREPARING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Download is still being prepared. Please check status and try again when ready."
        )

    if download.state == DownloadState.ERROR:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download preparation failed: {download.error_message}"
        )

    if download.state != DownloadState.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Download is not ready (state: {download.state.name})"
        )
    
    # Download should have file size when READY
    if download.file_size is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to determine download file size"
        )

    # Check file exists
    if not download.file_path or not os.path.exists(download.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download file not found"
        )

    # Capture values before commit (avoid lazy loading after commit)
    file_path = download.file_path
    file_size = download.file_size
    scenarios = download.scenarios

    # Mark as DOWNLOADING to prevent concurrent access
    download.state = DownloadState.DOWNLOADING
    await session.commit()

    # Emit download started event
    await emit_with_retry(
        'download-started',
        DownloadStartedEvent(
            download_id=download_id,
            state=DownloadState.DOWNLOADING.name
        ).model_dump(),
        room=f'user-{user_id}'
    )

    # Determine filename
    if len(scenarios) == 1:
        filename = f"{scenarios[0]}.zip"
    else:
        filename = f"scenarios_{len(scenarios)}.zip"

    # Simple file streamer (no cleanup inside)
    async def file_streamer(fp: str):
        """Stream file in chunks."""
        async with aiofiles.open(fp, 'rb') as f:
            while True:
                chunk = await f.read(DOWNLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk

    # Schedule cleanup to run after streaming completes
    background_tasks.add_task(
        cleanup_after_download,
        download_id
    )

    logger.info(f"Streaming download {download_id} to user {user_id}")

    return StreamingResponse(
        file_streamer(file_path),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(file_size),
            "Access-Control-Expose-Headers": "Content-Disposition, Content-Length"
        }
    )


async def cleanup_after_download(download_id: str):
    """
    Cleanup function that runs after file is fully streamed.
    Uses BackgroundTasks to run after response completes.

    Args:
        download_id: Download ID to cleanup
    """
    from cea.interfaces.dashboard.lib.database.session import get_session_context

    try:
        async with get_session_context() as session:
            await mark_download_downloaded(session, download_id)
        logger.info(f"Download {download_id} completed and cleaned up via BackgroundTask")
    except Exception as e:
        logger.error(f"Error in cleanup_after_download for {download_id}: {e}")


@router.delete("/{download_id}")
async def delete_download(
    download_id: str,
    user_id: CEAUserID,
    session: CEASession
):
    """
    Manually delete a download and clean up its files.

    Args:
        download_id: Download ID
        user_id: Current user ID
        session: Database session

    Returns:
        Success message
    """
    result = await session.execute(
        select(Download).where(Download.id == download_id)
    )
    download = result.scalar_one_or_none()

    if not download:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download not found"
        )

    # Check authorization
    if download.created_by != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this download"
        )

    # Prevent deletion while download is in progress
    if download.state == DownloadState.DOWNLOADING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete download while it is in progress. Please wait for download to complete or fail."
        )

    # Cleanup files
    await cleanup_download(session, download)

    # Delete from database
    await session.delete(download)
    await session.commit()

    logger.info(f"Download {download_id} deleted by user {user_id}")

    return {"message": "Download deleted successfully"}
