# CEA Software Improvement Recommendations

**Based on**: 3 months of user support analysis (Sept-Dec 2025)
**Compiled by**: Support team analysis of email exchanges with ETH IDP students and international users

---

## Executive Summary

This document identifies **systematic improvement opportunities** for CEA based on recurring user issues. Rather than simply documenting problems, we propose concrete solutions to prevent these issues from occurring.

### Issue Categories by Frequency:
1. **Database/Input Validation** (35% of issues)
2. **Error Messages & User Guidance** (25% of issues)
3. **Cloud Platform UX** (20% of issues)
4. **Documentation Gaps** (15% of issues)
5. **Workflow & Tool Integration** (5% of issues)

---

## Priority 1: Critical Improvements (High Impact, Frequent Issues)

### 1.1 Input Validation & Early Error Detection

**Problem**: Users spend hours running simulations that fail due to preventable input errors.

**Current Behaviour**:
- Errors only surface during Energy Demand Part 2 (after long DAYSIM run)
- Generic error messages (e.g., "KeyError: 'name'") don't guide users to root cause
- Format Helper doesn't catch all database inconsistencies

**Proposed Solutions**:

#### A. Pre-Flight Input Validator
Create a comprehensive pre-simulation validator that runs before any compute-intensive tasks:

```python
# Proposed: cea.utilities.input_validator.py

class PreFlightValidator:
    """
    Run before DAYSIM, Energy Demand, etc.
    Fast checks (~seconds) to catch 90% of common errors.
    """

    def validate_scenario(self, locator):
        """Comprehensive validation with actionable error messages"""
        errors = []
        warnings = []

        # 1. Geometry validation
        errors.extend(self.validate_geometry())

        # 2. Database consistency
        errors.extend(self.validate_database_consistency())

        # 3. Schedule validation
        errors.extend(self.validate_schedules())

        # 4. System assignment completeness
        errors.extend(self.validate_system_assignments())

        # 5. Temperature parameter logic
        errors.extend(self.validate_temperature_parameters())

        return ValidationReport(errors, warnings, suggestions)
```

**Checks to Include**:
- ✅ Duplicate building names
- ✅ Unclosed polygons, self-intersections
- ✅ Missing database references (ASSEMBLIES → COMPONENTS chain)
- ✅ All buildings have archetype assignments
- ✅ Heating/cooling schedules not all OFF
- ✅ Temperature parameters follow physical constraints
- ✅ CSV encoding issues (detect non-UTF-8)
- ✅ Year fields are integers, not floats
- ✅ Empty cells in mandatory fields (use_type2/3)

**UI Integration**:
- Add "Validate Inputs" button before each major simulation
- Show validation report with ✅/⚠️/❌ indicators
- Clickable errors that navigate to problem location
- "Fix automatically" option for simple issues

**Expected Impact**: Reduce support requests by 30-40%

---

### 1.2 Improved Error Messages with Actionable Guidance

**Problem**: Current error messages are developer-facing, not user-facing.

**Examples of Poor Error Messages**:
```python
# Current (not helpful)
KeyError: 'name'

# Proposed (actionable)
❌ Building Property Error

Building names are missing in the HVAC system verification step.

Likely causes:
1. Duplicate building names in zone.shp (most common)
2. Missing 'Name' column in zone.shp
3. Database archetype mapping incomplete

How to fix:
→ Check for duplicate building names: Open zone.shp and verify each name is unique
→ Re-run Archetype Mapper if you recently modified geometry
→ See troubleshooting guide: [link to FAQ section]

Buildings affected: [list from error context if available]
```

