Dependency Management Strategy
==============================

Overview
--------

City Energy Analyst (CEA) uses a dual dependency management approach combining:

1. **Standard Python dependencies** in ``pyproject.toml`` for pip/PyPI compatibility
2. **Pixi dependencies** for optimized conda-forge builds and development environment

This document explains the rationale, organization, and maintenance guidelines for CEA's dependency structure.

Background
----------

CEA is a scientific computing application that relies heavily on:

- Geospatial libraries (GDAL, Shapely, GeoPandas)
- Scientific computing stack (NumPy, SciPy, Matplotlib)
- System-level dependencies with native compiled code
- Pure Python web framework dependencies

The challenge is balancing:

- **Performance**: Optimized conda-forge builds for scientific packages
- **Compatibility**: Standard PyPI distribution for pip users
- **Development**: Unified environment management with system dependencies

Solution: Dual Declaration Strategy
-----------------------------------

Based on analysis of package compilation status and Pixi's conda-first resolution, we use a strategic dual declaration approach.

Dependency Categories
---------------------

1. Runtime Dependencies in Both Sections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Location**: ``[project.dependencies]`` AND ``[tool.pixi.dependencies]``

**Rationale**: These are packages that:

- Are required for CEA to function
- Have optimized conda-forge builds with compiled code
- Benefit from native compilation performance

**Examples**:

.. code-block:: toml

   # In [project.dependencies] - for pip users
   "numpy<2",
   "scipy", 
   "matplotlib",
   "geopandas",
   "shapely",
   
   # In [tool.pixi.dependencies] - conda-forge optimized builds
   numpy = "<2"
   scipy = "*"
   matplotlib = "*"
   geopandas = "*"
   shapely = "*"

**Packages in this category**:

- **Core scientific stack**: numpy, scipy, matplotlib, scikit-learn, numba, pyarrow
- **Geospatial**: geopandas, shapely, networkx
- **Compiled bindings**: pythonocc-core (C++ OpenCASCADE bindings)
- **Optional compiled extensions**: pvlib (C extensions for solar calculations)
- **System utilities**: pyyaml, psutil

