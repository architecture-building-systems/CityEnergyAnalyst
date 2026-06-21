"""
KPI feature — preset Key Performance Indicators surfaced in the
Canvas Builder and the OverviewCard ribbon.

Layout:

* ``definitions/<feature>.yml`` — declarative KPI catalogue, one
  yml per feature (demand, emissions, costs, solar, networks,
  optimisation). Each entry references a locator key from
  ``cea/schemas.yml`` plus the columns that the KPI's formula
  consumes.
* ``schema.py`` — the Pydantic model that every yml entry validates
  against.
* ``registry.py`` — loads the yml files at import time, validates
  each entry against ``schema.py`` and the schemas.yml column
  registry, returns the frozen ``dict[id, KPIDefinition]``.
* ``calculators.py`` — the primitive operations that the formula
  trees in yml dispatch to (``sum_columns``, ``divide``, …).
* ``resolver.py`` — ``compute_kpi(kpi_id, scenario, whatif=None)``
  reads the source CSV, walks the formula tree, returns a
  ``KPIResult``.
* ``exceptions.py`` — ``KPINotAvailable`` (the upstream tool hasn't
  run), ``KPIDefinitionError`` (the yml is malformed).

Custom KPI authoring is intentionally out of scope; the catalogue
ships fixed and is extended by adding entries to the yml files.
"""

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"
