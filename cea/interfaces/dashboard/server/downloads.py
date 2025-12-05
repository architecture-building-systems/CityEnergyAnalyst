"""
Download management for scenario downloads.
Handles download lifecycle, cleanup, and user limits.
"""
import os
import asyncio
import zipfile
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.concurrency import run_in_threadpool

import cea.config
from cea.interfaces.dashboard.lib.database.models import Download, DownloadState
from cea.interfaces.dashboard.lib.database.session import get_session_context
from cea.interfaces.dashboard.lib.logs import logger
from cea.interfaces.dashboard.lib.socketio import emit_with_retry

from cea.interfaces.dashboard.api.contents import VALID_EXTENSIONS, OutputFileType

# SocketIO Event Models
class DownloadProgressEvent(BaseModel):
    """Event emitted during download preparation."""
    download_id: str
    state: str
    progress_message: str
    progress_percent: int  # 0-100 for progress bar


class DownloadReadyEvent(BaseModel):
    """Event emitted when download is ready."""
    download_id: str
    state: str
    file_size_mb: float
    progress_message: str


class DownloadStartedEvent(BaseModel):
    """Event emitted when user starts downloading."""
    download_id: str
    state: str


class DownloadErrorEvent(BaseModel):
    """Event emitted when download preparation fails."""
    download_id: str
    state: str
    error_message: str
    progress_message: str


class DownloadDownloadedEvent(BaseModel):
    """Event emitted when download completes."""
    download_id: str
    state: str
    downloaded_at: Optional[str] = None


# Constants
MAX_DOWNLOADS_PER_USER = 5
DOWNLOAD_RETENTION_HOURS = 24
# Use system temp directory for cross-platform compatibility
DOWNLOAD_DIR_BASE = Path(tempfile.gettempdir()) / "cea_downloads"


async def create_download(
    session: AsyncSession,
    project_id: str,
    scenarios: list[str],
    input_files: bool,
    output_files: list[OutputFileType],
    user_id: str
) -> Download:
    """
    Create a new download request.

    Args:
        session: Database session
        project_id: Project ID
        scenarios: List of scenario names
        input_files: Include input files?
        output_files: List of output types (OutputFileType enum values)
        user_id: User creating the download

    Returns:
        Download object
    """
    # Enforce user download limit
    await enforce_user_download_limit(session, user_id)

    # Create download record (convert enum to strings for database storage)
    download = Download(
        project_id=project_id,
        scenarios=scenarios,
        input_files=input_files,
        output_files=[str(f) for f in output_files],
        created_by=user_id,
        state=DownloadState.PENDING,
        progress_message="Download request created"
    )

    session.add(download)
    await session.commit()
    await session.refresh(download)

    logger.info(f"Created download {download.id} for user {user_id}")
    return download


async def enforce_user_download_limit(session: AsyncSession, user_id: str, limit: int = MAX_DOWNLOADS_PER_USER):
    """
    Enforce per-user download limit. Delete oldest downloads if limit exceeded.
    Only counts downloads that are not yet DOWNLOADED (i.e., still active).

    Args:
        session: Database session
        user_id: User ID to check
        limit: Maximum number of active downloads per user
    """
    # Query user's active downloads (not yet downloaded)
    result = await session.execute(
        select(Download)
        .where(
            Download.created_by == user_id,
            Download.state != DownloadState.DOWNLOADED
        )
        .order_by(Download.created_at.desc())
    )
    downloads = result.scalars().all()

    # If at or over limit, delete oldest
    if len(downloads) >= limit:
        to_delete = downloads[limit - 1:]  # Keep limit-1, delete the rest to make room for new one
        logger.info(f"User {user_id} has {len(downloads)} active downloads, removing {len(to_delete)} oldest")

        for download in to_delete:
            await cleanup_download(session, download)
            await session.delete(download)

        await session.commit()


