# How to report a bug

A bug describes an existing feature that does not do what it should. Good bug reports help the team triage and reproduce issues fast.

## Step 1 — Gather the facts

A useful bug report contains:

1. **What you did** — the exact steps to reproduce, including the scenario, the feature you ran, and any non-default parameters.
2. **What you expected** to happen.
3. **What actually happened** — the full error message, including the stack trace if Python raised an exception.
4. **Your environment** — CEA version (visible in the dashboard footer, or `cea --version`), OS, and how you installed CEA (Pixi, Docker, NSIS installer).

## Step 2 — Submit the bug

1. Open the repository's **Issues** tab: <https://github.com/architecture-building-systems/CityEnergyAnalyst/issues>.
2. Click **New issue** and choose the **Bug report** template (`.github/ISSUE_TEMPLATE/bug_report.yml`).
3. Fill in the template fields. The title should be short and identify both the affected area and the CEA version, e.g. *"Optimisation crashes on Windows with multi-CPU in CEA 4.0.0-beta.7"*.
4. Reference related issues with `#1234` and people with `@username` if helpful.

## Before opening a new issue

- Search [existing issues](https://github.com/architecture-building-systems/CityEnergyAnalyst/issues?q=is%3Aissue) — your bug may already be filed.
- Check the [Known Issues page](https://city-energy-analyst.readthedocs.io/en/latest/known-issues.html).
- Ask in [Discussions](https://github.com/architecture-building-systems/CityEnergyAnalyst/discussions) if you're unsure whether it's a bug or an expected behaviour.
