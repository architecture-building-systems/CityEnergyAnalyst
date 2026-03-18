# C/C++ Binary Compilation Guide for CEA

> **Note**: Binary management for DAYSIM and CRAX is now handled by the `cea-external-tools` package. The source code for building these binaries can be found in the `external/` directory. This document is kept as a historical reference for the compilation strategies.

This document outlines strategies for integrating DAYSIM and CRAX C++ binaries into CEA's Python wheel distribution.

## Current CEA Integration Status

### DAYSIM Integration
- CEA expects pre-compiled binaries in `cea/resources/radiation/bin/{platform}/`
- Detection logic in `daysim.py:32-158` searches for required binaries
- Required binaries: `{"ds_illum", "epw2wea", "gen_dc", "oconv", "radfiles2daysim", "rtrace_dc"}`
- Required libraries: `{"rayinit.cal", "isotrop_sky.cal"}`

### CRAX Integration  
- CEA calls CRAX executables through `CRAXModel.py`
- Expects executables available via configuration
- Binaries placed in `cea/resources/radiationCRAX/bin/`

## Python Wheels Overview

**Wheels** are pre-compiled `.whl` files containing everything needed for fast installation:
- **Fast installation** - no compilation step needed
- **Platform-specific** - can include compiled C/C++ code for specific OS/architecture  
- **Dependency bundling** - can include shared libraries and binaries

## Build System Analysis

### DAYSIM (https://github.com/reyery/Daysim)
- **Build System**: CMake
- **Platform Support**: Windows (VS2013), Mac (XCode) - testing incomplete
- **Dependencies**: Optional Qt5 for rvu program
- **Special Notes**: Some programs require manual CMakeLists.txt intervention

### CRAX (https://github.com/wanglittlerain/CityRadiation-Accelerator-CRAX-V1.0)  
- **Build System**: CMake
- **Platform Support**: Windows (VS2022), Linux (GCC 13)
- **Dependencies**: Apache Arrow, thirdparty.rar contents
- **Build Scripts**: `build.bat` (Windows), `build.sh` (Linux)

## Integration Strategies

### Option 1: Conda-First Approach (Recommended for CEA)

Create separate conda packages for the binaries:

```yaml
# meta.yaml for conda-forge
requirements:
  build:
    - {{ compiler('c') }}
    - {{ compiler('cxx') }}
    - cmake
    - make  # [unix]
  host:
    - python
    - apache-arrow-cpp  # for CRAX
    - qt5-main  # [optional, for DAYSIM rvu]
  run:
    - python
    - daysim-binaries  # separate conda package
    - crax-binaries    # separate conda package
```

### Option 2: Wheel with Bundled Binaries

```python
# setup.py additions
from setuptools import setup
import subprocess
import os

def build_external_tools():
    """Build DAYSIM and CRAX during wheel creation"""
    
    # Build DAYSIM
    subprocess.run(['git', 'clone', 'https://github.com/reyery/Daysim.git', 'daysim_src'])
    os.chdir('daysim_src')
    subprocess.run(['cmake', '-B', 'build', '-DCMAKE_BUILD_TYPE=Release'])
    subprocess.run(['cmake', '--build', 'build', '--config', 'Release'])
    
    # Build CRAX  
    subprocess.run(['git', 'clone', 'https://github.com/wanglittlerain/CityRadiation-Accelerator-CRAX-V1.0.git', 'crax_src'])
    # Handle thirdparty.rar extraction and build...

setup(
    name="cityenergyanalyst",
    package_data={
        'cea': [
            'resources/radiation/bin/**/*',
            'resources/radiationCRAX/bin/**/*',
        ]
    },
)
```

### Option 3: scikit-build-core for CMake Integration

**Benefits for CEA:**
- **Native CMake Integration** - Both DAYSIM and CRAX use CMake
- **Cross-Platform Binary Building** - Handles platform-specific compilation automatically  
- **Automatic Binary Placement** - Places compiled binaries in correct package locations
- **cibuildwheel Integration** - For automated CI/CD across platforms

```toml
[build-system]
requires = ["scikit-build-core", "cmake"]
build-backend = "scikit_build_core.build"

[tool.scikit-build]
cmake.source-dir = "external"
cmake.build-type = "Release"
wheel.packages = ["cea"]
install.components = ["daysim_runtime", "crax_runtime"]
```

#### Selective Binary Compilation with scikit-build-core

Since CEA only needs specific DAYSIM binaries, use selective CMake targets:

```cmake
# external/CMakeLists.txt
project(cea_selective_build)

# Only build needed DAYSIM executables
add_executable(ds_illum ${DAYSIM_SOURCE_DIR}/src/daysim/ds_illum.c)
add_executable(epw2wea ${DAYSIM_SOURCE_DIR}/src/common/epw2wea.c)
add_executable(gen_dc ${DAYSIM_SOURCE_DIR}/src/gen/gen_dc.c)
add_executable(oconv ${DAYSIM_SOURCE_DIR}/src/cv/oconv.c)
add_executable(radfiles2daysim ${DAYSIM_SOURCE_DIR}/src/daysim/radfiles2daysim.c)
add_executable(rtrace_dc ${DAYSIM_SOURCE_DIR}/src/rt/rtrace_dc.c)

# Install only these binaries
install(TARGETS ds_illum epw2wea gen_dc oconv radfiles2daysim rtrace_dc
        DESTINATION cea/resources/radiation/bin/$<PLATFORM_ID>
        COMPONENT daysim_runtime)

# Install required library files        
install(FILES
    daysim/lib/rayinit.cal
    daysim/lib/isotrop_sky.cal  
    DESTINATION cea/resources/radiation/bin/$<PLATFORM_ID>
    COMPONENT daysim_runtime)
```

