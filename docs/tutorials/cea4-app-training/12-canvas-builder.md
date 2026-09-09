# Canvas Builder

Canvas Builder is a side-by-side comparison workspace. You choose what the **columns** mean —
different scenarios, different what-if variants, or different years of a pathway — then place
cards (plots, KPIs, maps, notes) that are drawn for every column at once.

It is the answer to "I have run the same analysis four ways; now show me the difference."

## When to use it

- Comparing design alternatives held in sibling scenarios
- Comparing supply what-ifs within one scenario
- Reading a pathway year by year
- Assembling a small report page for a meeting

For a single scenario's results, the ordinary [Visualisation](10-visualisation.md) plots are
quicker. Canvas earns its keep the moment you need two or more things beside each other.

## The four comparison modes

| Mode | Columns are… | Typical question |
|---|---|---|
| **Inter-scenario** | Sibling scenarios in the project | "Which masterplan performs best?" |
| **Inter-what-if** | What-if variants under one scenario | "Gas boiler vs heat pump?" |
| **Pathway (single)** | State years of one pathway | "How does the district evolve to 2050?" |
| **Pathway (multi)** | Several pathways | "Business-as-usual vs accelerated retrofit" |

The mode is chosen when you create the view and decides what a column can point at. Cards are
shared across columns, so adding one plot adds it everywhere — that is what keeps the
comparison honest.

## Card types

| Card | Shows |
|---|---|
| **Plot** | Any CEA plot, drawn per column with that column's data |
| **KPI** | A strip of headline numbers |
| **Map** | A geographic layer |
| **Text** | Free-form notes, per column |
| **Divider** | A visual separator, mirrored across columns |

Cards are placed on a free-form grid, so you can drag and resize them into a layout that reads
the way you want.

## KPIs

Canvas draws on a KPI registry covering nine domains:

| Domain | KPIs | Domain | KPIs |
|---|---|---|---|
| Architecture | 4 | Heat rejection | 3 |
| Costs | 3 | Networks | 8 |
| Demand | 3 | Optimisation | 2 |
| Emissions | 2 | Solar | 4 |
| Final energy | 5 | | |

A KPI is computed on demand from the results already on disk. If the feature behind it has not
been run for that column, the KPI reports as unavailable rather than showing a misleading zero.

## Comparing fairly: y-axis alignment

By default each plot scales to its own data, which makes two columns look similar even when
their magnitudes differ by an order of magnitude. Canvas can **align the y-axis** across
columns that share a slot, so the bars are drawn to one common scale.

Turn this on before drawing conclusions from bar heights. It is the single most common source
of misread comparisons in a side-by-side layout.

## Workflow

1. Open **Canvas** from the app navigation.
2. Create a view and pick one of the four comparison modes.
3. Choose what each column points at — scenarios, what-ifs, or pathway years.
4. Add cards. Each is drawn for every column.
5. Enable y-axis alignment where you are comparing magnitudes.
6. Arrange, resize, and annotate with text cards.

## Common issues

**"A column is empty."** The feature behind the card has not been run for that column's
scenario, what-if, or pathway year. Canvas reads existing results; it does not run analyses.

**"A KPI shows as unavailable."** Same cause — the underlying results are missing. This is
deliberate: an absent result is reported, never substituted with zero.

**"Two columns look identical but the numbers differ."** Y-axis alignment is off, so each plot
is using its own scale. Turn it on.

**"What-if columns are missing."** What-ifs come from the parent scenario. Run
[Final Energy](06-1-final-energy.md) first — it creates the what-if that the other LCA
features and their KPIs read.

## Related Features

- **[Visualisation](10-visualisation.md)** - The individual plots Canvas arranges
- **[Life Cycle Analysis (LCA)](06-0-life-cycle-analysis.md)** - Produces most comparison KPIs
- **[District Evolution Pathways](11-district-pathways.md)** - Supplies the pathway modes

---

[← Back: District Evolution Pathways](11-district-pathways.md) | [Back to Index](index.md)
