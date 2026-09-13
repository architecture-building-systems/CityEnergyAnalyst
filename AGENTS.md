# Guidelines for LLMs

**Creating new documentation for agents (e.g. AGENTS.md` or `CLAUDE.md`)**:
- **Always** create context-specific documentation as `AGENTS.md` (not `CLAUDE.md`)
- **Always** symlink the new `AGENTS.md` file as `CLAUDE.md` in the same directory
- **Don't create AGENTS.md in every directory** - Only create when the directory contains complex patterns that aren't obvious from code

**When to create AGENTS.md**:
- **DO create** when the directory has:
  - Complex architectural patterns not obvious from code

- **DON'T create** when:
  - Directory contains simple utility functions
  - Code is self-explanatory with good docstrings
  - It's a small module with straightforward logic
  - Parent directory's AGENTS.md already covers it adequately
  - Would duplicate information already in code/docstrings

**Writing style for AGENTS.md**:
- **Be concise and actionable** - ALWAYS aim for <150 lines when possible
- **Focus on patterns, not details** - What to do, not why it exists
- **Scannable structure** - Use headers, bullets, and short paragraphs

**Updating existing agent documentation**:
- **IMPORTANT**: When a code change makes AGENTS.md content in that directory inaccurate (a documented pattern, gotcha, limitation, or API changed) — or introduces a new pattern/gotcha as non-obvious as what's already there — update AGENTS.md in the same change: fix or remove what's now wrong, add what's now missing.
- **Never add**: status/progress notes, "completed features" checklists, changelog entries, or time/scope estimates. That's PR-description content — it goes stale immediately and isn't actionable guidance.
- **Create comprehensive user documentation** - When detailed explanations are needed, create proper documentation in `docs/` with sections, examples, and context for human readers. AGENTS.md should remain concise LLM reference only

**Code quality directives**:
- **Extract meaningful patterns, not trivial wrappers** - Only create helper functions when they add real value:
  - **DON'T extract** when:
    - It's just a 1-2 line wrapper around existing functions
    - It's standard library usage (file I/O, simple pandas operations)
    - The abstraction obscures rather than clarifies intent
    - It would be clearer to just write inline
  - **Rule of thumb**: If the helper function is shorter/simpler than its call sites, don't extract it
---
## Project Overview

City Energy Analyst (CEA) - Urban building energy simulation platform for low-carbon city design.

## Architecture Context to Keep in Mind

- **File-based today, object storage planned**: a scenario is a folder of CSV/shapefiles on disk,
  not a database — there is a plan to move towards object storage, but that has not happened yet.
  Don't assume today's file layout is permanent; don't assume a future object store either.
- **Both a local tool and a deployed multi-user web app**: the same code runs as a single-user
  local CLI/dashboard and as a web app serving concurrent users, potentially across containers
  with network-backed scenario storage. A solution that is fine for one user on local disk (a
  full-file re-read, a folder hash, an uncached recomputation on every request) can become a
  scaling or concurrency problem once deployed. When proposing a solution, say explicitly which
  of these two contexts it was designed for, and flag the tradeoff rather than silently picking
  whichever is simplest to implement. See `cea/interfaces/dashboard/AGENTS.md` for the concrete
  patterns this leads to (statelessness, pull-over-push, avoiding unbounded I/O per request).

## Environment Setup

See `pyproject.toml` for the `setup-dev` and `cea` pixi tasks, and `Dockerfile` for the container build.
