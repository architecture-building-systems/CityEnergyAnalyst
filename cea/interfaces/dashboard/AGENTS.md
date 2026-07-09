# Dashboard

## Frontend Code

The dashboard UI (React frontend) is in a **separate repository** — not here.

- **ALWAYS** run `ls ../CityEnergyAnalyst-GUI` (relative to this repo root) before concluding the frontend repo is absent — do NOT rely on name-based searches
- If not found, ask user before proceeding
- This directory (`cea/interfaces/dashboard/`) contains only the **Python/FastAPI backend** — API routes, job system, and SocketIO server
- For frontend changes (components, pages, API calls from the UI), work in the GUI repo instead

---

# API Auth

Route dependencies declare **security intent**; the deployment mode decides how
it is proven.

**No proxy is assumed.** The server runs locally or online and self-enforces auth
in both cases. Never rely on a gateway or reverse proxy to pre-filter requests.

**Default auth:** `require_authenticated` runs as an app-level dependency on every
route. In non-local mode it rejects unauthenticated callers (those that resolve to
`LOCAL_USER_ID`). No per-route annotation needed — add new routes freely and they
get auth for free.

**Public exceptions** are listed in `_PUBLIC_ROUTES` in `dependencies.py`:
session refresh, logout, and health-check endpoints. New public routes must be
added there explicitly (fail-secure by default).

| Primitive | When to use |
|---|---|
| `require_authenticated` | App-level. Do not add to individual routes. |
| `CEAUser` / `CEAUserID` | Routes that need to know *who* the caller is (ownership, quotas). |
| `require_public_demo_read(demo_id)` | Path-param dependency for anonymous read of allowlisted demo ids. Used in `api/demo.py`. |

**Public demo sub-app** — `api/demo.py` is a standalone `FastAPI()` instance mounted
at `/api/demo` by `app.py` when `Settings.public_demo_scenarios` is non-empty. Because
it is a sub-app (not a router), it does **not** inherit the main app's
`require_authenticated` dependency — the anonymous boundary is structural, not a code
branch. No edit to `require_authenticated` or `_PUBLIC_ROUTES` is needed.

`Settings.public_demo_scenarios` (`Dict[str, str]`, default `{}`):
- Env: `CEA_PUBLIC_DEMO_SCENARIOS="demo1:/abs/path/scenario1,demo2:/abs/path/scenario2"`
- JSON format also accepted: `'{"demo1": "/abs/path"}'`
- Empty → sub-app not mounted → zero overhead (local mode never needs this).

The sub-app resolves scenario paths exclusively through `require_public_demo_read`,
which checks `demo_id` against the allowlist. No arbitrary filesystem paths are
accepted. No write verbs are defined — the surface is read-only by construction.

**Topology**: built in-process now; can be promoted to a standalone service with no
code change (deploy `demo_app` alone, gateway `/api/demo/*` to it).

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

## Prefer pull over push

When a consumer needs fresh data, it should fetch and compute on demand rather than relying on a producer to push updates at the right moment. Push-based side effects (post-job hooks, event handlers, eager refreshes) couple producers to consumers, run unconditionally regardless of who needs the result, and compound under concurrency.

Before adding a push mechanism, ask: does the consumer already recompute correctly when it reads? If yes, the push is redundant — decline to add it.

## Framing

Users describe requirements in UI and event terms: "after X finishes", "when the user clicks Y", "the panel should refresh when Z". These are valid UX descriptions but are not backend specifications — translate them before deciding on an implementation.

For any trigger-phrased request:
1. Identify the **invariant** the user actually wants: "the panel always shows current data" rather than "refresh after job completion".
2. Check whether the invariant is already satisfied by the existing read path.
3. Only if it isn't, consider a push mechanism — and evaluate it against scalability first: does it run unconditionally for every event regardless of who needs the result? Does it compound under concurrent users or jobs?

UI language hides scalability assumptions that hold for a single local user but break under concurrent load. A feature that "works fine" with one user triggering one job can become a bottleneck when 20 jobs complete simultaneously or when the server runs across multiple containers. Reframe the requirement as an invariant first, then choose the implementation.

The user describing a feature may not be a software engineer and won't catch an architectural shortcut. When a request is ambiguous, prefer the more separated/conservative design and explain the tradeoff in plain language rather than guessing.

## Statelessness (important for container scaling)

Treat the dashboard server as stateless. Do not persist request-scoped selections (e.g. scenario) to `config` or any server-side store. Pass context per request via `X-CEA-*` headers; do not use `config.save()` to persist request-scoped scenario selection.

**Config is per-request**: `get_cea_config()` creates a fresh instance on every request (local: `CEALocalConfig` from disk, non-local: `CEAStatelessConfig` from `DEFAULT_CONFIG`). There is no shared config singleton — mutations are request-scoped and need no snapshot/restore.

