# CEA Dashboard Job System

## Architecture

**Job Flow**: Client → Server (`jobs.py`) → Worker Process (`cea/worker.py`) → Server
- **Server**: Manages job lifecycle, database (SQLModel), SocketIO events
- **Worker**: Separate subprocess executing CEA scripts via `subprocess.Popen`
- **Streams**: Captures stdout/stderr via HTTP (`streams.py`)
- **Communication**: Worker POSTs to server endpoints, server emits SocketIO to client

## Job States (`models.py:JobState`)

`PENDING(0)` → `STARTED(1)` → `SUCCESS(2)`/`ERROR(3)`/`CANCELED(4)`/`KILLED(5)`

**Soft Deletion**: Jobs are soft-deleted using `JobInfo.deleted_at` and `JobInfo.deleted_by` fields rather than a state change. This preserves the original completion state (SUCCESS/ERROR/CANCELED/KILLED) for analytics and audit purposes.

## Job Creation

**POST /jobs/new** (`jobs.py:create_new_job`):
- Input: `script` (e.g., "demand"), `parameters` (JSON or form data)
- Creates `JobInfo` with UUID, state=`PENDING`
- **File uploads**: Saved to `/tmp/cea_job_{job_id}_*`, path replaces `UploadFile` in parameters
- Emits `'cea-job-created'` via SocketIO

**GET /jobs/list** (`jobs.py:get_jobs`):
- Query params: `limit`, `state`, `exclude_deleted` (default: true)
- Filters by `deleted_at == None` when `exclude_deleted=true`
- This preserves ability to query by completion state for deleted jobs

**POST /jobs/start/{job_id}** (`jobs.py:start_job`):
- Requires authorization: only job creator can start
- Row-level locking (TOCTOU protection)
- Validates job state (must be PENDING and not deleted)
- Validates UUID and server URL
- Spawns: `python -m cea.worker --suppress-warnings {job_id} {server_url}`
- Tracks PID in `worker_processes` cache (TTL-based)

## Worker Execution (`worker.py`)

**Lifecycle** (`worker.py:worker`):
1. Registers signal handlers (`SIGTERM`, `SIGINT`) for graceful shutdown
2. `GET /jobs/{jobid}` → Fetch job details
3. `configure_streams()` → Replace `sys.stdout/stderr` with `JobServerStream`
4. `POST /jobs/started/{jobid}` → Notify server
5. `run_job()` → Execute `cea.api.{script_name}(**parameters)`
6. `POST /jobs/success/{jobid}` or `POST /jobs/error/{jobid}`

**Signal Handling** (`signal_handler`):
- Handles `SIGTERM` (from `process.terminate()`) and `SIGINT` (Ctrl+C) for immediate shutdown
- **Minimal handler**: Only raises `SystemExit(0)` to trigger finally block cleanup
- **Avoids unsafe operations**: No I/O, threading, or complex operations in signal context
- **Cleanup in finally block**: Stream flushing happens in `worker()` finally, not in signal handler
- **Prevents double cleanup**: SystemExit(0) caught separately from errors, no duplicate `close_streams()`
- **Immediate termination**: Job interrupted mid-execution (by design, matches server cancel flow)
- **Design rationale**: Server sets state=CANCELED before sending signal; implementing checkpoints would require modifying 50+ CEA scripts
- Critical for Docker: Combined with tini, ensures graceful termination within timeout window
- **Exit code handling**: Code 0 = signal shutdown (no error report), non-zero = job error

**Stream Capture** (`JobServerStream`):
- Redirects `print()` output to queue → background thread POSTs to `PUT /streams/write/{jobid}`
- Server emits `'cea-worker-message'` via SocketIO
- `close_streams()` flushes on job completion

**Script Execution** (`run_job`):
- Converts parameter keys: `"general-settings"` → `"general_settings"`
- Loads from `cea.api` module: `cea.api.demand`, `cea.api.emissions`, etc.
- Suppresses warnings (FutureWarning, DeprecationWarning, UserWarning)

## State Transitions (Server)

**POST /jobs/started/{job_id}**:
- Sets `state=STARTED`, `start_time=now()`, emits `'cea-worker-started'`

**POST /jobs/success/{job_id}**:
- Sets `state=SUCCESS`, `end_time=now()`, `stdout=streams.pop()`
- Graceful cleanup: `terminate()` → wait 3s → `kill()` if needed
- Removes temp files, emits `'cea-worker-success'`

**POST /jobs/error/{job_id}**:
- Sets `state=ERROR`, `error=message`, `stderr=stacktrace`, `stdout=streams.pop()`
- Graceful cleanup, removes temp files, emits `'cea-worker-error'`

