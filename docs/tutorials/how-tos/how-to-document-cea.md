# How to document CEA

## Documentation language

CEA documentation is written in **British English** (matches the convention in user-facing strings throughout the codebase).

Two formats coexist in `docs/`:

- **reStructuredText (`.rst`)** — the developer reference; rendered by [Sphinx](https://www.sphinx-doc.org/) into the [Read the Docs site](https://city-energy-analyst.readthedocs.io). The `docs/conf.py` file pins extensions and theme.
- **Markdown (`.md`)** — tutorial content under `docs/tutorials/cea4-app-training/`, `docs/tutorials/glossary/`, and these how-to guides. Lives outside the Sphinx build; rendered by GitHub and any Markdown viewer.

When in doubt: **new tutorial / how-to content → Markdown**; **API reference, autodoc-driven pages → RST**.

The [Quick reStructuredText reference](https://docutils.sourceforge.io/docs/user/rst/quickref.html) is the best primer for `.rst` syntax.

---

## Module and function docstrings

Use [Sphinx field-list docstrings](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#field-lists) — these are what get parsed by `sphinx.ext.autodoc` for the API reference. Only triple-quoted strings are extracted; `#` comments are ignored.

```python
"""
i_like_pie.py

Brief description of what the module does.
"""


def non_return_method(parameter1, parameter2):
    """This method does X. Why it exists.

    :param parameter1: description of parameter1
    :type parameter1: type of parameter1
    :param parameter2: description of parameter2
    :type parameter2: type of parameter2
    """


def single_return_method(parameter1, parameter2):
    """One-line summary.

    :param parameter1: description
    :type parameter1: type
    :returns: **return1** — description
    :rtype: return1_type
    """


def multiple_return_method(parameter1, parameter2):
    """One-line summary.

    :param parameter1: description
    :type parameter1: type
    :param parameter2: description
    :type parameter2: type
    :returns:
        - **return1** — description
        - **return2** — description
    :rtype: (return1_type, return2_type)
    """
```

### Physics functions

Functions implementing physics (hydraulics, heat transfer, thermodynamics, fluid properties) follow a stricter spec — see **[`docs/developer/documenting-physics/docstring-specification.md`](../../developer/documenting-physics/docstring-specification.md)** for the rules. In short:

- All parameters and returns must have units in `[square brackets]`
- Include formulas using Unicode symbols
- Use standards citations: `[Tag] Author (Year). Title. Journal, Volume, Pages`

---

## Documentation CLI commands

The `cea` CLI exposes several documentation utilities (registered in `cea/scripts.yml` with `interfaces: [doc]`). Run them from the repo root with the `cea` environment activated.

| Command | What it does |
|---------|---|
| `cea html` | Cross-references all API documentation via [`sphinx-apidoc`](https://www.sphinx-doc.org/en/master/man/sphinx-apidoc.html), runs `sphinx-build` from `docs/`, and opens the HTML files relevant to your current git diff. |
| `cea graphviz` | Renders the `graphviz.gv` files for every script in `cea/schemas.yml` and writes them to `docs/graphviz/`. |
| `cea glossary` | Regenerates the **legacy** RST glossary (`input_methods.rst`, `intermediate_input_methods.rst`, `output_methods.rst`) from `cea/schemas.yml`. |
| `cea schema --locator <method>` | Print the schema for a given locator method to stdout. Handy for spot-checks. |

The **newer** tutorial-style glossary at `docs/tutorials/glossary/` is regenerated with `scripts/generate_tutorial_glossary.py` — see [Variable & File Glossary](../glossary/index.md).

---

## Sphinx `make` targets

The classic Sphinx make targets live in `docs/make.bat` (Windows) and `docs/Makefile` (POSIX). Run from inside `docs/`:

| Target | Purpose |
|--------|---------|
| `make html` | Build HTML into `docs/_build/`. Skips files that haven't changed. |
| `make clean` | Delete the entire `_build/` output. |
| `make-warnings` (Windows only) | Run `sphinx-build` and stop on the **first** error — useful when debugging a broken build. |

For the full list of `make` targets, run `make help`.
