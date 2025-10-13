# Utilities

Utility features provide supporting tools for data conversion, format verification, sensitivity analysis, batch processing, and other workflow-enhancing capabilities.

---

## CEA-4 Format Helper

### Overview
Verifies that input data is in the correct format for CEA-4 and migrates Late-CEA-3 data to CEA-4 format. This feature ensures data compatibility and helps users transition from CEA version 3 to version 4.

### When to Use
- **Recommended before any analysis**: Verify data format is correct
- Migrating projects from CEA-3 to CEA-4
- After manually editing input files
- Troubleshooting data-related errors

### What It Checks

**Data Format Verification**:
- File structure and naming
- Required columns present
- Data types correct (numbers, strings, etc.)
- Value ranges valid
- Cross-file consistency
- Geometry validity

**Migration Capabilities**:
- Converts CEA-3 Late schema to CEA-4
- Updates file structures
- Renames columns as needed
- **Note**: Migration is irreversible

### How to Use

#### Verify Mode (Recommended First Step)

1. Navigate to **Utilities**
2. Select **CEA-4 Format Helper**
3. Choose mode: **Verify**
4. Click **Run**
5. Review verification report

The feature will check all input files and report:
- ✅ Files that pass validation
- ⚠️ Warnings (non-critical issues)
- ❌ Errors (must be fixed)

#### Migrate Mode (One-Time Operation)

⚠️ **Warning**: Migration is irreversible. Back up your data first!

1. **Back up your scenario folder**
2. Navigate to **Utilities**
3. Select **CEA-4 Format Helper**
4. Choose mode: **Migrate**
5. Click **Run**
6. Data is converted from CEA-3 to CEA-4 format

### Verification Report

The report includes:
- File-by-file status
- Specific errors or warnings
- Suggested fixes
- Line numbers for errors

### Common Issues Detected

**Missing Required Columns**:
- Solution: Add missing columns with default values

**Invalid Data Types**:
- Solution: Check that numbers are not text, dates are formatted correctly

**Out of Range Values**:
- Solution: Review and correct unrealistic values (e.g., negative areas)

**Geometry Errors**:
- Solution: Fix building footprints (self-intersections, invalid polygons)

### Tips
- **Run verification first**: Don't migrate until verification passes
- **Fix errors incrementally**: Address one file at a time
- **Back up before migration**: Migration cannot be undone
- **Use after manual edits**: Verify after editing input files in Excel

### Troubleshooting

**Issue**: Verification fails with many errors
- **Solution**: Start with a fresh scenario from example projects
- **Solution**: Use Archetypes Mapper to regenerate property files

**Issue**: Migration fails partway through
- **Solution**: Restore from backup and retry
- **Solution**: Check CEA version is up to date

---

## Generate Samples for Sensitivity Analysis (SA)

### Overview
Generates parameter samples for sensitivity analysis using the Sobol method. Sensitivity analysis quantifies how input parameter uncertainties affect output uncertainties, helping identify which parameters most influence results.

### When to Use
- Uncertainty quantification studies
- Identifying critical input parameters
- Validating model robustness
- Research and publication purposes
- Risk assessment

### How It Works

**Sobol Sequence Sampling**:
- Generates quasi-random parameter samples
- Ensures good coverage of parameter space
- More efficient than pure random sampling
- Suitable for global sensitivity analysis

**Typical Parameters to Vary**:
- Envelope U-values (±20%)
- Occupancy densities (±30%)
- Equipment loads (±20%)
- HVAC system efficiencies (±10%)
- Window-wall ratios (±20%)
- Infiltration rates (±30%)

### Prerequisites
- Base scenario with defined parameters
- Parameter ranges or uncertainty distributions

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Number of samples** | Sample size | 512, 1024, or 2048 |
| **Parameters to vary** | Which inputs to sample | User-defined |
| **Sampling method** | Sobol or other | Sobol (recommended) |

### How to Use

1. **Define parameters to vary**:
   - Create parameter configuration file
   - Specify ranges or distributions for each parameter

2. **Run sample generation**:
   - Navigate to **Utilities**
   - Select **Generate Samples for Sensitivity Analysis**
   - Set number of samples (recommend 512 or 1024)
   - Click **Run**

3. **Output**: Scenario folders with parameter variations
   - `scenario_SA_001/` - First sample
   - `scenario_SA_002/` - Second sample
   - ...
   - `scenario_SA_N/` - Nth sample

### Next Steps After Sample Generation

1. **Run CEA analyses** on all sample scenarios:
   - Use Batch Process Workflow (see below)
   - Run demand, emissions, costs, etc.

2. **Collect results** from all scenarios

