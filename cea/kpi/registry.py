"""
KPI registry — loads ``definitions/<feature>.yml`` files at module
import, validates each entry against :class:`KPIDefinition`, and
checks that every ``locator`` reference points at a real
:class:`InputLocator` method and every column reference exists in
``cea/schemas.yml``.

Every :class:`KPIDefinition` returned from :func:`load_registry`
carries a ``definition_hash`` attached as a non-pydantic attribute —
the SHA256 of the canonical-JSON serialisation of the entry, used
by the cache layer to invalidate stored values when the formula
changes.

Failures at load time raise :class:`KPIDefinitionError` with the
offending field named. The registry is loaded lazily (first call
to :func:`load_registry`) and cached; tests can call
:func:`reload_registry` to force a re-read after editing yml.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import yaml

from cea.inputlocator import InputLocator
from cea.kpi.calculators import columns_referenced
from cea.kpi.exceptions import KPIDefinitionError
from cea.kpi.schema import KPIDefinition, KPIDefinitionFile
from cea.utilities.fingerprint import hash_payload

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

_DEFINITIONS_DIR = Path(__file__).parent / "definitions"
_SCHEMAS_PATH = Path(__file__).parents[1] / "schemas.yml"

_cached_registry: dict[str, KPIDefinition] | None = None
_cached_schemas: dict | None = None


def load_registry() -> dict[str, KPIDefinition]:
    """Return the validated KPI registry, loading on first call."""
    global _cached_registry
    if _cached_registry is None:
        _cached_registry = _load()
    return _cached_registry


def reload_registry() -> dict[str, KPIDefinition]:
    """Force a re-read of the yml files. Used by tests."""
    global _cached_registry, _cached_schemas
    _cached_registry = None
    _cached_schemas = None
    return load_registry()


def _load() -> dict[str, KPIDefinition]:
    schemas = _load_schemas()
    locator_methods = _locator_method_names()
    registry: dict[str, KPIDefinition] = {}
    for yml_path in sorted(_DEFINITIONS_DIR.glob("*.yml")):
        feature_stem = yml_path.stem
        with open(yml_path, "r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
        try:
            file_model = KPIDefinitionFile.model_validate(raw)
        except Exception as exc:
            raise KPIDefinitionError(
                f"{yml_path.name}: yml shape invalid — {exc}"
            ) from exc
        if file_model.feature != feature_stem:
            raise KPIDefinitionError(
                f"{yml_path.name}: 'feature: {file_model.feature}' must "
                f"match the filename stem '{feature_stem}'"
            )
        for kpi in file_model.kpis:
            _validate_one(kpi, schemas=schemas, locator_methods=locator_methods)
            if kpi.id in registry:
                raise KPIDefinitionError(
                    f"duplicate KPI id '{kpi.id}' (second occurrence in "
                    f"{yml_path.name})"
                )
            # Stash the definition_hash on the model. Pydantic models
            # are frozen so we go through ``object.__setattr__`` —
            # safe because the hash is computed once at load and
            # never mutated.
            object.__setattr__(
                kpi,
                "definition_hash",
                hash_payload(kpi.model_dump(mode="python")),
            )
            registry[kpi.id] = kpi
    return registry


def _validate_one(
    kpi: KPIDefinition,
    *,
    schemas: dict,
    locator_methods: set[str],
) -> None:
    if kpi.source.locator not in locator_methods:
        raise KPIDefinitionError(
            f"{kpi.id}: source.locator '{kpi.source.locator}' is not a "
            f"method on InputLocator"
        )
    schema_entry = schemas.get(kpi.source.locator)
    if schema_entry is None:
        raise KPIDefinitionError(
            f"{kpi.id}: source.locator '{kpi.source.locator}' has no entry "
            f"in cea/schemas.yml — add one before referencing it from a KPI"
        )
    declared_columns = set(
        ((schema_entry or {}).get("schema") or {}).get("columns", {}).keys()
    )
    if not declared_columns:
        raise KPIDefinitionError(
            f"{kpi.id}: schemas.yml entry '{kpi.source.locator}' declares no "
            f"columns; KPI source must point at a CSV with a column schema"
        )
    for column in columns_referenced(kpi.source.formula):
        if column not in declared_columns:
            raise KPIDefinitionError(
                f"{kpi.id}: column '{column}' is not declared on "
                f"schemas.yml entry '{kpi.source.locator}'"
            )


def _load_schemas() -> dict:
    global _cached_schemas
    if _cached_schemas is None:
        with open(_SCHEMAS_PATH, "r", encoding="utf-8") as handle:
            _cached_schemas = yaml.safe_load(handle) or {}
    return _cached_schemas


def _locator_method_names() -> set[str]:
    # Inspect the InputLocator class for ``get_*`` methods that take
    # no required positional args beyond ``self`` — those are the
    # ones safely callable from a yml entry. Methods needing extra
    # args (like ``get_export_results_summary_*`` which takes a
    # ``summary_folder``) are flagged explicitly: the resolver will
    # refuse to call them, the registry refuses to register them.
    return {
        name
        for name in dir(InputLocator)
        if name.startswith("get_") and callable(getattr(InputLocator, name))
    }


def kpis_for_feature(feature: str) -> Iterable[KPIDefinition]:
    """Iterate over KPIs whose id starts with ``<feature>.``.

    Filters by id-prefix rather than the ``category`` field so the
    yml's ``category`` is free to carry plot-group keys
    (`lifecycle-emissions`, `cost-breakdown`, etc.) used by the
    picker for visual grouping. Feature membership tracks the file
    each KPI lives in (one file per feature; ids namespaced by
    that feature's name).
    """
    prefix = f"{feature}."
    return (k for k in load_registry().values() if k.id.startswith(prefix))