**Implementation Pattern**:
```python
# Proposed: cea.utilities.user_friendly_errors.py

class UserFriendlyError(Exception):
    """
    CEA errors with user-actionable guidance
    """
    def __init__(self, error_code, context=None):
        self.error_code = error_code
        self.context = context or {}

        # Load error metadata from database
        self.metadata = ERROR_DATABASE[error_code]

    def __str__(self):
        return f"""
        ❌ {self.metadata['title']}

        {self.metadata['description']}

        Likely causes:
        {self._format_causes()}

        How to fix:
        {self._format_solutions()}

        Context: {self._format_context()}

        Documentation: {self.metadata['doc_link']}
        """

# Usage in existing code
try:
    building_name = result.loc[idx, 'name']
except KeyError:
    raise UserFriendlyError(
        'MISSING_BUILDING_NAME',
        context={'index': idx, 'columns': result.columns}
    )
```

**Error Database Structure**:
```yaml
# cea/utilities/error_messages.yml

MISSING_BUILDING_NAME:
  title: "Building Property Error"
  description: "Building names are missing in HVAC system verification."
  causes:
    - "Duplicate building names in zone.shp (most common)"
    - "Missing 'Name' column in zone.shp"
    - "Database archetype mapping incomplete"
  solutions:
    - action: "Check for duplicate names"
      details: "Open zone.shp and verify each building name appears only once"
    - action: "Re-run Archetype Mapper"
      details: "Required after geometry changes"
  doc_link: "docs/faq#missing-building-name"
  severity: "error"

INVALID_TEMPERATURE_CONFIG:
  title: "Invalid HVAC Temperature Configuration"
  description: "Heat exchanger temperature configuration violates thermodynamic constraints."
  causes:
    - "Supply temperature higher than return temperature"
    - "Missing temperature parameters in HVAC assembly"
  solutions:
    - action: "Check HVAC system definition"
      details: "Navigate to ASSEMBLIES > HVAC > [HEATING|COOLING]"
    - action: "Verify temperature parameters"
      details: "Ensure Tcs0_aru_C and DTcs0_aru_C are defined"
    - action: "Consult reference database"
      details: "See Zurich database for correct system examples"
  doc_link: "docs/faq#invalid-temperature"
  severity: "error"
  related_errors: ["NEGATIVE_COOLING_LOAD"]
```

**Expected Impact**: Reduce average resolution time by 50-70%

---

### 1.3 Smart Database Reference Checker

**Problem**: Users define ASSEMBLIES that reference non-existent COMPONENTS, causing cryptic errors later.

**Proposed Feature**: Real-time database reference validation

**Implementation**:
```python
# cea/utilities/database_validator.py

class DatabaseReferenceValidator:
    """
    Validates that ASSEMBLIES → COMPONENTS references are complete
    """

    def validate_assembly(self, assembly_name, assembly_type):
        """
        Check if all components referenced by assembly exist

        Example:
            HVAC_COOLING_AS3 references:
            - primary_component: CH1 (in VAPOR_COMPRESSION_CHILLERS?)
            - secondary_component: HEX3 (in HEAT_EXCHANGERS?)
            - tertiary_component: CT1 (in COOLING_TOWERS?)
        """
        missing = []
        for component_ref in assembly.get_component_references():
            if not self._component_exists(component_ref):
                missing.append(component_ref)

        if missing:
            return ValidationError(
                f"Assembly '{assembly_name}' references missing components: {missing}",
                suggestions=[
                    f"Add {comp} to {self._guess_component_db(comp)}.csv"
                    for comp in missing
                ]
            )

        return ValidationSuccess()

    def suggest_component_database(self, component_code):
        """Guess which database file should contain component"""
        # CH* → VAPOR_COMPRESSION_CHILLERS
        # B* → BOILERS
        # HEX* → HEAT_EXCHANGERS
        # etc.
```

**UI Integration**:
- Run automatically when user edits ASSEMBLIES in CEA Cloud
- Show real-time validation indicators (✅/❌) next to component references
- "Create missing component" quick action button
- Suggest similar existing components as templates

**Expected Impact**: Eliminate ~25% of database-related errors

---

