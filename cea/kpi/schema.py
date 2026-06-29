"""
Pydantic schema for a KPI definition (one entry in a
``definitions/<feature>.yml`` file).

The yml shape — every entry validates against :class:`KPIDefinition`:

.. code-block:: yaml

    - id: demand.eui_kwh_m2
      label: Energy Use Intensity
      category: demand
      unit: kWh/m²/yr
      better_direction: lower
      headline: true
      info_note: Normalised by gross floor area (GFA).
      source:
        locator: get_total_demand
        formula:
          kind: divide
          numerator:
            kind: aggregate
            op: sum
            of:
              kind: sum_columns
              columns: [E_sys_MWhyr, Qhs_sys_MWhyr, Qcs_sys_MWhyr, Qww_sys_MWhyr]
          denominator:
            kind: aggregate
            op: sum
            of:
              kind: column
              name: GFA_m2
          scale: 1000  # MWh -> kWh

The formula tree is recursive: every leaf produces a
``pandas.Series`` (one value per row of the source CSV), every
inner node consumes one or more children and produces either a
Series or a scalar. The root must yield a scalar — that's the KPI
value.
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, UUEN PTE. LTD."
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class _StrictBase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# ── Formula tree ────────────────────────────────────────────────────


class _ColumnNode(_StrictBase):
    kind: Literal["column"]
    name: str  # column name, validated against schemas.yml at registry load


class _SumColumnsNode(_StrictBase):
    kind: Literal["sum_columns"]
    columns: List[str] = Field(min_length=1)


class _AggregateNode(_StrictBase):
    kind: Literal["aggregate"]
    op: Literal["sum", "max", "min", "mean"]
    of: "FormulaNode"
    # Optional unit-conversion factor applied to the aggregated
    # scalar (e.g. 1000 to convert MWh→kWh or ton→kg without
    # introducing a denominator). Defaults to 1.0 (no-op).
    scale: float = 1.0


class _DivideNode(_StrictBase):
    kind: Literal["divide"]
    numerator: "FormulaNode"
    denominator: "FormulaNode"
    # Optional unit conversion applied to the *result* (e.g. 1000 to
    # convert MWh→kWh when num is in MWh and den is in m²).
    scale: float = 1.0


class _ShareOfNode(_StrictBase):
    kind: Literal["share_of"]
    part: "FormulaNode"
    whole: "FormulaNode"
    # Returns ``part / whole * 100`` so consumers get a percentage
    # already; the unit on the KPI entry should be ``%``.


# Discriminated union over `kind` — pydantic picks the right node
# class by inspecting the literal field, so yml typos surface as
# crisp validation errors instead of silently picking the wrong
# variant.
FormulaNode = Annotated[
    Union[
        _ColumnNode,
        _SumColumnsNode,
        _AggregateNode,
        _DivideNode,
        _ShareOfNode,
    ],
    Field(discriminator="kind"),
]

_AggregateNode.model_rebuild()
_DivideNode.model_rebuild()
_ShareOfNode.model_rebuild()


# ── KPI parameters ──────────────────────────────────────────────────


class KPIParameter(_StrictBase):
    """A user-configurable input the KPI accepts at fetch time.

    Mirrors the shape of map-layer parameter definitions so the
    canvas's step-2 form can render the same primitives (dropdowns,
    text inputs) that already work for the map's
    ``MapLayerPropertiesCard``.

    ``options_generator`` names a Python function (resolved by the
    KPI parameter endpoint) that returns the choice list against the
    active scenario context — e.g. for ``panel_type`` it scans
    ``outputs/data/potentials/solar`` for actual ``PV_*_total.csv``
    files and returns the discovered codes. ``default`` is what the
    canvas pre-selects on first open and what the resolver falls
    back to when no override is supplied.

    ``depends_on`` declares other parameter names this generator
    reads from the user's current draft (e.g. ``phases_for_plan``
    depends on ``plan_name``). The picker watches those keys and
    re-fetches the parameter spec whenever a dependency changes so
    dependent dropdowns stay in sync.
    """

    label: str
    type: Literal["string"] = "string"
    options_generator: Optional[str] = None
    default: Optional[str] = None
    description: Optional[str] = None
    depends_on: List[str] = Field(default_factory=list)


class KPISource(_StrictBase):
    locator: str  # InputLocator method name, e.g. "get_total_demand"
    # Default kwargs forwarded to the locator method when it
    # requires them. Per-card overrides flow through the resolver's
    # ``locator_args_override`` parameter and merge over these
    # defaults (override wins on collisions). KPIs that take no
    # locator arguments omit this field entirely.
    locator_args: Dict[str, Any] = Field(default_factory=dict)
    # User-configurable inputs that the canvas's KPI picker
    # surfaces in step 2. Each parameter's name matches a key in
    # ``locator_args``; a card's saved override fills that key
    # at fetch time. KPIs whose locator_args are fully fixed in
    # the yml (e.g. demand reads ``get_total_demand`` with no
    # parameters) omit this field.
    parameters: Dict[str, KPIParameter] = Field(default_factory=dict)
    formula: FormulaNode


class KPIDefinition(_StrictBase):
    id: str  # globally unique, dotted: "<category>.<short_name>"
    label: str  # human label rendered on the tile
    category: str  # demand, emissions, costs, solar, networks, optimisation
    unit: str  # rendered inline by the frontend's formatter
    better_direction: Literal["lower", "higher", "neutral"] = "neutral"
    headline: bool = False  # surfaces in the OverviewCard ribbon
    info_note: Optional[str] = None  # tooltip body (e.g. GFA caveat)
    description: Optional[str] = None  # longer explainer for hover
    source: KPISource


class KPIDefinitionFile(_StrictBase):
    """Top-level shape of one ``definitions/<feature>.yml`` file."""

    feature: str  # must match the filename stem; double-checked at load
    kpis: List[KPIDefinition] = Field(min_length=1)
