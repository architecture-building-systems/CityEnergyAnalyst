# How to test CEA

This guide covers how to run and write tests for CEA during development. Tests are required for any non-trivial change merged into `master`.

## What runs where

CEA has two test layers:

| Layer | What it does | Where it runs |
|-------|---|---|
| **Unit tests** | Fast `pytest` tests of individual modules. Files in `cea/tests/test_*.py`. | Locally via `pixi run unittest`; in CI on every PR. |
| **Integration tests** | End-to-end runs of CEA scripts against reference scenarios (`zug_heating`, `sg_cooling`). Driven by `cea test --type integration`. | Locally via `pixi run integration`; in CI on every non-draft PR. |

CI is **GitHub Actions** — see `.github/workflows/ci.yml`. It runs the unit + integration suites on Ubuntu, macOS, and Windows for every PR that touches `cea/**`, `pyproject.toml`, or `pixi.lock`. Changes confined to `cea/interfaces/**` or `**/*.md` skip CI.

When a build fails, the workflow uploads the contents of `~/zug_heating/` and `~/sg_cooling/` as artifacts (3-day retention) so you can inspect what went wrong without re-running locally.

## Running tests locally

From the repo root, with the `cea` Pixi environment activated:

```bash
# Unit tests only — fastest feedback (~seconds to a few minutes)
pixi run unittest

# Integration tests — runs reference scenarios end-to-end (~10-30 minutes)
pixi run integration

# Unit tests with coverage report
pixi run coverage
```

The pixi task definitions are in `pyproject.toml`:

| Task | Command |
|------|---------|
| `unittest` | `pytest cea/tests/` |
| `integration` | `cea test --type integration` |
| `coverage` | `pytest --cov=cea cea/tests/` |

You can also run a single test file directly:

```bash
pixi run pytest cea/tests/test_demand.py -v
pixi run pytest cea/tests/test_demand.py::test_specific_thing -v
```

## Writing unit tests

Every new test file goes in `cea/tests/` (see `cea/CLAUDE.md` — tests live there and nowhere else). Use the existing files as templates:

- **Naming**: `test_<module>.py` for the file, `test_<behaviour>()` for each function.
- **Fixtures**: scenario fixtures live in `cea/tests/conftest.py`. Reuse them — don't roll your own scenario from scratch in each test.
- **Reference data**: integration-style tests that compare numeric outputs against a known-good baseline store the baseline as a `.config` file next to the test (e.g. `test_district_cooling.config` for `test_district_cooling.py`).

If results legitimately change (e.g. a corrected formula), regenerate the baseline with `cea/tests/create_unittest_data.py` — then **verify the new results by hand or a second method** before committing the updated `.config`.

## CI gotchas

- **Drafts skip integration tests.** The integration step is gated on `github.event.pull_request.draft == false`. Mark your PR ready for review to trigger them.
- **Concurrency cancels in-flight PR builds.** Pushing a new commit to a PR cancels the previous run for that PR (saves CI minutes). Pushes to `master` are never cancelled.
- **`cea/interfaces/**` is exempt from CI.** That directory has no automated tests today (tracked as a TODO in `ci.yml`). If you change it, run the affected interface manually before merging.

## Test-driven development

For new physics or numerical code, start with a test of the expected output and work inward. This is faster than running the full CEA pipeline every time you tweak an equation, and it documents the intended behaviour. See the [Wikipedia article on TDD](https://en.wikipedia.org/wiki/Test-driven_development) for the general method.
