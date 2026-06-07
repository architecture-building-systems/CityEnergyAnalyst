#!/usr/bin/env python
"""
Generate a cleaner, feature-grouped glossary from cea/schemas.yml.

Writes one markdown page per feature category (matching the cea4-app-training
categories) plus an index.md to docs/tutorials/glossary/. Re-run after
modifying schemas.yml to refresh the docs.

    python scripts/generate_tutorial_glossary.py
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_YML = REPO_ROOT / "cea" / "schemas.yml"
SCRIPTS_YML = REPO_ROOT / "cea" / "scripts.yml"
INPUTLOCATOR_PY = REPO_ROOT / "cea" / "inputlocator.py"
DATABASES_VERIFICATION_PY = REPO_ROOT / "cea" / "datamanagement" / "databases_verification.py"
OUTPUT_DIR = REPO_ROOT / "docs" / "tutorials" / "glossary"


CATEGORIES: list[tuple[str, str]] = [
    ("00-user-inputs", "User Inputs"),
    ("01-import-export", "Import & Export"),
    ("02-solar-radiation", "Solar Radiation Analysis"),
    ("03-renewable-energy", "Renewable Energy Potential Assessment"),
    ("04-demand-forecasting", "Energy Demand Forecasting"),
    ("05-thermal-network", "Thermal Network Design"),
    ("06-life-cycle-analysis", "Life Cycle Analysis (BETA)"),
    ("07-supply-optimisation", "Energy Supply System Optimisation"),
    ("08-data-management", "Data Management"),
    ("09-utilities", "Utilities"),
    ("99-other", "Other"),
]

CATEGORY_ALIASES = {
    "Life Cycle Analysis": "Life Cycle Analysis (BETA)",
    # scripts.yml top-level `default:` is a catch-all for legacy/internal scripts;
    # the only data-producing one here is multi-criteria-analysis, which fits Utilities.
    "default": "Utilities",
}

# created_by names found in schemas.yml that don't map cleanly to a script in
# scripts.yml (legacy names, typos, sub-modules).
LEGACY_SCRIPT_TO_CATEGORY = {
    "optimization": "Energy Supply System Optimisation",
    "decentrlized": "Energy Supply System Optimisation",
    "anthropogenic_heat": "Life Cycle Analysis (BETA)",
    "emission_time_dependent": "Life Cycle Analysis (BETA)",
    "tree_helper": "Data Management",
}


def load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def find_inputlocator_methods(path: Path) -> set[str]:
    """Return the set of method names defined in cea/inputlocator.py.

    Schemas.yml keys are matched against this set; some locators (PV_results, etc.)
    are defined without a `get_` prefix.
    """
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r"def\s+([A-Za-z_][A-Za-z0-9_]*)", text))


def find_string_referenced_locators(path: Path) -> set[str]:
    """Return locator names referenced as string literals (e.g. 'get_database_...')."""
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r"['\"](get_[A-Za-z0-9_]+)['\"]", text))


def build_script_category_map(scripts: dict) -> dict[str, str]:
    """{snake_case script name -> category title} from scripts.yml."""
    mapping: dict[str, str] = {}
    for category_title, scripts_list in scripts.items():
        if not isinstance(scripts_list, list):
            continue
        for script in scripts_list:
            if not isinstance(script, dict) or "name" not in script:
                continue
            snake = script["name"].replace("-", "_")
            mapping[snake] = category_title
    return mapping


def category_for(locator_info: dict, script_to_category: dict[str, str]) -> str:
    created_by = locator_info.get("created_by") or []
    if not created_by:
        return "User Inputs"
    first = created_by[0]
    category = script_to_category.get(first) or LEGACY_SCRIPT_TO_CATEGORY.get(first, "Other")
    return CATEGORY_ALIASES.get(category, category)


def format_values(col: dict) -> str:
    choice = col.get("choice") or col.get("choice_properties") or {}
    if "values" in choice:
        vals = choice["values"]
        if isinstance(vals, list):
            return "{" + ", ".join(str(v) for v in vals) + "}"
        return str(vals)

    col_type = col.get("type")
    if col_type == "boolean":
        return "{true, false}"
    if col_type in ("int", "float"):
        mn, mx = col.get("min"), col.get("max")
        fmt = (lambda v: f"{float(v)}") if col_type == "float" else (lambda v: f"{int(v)}")
        mn_s = "n" if mn is None else fmt(mn)
        mx_s = "n" if mx is None else fmt(mx)
        return f"{{{mn_s}...{mx_s}}}"
    if col_type == "string":
        if "pattern" in col:
            return f"pattern: {col['pattern']}"
        return "alphanumeric"
    if col_type == "date":
        return "YYYY-MM-DD"
    if col_type == "datetime":
        return "YYYY-MM-DD HH:MM:SS"
    if col_type == "time":
        return "HH:MM:SS"
    return ""


def cell(text: object) -> str:
    """Escape a description / value for a markdown table cell."""
    if text is None:
        return ""
    s = str(text).replace("|", "\\|").replace("\n", " ").replace("\r", " ").strip()
    return s


def render_column_table(columns: dict) -> list[str]:
    lines = [
        "| Variable | Description | Type | Unit | Values |",
        "|----------|-------------|------|------|--------|",
    ]
    for name in sorted(columns.keys(), key=lambda x: str(x).lower()):
        cd = columns[name] or {}
        desc = cell(cd.get("description", ""))
        col_type = cell(cd.get("type", ""))
        unit = cd.get("unit", "")
        unit_cell = f"`{unit}`" if unit else ""
        values = cell(format_values(cd))
        lines.append(f"| `{name}` | {desc} | {col_type} | {unit_cell} | {values} |")
    return lines


def render_locator(name: str, info: dict, *, is_stale: bool = False, string_referenced: bool = False) -> list[str]:
    out: list[str] = []
    out.append(f"### `{name}`")
    out.append("")
    if is_stale:
        if string_referenced:
            out.append(
                "> ⚠️ **Stale**: no matching `InputLocator` method exists, but the locator name is "
                "still referenced by string in `cea/datamanagement/databases_verification.py`. "
                "Removing this from `schemas.yml` will also require updating that reference."
            )
        else:
            out.append(
                "> ⚠️ **Stale**: no matching `InputLocator` method exists for this name — safe to "
                "remove from `cea/schemas.yml`."
            )
        out.append("")
    out.append(f"- **Path**: `{info.get('file_path', '')}`")
    out.append(f"- **File type**: `{info.get('file_type', '')}`")

    created_by = info.get("created_by") or []
    used_by = info.get("used_by") or []

    if created_by:
        out.append("- **Created by**: " + ", ".join(f"`{s}`" for s in created_by))
    else:
        out.append("- **Created by**: _user input_")
    if used_by:
        out.append("- **Used by**: " + ", ".join(f"`{s}`" for s in used_by))
    else:
        out.append("- **Used by**: _(none)_")
    out.append("")

    schema = info.get("schema")
    if not schema:
        out.append("_No column schema._")
        out.append("")
        return out

    if isinstance(schema, dict) and "columns" in schema:
        out.extend(render_column_table(schema["columns"]))
        out.append("")
    elif isinstance(schema, dict):
        for ws in sorted(schema.keys(), key=lambda x: str(x).lower()):
            ws_def = schema[ws]
            if not isinstance(ws_def, dict) or "columns" not in ws_def:
                continue
            out.append(f"**Worksheet**: `{ws}`")
            out.append("")
            out.extend(render_column_table(ws_def["columns"]))
            out.append("")
    else:
        out.append("_Schema present but not in a recognised shape._")
        out.append("")
    return out


def anchor(name: str) -> str:
    """GitHub-flavoured markdown anchor for a header containing `` `name` ``."""
    return name.lower()


def render_category_page(
    slug: str,
    title: str,
    entries: list[tuple[str, dict]],
    sibling_categories: list[tuple[str, str]],
    stale_locators: set[str],
    string_referenced_locators: set[str],
) -> str:
    nav_prev = None
    nav_next = None
    for i, (s, _) in enumerate(sibling_categories):
        if s == slug:
            if i > 0:
                nav_prev = sibling_categories[i - 1]
            if i + 1 < len(sibling_categories):
                nav_next = sibling_categories[i + 1]
            break

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(
        "_Generated from `cea/schemas.yml` by `scripts/generate_tutorial_glossary.py`. "
        "Do not hand-edit — re-run the script to refresh._"
    )
    lines.append("")
    stale_count = sum(1 for n, _ in entries if n in stale_locators)
    lines.append(f"Files in this category: **{len(entries)}**" + (f" (⚠️ {stale_count} stale)" if stale_count else ""))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    for name, _ in entries:
        marker = " ⚠️" if name in stale_locators else ""
        lines.append(f"- [`{name}`](#{anchor(name)}){marker}")
    lines.append("")
    lines.append("---")
    lines.append("")
    for name, info in entries:
        lines.extend(render_locator(
            name, info,
            is_stale=(name in stale_locators),
            string_referenced=(name in string_referenced_locators),
        ))
        lines.append("---")
        lines.append("")

    nav_bits = []
    if nav_prev:
        nav_bits.append(f"[← {nav_prev[1]}]({nav_prev[0]}.md)")
    nav_bits.append("[Glossary index](index.md)")
    if nav_next:
        nav_bits.append(f"[{nav_next[1]} →]({nav_next[0]}.md)")
    lines.append(" | ".join(nav_bits))
    lines.append("")
    return "\n".join(lines)


def render_stale_report(
    stale: list[tuple[str, dict]],
    string_referenced: set[str],
    locator_to_category: dict[str, str],
) -> str:
    """One-page report listing every stale schema entry."""
    lines: list[str] = []
    lines.append("# Stale Schema Entries")
    lines.append("")
    lines.append(
        "_Generated from `cea/schemas.yml` by `scripts/generate_tutorial_glossary.py`._"
    )
    lines.append("")
    lines.append(
        f"**{len(stale)}** entries in `cea/schemas.yml` have no matching method on "
        "`InputLocator` (`cea/inputlocator.py`). They are dead schema definitions left behind "
        "after refactors and can be removed."
    )
    lines.append("")
    string_ref = [n for n, _ in stale if n in string_referenced]
    if string_ref:
        lines.append(
            f"Of those, **{len(string_ref)}** are still referenced by name (as string literals) "
            "in `cea/datamanagement/databases_verification.py`. Those references must be updated "
            "or removed before the schema entry can be deleted safely."
        )
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Punch list")
    lines.append("")
    lines.append("| Locator name | Category | Path | Still referenced by string? |")
    lines.append("|--------------|----------|------|:---:|")
    for name, info in sorted(stale, key=lambda x: x[0].lower()):
        cat = locator_to_category.get(name, "—")
        path = info.get("file_path", "")
        marker = "yes" if name in string_referenced else ""
        lines.append(f"| `{name}` | {cat} | `{path}` | {marker} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## How to clean up")
    lines.append("")
    lines.append("For each entry above:")
    lines.append("")
    lines.append("1. Confirm no `InputLocator` method is being added back — `grep -n 'def get_<name>' cea/inputlocator.py`.")
    lines.append("2. Remove the entry from `cea/schemas.yml`.")
    lines.append(
        "3. If the locator appears in the 'still referenced by string' column above, also remove or "
        "replace its entry in `cea/datamanagement/databases_verification.py` (around lines 416-423)."
    )
    lines.append("4. Re-run `scripts/generate_tutorial_glossary.py` to regenerate the glossary and this report.")
    lines.append("")
    lines.append("[← Back to Glossary index](index.md)")
    lines.append("")
    return "\n".join(lines)


def render_index(written: list[tuple[str, str, int]], stale_count: int = 0) -> str:
    total = sum(n for _, _, n in written)
    lines: list[str] = []
    lines.append("# CEA Variable & File Glossary")
    lines.append("")
    lines.append(
        f"A reference of the **{total}** input, intermediate, and output files used by the "
        "City Energy Analyst, grouped by feature. Each entry lists the file path, the script that "
        "produces it, the scripts that consume it, and the full column schema with type, unit, and "
        "valid values."
    )
    lines.append("")
    lines.append(
        "_Generated from `cea/schemas.yml` by `scripts/generate_tutorial_glossary.py`. "
        "Re-run after modifying the schema to refresh._"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Categories")
    lines.append("")
    lines.append("| # | Category | Files |")
    lines.append("|---|----------|------:|")
    for slug, title, count in written:
        num = slug.split("-", 1)[0]
        lines.append(f"| {num} | [{title}]({slug}.md) | {count} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    if stale_count:
        lines.append("## Schema Hygiene")
        lines.append("")
        lines.append(
            f"⚠️ **{stale_count} stale schema entries** detected — see "
            "[Stale Schema Entries](_stale-entries.md) for the cleanup punch list. These are "
            "entries in `cea/schemas.yml` with no matching `InputLocator` method; they appear in "
            "the per-category pages with a ⚠️ marker."
        )
        lines.append("")
        lines.append("---")
        lines.append("")
    lines.append("## Reading a Glossary Entry")
    lines.append("")
    lines.append(
        "Each file has a heading with its **locator method** (the function on `InputLocator` "
        "that returns its path), followed by:"
    )
    lines.append("")
    lines.append("- **Path** — relative to the scenario folder")
    lines.append("- **File type** — `csv`, `shp`, `dbf`, `xlsx`, `epw`, `tif`, etc.")
    lines.append("- **Created by** — the script that writes the file (empty for user inputs)")
    lines.append("- **Used by** — scripts that read the file downstream")
    lines.append("- A column table with **Variable**, **Description**, **Type**, **Unit**, and **Values**")
    lines.append("")
    lines.append(
        "The **Values** column auto-summarises valid ranges: `{min...max}` for numeric, "
        "`{true, false}` for boolean, `{a, b, c}` for choice, `alphanumeric` for free-form strings."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## How to Regenerate")
    lines.append("")
    lines.append("```bash")
    lines.append("pixi run python scripts/generate_tutorial_glossary.py")
    lines.append("```")
    lines.append("")
    lines.append(
        "Run this whenever `cea/schemas.yml` changes. The generator is also safe to wire into "
        "CI via the same command."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    schemas = load_yaml(SCHEMAS_YML)
    scripts = load_yaml(SCRIPTS_YML)
    script_to_category = build_script_category_map(scripts)

    # Stale-entry detection: any schema key without a matching `def get_*` in inputlocator.py.
    inputlocator_methods = find_inputlocator_methods(INPUTLOCATOR_PY)
    string_referenced = find_string_referenced_locators(DATABASES_VERIFICATION_PY)
    stale_locators: set[str] = {n for n in schemas if n not in inputlocator_methods}
    # Restrict the "string referenced" set to actually-stale entries — we only flag the warning
    # for entries that are both stale AND still pointed at by name elsewhere.
    string_referenced_stale = stale_locators & string_referenced

    by_category: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    locator_to_category: dict[str, str] = {}
    unmapped: list[tuple[str, str]] = []
    for name, info in schemas.items():
        cat = category_for(info, script_to_category)
        if cat == "Other":
            cb = (info.get("created_by") or ["<none>"])[0]
            unmapped.append((name, cb))
        by_category[cat].append((name, info))
        locator_to_category[name] = cat

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # First pass: figure out which categories actually have entries (for navigation).
    populated: list[tuple[str, str, list[tuple[str, dict]]]] = []
    for slug, title in CATEGORIES:
        entries = sorted(by_category.get(title, []), key=lambda x: x[0].lower())
        if entries:
            populated.append((slug, title, entries))

    sibling_categories = [(slug, title) for slug, title, _ in populated]

    written: list[tuple[str, str, int]] = []
    for slug, title, entries in populated:
        page = render_category_page(
            slug, title, entries, sibling_categories, stale_locators, string_referenced_stale,
        )
        out_path = OUTPUT_DIR / f"{slug}.md"
        out_path.write_text(page, encoding="utf-8")
        written.append((slug, title, len(entries)))

    (OUTPUT_DIR / "index.md").write_text(render_index(written, stale_count=len(stale_locators)), encoding="utf-8")

    # Stale-entries report
    stale_entries = [(n, schemas[n]) for n in sorted(stale_locators)]
    (OUTPUT_DIR / "_stale-entries.md").write_text(
        render_stale_report(stale_entries, string_referenced_stale, locator_to_category),
        encoding="utf-8",
    )

    print(f"Wrote {len(written)} category pages + index.md to {OUTPUT_DIR.relative_to(REPO_ROOT)}")
    for slug, title, count in written:
        stale_in_cat = sum(1 for n, _ in by_category.get(title, []) if n in stale_locators)
        suffix = f"  (⚠️ {stale_in_cat} stale)" if stale_in_cat else ""
        print(f"  {slug}.md  ({count:3d})  {title}{suffix}")
    print(
        f"\nStale schema entries: {len(stale_locators)} "
        f"({len(string_referenced_stale)} still referenced by string) "
        f"-> see _stale-entries.md"
    )
    if unmapped:
        print()
        print(f"WARNING: {len(unmapped)} locators fell through to 'Other' (unmapped created_by):")
        for name, cb in unmapped:
            print(f"  {name}  <- created_by: {cb}")


if __name__ == "__main__":
    main()
