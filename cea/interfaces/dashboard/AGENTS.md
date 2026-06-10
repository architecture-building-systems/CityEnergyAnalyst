# Dashboard

## Frontend Code

The dashboard UI (React frontend) is in a **separate repository** — not here.

- If unsure, check: `ls ../../../CityEnergyAnalyst-GUI` (relative to this repo root)
- If not found, ask user before proceeding
- This directory (`cea/interfaces/dashboard/`) contains only the **Python/FastAPI backend** — API routes, job system, and SocketIO server
- For frontend changes (components, pages, API calls from the UI), work in the GUI repo instead

---

# Dashboard Job System

## Architecture

```
Client → Server (jobs.py) → Worker (cea/worker.py) → Server
         ↓                    ↓
    Database (SQLModel)   CEA Scripts
         ↓
    SocketIO Events
```

- **Server**: Job lifecycle, database, SocketIO
- **Worker**: Subprocess executing CEA scripts
- **Communication**: Worker POSTs to server → server emits SocketIO to client

## Job States

`PENDING → STARTED → SUCCESS/ERROR/CANCELED/KILLED`

**Soft Deletion**: Uses `deleted_at`/`deleted_by` fields (not state change) to preserve completion state.

## Job Lifecycle

**Creation** (`POST /jobs/new`): Creates `JobInfo` UUID+PENDING, handles file uploads to `/tmp/cea_job_{job_id}_*`.

**Start** (`POST /jobs/start/{job_id}`): Auth-checked, row-locked. Spawns `python -m cea.worker {job_id} {server_url}`.

**Worker steps**:
1. Register signal handlers → fetch job → redirect stdout/stderr to `JobServerStream`
2. `POST /jobs/started` → `cea.api.{script_name}(**parameters)` → `POST /jobs/success` or `/jobs/error`

**Signal handling**: Worker uses `os._exit(0)` on `SIGTERM`/`SIGINT` — immediate exit, no cleanup needed (server already set state before signalling).

**Stream capture**: `JobServerStream` queues output → daemon thread POSTs to server → server emits `cea-worker-message` via SocketIO.

## State Transitions

All transitions are auth-checked and row-locked (TOCTOU protection).

| Endpoint | Sets state | Notes |
|---|---|---|
| `POST /jobs/started/{id}` | STARTED | Worker-initiated |
| `POST /jobs/success/{id}` | SUCCESS | Graceful cleanup |
| `POST /jobs/error/{id}` | ERROR | Graceful cleanup |
| `POST /jobs/cancel/{id}` | CANCELED | User-initiated; must be PENDING or STARTED |
| `kill_job()` | KILLED | Internal; force kill |
| `DELETE /jobs/{id}` | *(soft delete)* | Sets `deleted_at`, preserves state; blocked if STARTED |

**Cleanup**: Graceful = `terminate()` → wait → `kill()`. Force = immediate `kill()`. Temp files removed on all transitions.

**Pitfalls**:
- Commit DB **before** emitting SocketIO (emit outside try-except to prevent rollback)
- Serialise SocketIO payloads with captured strings, not `job.model_dump()` on expired ORM state
- Keep FastAPI responses as Python objects; JSON-safe conversion too early breaks computed fields like `duration`
- Prefer FastAPI `status.HTTP_*` constants over numeric status codes in `HTTPException` and response constructors

## Caching (`dependencies.py`)

- `worker_processes`: `job_id → PID` (TTL-based)
- `streams`: `job_id → List[str]` stdout/stderr chunks (TTL-based)

## SocketIO Events (room: `user-{user_id}`)

`cea-job-created`, `cea-worker-started`, `cea-worker-message`, `cea-worker-success`, `cea-worker-error`, `cea-worker-canceled`, `cea-worker-killed`, `cea-job-deleted`

Retry: `emit_with_retry()` (3 retries, exponential backoff).

## Dashboard API Pattern

Not every user action should become a background job. Keep fast synchronous API routes for lightweight, reusable domain operations. Promote an action to a native job when the user experience depends on persistent Job Info logs, streamed stdout/stderr, or parity with long-running workflow actions. In both cases, keep the business logic in shared service functions so API routes and jobs call the same implementation.

## Docker

Server runs as PID 1 with a `SIGCHLD` handler (`setup_sigchld_handler` in `app.py`) that reaps zombie workers via `os.waitpid(-1, WNOHANG)`. Tini not required but easy to re-enable.