## Priority 2: Cloud Platform UX Improvements

### 2.1 Smart Download Manager

**Problem**: Large scenario downloads (>10GB) fail mid-way due to network instability. No resume capability.

**Proposed Solutions**:

#### A. Chunked Download with Resume Support
```python
# Backend: cea.interfaces.dashboard.api.download.py

@app.route('/download/scenario/<id>/chunked')
def download_scenario_chunked(id):
    """
    Support HTTP Range requests for resumable downloads
    """
    file_path = prepare_scenario_zip(id)

    # Support Range header for resume
    return send_file(
        file_path,
        as_attachment=True,
        conditional=True,  # Enable Range support
        max_age=3600
    )
```

#### B. Smart Download Options UI
```
┌─────────────────────────────────────────────┐
│ Download Scenario: fuxing_idp_2025          │
├─────────────────────────────────────────────┤
│                                             │
│ Select Components to Download:             │
│                                             │
│ ✅ Inputs (125 MB)              [Required] │
│ ✅ Summary Results (15 MB)      [Recommended] │
│ ⬜ Detailed Outputs (8.2 GB)    [Optional] │
│ ⬜ DAYSIM Raw Data (2.1 GB)     [Optional] │
│ ⬜ Visualisation Files (45 MB)  [Optional] │
│                                             │
│ Total size: 140 MB                          │
│                                             │
│ [Download]  [Email Link Instead]           │
└─────────────────────────────────────────────┘
```

**Additional Features**:
- Estimate download time based on connection speed
- Warn if file size > 1GB on mobile/slow connections
- Split large downloads into multiple smaller ZIPs automatically
- Stream directly to cloud storage (Google Drive, Dropbox integration)

**Expected Impact**: Reduce download-related support requests by 80%

---

### 2.2 Change Tracking & Version Control

**Problem**: Users report "changes not saving" in Cloud UI. No way to verify what actually changed.

**Proposed Feature**: Git-like change tracking for scenarios

**UI Mockup**:
```
┌─────────────────────────────────────────────┐
│ Scenario: fuxing_idp_2025                   │
├─────────────────────────────────────────────┤
│                                             │
│ Recent Changes (Last 7 days):               │
│                                             │
│ 📝 2 hours ago - You                        │
│    Modified: HVAC_COOLING_AS3 in database   │
│    Changed: Tcs0_aru_C from 12 to 8         │
│    [View Diff] [Revert]                     │
│                                             │
│ 🔄 5 hours ago - You                        │
│    Ran: Archetype Mapper                    │
│    Updated: 285 buildings                   │
│    [View Log]                               │
│                                             │
│ 📝 1 day ago - You                          │
│    Modified: zone.shp (via Input Editor)    │
│    Added: 12 buildings                      │
│    [View Diff] [Revert]                     │
│                                             │
│ [View Full History] [Create Checkpoint]    │
└─────────────────────────────────────────────┘
```

**Implementation**:
- Track all file modifications with timestamps
- Store diffs (not full copies) for CSV/text files
- Allow creating named checkpoints ("Before heating system change")
- One-click revert to any previous state
- Export change log for documentation

**Expected Impact**: Eliminate "changes not saving" confusion, improve reproducibility

---

### 2.3 Simulation Queue & Progress Visibility

**Problem**: Long-running simulations appear "stuck". Users don't know if simulation is progressing or failed silently.

**Current Behaviour**:
- "Running..." spinner with no progress indicator
- No visibility into which buildings are being processed
- Non-fatal errors don't stop simulation but aren't visible

**Proposed Improvements**:

