# How to add a new script

This guide walks you through extending CEA with a new script.

The four steps are:

1. **Start from the template** at `cea/examples/template.py`.
2. **Develop your script** — follow the CEA conventions.
3. **Register the script** in `cea/scripts.yml`.
4. **Declare any parameters** in `cea/default.config`.

---

## Step 1: Start from the template

Copy `cea/examples/template.py` into a sensible location under `cea/` (e.g. `cea/analysis/my_feature/main.py`). If you create a new subfolder, add an empty `__init__.py` so Python treats it as a package.

Rename the copied file to something descriptive (snake_case). You should now be able to run it with:

```bash
pixi run python -m cea.analysis.my_feature.main
```

Inside the template you'll find:

- A module-level docstring — update it with what your script does and why (include references to publications).
- A `__author__` / `__credits__` / `__copyright__` block — update it with your name and the year.
- A core function (named `template`) — rename it to match the module name. This is where the work happens.
- A `main(config: cea.config.Configuration)` entry point — this is what `cea/scripts.yml` invokes.

Inside `main`, build an `InputLocator` and call your core function:

```python
def main(config: cea.config.Configuration):
    locator = cea.inputlocator.InputLocator(config.scenario)
    my_feature(locator, config)
```

If your function ends up with more than a few parameters, pass `config` (or specific values from it) directly instead — long argument lists are hard to maintain.

---

## Step 2: Develop your script

Each script is unique, but to fit the CEA ecosystem:

- **Names matter.** Don't use abbreviations except for loop indices. Use domain-meaningful names — readers should be able to bridge the literature and the code.
- **Use plurals** for collections (lists, tuples, sets, dicts): `buildings`, not `building_list`.
- **No hardcoded paths.** Use `cea.inputlocator.InputLocator` to resolve every file path. If you must compose one manually, use `os.path.join` or `pathlib.Path`.
- **Never call `os.chdir`.** If you think you need to, you're doing something else wrong.
- **British English** in all user-facing strings (help text, labels, descriptions).
- **No emojis** in code, comments, or print statements.
- **Tests go in `cea/tests/` only** — name them `test_*.py`.

For physics functions (heat transfer, hydraulics, thermodynamics, fluid properties), follow the stricter docstring spec at [`docs/developer/documenting-physics/docstring-specification.md`](../../developer/documenting-physics/docstring-specification.md).

---

## Step 3: Register in `cea/scripts.yml`

`cea/scripts.yml` tells the `cea` CLI:

- The name of each script
- The module path (`cea.analysis.my_feature.main`)
- The parameters the script accepts
- Which interfaces (`cli`, `dashboard`) expose it
- The category to list it under

Adding the script makes it runnable as:

```bash
cea my-feature
cea my-feature --scenario /path/to/scenario --my-flag true
```

It is also a **prerequisite for the dashboard interface** — without an entry in `scripts.yml`, the dashboard cannot expose your script.

### Entry format

`cea/scripts.yml` is grouped by category. Pick the existing category that fits, or add a new one. Use kebab-case for the `name` field (it becomes the CLI command). Example based on `thermal-network`:

```yaml
Thermal Network Design:
  - name: my-feature
    label: "My Feature (BETA)"
    short_description: One-line summary used in lists.
    description: |
      Multi-line description, rendered as markdown in the dashboard.
      Explain the inputs, outputs, and a typical use case.
    interfaces: [cli, dashboard]
    module: cea.analysis.my_feature.main
    parameters: ['general:scenario', 'general:multiprocessing', 'my-feature']
    input-files:
      - [get_zone_geometry]
      - [get_total_demand]
```

**Field reference**

| Field | Purpose |
|-------|---------|
| `name` | CLI command (kebab-case). |
| `label` | Display name in the dashboard. Mark `BETA` features by appending `(BETA)`. |
| `short_description` | One-line summary used in lists. |
| `description` | Long description (markdown). Shown in the dashboard. |
| `interfaces` | Where to expose the script. Use `[cli]` for developer-only scripts, `[cli, dashboard]` for user-facing features. |
| `module` | Fully qualified module path. Must define a `main(config)` function. |
| `parameters` | List of parameters consumed. Use `section:parameter` for a single value, `section` to pull every parameter in that section. |
| `input-files` | Optional. List of `[locator_method, *args]` entries the script reads. Used for dependency graphs and pre-run validation. |

Programmatic access: `cea.api` exposes every script as a function with dashes replaced by underscores, e.g. `from cea.api import my_feature`.

---

## Step 4: Declare parameters in `cea/default.config`

`cea/default.config` lists every parameter the user can set. Each section corresponds to a script (or a closely related group of scripts).

Add a section named after your script and one entry per parameter:

```ini
[my-feature]
input-mode = automatic
input-mode.type = ChoiceParameter
input-mode.choices = automatic, manual
input-mode.help = How to source the input data.

threshold-kwh = 100.0
threshold-kwh.type = RealParameter
threshold-kwh.help = Threshold below which buildings are filtered out (kWh).
```

Each parameter has at minimum:

- The default value: `parameter-name = value`
- The type: `parameter-name.type = <ParameterClass>` — see `cea/config.py` for the full list (`StringParameter`, `IntegerParameter`, `RealParameter`, `BooleanParameter`, `PathParameter`, `ChoiceParameter`, `MultiChoiceParameter`, `ListParameter`, etc.)
- A help string: `parameter-name.help = ...` — shown in the dashboard tooltip.

Optional:

- `parameter-name.category = Advanced` — groups the parameter under an "Advanced" expander in the dashboard.
- `parameter-name.choices = a, b, c` — for `ChoiceParameter` / `MultiChoiceParameter`.

### After modifying `cea/config.py`

If you add a **new Parameter class** to `cea/config.py`, regenerate the type stubs so the IDE picks it up:

```bash
pixi run python scripts/config_type_generator.py
```

This regenerates `cea/config.pyi`. CI also runs this automatically on PRs that touch `cea/config.py` or `cea/default.config` (see `.github/workflows/update-config-stubs.yml`).

---

## Checklist before opening a PR

- [ ] Script lives under `cea/<category>/` with an `__init__.py` in any new subfolder.
- [ ] `main(config: cea.config.Configuration)` signature.
- [ ] Module docstring with what / why / references.
- [ ] Entry added to `cea/scripts.yml` (correct category, kebab-case name, parameters listed).
- [ ] Section added to `cea/default.config` if your script has parameters.
- [ ] Tests in `cea/tests/test_<name>.py`.
- [ ] If you added a new Parameter class to `cea/config.py`: ran `scripts/config_type_generator.py`.
- [ ] Schema entries added to `cea/schemas.yml` for any new input/output files (otherwise the file won't appear in the [glossary](../glossary/index.md) and `cea schema` won't know about it).