async def cleanup_download(session: AsyncSession, download: Download):
    """
    Clean up download files.

    Args:
        session: Database session
        download: Download object to clean up
    """
    # Remove download directory (run blocking I/O in threadpool)
    download_dir = DOWNLOAD_DIR_BASE / download.id
    if download_dir.exists():
        try:
            await asyncio.to_thread(shutil.rmtree, download_dir)
            logger.info(f"Removed download directory: {download_dir}")
        except Exception as e:
            logger.error(f"Error removing download directory {download_dir}: {e}")

    # Also try to remove individual file if path is set (run blocking I/O in threadpool)
    if download.file_path and os.path.exists(download.file_path):
        try:
            await asyncio.to_thread(os.remove, download.file_path)
            logger.info(f"Removed download file: {download.file_path}")
        except Exception as e:
            logger.error(f"Error removing download file {download.file_path}: {e}")


async def cleanup_old_downloads(session: AsyncSession):
    """
    Delete downloads older than DOWNLOAD_RETENTION_HOURS.
    Runs on server startup and periodically.
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=DOWNLOAD_RETENTION_HOURS)

    result = await session.execute(
        select(Download).where(Download.created_at < cutoff_time)
    )
    old_downloads = result.scalars().all()

    if old_downloads:
        logger.info(f"Cleaning up {len(old_downloads)} downloads older than {DOWNLOAD_RETENTION_HOURS}h")

        for download in old_downloads:
            await cleanup_download(session, download)
            await session.delete(download)

        await session.commit()
        logger.info(f"Cleaned up {len(old_downloads)} old downloads")
    else:
        logger.debug("No old downloads to clean up")


async def cleanup_stale_downloads(session: AsyncSession):
    """
    Reset downloads stuck in DOWNLOADING state (client disconnects).
    Runs on server startup.
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)

    result = await session.execute(
        select(Download).where(
            Download.state == DownloadState.DOWNLOADING,
            Download.created_at < cutoff_time
        )
    )
    stale = result.scalars().all()

    if stale:
        logger.info(f"Resetting {len(stale)} stale downloads (stuck in DOWNLOADING state)")

        for download in stale:
            download.state = DownloadState.READY
            download.progress_message = "Ready (reset from stale download)"
            logger.warning(f"Reset stale download {download.id} to READY")

        await session.commit()
        logger.info(f"Reset {len(stale)} stale downloads")
    else:
        logger.debug("No stale downloads to reset")


async def mark_download_ready(
    session: AsyncSession,
    download_id: str,
    file_path: str,
    file_size: int
):
    """
    Mark download as ready after preparation completes.

    Args:
        session: Database session
        download_id: Download ID
        file_path: Path to prepared zip file
        file_size: Size of zip file in bytes
    """
    result = await session.execute(
        select(Download).where(Download.id == download_id)
    )
    download = result.scalar_one_or_none()

    if not download:
        logger.warning(f"Download {download_id} not found when marking ready")
        return

    download.state = DownloadState.READY
    download.file_path = file_path
    download.file_size = file_size
    progress_msg = f"Download ready: {round(file_size / (1024 * 1024), 2)} MB"
    download.progress_message = progress_msg

    # Capture values before commit (avoid lazy loading issues)
    user_id = download.created_by

    await session.commit()
    logger.info(f"Download {download_id} marked as ready: {file_path} ({file_size} bytes)")

    # Emit SocketIO event
    await emit_with_retry(
        'download-ready',
        DownloadReadyEvent(
            download_id=download_id,
            state=DownloadState.READY.name,
            file_size_mb=round(file_size / (1024 * 1024), 2),
            progress_message=progress_msg
        ).model_dump(),
        room=f'user-{user_id}'
    )

    return download


async def mark_download_error(
    session: AsyncSession,
    download_id: str,
    error_message: str
):
    """
    Mark download as error after preparation fails.

    Args:
        session: Database session
        download_id: Download ID
        error_message: Error details
    """
    result = await session.execute(
        select(Download).where(Download.id == download_id)
    )
    download = result.scalar_one_or_none()

    if not download:
        logger.warning(f"Download {download_id} not found when marking error")
        return

    download.state = DownloadState.ERROR
    download.error_message = error_message
    download.progress_message = "Download preparation failed"

    # Capture values before commit (avoid lazy loading issues)
    user_id = download.created_by

    await session.commit()
    logger.error(f"Download {download_id} failed: {error_message}")

    # Emit SocketIO event
    await emit_with_retry(
        'download-error',
        DownloadErrorEvent(
            download_id=download_id,
            state=DownloadState.ERROR.name,
            error_message=error_message,
            progress_message='Download preparation failed'
        ).model_dump(),
        room=f'user-{user_id}'
    )

    return download