3. **Perform sensitivity analysis**:
   - Calculate Sobol indices
   - Identify influential parameters
   - Quantify output uncertainties

### Tips
- **Start small**: Test with 64-128 samples before full run
- **Computational cost**: N samples × analysis time
- **Use batch processing**: Automate with Batch Process Workflow
- **High-performance computing**: Consider cluster for large SA

### Troubleshooting

**Issue**: Too many scenario folders (disk space)
- **Solution**: Reduce number of samples
- **Solution**: Use symbolic links for common files (advanced)

**Issue**: Long computation time
- **Solution**: Reduce sample size
- **Solution**: Use multiprocessing and batch workflow

---

## Batch Process Workflow

### Overview
Automatically processes multiple scenarios using a user-configured workflow. This feature enables running the same sequence of CEA analyses across many scenarios, essential for sensitivity analysis, scenario comparisons, and parametric studies.

### When to Use
- Processing sensitivity analysis samples
- Comparing multiple design scenarios
- Parametric studies
- Automating repetitive workflows
- Large-scale district analyses

### How It Works

1. **Define workflow**: Create `workflow.yml` file specifying sequence of CEA features to run
2. **Select scenarios**: Choose which scenarios to process
3. **Execute batch**: Run workflow on all selected scenarios
4. **Collect results**: Aggregate outputs from all scenarios

### Workflow Configuration

Create a `workflow.yml` file:

```yaml
---
- radiation  # Solar radiation analysis
- occupancy-helper  # Building occupancy
- demand  # Energy demand calculation
- emissions  # Emissions calculation
```

Workflow runs features in order, respecting dependencies.

### Prerequisites
- Multiple scenarios to process
- Workflow configuration file (`workflow.yml`)
- All scenarios have required input data

### How to Use

1. **Create workflow file**:
   - Define sequence of features
   - Save as `workflow.yml` in project folder

2. **Run batch process**:
   - Navigate to **Utilities**
   - Select **Batch Process Workflow**
   - Select scenarios to process
   - Provide workflow file path
   - Click **Run**

3. **Monitor progress**:
   - Check log for progress through scenarios and features
   - Errors in one scenario don't stop others

### Processing Time

Total time = Number of scenarios × Workflow time per scenario

Example:
- 100 scenarios
- Workflow: radiation + demand (~30 min per scenario)
- Total: ~50 hours
- With multiprocessing: ~12-24 hours

### Tips
- **Test workflow first**: Run on 2-3 scenarios before full batch
- **Use overnight/weekend**: Long processing times
- **Enable multiprocessing**: In each feature's parameters
- **Log monitoring**: Check logs periodically for errors
- **High-performance computing**: Use cluster for very large batches

### Troubleshooting

**Issue**: Batch process stops after first error
- **Solution**: Check that all scenarios have required inputs
- **Solution**: Verify workflow.yml syntax is correct

**Issue**: Some scenarios fail
- **Solution**: Review failed scenario logs
- **Solution**: Re-run failed scenarios individually to debug

---

## DBF to CSV to DBF

### Overview
Converts files between .dbf (dBase format) and .csv/.xlsx formats for editing. DBF files are used by shapefiles to store attribute data; this tool allows editing in Excel or other spreadsheet programs.

### When to Use
- Editing shapefile attributes (building properties, etc.)
- Converting data for external analysis
- Bulk editing building properties
- Creating data in Excel and converting to DBF

### How It Works

**DBF → CSV/XLSX**:
- Extracts tabular data from .dbf file
- Saves as .csv or .xlsx
- Opens in Excel for editing

**CSV/XLSX → DBF**:
- Reads edited spreadsheet
- Converts back to .dbf format
- Preserves data types and structure

### Prerequisites
- DBF file (e.g., from shapefile attributes) or CSV/XLSX to convert

### How to Use

#### Converting DBF to CSV

1. Navigate to **Utilities**
2. Select **DBF to CSV to DBF**
3. Choose mode: **DBF to CSV**
4. Select input .dbf file
5. Specify output .csv file path
6. Click **Run**
7. Open .csv in Excel to edit

#### Converting CSV back to DBF

1. After editing .csv in Excel, save and close
2. Select mode: **CSV to DBF**
3. Select input .csv file
4. Specify output .dbf file path
5. Optionally provide original .dbf as template (to preserve field types)
6. Click **Run**

### Data Type Preservation

**Important**: DBF files have specific field types:
- Text (Character)
- Numbers (Numeric, Float, Double)
- Dates
- Boolean (Logical)

When converting CSV → DBF:
- Provide original .dbf as template to preserve types
- Otherwise, tool infers types (may not be perfect)

### Tips
- **Keep original .dbf**: Use as template when converting back
- **Check field types**: Verify after conversion
- **Column name rules**: DBF limits to 10 characters, no spaces