#### A. Detailed Progress Tracking
```
┌─────────────────────────────────────────────┐
│ Energy Demand Simulation                    │
├─────────────────────────────────────────────┤
│                                             │
│ Status: Running                             │
│                                             │
│ Progress: ████████░░░░░░░░ 52% (148/285)   │
│                                             │
│ Current: Building B1234 (28%)               │
│ Estimated time remaining: 12 minutes        │
│                                             │
│ Completed: 147 buildings ✅                 │
│ Warnings: 3 buildings ⚠️  [View]           │
│ Errors: 0 buildings ❌                      │
│                                             │
│ Recent activity:                            │
│ • B1233 completed (1.2 min)                 │
│ • B1232 completed with warnings (0.8 min)   │
│ • B1231 completed (1.5 min)                 │
│                                             │
│ [Cancel] [Pause] [View Detailed Log]       │
└─────────────────────────────────────────────┘
```

#### B. Non-Fatal Error/Warning Stream
- Show warnings as they occur (not just at end)
- Allow filtering: "Show errors only" / "Show all"
- Click warning to see context & suggested fixes
- Option to "Stop simulation if warning occurs"

#### C. Stuck Simulation Detection
- If no progress for >5 minutes, show alert:
  ```
  ⚠️ Simulation appears stuck

  No progress for 6 minutes on Building B1234.
  This may indicate an error.

  [Cancel & Show Log] [Wait Longer]
  ```

**Expected Impact**: Reduce "is it stuck?" support questions, faster issue identification

---

## Priority 3: Enhanced Documentation & In-App Guidance

### 3.1 Contextual Help System

**Problem**: Users encounter errors but don't know where to look in documentation.

**Proposed Feature**: In-app contextual help linked to FAQ/Troubleshooting

**Implementation**:

#### A. Smart Search in Error Messages
```python
# When error occurs, show:

❌ KeyError: 'name'

💡 Smart Help:
   Found 3 related FAQ entries:
   • "Duplicate building names error" (⭐ Most relevant)
   • "Missing building properties"
   • "Archetype mapping issues"

   [Show Solutions] [Search FAQ] [Contact Support]
```

#### B. Inline Documentation Tooltips
- Hover over any input field → see description + valid range
- Example: Hover over "Tcs0_aru_C" →
  ```
  Nominal supply temperature of water side of air-recirculation units

  Typical values: 6-12°C for cooling
  Must be lower than return temperature (Tcs_re)

  [Learn More] [See Examples]
  ```

#### C. Workflow Wizard for Common Tasks
```
🧙 Workflow Helper

You're about to run Energy Demand Part 2.
Have you completed these prerequisites?

✅ DAYSIM completed for all buildings
✅ Archetype Mapper run after geometry changes
❌ Database validation passed
   → Run "Validate Inputs" before proceeding

[Validate Now] [Run Anyway] [Learn More About Prerequisites]
```

**Expected Impact**: Empower users to self-solve 50% of issues

---

### 3.2 Interactive Database Editor with Validation

**Problem**: Editing databases in Excel/CSV is error-prone (encoding, types, references).

**Proposed Feature**: Browser-based smart database editor

**Key Features**:
- **Dropdown selectors** for references (not free text)
  ```
  HVAC_COOLING_AS3:
    primary_component: [▼ Select from VAPOR_COMPRESSION_CHILLERS]
                       → CH1 ✅ (exists)
                       → CH2 ✅ (exists)
                       → CH99 ❌ (not found - create?)
  ```

- **Type validation** on input
  - Year fields: Only accept integers
  - Temperature fields: Validate ranges (e.g., -50 to 100°C)
  - Efficiency fields: Validate 0-1 range

- **Visual dependency graph**
  ```
  STANDARD1 (Construction Type)
    └─> ENVELOPE_AS1 (Assembly)
        ├─> WALL_AS1 (Component)
        ├─> ROOF_AS1 (Component)
        └─> WINDOW_AS1 (Component)

  Click any node to edit
  ❌ marks indicate missing definitions
  ```

- **Copy from template**
  - "Create new similar to..." feature
  - Suggest nearest match from Zurich database
  - Auto-fill related parameters

**Expected Impact**: Reduce database definition errors by 60%