**Scenario dependencies** (`api/utils.py`):
- `CEAScenario` enforces that the resolved scenario directory exists (use for endpoints that read/write scenario files).
- `CEAScenarioLenient` resolves and validates path boundaries but does not require directory existence (use for metadata/config endpoints).

Both dependencies read scenario context from `X-CEA-*` headers. In local mode, falls back to `config.scenario` if no headers are present. In non-local mode, missing headers return 400 — `config.scenario` resolves to `DEFAULT_CONFIG` which is meaningless in a stateless context. They enforce `project_root` boundaries; in non-local mode, absolute `X-CEA-Project` values are rejected.

**Project dependencies** (`api/utils.py`): the project-level counterpart to `CEAScenario` for routes that operate on a project as a whole (list/delete a project, create/delete/duplicate/rename a scenario, upload, prepare a download) rather than an existing scenario.
- `CEAProject` requires the resolved project directory to exist (404 if not).
- `CEAProjectLenient` resolves and boundary-checks the path without requiring existence (use where the project may not exist yet, e.g. scenario upload with `type="new"`).

Same header (`X-CEA-Project`), same local-mode `config.project` fallback, same absolute-path rejection in non-local mode. Never accept a raw `project: str` query/body/form param and hand-roll `os.path.join(project_root, project)` + `secure_path(...)` — that duplicates this dependency and is easy to get inconsistent (e.g. forgetting `root=project_root`, or not rejecting absolute paths).

**Route path safety helpers** (`utils.py`):
- Use `InputLocator(scenario)` directly in route handlers — `CEAScenario` / `CEAScenarioLenient` already sanitise the path.
- Use `secure_join_under_root(base, user_segment)` when appending user-provided path segments before filesystem checks.
- See `api/AGENTS.md` for the full DO/DON'T pattern.

**`save()` behaviour**: `CEALocalConfig.save()` writes `~/cea.config`; `CEAStatelessConfig.save()` is a no-op. Call `config.save()` unconditionally where appropriate — it does the right thing in both modes.

## Scenario Context — Header Contract

Scenario context travels as `X-CEA-*` request headers. Falls back to `config.scenario` when no headers are present.

| Header | Purpose |
|---|---|
| `X-CEA-Project` | Project directory (relative under `project_root` in non-local mode) |
| `X-CEA-Scenario-Name` | Bare scenario name — always the parent scenario |
| `X-CEA-Child-Scenario` | Logical pathway child token `<pathway_name>/<year>`; requires the two above |

**Resolution priority**: `X-CEA-*` headers > `config.scenario` (local mode only — non-local returns 400 when headers are absent).

**Child scenario**: `X-CEA-Child-Scenario: <pathway_name>/<year>` is a logical token — the backend resolves it to a filesystem path via `InputLocator.get_state_in_time_scenario_folder(pathway_name, year)`. No filesystem path is sent by the client; the physical layout (`outputs/pathways/<name>/state_<year>`) stays an implementation detail.

**Canvas compare mode**: send per-request `headers` on each Axios call to target different scenarios concurrently — one global header/cookie cannot express this, which is why headers (not cookies) were chosen.

**Future phase (separate plan)**: URL path hierarchy `PUT /projects/{id}/scenarios/{name}/...` requires a `project_id → project_path` mapping table (works for local and non-local modes). Deferred: no `project_id` migration needed until online multi-user requires stable IDs.

## State Ownership

Use this to decide where state lives before implementing any feature.

**The boundary rule**: if removing the server-side state would break correctness for a *different* client (a second browser tab, a CLI user, a different container), it belongs on the backend. If it only affects the current user's current view, it belongs on the frontend.

### Backend owns
- **Persisted domain state** — scenario files, input/output data, pathway YAML, job logs, status files; anything that must survive a page reload or server restart
- **Derived reads requiring disk or computation** — KPI results, geometry queries, timeline data; computed on demand from files, never cached server-side between requests
- **Authentication and session tokens** — access/refresh tokens, cookie management
- **Job lifecycle** — queuing, worker process management, stdout/stderr streaming

### Frontend owns (lives in the GUI repo — see Frontend Code above; not actionable in this repo)
- **UI state** — which panel is open, active tab, scroll position, expanded/collapsed sections
- **Form state** — draft values typed but not yet submitted
- **Selection state** — which scenario, pathway, or year is active in the UI (per Statelessness)
- **Sequence orchestration** — calling routes in the correct order for multi-step flows
- **Optimistic updates** — reflecting a write in the UI before the server confirms
- **Refetch logic** — when to re-fetch after a write (per Prefer pull over push)
