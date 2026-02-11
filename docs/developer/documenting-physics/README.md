# Documenting Physics Functions

Guidelines for documenting physics-based calculations in CEA.

## Contents

- **[docstring-specification.md](docstring-specification.md)** - Standard docstring format for physics and engineering functions

## Overview

The physics module (`cea/technologies/thermal_network/physics/`) implements standards-compliant calculations for district heating and cooling networks:

- **hydraulics.py** - ISO 5167, EN 13941 (pressure loss, friction, Reynolds)
- **heat_transfer.py** - VDI Heat Atlas (Nusselt, Prandtl)
- **fluid_properties.py** - Temperature-dependent water properties
- **thermal_loss.py** - EN 13941 (pipe heat loss)

## For Contributors

When adding new physics functions:
1. Follow the [docstring specification](docstring-specification.md)
2. Ensure standards references are accurate
3. Include formulas, valid ranges, and proper units
4. Use Unicode symbols for mathematical notation

## Standards References

Functions reference international standards including:
- EN 13941-1:2019 (District heating pipes)
- VDI Heat Atlas (Heat transfer)
- Colebrook-White, Swamee-Jain (Friction factors)
- Incropera et al. (Heat and mass transfer)
