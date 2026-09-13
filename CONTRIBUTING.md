# Contributing to City Energy Analyst (CEA)

Thanks for taking the time to contribute! This guide covers what you need to know to get a change merged. If anything here is unclear, please open an issue or ask — and feel free to propose edits to this file in a PR.

## Before you start

- **Open an issue first** (or comment on an existing one) for anything beyond a small fix, so we can coordinate and avoid duplicate work: https://github.com/architecture-building-systems/CityEnergyAnalyst/issues/new/choose
- Set up your development environment with [Pixi](https://pixi.sh):
  ```bash
  pixi install && pixi run setup-dev
  pixi run cea dashboard  # launch the dashboard to check your setup
  ```

## Making a change

1. **Branch from `master`** — never commit directly to `master`.
2. **Commit your changes within your branch.** All PRs are **squash-merged**: your branch collapses into a single commit when it lands on `master`. That said, a few things still matter regardless of squash:
   - **Never commit secrets or credentials** (API keys, passwords, `.env` files, tokens) — squash doesn't erase them from the branch/PR history, and they're hard to fully remove once pushed.
   - **Don't commit large data files, build artifacts, or generated output** — check `.gitignore` covers your tool's output before committing; ask if unsure.
   - **Keep a PR scoped to one thing.** Don't bundle an unrelated fix, formatting pass, or second feature into the same branch — it becomes one unreviewable diff and one squashed commit that mixes unrelated changes. Open a separate PR instead.
   - **Make each commit one coherent, reversible change.** A clean sequence makes review, debugging, and selective reverts easier, even though the PR is ultimately squashed.
   - **Write an imperative, descriptive subject.** For example, use `Handle empty weather files` rather than `handled weather files` or `updates`. Add a short body when the reason for a change is not obvious from the diff.
   - **Stage deliberately and inspect what you will commit.** Before committing, review `git diff --staged`, `git diff --check`, and `git status`. Do not accidentally include another task's files, conflict markers, local configuration, or editor settings.
   - **Update `pixi.lock` only when its dependency resolution intentionally changes.** Include it with dependency changes; do not add unrelated lockfile churn to another PR.
   - **Never force-push (`git push --force`) to a branch anyone else might also be working on** — it can silently delete their commits.
3. **Keep your branch up to date with `master`** using the **"Update branch"** button on the PR page in GitHub. This works entirely in the browser — no need to run `git rebase` or `git merge` locally.
   - If GitHub reports a conflict it can't resolve automatically, don't try to fix it yourself — leave a comment on the PR and a maintainer will help.
4. **Run tests locally before opening a PR:**
   ```bash
   pixi run unittest
   ```
   For changes that affect CEA behavior, also run the end-to-end integration suite when practical:
   ```bash
   pixi run integration
   ```
   See the [testing guide](docs/tutorials/how-tos/how-to-test-the-cea.md) for details.

## Opening a Pull Request

- Give the PR a clear, descriptive title — it becomes the permanent commit message on `master` after squash-merge, so "fix bug" or "updates" isn't enough.
- Use the PR template — describe what the PR does, how to test it, and the expected behavior.
- Link the issue it resolves (e.g. "Fixes #1234").
- GitHub Actions runs unit tests on qualifying source and dependency changes. For non-draft PRs, it also runs the integration suite; check results on the PR page. Documentation-only changes do not trigger this test workflow.
- A maintainer will review your PR, may ask for changes, and will handle merging (squash merge) once it's ready. See [how to review a pull request](docs/developer/how-to-review-a-pull-request.rst) if you're reviewing others' work.

## Code style

- Follow the existing naming conventions in the codebase — see the [variable naming guide](docs/tutorials/how-tos/how-to-name-variables.md).
- Run `pixi run lint` before opening a PR that changes Python code. This task applies Ruff's safe fixes automatically, so review the resulting diff before committing. CI also checks Ruff, and lint failures must be fixed before merge.

## Questions

- Documentation: https://city-energy-analyst.readthedocs.io/en/latest/index.html
- Contact: https://www.cityenergyanalyst.com/contact
