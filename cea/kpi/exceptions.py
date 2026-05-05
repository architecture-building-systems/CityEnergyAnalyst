"""KPI-feature exceptions."""

from __future__ import annotations

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class KPIError(Exception):
    """Base class for KPI-feature errors."""


class KPIDefinitionError(KPIError):
    """A KPI yml entry is malformed or references something that
    doesn't exist (unknown locator key, unknown column, calc kind
    the resolver can't dispatch). Raised at registry load — never
    at request time."""


class KPINotAvailable(KPIError):
    """The KPI is well-defined but cannot be computed for this
    scenario right now — usually because the upstream tool that
    produces its source CSV hasn't run yet, or the CSV is missing
    a required column. The endpoint catches this and returns the
    KPI with ``available: false`` rather than a 500.
    """

    def __init__(
        self,
        kpi_id: str,
        *,
        reason: str,
        upstream_tool: str | None = None,
        missing_file: str | None = None,
    ):
        super().__init__(f"{kpi_id}: {reason}")
        self.kpi_id = kpi_id
        self.reason = reason
        self.upstream_tool = upstream_tool
        self.missing_file = missing_file