async def mark_download_downloaded(
    session: AsyncSession,
    download_id: str
):
    """
    Mark download as downloaded and clean up the file.
    Called after user successfully downloads the file.

    Args:
        session: Database session
        download_id: Download ID
    """
    result = await session.execute(
        select(Download).where(Download.id == download_id)
    )
    download = result.scalar_one_or_none()

    if not download:
        logger.warning(f"Download {download_id} not found when marking downloaded")
        return

    download.state = DownloadState.DOWNLOADED
    downloaded_at = datetime.now(timezone.utc)
    download.downloaded_at = downloaded_at
    download.progress_message = "Downloaded"

    # Clean up file immediately (single-use policy)
    await cleanup_download(session, download)
    download.file_path = None  # File no longer exists

    # Capture values before commit (avoid lazy loading issues)
    user_id = download.created_by

    await session.commit()
    logger.info(f"Download {download_id} marked as downloaded and cleaned up")

    # Emit SocketIO event
    await emit_with_retry(
        'download-downloaded',
        DownloadDownloadedEvent(
            download_id=download_id,
            state=DownloadState.DOWNLOADED.name,
            downloaded_at=downloaded_at.isoformat() if downloaded_at else None
        ).model_dump(),
        room=f'user-{user_id}'
    )

    return download


async def update_download_progress(
    session: AsyncSession,
    download_id: str,
    progress_message: str,
    state: Optional[DownloadState] = None,
    progress_percent: int = 0,
    persist_message: bool = True
):
    """
    Update download progress message (called from background task).

    Args:
        session: Database session
        download_id: Download ID
        progress_message: Progress message to display
        state: Optional state update
        progress_percent: Progress percentage (0-100) for progress bar
        persist_message: If True, write message to DB; if False, only emit SocketIO
    """
    # Load download object (session cache makes this efficient for repeated calls)
    result = await session.execute(
        select(Download).where(Download.id == download_id)
    )
    download = result.scalar_one_or_none()

    if not download:
        return  # Download may have been deleted, skip update

    # Update database for persistent milestones
    if persist_message:
        download.progress_message = progress_message
    if state is not None:
        download.state = state

    # Capture values before commit (avoid lazy loading after commit)
    current_state = download.state
    user_id = download.created_by

    # Only commit if we actually changed something in the database
    if persist_message or state is not None:
        await session.commit()

    logger.debug(f"Download {download_id} progress: {progress_message} ({progress_percent}%)")

    # Always emit SocketIO event for real-time updates
    await emit_with_retry(
        'download-progress',
        DownloadProgressEvent(
            download_id=download_id,
            state=current_state.name,
            progress_message=progress_message,
            progress_percent=progress_percent
        ).model_dump(),
        room=f'user-{user_id}'
    )


def get_download_directory(download_id: str) -> Path:
    """Get the directory path for a download."""
    return DOWNLOAD_DIR_BASE / download_id


def get_download_zip_path(download_id: str) -> Path:
    """Get the zip file path for a download."""
    return get_download_directory(download_id) / "scenario_download.zip"


# ============================================================================
# Download Preparation Functions (run in threadpool)
# ============================================================================

