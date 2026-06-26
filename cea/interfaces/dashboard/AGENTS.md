# Dashboard

## Frontend Code

The dashboard UI (React frontend) is in a **separate repository** — not here.

- **ALWAYS** run `ls ../CityEnergyAnalyst-GUI` (relative to this repo root) before concluding the frontend repo is absent — do NOT rely on name-based searches
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

## Logging

Use `getCEAServerLogger` from `cea.interfaces.dashboard.lib.logs` — never `logging.getLogger(__name__)`.

```python
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
logger = getCEAServerLogger("cea-server-<module>")
```

Use a descriptive name matching the module (e.g. `"cea-server-utils"`, `"cea-server-inputs"`).

## Caching (`dependencies.py`)

- `worker_processes`: `job_id → PID` (TTL-based)
- `streams`: `job_id → List[str]` stdout/stderr chunks (TTL-based)

## SocketIO Events (room: `user-{user_id}`)

`cea-job-created`, `cea-worker-started`, `cea-worker-message`, `cea-worker-success`, `cea-worker-error`, `cea-worker-canceled`, `cea-worker-killed`, `cea-job-deleted`

Retry: `emit_with_retry()` (3 retries, exponential backoff).

## Dashboard API Pattern

Not every user action should become a background job. Keep fast synchronous API routes for lightweight, reusable domain operations. Promote an action to a native job when the user experience depends on persistent Job Info logs, streamed stdout/stderr, or parity with long-running workflow actions. In both cases, keep the business logic in shared service functions so API routes and jobs call the same implementation.

## Statelessness (important for container scaling)

Treat the dashboard server as stateless. Do not persist request-scoped selections (e.g. scenario) to `config` or any server-side store. Pass context per request via `X-CEA-*` headers (preferred) or query params (deprecated compat); never call `save()` on it.

**Config is per-request**: `get_cea_config()` creates a fresh instance on every request (local: `CEALocalConfig` from disk, non-local: `CEAStatelessConfig` from `DEFAULT_CONFIG`). There is no shared config singleton — mutations are request-scoped and need no snapshot/restore.

**Scenario dependencies** (`api/utils.py`):
- `CEAScenario` enforces that the resolved scenario directory exists (use for endpoints that read/write scenario files).
- `CEAScenarioLenient` resolves and validates path boundaries but does not require directory existence (use for metadata/config endpoints).

Both dependencies read scenario context from `X-CEA-*` headers first; if absent they fall back to query params. They enforce `project_root` boundaries in both cases; in non-local mode, absolute `X-CEA-Project` / `project` values are rejected.

**`save()` behaviour**: `CEALocalConfig.save()` writes `~/cea.config`; `CEAStatelessConfig.save()` is a no-op. Call `config.save()` unconditionally where appropriate — it does the right thing in both modes.

## Scenario Context — Header Contract

Scenario context travels as HTTP request headers. Query params (`project`, `scenario_name`, `scenario_path`) are deprecated compat, accepted during frontend migration.

| Header | Purpose |
|---|---|
| `X-CEA-Project` | Project directory (relative under `project_root` in non-local mode) |
| `X-CEA-Scenario-Name` | Bare scenario name — always the parent scenario |
| `X-CEA-Child-Scenario` | Logical pathway child token `<pathway_name>/<year>`; requires the two above |

**Resolution priority**: header values (if any header present) > query params > `config.scenario`.

**Child scenario**: `X-CEA-Child-Scenario: <pathway_name>/<year>` is a logical token — the backend resolves it to a filesystem path via `InputLocator.get_state_in_time_scenario_folder(pathway_name, year)`. No filesystem path is sent by the client; the physical layout (`outputs/pathways/<name>/state_<year>`) stays an implementation detail.

**Canvas compare mode**: send per-request `headers` on each Axios call to target different scenarios concurrently — one global header/cookie cannot express this, which is why headers (not cookies) were chosen.

**Future phase (separate plan)**: URL path hierarchy `PUT /projects/{id}/scenarios/{name}/...` requires a `project_id → project_path` mapping table (works for local and non-local modes). Deferred: no `project_id` migration needed until online multi-user requires stable IDs.

## Docker

Server runs as PID 1 with a `SIGCHLD` handler (`setup_sigchld_handler` in `app.py`) that reaps zombie workers via `os.waitpid(-1, WNOHANG)`. Tini not required but easy to re-enable.