### Troubleshooting

**Issue**: Data types wrong after conversion
- **Solution**: Provide original .dbf as template

**Issue**: Column names truncated
- **Solution**: DBF limits column names to 10 characters; edit names accordingly

---

## SHP to CSV to SHP

### Overview
Converts shapefiles (geometry + attributes) to CSV/XLSX and back. Similar to DBF conversion but handles geometry information, allowing viewing and editing of spatial data in spreadsheet format.

### When to Use
- Editing building coordinates and properties together
- Viewing shapefile data in tabular format
- Creating new shapefiles from spreadsheet data
- Bulk editing geometries and attributes

### How It Works

**SHP → CSV/XLSX**:
- Extracts geometry (as WKT - Well-Known Text) and attributes
- Saves as CSV/XLSX with geometry column

**CSV/XLSX → SHP**:
- Reads spreadsheet with geometry column
- Recreates shapefile with geometries and attributes

### Prerequisites
- Shapefile (.shp + .shx + .dbf) or CSV/XLSX with geometry

### How to Use

#### Converting SHP to CSV

1. Navigate to **Utilities**
2. Select **SHP to CSV to SHP**
3. Choose mode: **SHP to CSV**
4. Select input .shp file
5. Specify output .csv file path
6. Click **Run**

CSV will contain:
- All attribute columns
- `geometry` column with WKT representation

#### Converting CSV back to SHP

1. After editing, ensure:
   - `geometry` column is preserved
   - WKT format is valid
2. Select mode: **CSV to SHP**
3. Select input .csv file
4. Specify output .shp file path
5. Click **Run**

### Editing Geometries in CSV

Geometry is stored as WKT (Well-Known Text):
- Point: `POINT (x y)`
- Polygon: `POLYGON ((x1 y1, x2 y2, ..., x1 y1))`

**Warning**: Editing WKT is error-prone. For complex geometry edits, use GIS software (QGIS, ArcGIS).

### Tips
- **Simple edits**: Use for attribute editing, not geometry
- **Complex geometry**: Use QGIS instead
- **Coordinate system**: Preserved during conversion
- **Backup**: Always keep original shapefile

### Troubleshooting

**Issue**: Geometry invalid after conversion
- **Solution**: Check WKT syntax in CSV
- **Solution**: Use GIS software for geometry edits instead

---

## Rename Building

### Overview
Facilitates renaming a building across all scenario files. When you rename a building, CEA must update the ID in multiple files (zone geometry, property files, output files, etc.). This tool automates the process.

### When to Use
- Standardizing building naming conventions
- Fixing building ID errors
- Reorganizing building identifiers
- After importing external data with different IDs

### How It Works
The tool updates building names/IDs in:
- Zone geometry shapefile
- Building property files (architecture, internal_loads, etc.)
- Existing output files (if any)
- Network connection files (if any)

### Prerequisites
- Zone geometry with buildings
- Old building name/ID to rename
- New building name/ID

### Key Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| **Old name** | Current building ID | "B001" |
| **New name** | Desired building ID | "Building_A" |

### How to Use

1. Navigate to **Utilities**
2. Select **Rename Building**
3. Enter old building name (exact match)
4. Enter new building name:
   - Must be unique
   - Avoid special characters
   - Convention: alphanumeric, underscores OK
5. Click **Run**

The tool will:
- Update zone geometry
- Rename property file entries
- Update any existing output files
- Report which files were modified

### Building Naming Conventions

**Recommended**:
- Start with letter (not number)
- Use consistent prefixes (e.g., "RES_01", "OFF_01")
- Alphanumeric only (avoid spaces, special chars)
- Length: Keep reasonable (<30 characters)

**Examples**:
- ✅ Good: "B001", "RES_Building_A", "Office_North"
- ❌ Avoid: "1", "Building #1", "A B C"

### Tips
- **Backup first**: Renaming affects many files
- **One at a time**: Rename buildings individually, not in batch
- **Check results**: Verify new name appears in all files
- **Before outputs**: Easier to rename before running analyses

### Troubleshooting

**Issue**: Some files not updated
- **Solution**: Manually check and update missed files
- **Solution**: Re-run the tool

**Issue**: New name already exists
- **Solution**: Choose a unique name

---

## Related Features
- **[Data Management](08-data-management.md)** - Database and data preparation helpers
- **[CEA-4 Format Helper](#cea-4-format-helper)** - Verify and migrate data format
- **[Import & Export](01-import-export.md)** - Export results to CSV for external analysis

---

[← Back: Data Management](08-data-management.md) | [Back to Index](index.md) | [Next: Visualisation →](10-visualisation.md)
