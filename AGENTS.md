# Guidelines for LLMs

**Creating new documentation for agents (e.g. AGENTS.md` or `CLAUDE.md`)**:
- **Always** create context-specific documentation as `AGENTS.md` (not `CLAUDE.md`)
- **Always** symlink the new `AGENTS.md` file as `CLAUDE.md` in the same directory
- **Don't create AGENTS.md in every directory** - Only create when the directory contains complex patterns that aren't obvious from code

**When to create AGENTS.md**:
- ✅ **DO create** when the directory has:
  - Complex architectural patterns not obvious from code
  - Critical design decisions that affect how code should be written
  - Non-obvious relationships between components
  - Common pitfalls or important DO/DON'T patterns
  - State management, data flow, or API patterns needing explanation

- ❌ **DON'T create** when:
  - Directory contains simple utility functions
  - Code is self-explanatory with good docstrings
  - It's a small module with straightforward logic
  - Parent directory's AGENTS.md already covers it adequately
  - Would duplicate information already in code/docstrings

**Writing style for AGENTS.md**:
- **Be concise and actionable** - Aim for <150 lines when possible
- **Lead with API signatures** - Show function signatures and return types first
- **Use code examples over prose** - Show DO/DON'T patterns instead of long explanations
- **Focus on patterns, not details** - What to do, not why it exists
- **Scannable structure** - Use headers, bullets, and short paragraphs
- **Reference, don't explain** - Link to related files instead of duplicating information
- **No emoticons in code** - Never add emoji or emoticons to code files, comments, or print statements

**Good example structure**:
```markdown
# Module Name

## Main API
- `function_name(args) → ReturnType` - One-line description

## Key Patterns
### ✅ DO: Pattern name
```code example```

### ❌ DON'T: Anti-pattern name
```code example```

## Related Files
- `file.py` - Purpose
```

**Updating existing agent documentation**:
- **IMPORTANT**: When making code changes in a directory, ALWAYS update the corresponding `AGENTS.md` file in that directory
- If no `AGENTS.md` exists in the directory where you're making changes, create one following the structure above
- Keep documentation synchronized with code changes to help other LLMs understand the current state
- Update immediately after making code changes, not as an afterthought
- **Prune verbose sections** - If AGENTS.md is >200 lines, look for opportunities to condense
- Focus on architectural patterns, state management, data flow, and key concepts that aren't obvious from code alone
- If you need to preserve detailed explanations, move them to a separate `*_GUIDE.md` file for human readers

**Code quality directives**:
- **Avoid code duplication** - If you find yourself writing the same logic in 2+ places during editing:
  - First, search for existing helper functions that do the same thing
  - If none exist, extract the logic into a reusable helper function
  - Place helper functions in an appropriate module (utility file or relevant domain module)
  - Document the helper function with clear docstring explaining when to use it
  - Example: Instead of repeating node name generation logic, use/create `get_next_node_name()`

**Directory-specific AGENTS.md files**:
- `cea/databases/AGENTS.md` - Database structure, COMPONENTS vs ASSEMBLIES
- `cea/analysis/costs/AGENTS.md` - Cost calculation patterns
- `cea/demand/AGENTS.md` - Demand calculations, HVAC vs SUPPLY, output columns
- `cea/interfaces/dashboard/AGENTS.md` - Dashboard job system, worker process
- `cea/technologies/network_layout/AGENTS.md` - Network connectivity, coordinate normalization

---
## Project Overview

City Energy Analyst (CEA) - Urban building energy simulation platform for low-carbon city design.

**Version**: 4.0.0-beta.5 | **Python**: >=3.10 | **License**: MIT

## Environment Setup

**Pixi (Recommended)**:
```bash
pixi install && pixi run setup-dev
pixi run cea dashboard  # Run dashboard
```

**Docker**:
```bash
docker build -t cea .
docker run -p 5050:5050 cea  # Dashboard on port 5050
```

## Core Architecture

**Scenario-Based Workflow**: Work organized around scenarios (folders with `/inputs/`, `/outputs/`)

**Key Components**:
- `InputLocator` (`inputlocator.py`) - File path resolution for scenarios
- `Configuration` (`config.py`) - Typed parameters (PathParameter, BooleanParameter, etc.)
- `scripts.yml` - Script registry with metadata
- `cea.api` - Dynamic script loading and execution

**Database Hierarchy**: `ARCHETYPES → ASSEMBLIES → COMPONENTS` (see `cea/databases/AGENTS.md`)

**Dashboard**: FastAPI + SocketIO job system (see `cea/interfaces/dashboard/AGENTS.md`)

## Key Patterns

### Adding a New Script
1. Create `cea/<module>/script.py` with `main(config: Configuration)`
2. Add entry to `scripts.yml`
3. Auto-registers via `cea.api`

### Using Core APIs

```python
# InputLocator - always use for file paths
from cea.inputlocator import InputLocator
locator = InputLocator(config.scenario)
path = locator.get_zone_geometry()

# Configuration
from cea.config import Configuration
config = Configuration()
scenario = config.scenario

# Running scripts
import cea.api
cea.api.demand(scenario='/path/to/scenario')
```

### Testing
- **All test files**: Place in `cea/tests/` (never in other directories)
- Reference scenarios: `cea/examples/`
- Config: `cea/tests/cea.config`

## Common Pitfalls

1. **File Paths**: Always use `InputLocator` methods, never hardcode
2. **Test Location**: All test files in `cea/tests/` only
3. **Config in Workers**: Don't modify `config` directly; use kwargs or create new instance
4. **Multiprocessing**: Check `config.multiprocessing` before using `Pool`
5. **Scenario Structure**: Respect `/inputs/`, `/outputs/` conventions
6. **Config Type Hints**: After modifying `config.py`, regenerate `config.pyi` by running `pixi run python cea/utilities/config_type_generator.py`
7. **F-strings**: Only use f-strings when string contains variables (e.g., `f"Value: {x}"`). Use regular strings otherwise (e.g., `"No variables"`) to avoid linter warnings

## Module Documentation

For detailed patterns in specific modules, see:
- `cea/databases/AGENTS.md` - Database structure, COMPONENTS vs ASSEMBLIES
- `cea/analysis/costs/AGENTS.md` - Cost calculations
- `cea/demand/AGENTS.md` - Demand simulation, HVAC vs SUPPLY
- `cea/interfaces/dashboard/AGENTS.md` - Job system, worker processes
- `cea/technologies/network_layout/AGENTS.md` - Network connectivity

## Resources

- **Docs**: https://city-energy-analyst.readthedocs.io/
- **Issues**: https://github.com/architecture-building-systems/CityEnergyAnalyst/issues
