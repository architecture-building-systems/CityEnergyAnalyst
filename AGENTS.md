# Guidelines for LLMs

**Creating new documentation**:
- **Always** create context-specific documentation as `AGENTS.md` (not `CLAUDE.md`)
- **Always** symlink the new `AGENTS.md` file as `CLAUDE.md` in the same directory
- This maintains consistency with the existing documentation structure where topic-specific instructions live in `AGENTS.md` files and are symlinked for compatibility

**Updating existing documentation**:
- Update the relevant `AGENTS.md` file when you make changes to code in that directory
- Keep documentation synchronized with code changes to help other LLMs understand the current state
- Focus on architectural patterns, state management, data flow, and key concepts that aren't obvious from code alone

---
## Project Overview

City Energy Analyst (CEA) is an urban building energy simulation platform for designing low-carbon cities. It combines urban planning and energy systems engineering to analyze building energy demand, renewable energy potential, thermal networks, and optimization strategies.

**Version**: 4.0.0-beta.5
**Python**: >=3.10
**License**: MIT

## Development Environment Setup

### Using Pixi (Recommended)

```bash
# Install dependencies and setup dev environment
pixi install
pixi run setup-dev

# Run the dashboard
pixi run cea dashboard
```

### Using Conda/Mamba (Alternative)

```bash
# Create environment from lock file
conda install --file conda-lock.yml
pip install -e .
```

### Docker

```bash
# Build image
docker build -t cea .

# Run dashboard (exposed on port 5050)
docker run -p 5050:5050 cea

# Run worker
docker run cea cea-worker <job_id> <server_url>
```

## Common Commands

### CLI Entry Points

- **`cea`** - Main CLI interface for running scripts
- **`cea-config`** - Configuration management
- **`cea-doc`** - Documentation utilities
- **`cea-dev`** - Development tools
- **`cea-worker`** - Background job worker process
- **`cea-plot`** - Plotting utilities

### Testing

```bash
# Run integration tests
pixi run test
# or: cea test --type integration

# Run unit tests with coverage
pixi run coverage
# or: pytest --cov=cea cea/tests/

# Run single test file
pytest cea/tests/test_calc_thermal_loads.py

# Run single test function
pytest cea/tests/test_calc_thermal_loads.py::test_calc_thermal_loads
```

### Linting & Building

```bash
# Lint and auto-fix
pixi run lint
# or: ruff check --fix .

# Build wheel
pixi run build-wheel
# or: uv build

# Export conda environment
pixi run export-conda
```

### Running Scripts

```bash
# Run a CEA script (e.g., demand calculation)
cea demand --scenario path/to/scenario

# Run with custom config
cea demand --config path/to/config.config

# List available scripts
cea --help
```

## Architecture

### High-Level Structure

```
cea/
├── api.py                  # Script registry and lazy-loading wrapper
├── config.py               # Configuration management
├── inputlocator.py         # File path resolution for scenarios
├── scripts.yml             # Script definitions and metadata
├── schemas.yml             # Database schemas and validation
├── worker.py               # Background job worker with signal handling
├── analysis/               # Analysis scripts (costs, etc.)
├── databases/              # Archetype data (construction types, HVAC, etc.)
├── datamanagement/         # Data import/export and weather
├── demand/                 # Building energy demand simulation
├── interfaces/
│   ├── cli/                # Command-line interface
│   └── dashboard/          # FastAPI web dashboard
├── optimization/           # Legacy optimization module
├── optimization_new/       # New optimization implementation
├── plots/                  # Plotting and visualization
├── resources/              # Solar radiation and other resources
├── technologies/           # HVAC, networks, solar technologies
├── tests/                  # Test suite
├── utilities/              # Shared utilities
├── visualisation/          # Geographic visualizations
└── workflows/              # Pre-defined workflow definitions
```

### Core Concepts

**Scenario-Based Workflow**: CEA organizes work around "scenarios" - a folder structure containing:
- Input data: `/inputs/` (zone geometry, building properties, databases)
- Output data: `/outputs/` (demand results, network layouts, optimization results)

**InputLocator**: Central class (`cea/inputlocator.py`) that resolves file paths within scenarios using conventions. All scripts use this to locate inputs/outputs.

**Script System**: Scripts are defined in `scripts.yml` with metadata (parameters, input files, interfaces). The `cea.api` module dynamically registers all scripts as callable functions using lazy loading.

**Configuration**: `cea.config.Configuration` manages parameters from `default.config`. Parameters are typed (PathParameter, BooleanParameter, etc.) and can be overridden via CLI, config files, or environment variables.

### Dashboard Architecture

**Stack**: FastAPI + SQLModel + SocketIO + Redis (optional caching)

**Job System** (see `cea/interfaces/dashboard/AGENTS.md` for details):
- **Server** (`cea/interfaces/dashboard/server/jobs.py`): Manages job lifecycle, database, SocketIO events
- **Worker** (`cea/worker.py`): Separate subprocess executing CEA scripts
- **Communication**: Worker POSTs to server HTTP endpoints; server emits SocketIO events to clients

**Job States**: `PENDING → STARTED → SUCCESS/ERROR/CANCELED/KILLED`

