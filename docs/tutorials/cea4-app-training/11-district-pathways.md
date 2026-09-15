# District Evolution Pathways

An ordinary CEA scenario is a **photograph**: one district, frozen at one moment. A pathway is
a **film**: the same district at 2020, 2030, 2040 and 2050, with buildings appearing,
disappearing and being retrofitted between the frames.

This page builds that idea up slowly, because the feature has a few concepts that only make
sense together.

## Contents

- [The core idea](#the-core-idea)
- [Two things change over time](#two-things-change-over-time)
- [Why interventions target archetypes, not buildings](#why-interventions-target-archetypes-not-buildings)
- [Everything is cumulative](#everything-is-cumulative)
- [Definition vs. materialisation: why "bake" exists](#definition-vs-materialisation-why-bake-exists)
- [The four phases of a state](#the-four-phases-of-a-state)
- [A worked example](#a-worked-example)
- [Workflow](#workflow)
- [Using the Pathway Builder panel](#using-the-pathway-builder-panel)
- [Step by step: your first pathway](#step-by-step-your-first-pathway)
- [Where the files live](#where-the-files-live)
- [Troubleshooting](#troubleshooting)

## The core idea

A pathway belongs to a scenario and holds a series of **states**. Each state is one year, and
each state is a *complete, ordinary CEA scenario on disk*.

```
my_scenario/                      ← the starting photograph
└── pathway "retrofit_2050"
    ├── state_2030   ← a full scenario: inputs/ + outputs/
    ├── state_2040   ← a full scenario: inputs/ + outputs/
    └── state_2050   ← a full scenario: inputs/ + outputs/
```

That last point is what makes the feature tractable: **a state is not a special object.** Once
built, `state_2040` is just a scenario. Every CEA feature that runs on a scenario runs on it,
and the results land where you would expect.

So the pathway itself does only one job: *describe how each year differs from the starting
scenario, and generate the scenarios accordingly.*

### When to use it

- Phasing studies — which buildings connect to a network, and in which year
- Retrofit programmes rolled out progressively across a building stock
- Comparing "business as usual" against an accelerated trajectory
- Any question of the form *"what does this district look like in 2040?"*

If you only need one point in time, use an ordinary scenario. Pathways add bookkeeping you
will not need.

## Two things change over time

A pathway tracks change along two independent axes. Keeping them apart is the single most
useful thing you can do when learning this feature.

| Axis | Question | Recorded as |
|---|---|---|
| **Stock** | *Which buildings exist this year?* | Building events (constructions, demolitions) |
| **Interventions** | *What are those buildings made of?* | Modifications (envelope, systems) |

A building being demolished in 2040 is a **stock** change. Every wall in the district gaining
150 mm of insulation is an **intervention**. They are stored separately, edited separately, and
answer different questions.

### Stock: which buildings exist

Two sources feed the stock:

1. **Derived from your zone data.** Buildings carry a construction year, so CEA already knows
   that a building built in 2035 should not appear in `state_2030`. You do not record this;
   it is inferred.
2. **Explicit building events.** Constructions and demolitions you record for a year, using
   **Create Building Events**.

This is why the timeline sometimes shows a year you never created — see
[stock-only years](#stock-only-years).

### Interventions: what buildings are made of

Recorded as **modifications** on a year, either directly or through a reusable
**intervention template**.

## Why interventions target archetypes, not buildings

This is the part that most often surprises people, and it is worth understanding before you
build anything.

In CEA, buildings do not store their own envelope. They point at an **archetype** (a
construction type), and the archetype holds the wall, roof, floor and window definitions:

```
B1001 ─┐
B1002 ─┼─→ archetype "STANDARD4"  ─→  wall / roof / floor / window definitions
B1003 ─┘
```

So an intervention edits the **archetype**, and every building mapped to it inherits the
change. A recipe is a nested structure of *archetype → component → field*:

```yaml
STANDARD4:                       # archetype (const_type), from construction_types.csv
  wall:                          # component: wall / roof / base / floor
    material_name_1: glass_wool
    thickness_1_m: 0.15
  construction_type:             # direct fields on the archetype row
    type_win: WINDOW_AS4
    supply_type_hs: SUPPLY_HEATING_AS3
```

The values are real database codes: archetypes are `const_type` values, materials are `name`
values from the materials database, and component codes come from the relevant assembly file.

Two consequences follow, and both matter:

**You cannot retrofit one building in isolation** by editing its envelope. Interventions are
archetype-level. To treat a building differently, it needs a different archetype.

**Baking re-runs the Archetypes Mapper.** Since buildings derive their properties from
archetypes, CEA regenerates the per-building property files after modifying the archetype
databases. You do not run the mapper yourself.

Behind the scenes, changing a component does not overwrite the shared envelope row — CEA
creates a *new* envelope row with your values and repoints the archetype at it. Other
archetypes sharing the original are untouched.

## Everything is cumulative

Each state shows the district **as it stands in that year**, not the changes made during it.

Both axes accumulate:

```
        modifications recorded        what state_YYYY actually contains
2030    insulate walls                walls insulated
2040    replace windows               walls insulated + windows replaced
2050    heat pumps                    walls insulated + windows replaced + heat pumps
```

The same applies to stock: a building constructed in 2030 is present in 2040 and 2050 unless
something demolishes it.

**You therefore record only the change, never the running total.** A common mistake is
re-entering the 2030 insulation in the 2040 entry. That is unnecessary, and makes the intent
of each year harder to read.

## Definition vs. materialisation: why "bake" exists

A pathway lives in two places at once, and separating them explains most of its behaviour.

| | The definition | The states |
|---|---|---|
| **What** | A YAML log — years, events, modifications | `state_{year}` scenario folders |
| **Size** | Small; a description of intent | Large; complete input datasets |
| **Created by** | Editing the timeline | **Bake Pathway States** |
| **Cheap to change?** | Yes | No — regenerating costs time |

Editing the timeline changes **only the definition**. Nothing appears on disk until you bake.
This is deliberate: it keeps editing fast, and stops every keystroke from regenerating
gigabytes of input files.

The consequence is the thing to internalise:

> **The definition and the states can disagree.** Edit 2040 after baking it, and the folder
> on disk no longer matches the description that produced it.

Hence validation, below.

## The four phases of a state

Each year sits in one of four phases:

| Phase | Meaning |
|---|---|
| **Defined** | It exists in the definition; nothing on disk yet |
| **Baked** | `state_{year}` has been generated with its input files |
| **Validated** | The baked state has been checked against the current definition |
| **Simulated** | Analyses have run and results exist |

CEA records a **hash** at each phase rather than just a timestamp, so it can tell that a state
has *drifted* — that the definition changed after baking — instead of only knowing the folder
exists.

Two behaviours follow from this, both intentional:

**A simulation stamp is never trusted without results.** Delete a state's `outputs/` and it
reports as no longer simulated, even though it was simulated once. A stamp can outlive its
results — for instance when a cleanup wipes outputs for a re-run that then fails — so the
stamp alone is not accepted as proof.

**Clearing inputs also clears outputs.** Results cannot outlive the inputs that produced them;
an orphaned results folder fails the integrity check. `delete-outputs` alone drops results and
leaves the state baked, which is what you usually want for a re-run.

### Stock-only years

A year implied by construction years in your zone data, with no manual edits of its own.

It appears on the timeline automatically, so you can see the stock changing, but it has no
entry in the definition until you give it one. It is informational, not a mistake, and you can
leave it alone.

## A worked example

A district whose blocks share one archetype, `STANDARD4`. The plan: insulate in 2030, electrify heating in 2040,
and add two new blocks in 2040.

**1. Create the pathway** — `retrofit_2050`, based on the current scenario.

**2. Define the 2030 intervention.** Insulation applies to every block on that archetype, so it belongs in
a template rather than being typed once per year:

```yaml
deep_insulation:
  description: 150 mm glass wool to walls
  modifications:
    STANDARD4:
      wall:
        material_name_1: glass_wool
        thickness_1_m: 0.15
```

Apply it to 2030.

**3. Define 2040.** Apply an `electrify_heating` template, *and* record the two new blocks as
a building event. One is an intervention, the other is stock — different axes, same year.

**4. Bake.** CEA generates `state_2030`, `state_2040` and `state_2050`, each with cumulative
changes: 2040 has insulation *and* heat pumps *and* the new blocks.

**5. Simulate**, then read the years side by side in
[Canvas Builder](12-canvas-builder.md).

**6. Change your mind.** Move electrification to 2045: edit the definition, re-bake. Validation
flags 2040 and 2050 as drifted until you do.

## Workflow

### 1. Create the pathway

**Create District Evolution Pathway** creates the trajectory under the active scenario. Your
zone data supplies the starting stock and the construction years that seed the timeline.

### 2. Define what changes

- **Create Building Events** — constructions and demolitions for a year (*stock*)
- **Define Intervention Template**, then **Apply Intervention Templates to Year** —
  reusable bundles of modifications (*interventions*)

Templates are defined once per scenario and applied to as many years as you like. Applying
several at once merges them, and CEA **refuses to apply templates that overlap**: if two
templates touch the same archetype-component-field, that is reported as a conflict and
nothing is applied.

Note this triggers on the field being touched twice, **not** on the values disagreeing — two
templates setting the same field to the *same* value still conflict. The rule is deliberately
blunt: rather than guess which template should win, CEA asks you to say.

Advanced users can edit a year's raw YAML and persist it with **Save YAML**, which validates
before writing.

### 3. Bake the states

**Bake Pathway States** turns the definition into scenario folders. Nothing can be simulated
before this. Expect it to overwrite the inputs of the states it rebuilds.

### 4. Simulate

**Simulate Pathway** runs the configured simulations across every state, giving results per
year rather than per scenario.

### 5. Keep states honest

- **Validate State** — check one year against the current definition
- **Validate All States** — check every required year; fails if any has drifted

### 6. Clean up

- **Clear State** — one year's data. `delete-outputs` keeps the state baked; `delete-inputs`
  removes the whole folder.
- **Delete Pathway** — an entire pathway, including all baked states.

## Using the Pathway Builder panel

The workflow above names the scripts. In the app you drive nearly all of it from the **Pathway
Builder** panel, opened from the bottom toolbar (marked *BETA*). The panel is not available in
the public demo.

It opens as a card along the bottom of the map. Drag the grey handle at its top edge to resize
it, or use the expand control to take over the window when you are editing a busy timeline.

### Choosing a pathway

The top row selects the pathway. **Create Pathway** starts a new one against the active
scenario; the icons beside the selector duplicate or delete the one you are on. Until a pathway
is selected the rest of the panel is inert and prompts you to *Create or select a Pathway*.

Deleting a pathway removes its baked states with it. That is the point — the states are derived
data — but it is not recoverable from inside the app.

### Reading the timeline

The timeline is the row of year nodes. Each node's fill tells you how far that year has got:

| fill | meaning |
|---|---|
| grey | defined but not baked — nothing to simulate yet |
| blue | **baked** — the state folder exists with its inputs written |
| black | **simulated** — results exist for that state |
| purple | **custom** — the state's inputs were edited directly rather than generated |

Two accents overlay that fill: **amber** where a state has changed since it was baked or
simulated, and **red** where validation found a problem. Both mean the results you can see no
longer match the definition.

Each year also carries a label saying why it is on the timeline:

| label | why the year exists |
|---|---|
| `Auto-Stock` | derived from building construction years in `zone.shp` — you did not create it |
| `Construct-Event` | buildings are added in this year |
| `Demolish-Event` | buildings are removed in this year |
| `Custom-Input` | the state's inputs were edited directly |

`Auto-Stock` years are the ones that surprise people. See [stock-only years](#stock-only-years):
they appear because a building is born that year, and they stay informational until you add
something to them.

### Editing a year

Select a year to open its editor.

- **Create Building Event** — add or remove buildings for that year. This is the *stock* half.
- **Apply Selected Intervention** — apply one or more intervention templates to the year. Pick
  templates in the selector first; the button then reports how many it will apply.
- **Copy State** — seed this year from another one, rather than rebuilding its edits by hand.

Templates are edited and deleted from the same selector. Applying several at once merges them,
and CEA refuses overlapping templates — see [Everything is cumulative](#everything-is-cumulative)
for why, and what counts as an overlap.

A **stock-only** year is locked against intervention edits: it exists only because buildings
appear or disappear in it. If you genuinely want to author interventions there, **Edit anyway**
takes the lock off and the year becomes a normal edited year.

### Baking, simulating and clearing

**Bake** builds the state folders from the definition. **Simulate Pathway** runs the configured
simulations across them. Both report progress through the normal job system, so you can watch
them in the Jobs card.

**Clear State** removes a year's data, and asks what to clear: *inputs*, *outputs*, or both.
Clearing outputs only keeps the state baked, so you can re-simulate without re-baking. **Delete
Log** removes a year's job log.

### When validation complains

Validation issues appear as banners above the timeline, split in two:

- issues on **any** year in the pathway
- issues on the year you currently have selected

Both are warnings rather than blocks — CEA tells you the definition and the baked state have
drifted apart, and leaves it to you to re-bake or accept.

---

## Step by step: your first pathway

A complete run-through, from a scenario that has never seen a pathway to results you can read
side by side. The example insulates one archetype in 2030 and adds two buildings in 2040.

### Before you start

You need a scenario that already works on its own:

- **`zone.shp` must have a `year` column.** Pathways read it to seed the timeline, and refuse to
  start without it.
- **The archetype databases must be loaded**, since interventions are written against archetypes
  rather than buildings.
- **A weather file must be present.** Scenarios created through the app already have one — the
  wizard runs the Weather Helper — so this only bites if you assembled the scenario by hand.

You do *not* need to have run demand or emissions on the base scenario. Simulation runs them
per state.

### 1. Create the pathway

Open **Pathway Builder** from the bottom toolbar, then **Create Pathway** and give it a name —
`retrofit_2050`. It is created against the scenario you have open.

The timeline fills immediately with grey `Auto-Stock` nodes, one per distinct construction year
in `zone.shp`. You did not create these and you do not have to use them; see
[stock-only years](#stock-only-years).

### 2. Define an intervention template

Interventions are reusable bundles, defined once per scenario. Use **Define Intervention
Template** and describe what changes, by archetype and component:

```yaml
deep_insulation:
  description: 150 mm glass wool to walls
  modifications:
    STANDARD4:
      wall:
        material_name_1: glass_wool
        thickness_1_m: 0.15
```

Define the template before you need it — a template is not attached to any year until you apply
it.

### 3. Add the years you care about

Pick the year on the timeline, or add it if it is not there yet.

- **2030** — select the `deep_insulation` template, then **Apply Selected Intervention**.
- **2040** — apply any template for that year *and* use **Create Building Event** to record the
  two new buildings. Interventions and stock are different axes; a year can carry both.

Remember every change is [cumulative](#everything-is-cumulative): 2040 inherits the 2030
insulation without you restating it.

### 4. Bake

**Bake** turns definitions into real scenario folders. Nothing can be simulated before this.

The nodes you baked turn **blue**. Baking overwrites the inputs of the states it rebuilds, so
anything you hand-edited inside a state folder is lost — that is what the purple *custom* state
exists to warn you about.

### 5. Simulate

**Simulate Pathway** runs the whole chain for each state year — radiation, occupancy, demand,
PV where emissions include it, the thermal network where the state needs district services, and
emissions last. It then assembles the pathway emissions timeline.

This is the long step. Nodes turn **black** as each year completes.

Two options are worth knowing:

- **Skip already-simulated states** (on by default) leaves black, up-to-date nodes alone. Stale
  and baked-only nodes are always re-run.
- **Skip custom states** (off by default) leaves purple, hand-edited states out of the automatic
  run — turn it on when you want to simulate those yourself.

### 6. Read the results

Results live per year rather than per scenario, so the ordinary single-scenario plots only show
you one slice. Open **[Canvas Builder](12-canvas-builder.md)** and create a view in
**Pathway (single)** mode: each column becomes one state year, and every card you add is drawn
for all of them at once.

Start with [Your first canvas](12-canvas-builder.md#your-first-canvas).

### 7. Change your mind

Move the electrification to 2045: edit the definition and **Bake** again. Validation flags 2040
and 2050 as drifted until you do, and the affected nodes carry an amber accent — the results on
screen no longer match the definition behind them.

---

## Where the files live

```
outputs/pathways/{pathway_name}/
├── state_2030/          # a full scenario: inputs/ and outputs/
├── state_2040/
└── state_status/        # bake, validation and simulation stamps
```

To point a feature at a state, select the pathway and year in the app rather than browsing to
the folder.

## Troubleshooting

**"The timeline shows a year I never created."**
A [stock-only year](#stock-only-years), derived from building construction years. Informational
until you add edits to it.

**"Validation says the state is out of sync."**
The definition changed after baking. Re-bake that year. This is the
[definition/state split](#definition-vs-materialisation-why-bake-exists) working as intended.

**"A state says it is not simulated, but I ran it."**
Its `outputs/` folder is missing — usually cleared for a re-run that then failed. CEA will not
trust a simulation stamp with no results behind it.

**"Clearing inputs removed my results too."**
Intended. Results cannot outlive their inputs. Use `delete-outputs` to keep the state baked.

**"My retrofit changed buildings I did not intend to change."**
Interventions apply to [archetypes](#why-interventions-target-archetypes-not-buildings), so
every building mapped to that archetype changed. Give the buildings you want to treat
separately their own archetype.

**"I applied two templates and got a conflict error."**
Both touch the same archetype-component-field. This is reported even when they set the same
value — CEA will not pick a winner for you. Split them across different years, or merge the
overlapping part into one deliberate template.

**"Nothing appeared on disk after I edited the timeline."**
Editing changes only the definition. Run **Bake Pathway States**.

**"Changes from an earlier year vanished in a later one."**
They should not — modifications are [cumulative](#everything-is-cumulative). Check that the
earlier year is still in the definition and has itself been re-baked.

## Related Features

- **[Data Management](08-data-management.md)** - Preparing the zone data that seeds the stock
- **[Life Cycle Analysis (LCA)](06-0-life-cycle-analysis.md)** - Emissions per state year
- **[Canvas Builder](12-canvas-builder.md)** - Compare pathway years side by side

---

[← Back: Visualisation](10-visualisation.md) | [Back to Index](index.md) | [Next: Canvas Builder →](12-canvas-builder.md)