def collect_files_for_download(
    project_path: str,
    scenarios: list[str],
    input_files: bool,
    output_files: list[OutputFileType]
) -> list[tuple[Path, str]]:
    """
    Collect all files to be included in the download.

    Args:
        project_path: Path to the project
        scenarios: List of scenario names
        input_files: Include input files?
        output_files: List of output types (OutputFileType enum values)

    Returns:
        List of (file_path, archive_name) tuples
    """
    files_to_zip = []
    base_path = Path(project_path)

    # Map output types to their folder paths relative to scenario root
    # Format: (type_key, folder_path_relative_to_scenario)
    output_folders = []
    if OutputFileType.DETAILED in output_files:
        output_folders.append(('outputs', Path('outputs')))
    if OutputFileType.SUMMARY in output_files:
        output_folders.append(('export/results', Path('export') / 'results'))
    if OutputFileType.EXPORT in output_files:
        # Export can include multiple subfolders
        output_folders.append(('export/rhino', Path('export') / 'rhino'))

    def collect_from_folder(scenario_name: str, scenario_path: Path, folder_key: str, folder_path: Path):
        """Helper to collect files from a folder."""
        full_path = scenario_path / folder_path
        if not full_path.exists():
            return

        for root, _, files in os.walk(full_path):
            root_path = Path(root)
            for file in files:
                if Path(file).suffix in VALID_EXTENSIONS:
                    item_path = root_path / file
                    relative_path = str(Path(scenario_name) / folder_path / item_path.relative_to(full_path))
                    files_to_zip.append((item_path, relative_path))

    for scenario in scenarios:
        scenario_name = Path(scenario).name
        scenario_path = base_path / scenario_name

        if not scenario_path.exists():
            logger.warning(f"Scenario {scenario_name} does not exist, skipping")
            continue

        # Collect input files
        if input_files:
            collect_from_folder(scenario_name, scenario_path, 'inputs', Path('inputs'))

        # Collect output files based on requested types
        for folder_key, folder_path in output_folders:
            collect_from_folder(scenario_name, scenario_path, folder_key, folder_path)

    return files_to_zip


def generate_summary_for_scenario(project_path: str, scenario_name: str):
    """
    Generate summary files for a scenario.

    Args:
        project_path: Path to the project
        scenario_name: Name of the scenario
    """
    try:
        logger.info(f"Generating summary for scenario: {scenario_name}")

        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.project = project_path
        config.scenario_name = scenario_name
        config.result_summary.aggregate_by_building = True

        from cea.import_export.result_summary import main as result_summary_main
        result_summary_main(config)

        logger.info(f"Summary generated successfully for {scenario_name}")
    except Exception as e:
        logger.error(f"Error generating summary for {scenario_name}: {e}")
        raise


def prepare_download_sync(
    download_id: str,
    project_path: str,
    scenarios: list[str],
    input_files: bool,
    output_files: list[OutputFileType],
    loop: asyncio.AbstractEventLoop,
    progress_queue: asyncio.Queue
):
    """
    Synchronous function to prepare download (runs in threadpool).

    Args:
        download_id: Download ID
        project_path: Path to the project
        scenarios: List of scenario names
        input_files: Include input files?
        output_files: List of output types (OutputFileType enum values)
        loop: Event loop for thread-safe queue operations
        progress_queue: Async queue for sending progress updates to async monitor
    """
    def put_progress(msg):
        """Helper to safely put message from thread to async queue."""
        loop.call_soon_threadsafe(progress_queue.put_nowait, msg)

    try:
        # Progress breakdown: Summary (0-40%), Collect (40-45%), ZIP (45-100%)

        # Update progress: Starting
        put_progress({
            'type': 'progress',
            'message': f"Preparing download for {len(scenarios)} scenario(s)...",
            'state': DownloadState.PREPARING,
            'percent': 0
        })

        # Generate summaries if requested (0-40% of total)
        if OutputFileType.SUMMARY in output_files:
            for i, scenario in enumerate(scenarios):
                scenario_name = Path(scenario).name
                # Calculate progress: 0-40% based on scenario completion
                percent = int(40 * (i / len(scenarios)))

                put_progress({
                    'type': 'progress',
                    'message': f"Generating summary for scenario {i+1}/{len(scenarios)}: {scenario_name}...",
                    'percent': percent,
                    'persist': False  # Don't write per-scenario counts to database
                })

                generate_summary_for_scenario(project_path, scenario_name)

        # Collect files (40-45%)
        put_progress({
            'type': 'progress',
            'message': "Collecting files...",
            'percent': 40
        })

        logger.info(f"Collecting files for download {download_id}")
        files_to_zip = collect_files_for_download(
            project_path,
            scenarios,
            input_files,
            output_files
        )

        if not files_to_zip:
            raise Exception("No valid files found for download")

        logger.info(f"Found {len(files_to_zip)} files to zip for download {download_id}")

        # Create ZIP file (45-100%)
        put_progress({
            'type': 'progress',
            'message': f"Creating ZIP archive ({len(files_to_zip)} files)...",
            'percent': 45
        })

        zip_path = get_download_zip_path(download_id)
        zip_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, (item_path, archive_name) in enumerate(files_to_zip):
                zip_file.write(item_path, arcname=archive_name)

                # Update progress every 50 files (45-100%)
                if (i + 1) % 50 == 0 or (i + 1) == len(files_to_zip):
                    # Calculate progress: 45% + (55% * file_completion)
                    file_progress = (i + 1) / len(files_to_zip)
                    percent = int(45 + (55 * file_progress))

                    put_progress({
                        'type': 'progress',
                        'message': f"Adding files to archive... ({i+1}/{len(files_to_zip)})",
                        'percent': percent,
                        'persist': False  # Don't write file counts to database
                    })

        # Get file size
        file_size = os.path.getsize(zip_path)

        logger.info(f"Download {download_id} prepared successfully: {zip_path} ({file_size} bytes)")

        # Mark download as ready
        put_progress({
            'type': 'ready',
            'file_path': str(zip_path),
            'file_size': file_size
        })

    except Exception as e:
        logger.error(f"Error preparing download {download_id}: {e}")

        # Mark download as error
        put_progress({
            'type': 'error',
            'error_message': str(e)
        })

        raise