#### Post-Build Hooks (Alternative)

If you need post-build filtering:

```python
# build_helpers.py
from setuptools.command.build_ext import build_ext
import os

class PostBuildHook(build_ext):
    def run(self):
        super().run()  # Run scikit-build first
        self.filter_binaries()
    
    def filter_binaries(self):
        """Keep only needed DAYSIM binaries"""
        needed_bins = {'ds_illum', 'epw2wea', 'gen_dc', 'oconv', 'radfiles2daysim', 'rtrace_dc'}
        
        bin_dir = "cea/resources/radiation/bin"
        for platform_dir in os.listdir(bin_dir):
            platform_path = os.path.join(bin_dir, platform_dir)
            if os.path.isdir(platform_path):
                for file in os.listdir(platform_path):
                    name, ext = os.path.splitext(file)
                    if name not in needed_bins:
                        os.remove(os.path.join(platform_path, file))
```

```toml
[tool.setuptools.cmdclass]
build_ext = "build_helpers:PostBuildHook"
```

### Option 4: cibuildwheel for Cross-Platform Wheels

```yaml
# .github/workflows/build-wheels.yml
name: Build wheels
on: [push, pull_request]

jobs:
  build_wheels:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    
    steps:
    - uses: actions/checkout@v4
      with:
        submodules: recursive  # for DAYSIM/CRAX as submodules
    
    - name: Build wheels
      uses: pypa/cibuildwheel@v2.16.2
      env:
        CIBW_BEFORE_BUILD: |
          bash scripts/build_external_tools.sh
        CIBW_ARCHS_MACOS: "x86_64 arm64"
        CIBW_ARCHS_LINUX: "x86_64"
        CIBW_ARCHS_WINDOWS: "AMD64"
```

## Current Package Data Configuration

CEA's `pyproject.toml` has been updated to include runtime files via package-data:

```toml
[tool.setuptools.package-data]
cea = [
    # Configuration files
    "default.config",
    "schemas.yml",
    "scripts.yml", 
    "workflows/*.yml",
    
    # Data files
    "examples/*.zip",
    "datamanagement/weather_helper/weather.geojson",
    "databases/**/*.csv",
    "databases/weather/**/*.epw",
    
    # Compiled binaries
    "resources/radiation/bin/**/*",        # DAYSIM binaries
    "resources/radiationCRAX/bin/**/*",    # CRAX binaries
    
    # Web assets
    "interfaces/dashboard/plots/templates/*.html",
    "plots/*.html",
    "plots/naming.csv",
]
```

The `MANIFEST.in` has been reduced to only include test files:

```
recursive-include cea/tests *.config *.yml
```

## Recommended Implementation Plan

### For CEA's Current Workflow:

1. **Create build scripts** in `scripts/`:
   ```bash
   scripts/
   ├── build_daysim.sh
   ├── build_crax.sh  
   └── build_external_tools.sh
   ```

2. **Use scikit-build-core** with selective compilation:
   ```toml
   [build-system]
   requires = ["scikit-build-core>=0.8.0", "cmake>=3.15"]
   build-backend = "scikit_build_core.build"
   
   [tool.scikit-build]
   cmake.source-dir = "external"
   wheel.packages = ["cea"]
   install.components = ["cea_daysim", "cea_crax"]
   ```

3. **Project structure**:
   ```
   cea/
   ├── external/
   │   ├── CMakeLists.txt          # Master build file
   │   ├── daysim/                 # Git submodule
   │   └── crax/                   # Git submodule
   ├── cea/
   │   └── resources/
   │       ├── radiation/bin/      # Where DAYSIM binaries go
   │       └── radiationCRAX/bin/  # Where CRAX binaries go
   └── pyproject.toml
   ```

4. **Environment dependencies**:
   ```yaml
   # environment.yml additions
   dependencies:
     - cmake
     - make  # [unix]
     - {{ compiler('c') }}      # [build]
     - {{ compiler('cxx') }}    # [build]
   ```

## Comparison: setuptools vs scikit-build-core

### Traditional setuptools challenges:
- Manual binary management in `daysim.py:check_daysim_bin_directory()`
- Platform-specific path handling  
- Complex custom build scripts

### scikit-build-core advantages:
- **Automatic cross-compilation** for multiple platforms
- **Native wheel support** with proper binary embedding
- **CMake expertise** - handles complex C++ builds correctly
- **cibuildwheel integration** for automated CI/CD
- **Dependency management** - handles Arrow, Qt5, etc.

## Conclusion

For CEA's integration of DAYSIM and CRAX:

1. **Short-term**: Use conda packages for binaries (matches CEA's current conda-first approach)
2. **Long-term**: Migrate to scikit-build-core with selective compilation for automated wheel building
3. **Keep existing** binary detection logic in `daysim.py` - it works with any approach

The selective CMake approach is cleanest since you avoid building unnecessary tools entirely while maintaining compatibility with CEA's existing architecture.