---

## Priority 4: Workflow & Tool Integration Improvements

### 4.1 Scenario Branching & Comparison Tools

**Problem**: Users manually manage scenario variants. No built-in comparison.

**Proposed Feature**: Scenario branching like Git

**UI Concept**:
```
My Project
├─ Base_2025 (main)
│   ├─ Variant_A_High_Insulation
│   ├─ Variant_B_Heat_Pumps
│   └─ Variant_C_District_Heating
│
└─ Future_2060
    ├─ Scenario_1_Business_As_Usual
    └─ Scenario_2_Aggressive_Retrofit

[Create Branch] [Compare Scenarios] [Merge Results]
```

**Comparison View**:
```
┌─────────────────────────────────────────────────────────┐
│ Compare: Variant_A vs Variant_B                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Metric            Variant_A    Variant_B    Δ         │
│ ────────────────────────────────────────────────────── │
│ Total Demand      1,234 MWh   1,156 MWh   -6.3% 📉   │
│ Heating Demand      890 MWh     712 MWh  -20.0% 📉   │
│ Cooling Demand      234 MWh     289 MWh  +23.5% 📈   │
│ GHG Emissions       456 tCO2    389 tCO2  -14.7% 📉   │
│                                                         │
│ [Export Comparison] [Generate Report] [Visualise]     │
└─────────────────────────────────────────────────────────┘
```

**Expected Impact**: Streamline design iteration workflow

---

### 4.2 Batch Validation & Processing Tools

**Problem**: Testing on 1-2 buildings before running full scenario is manual.

**Proposed Feature**: Automated test suite

```python
# cea/utilities/scenario_test_suite.py

class ScenarioTestSuite:
    """
    Run validation tests on representative building sample
    before full scenario simulation
    """

    def run_smoke_tests(self, locator, sample_size=5):
        """
        Test random sample of buildings for common issues

        Returns: TestReport with pass/fail and estimated
                 full scenario success probability
        """
        sample_buildings = self.select_representative_sample(
            locator, size=sample_size
        )

        results = []
        for building in sample_buildings:
            result = self.test_building_pipeline(building)
            results.append(result)

        return TestReport(
            tests_run=len(results),
            passed=sum(r.passed for r in results),
            estimated_success_rate=self.estimate_full_scenario(results),
            problematic_patterns=self.identify_patterns(results)
        )
```

**UI Integration**:
```
🧪 Pre-Flight Test Suite

Testing 5 representative buildings...

✅ B1001 (MULTI_RES, 1950s) - All checks passed
✅ B1234 (OFFICE, 2010s) - All checks passed
⚠️  B1567 (INDUSTRIAL, 1970s) - 2 warnings
   • Heating schedule has only 10% on-hours
   • DHW demand unusually low (check use-type)
❌ B1890 (MIXED, 2025) - 1 error
   • Missing component: HEX7 in SUPPLY_COOLING

Estimated success rate: 60% (problems likely in 2/5 building types)

[Fix Issues & Retest] [View Details] [Run Full Scenario Anyway]
```

**Expected Impact**: Catch 90% of issues in <1 minute vs hours of full simulation

---

## Priority 5: Advanced Features for Power Users

### 5.1 Custom Validation Rules & Constraints

**Problem**: Different projects have different standards (e.g., Singapore vs Zurich codes).

**Proposed Feature**: User-definable validation rules

```yaml
# User can create: .cea/validation_rules.yml

rules:
  - name: "Singapore Window U-Value Standard"
    description: "Windows must meet BCA standards"
    applies_to: building_architecture
    condition: "latitude > 0 and latitude < 5"  # Singapore region
    constraint: "U_win <= 2.8"
    severity: warning

  - name: "No Gas Boilers in New Buildings"
    description: "Policy: New buildings must use heat pumps"
    applies_to: supply_systems
    condition: "year_built >= 2025"
    constraint: "heating_system_type != 'BOILER'"
    severity: error
    message: "Buildings after 2025 must use heat pumps or district heating"
```

