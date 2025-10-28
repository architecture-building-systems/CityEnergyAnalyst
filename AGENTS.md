# CEA Knowledge Base

Detailed documentation is organized by topic. When working in a specific area, refer to the relevant AGENTS.md file.

## Topic-Specific Documentation

- **Database Structure**: `cea/databases/AGENTS.md`
- **Cost Calculations**: `cea/analysis/costs/AGENTS.md`
- **Demand Calculations**: `cea/demand/AGENTS.md`

## Key Concepts

**Database Hierarchy**:
- `ASSEMBLIES/` = Simplified systems (building analysis, single cost values)
- `COMPONENTS/` = Detailed equipment (optimization, size-dependent costs)

**Critical Distinctions**:
- **ASSEMBLIES vs COMPONENTS**: Different purposes, not duplicates
- **HVAC vs SUPPLY**: HVAC = distribution (no costs), SUPPLY = generation (has CAPEX/OPEX)
- **End Use vs Final Energy**: `Q*_sys` = building needs, `GRID_*`/`NG_*` = energy purchased
  - Formula: `Final Energy = End Use / System Efficiency`

**Common Mistakes**:
1. Grid electricity requires TWO files: `SUPPLY_ELECTRICITY.csv` (CAPEX) + `GRID.csv` (OPEX)
2. HVAC costs are NOT tracked separately (included in SUPPLY)
3. ASSEMBLIES and COMPONENTS serve different use cases (not redundant)
4. End use ≠ Final energy (divided by efficiency)

## Important Code Locations

- Cost calculations: `cea/analysis/costs/system_costs.py`
- Demand calculations: `cea/demand/`
- Database schemas: `cea/schemas.yml`

## Documentation Guidelines for LLMs

When creating new documentation files in this codebase:
- **Always** create context-specific documentation as `AGENTS.md` (not `CLAUDE.md`)
- **Always** symlink the new `AGENTS.md` file as `CLAUDE.md` in the same directory
- This maintains consistency with the existing documentation structure where topic-specific instructions live in `AGENTS.md` files and are symlinked for compatibility
