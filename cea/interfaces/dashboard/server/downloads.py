"""
Download management for scenario downloads.
Handles download lifecycle, cleanup, and user limits.
"""
import os
import asyncio
import zipfile
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.concurrency import run_in_threadpool

import cea.config
from cea.interfaces.dashboard.lib.database.models import Download, DownloadState
from cea.interfaces.dashboard.lib.database.session import get_session_context
from cea.interfaces.dashboard.lib.logs import logger
from cea.interfaces.dashboard.lib.socketio import emit_with_retry

# Import file collection utilities from contents API
from cea.interfaces.dashboard.api.contents import VALID_EXTENSIONS

# Constants
MAX_DOWNLOADS_PER_USER = 5
DOWNLOAD_RETENTION_HOURS = 24
DOWNLOAD_DIR_BASE = Path("/tmp/cea_downloads")


async def create_download(
    session: AsyncSession,
    project_id: str,
    scenarios: list[str],
    input_files: bool,
    output_files: list[str],
    user_id: str
) -> Download:
    """
    Create a new download request.

    Args:
        session: Database session
        project_id: Project ID
        scenarios: List of scenario names
        input_files: Include input files?
        output_files: List of output types (SUMMARY, DETAILED, EXPORT)
        user_id: User creating the download

    Returns:
        Download object
    """
    # Enforce user download limit
    await enforce_user_download_limit(session, user_id)

    # Create download record
    download = Download(
        project_id=project_id,
        scenarios=scenarios,
        input_files=input_files,
        output_files=output_files,
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
    # Remove download directory
    download_dir = DOWNLOAD_DIR_BASE / download.id
    if download_dir.exists():
        try:
            shutil.rmtree(download_dir)
            logger.info(f"Removed download directory: {download_dir}")
        except Exception as e:
            logger.error(f"Error removing download directory {download_dir}: {e}")

    # Also try to remove individual file if path is set
    if download.file_path and os.path.exists(download.file_path):
        try:
            os.remove(download.file_path)
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
    download.progress_message = f"Download ready: {round(file_size / (1024 * 1024), 2)} MB"

    await session.commit()
    await session.refresh(download)
    logger.info(f"Download {download_id} marked as ready: {file_path} ({file_size} bytes)")

    # Emit SocketIO event
    await emit_with_retry(
        'download-ready',
        {
            'download_id': download_id,
            'state': DownloadState.READY.name,
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            'progress_message': download.progress_message
        },
        room=f'user-{download.created_by}'
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

    await session.commit()
    await session.refresh(download)
    logger.error(f"Download {download_id} failed: {error_message}")

    # Emit SocketIO event
    await emit_with_retry(
        'download-error',
        {
            'download_id': download_id,
            'state': DownloadState.ERROR.name,
            'error_message': error_message,
            'progress_message': 'Download preparation failed'
        },
        room=f'user-{download.created_by}'
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
    download.downloaded_at = datetime.now(timezone.utc)
    download.progress_message = "Downloaded"

    # Clean up file immediately (single-use policy)
    await cleanup_download(session, download)
    download.file_path = None  # File no longer exists

    await session.commit()
    await session.refresh(download)
    logger.info(f"Download {download_id} marked as downloaded and cleaned up")

    # Emit SocketIO event
    await emit_with_retry(
        'download-downloaded',
        {
            'download_id': download_id,
            'state': DownloadState.DOWNLOADED.name,
            'downloaded_at': download.downloaded_at.isoformat() if download.downloaded_at else None
        },
        room=f'user-{download.created_by}'
    )

    return download


async def update_download_progress(
    session: AsyncSession,
    download_id: str,
    progress_message: str,
    state: Optional[DownloadState] = None
):
    """
    Update download progress message (called from background task).

    Args:
        session: Database session
        download_id: Download ID
        progress_message: Progress message to display
        state: Optional state update
    """
    result = await session.execute(
        select(Download).where(Download.id == download_id)
    )
    download = result.scalar_one_or_none()

    if not download:
        return  # Download may have been deleted, skip update

    download.progress_message = progress_message
    if state is not None:
        download.state = state

    await session.commit()
    logger.debug(f"Download {download_id} progress: {progress_message}")

    # Emit SocketIO event for real-time updates
    await emit_with_retry(
        'download-progress',
        {
            'download_id': download_id,
            'state': download.state.name,
            'progress_message': progress_message
        },
        room=f'user-{download.created_by}'
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
    project_root: str,
    scenarios: list[str],
    input_files: bool,
    output_files: list[str]
) -> list[tuple[Path, str]]:
    """
    Collect all files to be included in the download.

    Args:
        project_root: Root directory of the project
        scenarios: List of scenario names
        input_files: Include input files?
        output_files: List of output types (SUMMARY, DETAILED, EXPORT)

    Returns:
        List of (file_path, archive_name) tuples
    """
    files_to_zip = []
    base_path = Path(project_root)

    for scenario in scenarios:
        scenario_name = Path(scenario).name
        scenario_path = base_path / scenario_name

        if not scenario_path.exists():
            logger.warning(f"Scenario {scenario_name} does not exist, skipping")
            continue

        # Collect input files
        if input_files:
            input_paths = scenario_path / "inputs"
            if input_paths.exists():
                for root, _, files in os.walk(input_paths):
                    root_path = Path(root)
                    for file in files:
                        if Path(file).suffix in VALID_EXTENSIONS:
                            item_path = root_path / file
                            relative_path = str(Path(scenario_name) / "inputs" / item_path.relative_to(input_paths))
                            files_to_zip.append((item_path, relative_path))

        # Collect detailed output files
        if "DETAILED" in output_files or "detailed" in output_files:
            output_paths = scenario_path / "outputs"
            if output_paths.exists():
                for root, _, files in os.walk(output_paths):
                    root_path = Path(root)
                    for file in files:
                        if Path(file).suffix in VALID_EXTENSIONS:
                            item_path = root_path / file
                            relative_path = str(Path(scenario_name) / "outputs" / item_path.relative_to(output_paths))
                            files_to_zip.append((item_path, relative_path))

        # Collect summary files
        if "SUMMARY" in output_files or "summary" in output_files:
            results_paths = scenario_path / "export" / "results"
            if results_paths.exists():
                for root, _, files in os.walk(results_paths):
                    root_path = Path(root)
                    for file in files:
                        if Path(file).suffix in VALID_EXTENSIONS:
                            item_path = root_path / file
                            relative_path = str(Path(scenario_name) / "export" / "results" / item_path.relative_to(results_paths))
                            files_to_zip.append((item_path, relative_path))

        # Collect export files (rhino, etc.)
        if "EXPORT" in output_files or "export" in output_files:
            export_folders = ["rhino"]
            for export_folder in export_folders:
                export_paths = scenario_path / "export" / export_folder
                if export_paths.exists():
                    for root, _, files in os.walk(export_paths):
                        root_path = Path(root)
                        for file in files:
                            if Path(file).suffix in VALID_EXTENSIONS:
                                item_path = root_path / file
                                relative_path = str(Path(scenario_name) / "export" / export_folder / item_path.relative_to(export_paths))
                                files_to_zip.append((item_path, relative_path))

    return files_to_zip


def generate_summary_for_scenario(project_root: str, scenario_name: str):
    """
    Generate summary files for a scenario.

    Args:
        project_root: Root directory of the project
        scenario_name: Name of the scenario
    """
    try:
        logger.info(f"Generating summary for scenario: {scenario_name}")

        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.project = project_root
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
    project_root: str,
    scenarios: list[str],
    input_files: bool,
    output_files: list[str]
):
    """
    Synchronous function to prepare download (runs in threadpool).

    Args:
        download_id: Download ID
        project_root: Root directory of the project
        scenarios: List of scenario names
        input_files: Include input files?
        output_files: List of output types
    """
    try:
        # Update progress: Starting
        asyncio.run(_update_progress_helper(
            download_id,
            f"Preparing download for {len(scenarios)} scenario(s)...",
            DownloadState.PREPARING
        ))

        # Generate summaries if requested
        if "SUMMARY" in output_files or "summary" in output_files:
            for i, scenario in enumerate(scenarios):
                scenario_name = Path(scenario).name

                asyncio.run(_update_progress_helper(
                    download_id,
                    f"Generating summary for scenario {i+1}/{len(scenarios)}: {scenario_name}..."
                ))

                generate_summary_for_scenario(project_root, scenario_name)

        # Collect files
        asyncio.run(_update_progress_helper(
            download_id,
            "Collecting files..."
        ))

        logger.info(f"Collecting files for download {download_id}")
        files_to_zip = collect_files_for_download(
            project_root,
            scenarios,
            input_files,
            output_files
        )

        if not files_to_zip:
            raise Exception("No valid files found for download")

        logger.info(f"Found {len(files_to_zip)} files to zip for download {download_id}")

        # Create ZIP file
        asyncio.run(_update_progress_helper(
            download_id,
            f"Creating ZIP archive ({len(files_to_zip)} files)..."
        ))

        zip_path = get_download_zip_path(download_id)
        zip_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zip_file:
            for i, (item_path, archive_name) in enumerate(files_to_zip):
                zip_file.write(item_path, arcname=archive_name)

                # Update progress every 50 files
                if (i + 1) % 50 == 0:
                    asyncio.run(_update_progress_helper(
                        download_id,
                        f"Adding files to archive... ({i+1}/{len(files_to_zip)})"
                    ))

        # Get file size
        file_size = os.path.getsize(zip_path)

        logger.info(f"Download {download_id} prepared successfully: {zip_path} ({file_size} bytes)")

        # Mark download as ready
        asyncio.run(_mark_download_ready_helper(download_id, str(zip_path), file_size))

    except Exception as e:
        logger.error(f"Error preparing download {download_id}: {e}")

        # Mark download as error
        asyncio.run(_mark_download_error_helper(download_id, str(e)))

        raise


async def prepare_download_background(
    download_id: str,
    project_root: str,
    scenarios: list[str],
    input_files: bool,
    output_files: list[str]
):
    """
    Async wrapper that runs sync preparation function in threadpool.

    Args:
        download_id: Download ID
        project_root: Root directory of the project
        scenarios: List of scenario names
        input_files: Include input files?
        output_files: List of output types
    """
    try:
        await run_in_threadpool(
            prepare_download_sync,
            download_id,
            project_root,
            scenarios,
            input_files,
            output_files
        )
    except Exception as e:
        logger.error(f"Download preparation failed for {download_id}: {e}")
        # Error already marked in prepare_download_sync


# ============================================================================
# Helper Functions (for use from sync context in threadpool)
# ============================================================================

async def _update_progress_helper(download_id: str, message: str, state: Optional[DownloadState] = None):
    """Helper to update progress from sync context."""
    async with get_session_context() as session:
        await update_download_progress(session, download_id, message, state)


async def _mark_download_ready_helper(download_id: str, file_path: str, file_size: int):
    """Helper to mark download ready from sync context."""
    async with get_session_context() as session:
        await mark_download_ready(session, download_id, file_path, file_size)


async def _mark_download_error_helper(download_id: str, error_message: str):
    """Helper to mark download error from sync context."""
    async with get_session_context() as session:
        await mark_download_error(session, download_id, error_message)
