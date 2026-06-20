# Dashboard

## Frontend Code

The dashboard UI (React frontend) is in a **separate repository** — not here.

- **ALWAYS** run `ls ../CityEnergyAnalyst-GUI` (relative to this repo root) before concluding the frontend repo is absent — do NOT rely on name-based searches
- If not found, ask user before proceeding
- This directory (`cea/interfaces/dashboard/`) contains only the **Python/FastAPI backend** — API routes, job system, and SocketIO server
- For frontend changes (components, pages, API calls from the UI), work in the GUI repo instead

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

## Statelessness (important for container scaling)

Treat the dashboard server as stateless. Do not persist request-scoped selections (e.g. pathway child scenario) to `config` or any server-side store. Prefer passing such context per request — accept it as a query or body parameter and apply it in memory for that request only; never call `save()` on it. Persisting shared global state blocks horizontal scaling across containers and causes cross-request / cross-client staleness bugs. When you must apply per-request state to a shared config object (e.g. as a FastAPI router-level dependency), snapshot the original values and restore them in a `finally` block.

**Current exception — project/scenario selection**: The active project and scenario (`general:project` + `general:scenario-name` in config) are still persisted to disk via `PUT /api/project/`. This is intentional for now; making scenario selection stateless is planned for a future refactor. Refrain from adding new server-side persistence beyond this existing exception. Warn if user insists on breaking this rule.
