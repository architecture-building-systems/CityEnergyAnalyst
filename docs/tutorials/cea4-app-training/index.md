# CEA-4 App User Training Guide

Welcome to the comprehensive training guide for the City Energy Analyst 4 (CEA-4) Application. This documentation covers all features available through the CEA-4 dashboard interface.

## About This Guide

This guide is designed for end users who want to learn how to use the CEA-4 App effectively. Each section provides detailed information about specific feature categories, including:

- What each feature does
- When to use it
- Required input files
- Step-by-step usage instructions
- Expected outputs
- Common issues and troubleshooting

## Quick Start

New to CEA-4? Start with these resources:

1. **Create New Scenario Wizard** - Use this in CEA-4 App to automate initial data setup
2. **[Quick Reference Guide](00-quick-reference.md)** - A single-page overview of all 41 features
3. **[Variable & File Glossary](../glossary/index.md)** - Reference of all 179 input/intermediate/output files, grouped by feature
4. **[Data Management](08-data-management.md)** - Understanding the automated data preparation
5. **[Energy Demand Forecasting](04-demand-forecasting.md)** - Core functionality for building energy analysis

## Feature Categories

The CEA-4 App organises its features into the following categories:

### 1. [Import & Export](01-import-export.md)
Tools for exchanging data with external applications and generating summary reports.
- Export to Rhino/Grasshopper
- Import from Rhino/Grasshopper
- Export Results to CSV

### 2. [Solar Radiation Analysis](02-solar-radiation.md)
Calculate solar radiation on building surfaces for renewable energy assessments.
- Building Solar Radiation using DAYSIM
- Building Solar Radiation using CRAX (BETA)

### 3. [Renewable Energy Potential Assessment](03-renewable-energy.md)
Evaluate renewable energy generation potential for buildings and districts.
- Photovoltaic (PV) Panels
- Photovoltaic-Thermal (PVT) Panels
- Solar Collectors (SC)
- Shallow Geothermal Potential
- Water Body Potential
- Sewage Heat Potential

### 4. [Energy Demand Forecasting](04-demand-forecasting.md)
Forecast hourly and annual energy demand for heating, cooling, electricity, and more.
- Building Occupancy Estimation
- Energy Demand Modelling

### 5. [Thermal Network Design](05-thermal-network.md)
Design and analyse district heating and cooling networks.
- Network Layout Generation
- Thermal Hydraulic Flow & Sizing

### 6. [Life Cycle Analysis](06-0-life-cycle-analysis.md)
Assess environmental impacts and costs of building energy systems using what-if supply scenarios. All four features run on a shared what-if scenario; **Final Energy must run first** and produces the `configuration.json` consumed by the other three.
- [Final Energy / Energy by Carrier](06-1-final-energy.md) (BETA) - Carrier consumption by buildings and plants; includes hourly SC/PVT-primary DHW tank dispatch
- [Emissions / GHG Emissions](06-2-emissions.md) (BETA) - Lifecycle and operational GHG emissions, with optional grid-decarbonisation trajectory
- [System Costs / Costs](06-3-system-costs.md) (BETA) - CAPEX, OPEX, and total annualised cost (TAC) at building, component, and plant level
- [Heat Rejection](06-4-heat-rejection.md) (BETA) - Anthropogenic waste heat to the environment, with map-layer visualisation

### 7. [Energy Supply System Optimisation](07-supply-optimisation.md)
Optimise energy supply systems for buildings and districts.
- Building-Scale Supply System Optimisation *(CLI only)*
- District Supply System Optimisation

### 8. [Data Management](08-data-management.md)
Prepare and validate input data for CEA analysis.
- Database Helper
- Archetypes Mapper
- Weather Helper
- Surroundings Helper
- Terrain Helper
- Streets Helper
- Trees Helper

### 9. [Utilities](09-utilities.md)
Supporting tools for data conversion, format verification, and more.
- CEA-4 Format Helper
- Sensitivity Analysis Sampler
- File Format Conversion Tools
- Building Rename Tool

### 10. [Visualisation](10-visualisation.md)
Create charts and plots to visualise CEA results.
- Plot Building Energy Demand
- Plot Solar Technology Results
- Plot Building Comfort Chart

## How to Use This Guide

### For New Users
1. **Create your first scenario** using the Create New Scenario Wizard in CEA-4 App (automates data preparation)
2. Start with the [Quick Reference Guide](00-quick-reference.md) to familiarise yourself with available features
3. Review [Data Management](08-data-management.md) to understand the automated data preparation
4. Follow the typical workflow: Solar Radiation → Demand Forecasting → Analysis

### For Experienced Users
- Use the Quick Reference Guide to quickly locate specific features
- Jump directly to the relevant category sections for detailed instructions
- Refer to troubleshooting sections when encountering issues

### Typical Workflow

A standard CEA-4 analysis typically follows this sequence:

1. **Create New Scenario** (One-time setup)
   - Use the **Create New Scenario Wizard** in CEA-4 App
   - The wizard automatically fetches weather, surroundings, terrain, and streets
   - Automatically loads databases and runs Archetypes Mapper
   - ⚠️ **Remember**: Re-run Archetypes Mapper if you manually edit input files

2. **Solar Analysis** (Solar Radiation Analysis)
   - Run solar radiation analysis on building surfaces

3. **Demand Analysis** (Energy Demand Forecasting)
   - Calculate building occupancy profiles
   - Forecast energy demand for all buildings

4. **Renewable Energy Assessment** (Renewable Energy Potential)
   - Evaluate PV, solar thermal, or geothermal potential

5. **Network Design** (Optional - for district systems)
   - Generate network layout
   - Size pipes and calculate thermal hydraulics

6. **Optimisation** (Optional)
   - Optimise building-scale or district-scale supply systems

7. **Impact Assessment** (Life Cycle Analysis - 4 BETA features)
   - Run **Final Energy** first (carrier consumption per what-if scenario)
   - Then **Emissions**, **System Costs**, and **Heat Rejection** for the same what-if

8. **Results & Reporting** (Visualisation & Export)
   - Generate plots and charts
   - Export results to CSV or external tools

## Additional Resources

- **CEA Website**: [https://www.cityenergyanalyst.com](https://www.cityenergyanalyst.com)
- **Documentation**: [https://city-energy-analyst.readthedocs.io](https://city-energy-analyst.readthedocs.io)
- **Video Tutorials**: [CEA YouTube Channel](https://youtube.com/playlist?list=PL4fIcvT_PXL0XYU_jPDKj50MSUc8GggFz)
- **Community Forum**: [https://github.com/architecture-building-systems/CityEnergyAnalyst/discussions](https://github.com/architecture-building-systems/CityEnergyAnalyst/discussions)

## Getting Help

If you encounter issues:
1. Check the troubleshooting section in the relevant feature guide
2. Review the [Known Issues](https://city-energy-analyst.readthedocs.io/en/latest/known-issues.html) page
3. Search existing [GitHub Issues](https://github.com/architecture-building-systems/CityEnergyAnalyst/issues)
4. Ask the community in [GitHub Discussions](https://github.com/architecture-building-systems/CityEnergyAnalyst/discussions)

---

**Last Updated**: May 2026
**CEA Version**: 4.0.0-beta.7