**POST /jobs/cancel/{job_id}** (user-initiated):
- Requires authorization: only job creator can cancel
- Row-level locking (TOCTOU protection)
- Validates job state (must be PENDING or STARTED, not deleted)
- Sets `state=CANCELED`, `error="Canceled by user"`
- **Graceful cleanup**: `terminate()` → wait 3s → `kill()` if needed (allows cleanup handlers)
- Removes temp files, emits `'cea-worker-canceled'`

**kill_job()** (internal, e.g., server shutdown):
- Sets `state=KILLED`, `error="Killed by server shutdown"`
- **Force kill**: Immediate `kill()` without graceful termination
- Removes temp files, emits `'cea-worker-killed'`

**DELETE /jobs/{job_id}** (soft delete):
- Requires authorization: only job creator can delete
- Row-level locking (TOCTOU protection)
- Sets `deleted_at=now()`, `deleted_by=user_id`
- Preserves original `state` (does NOT change to DELETED)
- Prevents deletion if job is still STARTED
- Prevents double deletion (checks if `deleted_at` already set)
- Removes temp files, emits `'cea-job-deleted'`

## Cleanup (`jobs.py:cleanup_worker_process`)

**Graceful** (`force=False`, SUCCESS/ERROR/CANCEL): `terminate()` → wait 3s → force kill if timeout (allows cleanup handlers)
**Force** (`force=True`, server shutdown/KILLED): Immediately `kill()` children + main process

**Temp Files** (`cleanup_job_temp_files`):
- Pattern: `/tmp/cea_job_{job_id}_*`
- Deleted on: completion, error, cancel, delete

## Caching (`dependencies.py`)

**`worker_processes`**: `AsyncDictCache` mapping `job_id → PID` (TTL-based)
**`streams`**: `AsyncDictCache` mapping `job_id → List[str]` (stdout/stderr chunks, TTL-based)

FastAPI dependencies: `CEAWorkerProcesses`, `CEAStreams`, `CEAProjectID`, `CEAUserID`, `CEAServerUrl`

## SocketIO Events (room: `user-{user_id}`)

`cea-job-created`, `cea-worker-started`, `cea-worker-message` (stdout chunk), `cea-worker-success`, `cea-worker-error`, `cea-worker-canceled`, `cea-worker-killed`, `cea-job-deleted`

Retry logic: `emit_with_retry()` (3 retries, 0.1s initial delay, exponential backoff)

## Error Handling

**Worker**: Catches `SystemExit` and `Exception`, POSTs to `/jobs/error/{jobid}`, always flushes streams
**Network**: `post_with_retry()`, `put_with_retry()` (3 retries, 0.5s initial)
**Database**: Catches `sqlalchemy.exc.OperationalError`, raises HTTPException

## Security

- **Validation**: Job ID must be UUID, server URL must be HTTP/HTTPS with hostname
- **File uploads**: Sanitized names (alphanumeric + `.`, `-`, `_`), path traversal prevention
- **Remote mode**: Forces `multiprocessing=False` to prevent resource exhaustion

## Docker Deployment

**Process Management** (`Dockerfile`):
- Uses `tini` as PID 1 init system for proper signal forwarding and zombie reaping
- Without `tini`, Docker containers may fail to properly handle `SIGTERM` signals
- `tini` ensures child processes are reaped to prevent zombie accumulation
- Critical for job cancellation: allows graceful termination within timeout window

**Why tini is needed**:
- Docker doesn't provide init system by default
- Without init, main process becomes PID 1 with special kernel behavior
- PID 1 doesn't receive default signal handlers (signals ignored unless explicitly handled)
- Zombie processes aren't automatically reaped, causing resource leaks
- Combined with worker signal handlers, provides robust process lifecycle management

## Key Files

- `cea/interfaces/dashboard/server/jobs.py` - Job lifecycle, endpoints
- `cea/worker.py` - Worker subprocess logic with signal handlers
- `cea/interfaces/dashboard/server/streams.py` - Stream capture endpoints
- `cea/interfaces/dashboard/lib/database/models.py` - JobInfo, JobState
- `cea/interfaces/dashboard/dependencies.py` - Caches, FastAPI dependencies
- `Dockerfile` - Container image with tini init system

## Code Patterns

**Adding job endpoint**:
1. Update job state in DB
2. Cleanup (streams, processes, temp files)
3. `await session.commit()` **before** emitting SocketIO
4. Emit outside try-except to prevent rollback

**Debugging**: Check `JobInfo.state`, `job.stdout/stderr`, server logs, `worker_processes`/`streams` caches