2. Pure Python (Dependency Resolution Only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Location**: ``[project.dependencies]`` AND ``[tool.pixi.dependencies]``

**Rationale**: Pure Python packages kept in both sections for:

- Unified dependency resolution across the scientific stack
- Version consistency with compiled dependencies
- Simplified maintenance

**Examples**:

.. code-block:: toml

   # Pure Python packages (conda-forge for unified dependency resolution)
   libpysal = "*"
   osmnx = "*"

**Analysis basis**: These packages were analyzed and found to be pure Python with no compiled extensions, but benefit from conda-forge's dependency management.

3. PyPI-Only Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~

**Location**: ``[project.dependencies]`` ONLY

**Rationale**: Pure Python packages without conda-forge optimization benefits:

- Web framework dependencies (FastAPI, Uvicorn, Pydantic)
- Database adapters (SQLAlchemy, AsyncPG)
- Pure Python utilities

**Examples**:

.. code-block:: toml

   # Backend dependencies (PyPI only)
   "fastapi",
   "uvicorn", 
   "pydantic-settings",
   "sqlalchemy[asyncio]",

4. System Dependencies (Pixi-Only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Location**: ``[tool.pixi.dependencies]`` ONLY

**Rationale**: System-level libraries with complex native dependencies:

- Require system libraries (GDAL, GEOS, PROJ)
- Not needed for basic CEA functionality
- Development or optional features

**Examples**:

.. code-block:: toml

   # System dependencies with native libraries (fetch from conda-forge)
   cvxopt = "*"  # For wntr
   fiona = "*"   # GDAL wrapper
   gdal = "*"    # Geospatial system library

5. Development Tools (Pixi-Only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Location**: ``[tool.pixi.dependencies]`` ONLY

**Rationale**: Development and build tools not needed for runtime:

**Examples**:

.. code-block:: toml

   # Development tools (pixi-only)
   notebook = "*"
   pixi-pycharm = ">=0.0.8,<0.0.9"  # for pycharm support
   rattler-build = "*"               # for conda package building

How Pixi Resolves Dependencies
------------------------------

Pixi uses a **conda-first approach**:

1. **Conda packages installed first**: All ``[tool.pixi.dependencies]`` are resolved
2. **Conda-to-PyPI mapping**: Conda packages are mapped to their PyPI equivalents
3. **PyPI gap filling**: Only PyPI packages not available via conda are installed from PyPI
4. **Priority**: When a package exists in both conda and PyPI, conda version is used

This means:

- Scientific packages get optimized conda-forge builds
- Pure Python packages can come from either source
- No conflicts between conda/PyPI versions of the same package

For detailed information on how Pixi handles dependency resolution with ``pyproject.toml``, see the official documentation: https://pixi.sh/latest/python/pyproject_toml/#dependency-section

Package Analysis Methodology
-----------------------------

To determine the correct category for each package, we analyzed:

1. **Compiled Code**: Does the package contain C/C++/Fortran extensions?
2. **Performance Benefits**: Does conda-forge provide optimized builds?
3. **Dependencies**: Does it depend on system libraries?
4. **Usage Pattern**: Runtime required vs development tool?

Example Analysis Results
~~~~~~~~~~~~~~~~~~~~~~~~

**pythonocc-core**:
  - **Status**: Extensive C++ bindings to OpenCASCADE
  - **Category**: Runtime + Optimized (both sections)
  - **Rationale**: True compiled package with significant performance benefits

**osmnx**:
  - **Status**: Pure Python (100% Python code)
  - **Category**: Runtime + Dependency Resolution (both sections)  
  - **Rationale**: No compiled code, but benefits from unified geospatial dependency management

**gdal**:
  - **Status**: System library with complex native dependencies
  - **Category**: System dependency (pixi-only)
  - **Rationale**: Not required for basic CEA functionality, complex system integration

Maintenance Guidelines
----------------------

Adding New Dependencies
~~~~~~~~~~~~~~~~~~~~~~~

When adding a new dependency, follow this decision tree:

1. **Is it required for CEA runtime?**
   
   - Yes → Add to ``[project.dependencies]``
   - No → Consider if it's a development tool

2. **Does it have compiled code or optimized conda-forge builds?**
   
   - Yes → Also add to ``[tool.pixi.dependencies]``
   - No → Consider dependency resolution benefits

3. **Is it a system library or development tool?**
   
   - Yes → Add only to ``[tool.pixi.dependencies]``

4. **Does it benefit from unified scientific stack dependency resolution?**
   
   - Yes → Add to both sections with appropriate comment
   - No → Keep in ``[project.dependencies]`` only

Version Synchronization
~~~~~~~~~~~~~~~~~~~~~~~

When updating versions:

1. **Both sections**: Update version constraints in both places simultaneously
2. **Comments**: Keep explanatory comments synchronized
3. **Testing**: Test both pip and pixi installations after changes

Example Workflow
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Test pip installation (uses PyPI versions)
   pip install -e .
   
   # Test pixi installation (uses conda-forge optimized versions)  
   pixi install
   pixi run cea --help

Documentation Updates
~~~~~~~~~~~~~~~~~~~~~

When modifying dependencies:

1. Update this documentation if categorization logic changes
2. Update comments in ``pyproject.toml`` to reflect current rationale
3. Consider impact on installation documentation

File Structure
--------------

The dependency configuration is organized as follows:

.. code-block:: toml

   [project]
   dependencies = [
       # Scientific/geospatial packages (optimized conda builds available)
       # Duplicated below in [tool.pixi.dependencies] - update both when needed
       "numpy<2",
       "scipy",
       # ... other runtime dependencies
       
       # Backend dependencies (PyPI only)
       "fastapi",
       "uvicorn",
       # ... web framework dependencies
   ]
   
   [tool.pixi.dependencies]
   # Scientific/geospatial packages (also in main dependencies - conda-forge preferred)
   # Duplicate of above in [project.dependencies] - update both when needed
   numpy = "<2"
   scipy = "*"
   pythonocc-core = "*"  # C++ bindings to OpenCASCADE
   pvlib = "*"           # has optional C extensions for solar calculations
   
   # Pure Python packages (conda-forge for unified dependency resolution)
   libpysal = "*"
   osmnx = "*"
   
   # System dependencies with native libraries (fetch from conda-forge)
   cvxopt = "*"  # For wntr
   fiona = "*"
   gdal = "*"
   
   # Development tools (pixi-only)
   notebook = "*"
   pixi-pycharm = ">=0.0.8,<0.0.9"
   rattler-build = "*"

Benefits of This Approach
-------------------------

**For Developers**:
- Optimized performance with conda-forge scientific packages
- Unified development environment management
- Clear separation of concerns

**For Users**:
- Standard pip installation works out of the box
- All runtime dependencies clearly declared
- Compatible with existing Python packaging tools

**For Maintainers**:
- Clear categorization reduces confusion
- Documented rationale for dependency decisions
- Consistent approach for future additions

**Performance Benefits**:
- Scientific packages use optimized BLAS/LAPACK
- Compiled extensions from conda-forge
- Consistent ABI across scientific stack

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Version Conflicts**:
  If you encounter version conflicts, check that:
  
  - Both sections have consistent version constraints
  - Pixi's lock file is up to date (``pixi update``)

**Missing Dependencies**:
  If a package is missing:
  
  - Check if it should be in both sections
  - Verify it's not a system dependency that needs conda-forge
  - Consider if it's missing from the correct category

**Performance Issues**:
  If scientific computations are slow:
  
  - Verify pixi is using conda-forge versions (``pixi list``)
  - Check that optimized packages are in both sections
  - Ensure BLAS/LAPACK are properly linked

Future Considerations
---------------------

This dependency strategy should be reviewed when:

1. **Pixi evolves**: New features might change optimal practices
2. **Package ecosystem changes**: New optimized builds become available
3. **CEA architecture changes**: New types of dependencies are introduced
4. **Performance requirements change**: Different optimization priorities

The current approach balances performance, compatibility, and maintainability based on CEA's needs as of 2025. Future updates should maintain these principles while adapting to ecosystem changes.