async def prepare_download_background(
    download_id: str,
    project_path: str,
    scenarios: list[str],
    input_files: bool,
    output_files: list[OutputFileType]
):
    """
    Async wrapper that runs sync preparation function in threadpool.
    Monitors progress queue and updates database.

    Args:
        download_id: Download ID
        project_path: Path to project
        scenarios: List of scenario names
        input_files: Include input files?
        output_files: List of output types (OutputFileType enum values)
    """
    # Create async queue for progress updates
    progress_queue = asyncio.Queue()

    # Get current event loop
    loop = asyncio.get_running_loop()

    # Start monitoring the queue
    monitor_task = asyncio.create_task(
        _monitor_download_progress(download_id, progress_queue)
    )

    try:
        # Run sync preparation in threadpool
        await run_in_threadpool(
            prepare_download_sync,
            download_id,
            project_path,
            scenarios,
            input_files,
            output_files,
            loop,
            progress_queue
        )
    except Exception as e:
        logger.error(f"Download preparation failed for {download_id}: {e}")
        # Error already sent to queue in prepare_download_sync
    finally:
        # Signal monitor to stop
        await progress_queue.put({'type': 'done'})
        # Wait for monitor to finish processing
        await monitor_task


async def _monitor_download_progress(download_id: str, progress_queue: asyncio.Queue):
    """
    Monitor progress queue and update database.
    Runs concurrently with download preparation.

    Args:
        download_id: Download ID
        progress_queue: Async queue containing progress updates from sync function
    """
    while True:
        try:
            # Block until message arrives (efficient, no polling)
            msg = await progress_queue.get()
            msg_type = msg.get('type')

            if msg_type == 'done':
                # Cleanup signal - exit monitor
                return

            # Create new session for each database operation
            async with get_session_context() as session:
                if msg_type == 'progress':
                    await update_download_progress(
                        session,
                        download_id,
                        msg['message'],
                        msg.get('state'),
                        msg.get('percent', 0),
                        msg.get('persist', True)  # Default to persist for milestones
                    )

                elif msg_type == 'ready':
                    await mark_download_ready(
                        session,
                        download_id,
                        msg['file_path'],
                        msg['file_size']
                    )

                elif msg_type == 'error':
                    await mark_download_error(
                        session,
                        download_id,
                        msg['error_message']
                    )

        except Exception as e:
            logger.error(f"Error monitoring download progress for {download_id}: {e}")
            # Continue monitoring despite errors