**Worker Process**:
1. Spawned by server: `python -m cea.worker --suppress-warnings {job_id} {server_url}`
2. Fetches job details via GET `/jobs/{job_id}`
3. Redirects stdout/stderr to stream capture (POSTs to `/streams/write/{job_id}`)
4. Executes script: `cea.api.{script_name}(**parameters)`
5. Reports completion: POST `/jobs/success/{job_id}` or `/jobs/error/{job_id}`

**Signal Handling**: Worker registers `SIGTERM`/`SIGINT` handlers for graceful shutdown. Raises `SystemExit(0)` to trigger cleanup in finally block. Critical for Docker deployments (combined with tini init system).

**Docker Deployment**: Uses `tini` as PID 1 init system for proper signal forwarding and zombie process reaping.

### Database Structure

CEA uses hierarchical CSV databases in `cea/databases/`:

**ARCHETYPES Layer** (`CONSTRUCTION_TYPES.csv`, `USE_TYPES.csv`):
- Construction types map to envelope systems (walls, roofs, windows) and HVAC systems
- Use types define occupancy, setpoints, and energy intensity

**ASSEMBLIES Layer** (Envelope, HVAC, Supply systems):
- `ENVELOPE_WALL/ROOF/WINDOW.csv`: U-values, thermal properties
- `HVAC_HEATING/COOLING.csv`: System capacities, convection types
- `SUPPLY_HEATING/COOLING/HOTWATER.csv`: Equipment references, efficiencies, costs

**COMPONENTS Layer** (`BOILERS.csv`, `CHILLERS.csv`, `HEAT_PUMPS.csv`):
- Equipment specifications: capacities, efficiencies, CAPEX

Buildings reference construction/use types → Archetypes reference assemblies → Assemblies reference components.

See `docs/developer/DATABASE_SCHEMA.md` for detailed relationships.

## Key Patterns

### Adding a New Script

1. Create module in appropriate directory (e.g., `cea/demand/new_script.py`)
2. Define `main(config: Configuration)` function
3. Add entry to `scripts.yml` with metadata (name, module, parameters, input-files)
4. Script auto-registers via `cea.api.register_scripts()`

### Using InputLocator

```python
from cea.inputlocator import InputLocator

locator = InputLocator(config.scenario)
zone_geometry = locator.get_zone_geometry()  # Returns path
demand_results = locator.get_total_demand()  # Returns path
```

Methods are defined in `InputLocator` class or dynamically added from `schemas.yml`.

### Configuration Access

```python
from cea.config import Configuration

config = Configuration()
scenario = config.scenario  # Access parameter
multiprocessing = config.multiprocessing

# Temporarily restrict to specific parameters
with config.temp_restrictions(['general:scenario', 'demand']):
    # Only these parameters are active
    pass
```

### Running Scripts Programmatically

```python
import cea.api

config = cea.api.Configuration()
config.scenario = '/path/to/scenario'

# Run demand calculation
cea.api.demand(config)

# Or with kwargs (overrides config)
cea.api.demand(scenario='/path/to/scenario')
```

### Adding Dashboard Job Endpoints

1. Update job state in database (with row-level locking if needed)
2. Cleanup resources (streams, processes, temp files)
3. `await session.commit()` **before** emitting SocketIO
4. Emit SocketIO events outside try-except to prevent rollback

### Testing

- Integration tests use reference scenarios from `cea/examples/`
- Test configuration: `cea/tests/cea.config`
- Mock/fixture pattern for expensive operations (radiation, optimization)

**Subdirectory Documentation**:
- `cea/databases/AGENTS.md` - Database structure and relationships
- `cea/analysis/costs/AGENTS.md` - Cost calculation architecture
- `cea/demand/AGENTS.md` - Demand simulation patterns
- `cea/interfaces/dashboard/AGENTS.md` - Job system architecture (detailed)

## Common Pitfalls

1. **File Paths**: Always use `InputLocator` methods, never hardcode paths
2. **Multiprocessing**: Check `config.multiprocessing` and use `multiprocessing.Pool` with `config.get_number_of_processes()`
3. **Config Mutations**: Don't modify `config` object directly in workers; use kwargs or create new instance
4. **Missing Input Files**: Scripts check `cea_script.missing_input_files(config)` before execution
5. **Docker Signal Handling**: Worker must handle `SIGTERM`/`SIGINT` for graceful shutdown; always use tini as init
6. **Scenario Structure**: Respect scenario folder conventions (inputs/, outputs/), use InputLocator for paths
7. **Database Regions**: Some databases are region-specific (CH, SG, etc.); use `config.region` to select

## External Dependencies

- **pythonocc-core**: 3D CAD kernel (pinned to 7.8.1, conda-only)
- **wntr**: Water network modeling (no osx-arm64 conda build, use pip)
- **DAYSIM**: External solar radiation engine (binary in `cea/resources/radiation/`)
- **CRAX**: Alternative solar model (experimental, beta)

## Resources

- **Documentation**: https://city-energy-analyst.readthedocs.io/
- **Website**: https://www.cityenergyanalyst.com/
- **Issues**: https://github.com/architecture-building-systems/CityEnergyAnalyst/issues
- **Zenodo DOI**: 10.5281/zenodo.14903253