**Expected Impact**: Enable CEA adaptation to local codes/policies

---

### 5.2 API for Automated Workflows

**Problem**: Repetitive manual tasks (run simulation → download → analyse → repeat).

**Proposed Feature**: Extend CEA Python API for automation

```python
# Example: Automated sensitivity analysis

from cea.api import CEAClient

client = CEAClient(cloud=True, api_key="...")

# Define parameter sweep
parameters = {
    'wall_insulation': [0.1, 0.2, 0.3, 0.4],  # U-values
    'window_type': ['DOUBLE', 'TRIPLE'],
    'heating_system': ['BOILER', 'HEATPUMP']
}

# Run automated experiments
results = client.run_parameter_sweep(
    base_scenario='fuxing_idp_2025',
    parameters=parameters,
    scripts=['demand', 'emissions'],
    max_concurrent=4
)

# Download results
df_results = results.to_dataframe()
df_results.to_csv('sensitivity_analysis.csv')
```

**Expected Impact**: Enable advanced users to build custom workflows

---

## Implementation Roadmap

### Phase 1 (Q1 2026): Quick Wins
- ✅ Enhanced error messages (Priority 1.2)
- ✅ Pre-flight input validator (Priority 1.1)
- ✅ Improved download UI (Priority 2.1)
- ✅ FAQ/Troubleshooting docs integrated into dashboard

**Estimated Effort**: 2-3 person-months
**Expected Impact**: 40% reduction in support requests

### Phase 2 (Q2 2026): UX Improvements
- ✅ Smart database editor (Priority 3.2)
- ✅ Simulation progress tracking (Priority 2.3)
- ✅ Change tracking system (Priority 2.2)
- ✅ Contextual help system (Priority 3.1)

**Estimated Effort**: 3-4 person-months
**Expected Impact**: 30% faster user workflows, 50% fewer errors

### Phase 3 (Q3-Q4 2026): Advanced Features
- ✅ Scenario branching & comparison (Priority 4.1)
- ✅ Automated test suite (Priority 4.2)
- ✅ Enhanced API (Priority 5.2)
- ✅ Custom validation rules (Priority 5.1)

**Estimated Effort**: 4-6 person-months
**Expected Impact**: Enable new research workflows, enterprise adoption

---

## Metrics for Success

Track these KPIs to measure improvement impact:

### Support Metrics
- **Support email volume** (target: -60% by end of Phase 2)
- **Average resolution time** (target: -50%)
- **Repeat issues** (same user, same problem: target <5%)

### User Experience Metrics
- **Time to first successful simulation** (new users: target <2 hours)
- **Simulation failure rate** (target <10% on first attempt)
- **FAQ search engagement** (target: 70% of users search before emailing)

### Platform Metrics
- **Scenario download success rate** (target >98%)
- **Database validation pass rate** (first attempt: target >80%)
- **Cloud storage usage** (target: -30% via better cleanup guidance)

---

## Conclusion

These improvements address **root causes**, not just symptoms:

1. **Shift-left validation**: Catch errors before expensive computations
2. **Actionable guidance**: Replace cryptic errors with solutions
3. **Transparency**: Show what's happening, not black-box processing
4. **Prevent, don't just fix**: Smart defaults and constraints

**Investment vs. Return**:
- Phase 1 (Quick Wins): ~3 months development → ~40% support reduction → ROI in 6 months
- Phase 2-3: ~10 months development → Enable new user segments (consulting, enterprise) → Strategic value

The user feedback shows CEA is powerful but has "usability debt". Addressing these systematically will:
- **Reduce support burden** (more time for new features)
- **Improve user retention** (fewer frustrated users)
- **Enable broader adoption** (lower learning curve)
- **Build user trust** (predictable, transparent behavior)
