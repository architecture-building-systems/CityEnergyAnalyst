# LCA Standard Coverage (EN 15978)

What CEA's emission phases mean in standard terms, and what is **not** covered. State this
boundary alongside any published result -- a declared scope is what makes an assessment
defensible, not full coverage.

| module | | CEA | source / note |
|---|---|---|---|
| A1-A3 | product (raw material, transport to plant, manufacture) | yes | reported as `production`; derived from `MATERIALS.csv` `GHG_emission_production` (KBOB *Herstellung*) |
| A4 | transport to site | **no** | not modelled |
| A5 | construction / installation | **no** | not modelled |
| B1 | in-use emissions (refrigerant leakage, off-gassing) | **no** | — |
| B2 | maintenance | estimated | `maintenance` phase: a fraction of production (RICS 1%), not a modelled schedule -- see `cea/analysis/lca/AGENTS.md` |
| B3 | repair | estimated | `repair` phase: a fraction of production (RICS 10%), not a modelled schedule -- see `cea/analysis/lca/AGENTS.md` |
| B4 | replacement | yes | envelope re-logged every `Service_Life_*`; supply components on their own `LT_yr`; replacement *quantity* is still the blanket per-GFA intensity |
| B5 | refurbishment | partly | not a module, but district pathways model retrofits explicitly by year |
| B6 | operational energy | yes | hourly, per carrier |
| B7 | operational water | **no** | hot-water *energy* is B6; water supply impact is absent |
| C1 | deconstruction / demolition activity | **no** | the gap behind the `demolition` label -- see below |
| C2-C4 | transport to disposal, waste processing, disposal | yes | reported as `demolition`; derived from `MATERIALS.csv` `GHG_emission_disposal` (KBOB *Entsorgung*) |
| D | benefits beyond the boundary (reuse, recovery, recycling) | **no** | biogenic storage and the PV offset are reported separately, not as module D |

**The `demolition` phase is C2-C4, not C1.** The underlying data is KBOB *Entsorgung* --
transport to the disposal route plus incineration, landfill or recycling processing. The
on-site demolition activity (C1: machinery, site energy) is not included. The name is kept for
continuity with the output columns and plot categories; read it as "end of life".

**Biogenic carbon is not a module.** It is a separate reporting item (RICS PS on Whole Life
Carbon, section 4.11), stored negative throughout. KBOB applies carbon-neutral accounting, so
the stored carbon is not re-released in the C2-C4 figure.
