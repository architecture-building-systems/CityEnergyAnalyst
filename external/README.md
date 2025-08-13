# CEA External Tools

**A standalone Python package containing compiled C++ tools for the City Energy Analyst (CEA).**

This package provides pre-compiled binary executables for radiation calculations and urban energy modeling, including DAYSIM (daylighting simulation) and CRAX (City Radiation Accelerator). 

By separating these computationally intensive C++ components into their own package, we enable faster CEA installations and reduce build complexity.

## Installation

```bash
pip install cea-external-tools
```

## Usage

```python
import cea_external_tools

# Get path to binary tools
bin_path = cea_external_tools.get_bin_path()
print(f"External tools located at: {bin_path}")
```

## Package Contents

This package includes compiled binaries for:
- **DAYSIM** - Advanced daylighting simulation tools
- **CRAX** - Fast urban radiation calculation engine

---

## Development & Build Configuration

This directory contains the CMake configuration for building external tools required by the City Energy Analyst (CEA).

## Structure

The build system has been modularized into separate configuration files:

- **`CMakeLists.txt`** - Main build configuration file
- **`DaysimConfig.cmake`** - DAYSIM-specific configuration and build logic  
- **`CraxConfig.cmake`** - CRAX-specific configuration and build logic

## Components

### DAYSIM
Daylighting simulation tool that provides various radiation calculation utilities.

**Executables built:**
- `ds_illum` - Illuminance calculation
- `epw2wea` - Weather file conversion  
- `gen_dc` - Daylight coefficient generation
- `oconv` - Octree conversion
- `radfiles2daysim` - Radiance file conversion
- `rtrace_dc` - Ray tracing for daylight coefficients

### CRAX
City Radiation Accelerator for fast urban radiation simulations.

**Executables built:**
- `radiation` - Main radiation calculation engine
- `mesh-generation` - 3D mesh generation utility

## Build Options

You can control which components to build using CMake options:

```bash
# Build both components (default)
cmake -DBUILD_DAYSIM=ON -DBUILD_CRAX=ON ..

# Build only DAYSIM
cmake -DBUILD_DAYSIM=ON -DBUILD_CRAX=OFF ..

# Build only CRAX  
cmake -DBUILD_DAYSIM=OFF -DBUILD_CRAX=ON ..
```

## CRAX-specific Options

CRAX has additional configuration options for Python wheel builds:

- `CRAX_USE_DYNAMIC_ARROW` (default: ON) - Enable dynamic Arrow linking to save space in wheels
- `CRAX_USE_AUTOMATED_DEPENDENCIES` (default: ON) - Use automated dependency fetching

## Source Configuration

Both tools support local source directories or automatic fetching from GitHub:

### DAYSIM
- `DAYSIM_SOURCE_DIR` - Path to local DAYSIM source (default: `./daysim`)
- `DAYSIM_GIT_REPOSITORY` - Git repository URL (default: `https://github.com/reyery/Daysim.git`)
- `DAYSIM_GIT_TAG` - Git tag/branch to use

### CRAX
- `CRAX_SOURCE_DIR` - Path to local CRAX source (default: `./crax`)
- `CRAX_GIT_REPOSITORY` - Git repository URL (default: `https://github.com/wanglittlerain/CityRadiation-Accelerator-CRAX-V1.0.git`)
- `CRAX_GIT_TAG` - Git tag/branch to use

## Installation

The built executables are installed to the CEA resources directory:
- CRAX tools: `cea_external_tools/bin`

## Build Targets

The build system includes a custom target `cea_all` that builds all required CEA components:

```bash
# Configure build
cmake -B build -S .

# Build all CEA targets (recommended)
cmake --build build --target cea_all

# Or build all targets
cmake --build build

# Install to CEA resources
cmake --install build
```

## Compiler Warnings

The build system automatically suppresses common warnings for cleaner output:
- GNU/Clang: Suppresses missing prototypes, unused variables, sign comparison, and deprecated declarations
- MSVC: Suppresses warning C4127 to prevent build failures on Windows
