# Docstring Specification for Physics-Based Functions

This document defines the standardised docstring format for physics and engineering calculation functions in CEA.

## Scope

This specification applies to:
- Functions implementing physics formulas (hydraulics, heat transfer, thermodynamics)
- Functions based on international standards (ISO, EN, VDI, SIA)
- Engineering calculations with empirical correlations

## Standard Docstring Structure

### Template

```python
def function_name(param1, param2):
    """
    [ONE-LINE SUMMARY: Verb phrase describing what the function calculates]

    Standards Compliance
    --------------------
    - [Standard/Reference 1]: [What it covers]
    - [Standard/Reference 2]: [What it covers]

    [OPTIONAL SECTION: Formula/Flow Regimes/Correlations]
    -------------------------------------------------------
    [Mathematical equations or regime descriptions]

    [OPTIONAL SECTION: Valid Ranges]
    --------------------------------
    [Parameter validity constraints]

    Parameters
    ----------
    param1 : type
        Description [units]
        [Optional: Additional constraints or typical values]
    param2 : type
        Description [units]

    Returns
    -------
    type
        Description [units]

    [OPTIONAL: Raises]
    ------------------
    ExceptionType
        Conditions when raised

    References
    ----------
    [Citation1] Author et al. (Year). Title. Journal, Volume, Pages.
    [Citation2] Standard: Standard Name

    Notes
    -----
    [Essential context, physical interpretation, usage notes]
    [Implementation details only if non-obvious]
    """
```

## Section Requirements

### 1. One-Line Summary (REQUIRED)
- **Format**: Start with verb (Calculate, Determine, Compute)
- **Length**: Single sentence, max 80 characters
- **Content**: What the function calculates (not how)

**Good:**
```python
"""Calculate Darcy friction factor using flow regime-appropriate correlations."""
```

**Bad:**
```python
"""This function uses the Swamee-Jain equation to calculate friction factors."""  # Too wordy
"""Friction factor calculation."""  # Too vague
```

### 2. Standards Compliance (REQUIRED for standards-based functions)
- **Format**: Bullet list with standard name and coverage
- **Order**: Most authoritative/primary standard first
- **Content**:
  - Standard name/number
  - What aspect it covers
  - Year if relevant

**Example:**
```python
Standards Compliance
--------------------
- Darcy-Weisbach equation: Fundamental fluid mechanics
- EN 13941-1:2019: District heating pipe hydraulic calculations
- Swamee-Jain equation: Swamee & Jain (1976)
```

### 3. Formula/Flow Regimes/Correlations (CONDITIONAL)

**Include when:**
- Function implements multiple regimes (laminar/turbulent)
- Formula is complex or non-obvious
- Multiple correlations used

**Format options:**

**Option A: Single formula**
```python
Formula
-------
ΔP = f × 8 × m² × L / (π² × D⁵ × ρ)  [Pa]

where:
    - f: Darcy friction factor
    - m: mass flow rate [kg/s]
    - L: pipe length [m]
```

**Option B: Multiple regimes**
```python
Flow Regimes
------------
Laminar (Re ≤ 2300):
    f = 64/Re
    [Standard laminar flow correlation]

Turbulent (Re > 5000):
    f = 1.325 × [ln(ε/(3.7D) + 5.74/Re⁰·⁹)]⁻²
    [Swamee-Jain explicit equation]
```

**Option C: Correlations by case**
```python
Correlations by Flow Regime
----------------------------
Laminar (Re ≤ 2300):
    Nu = 3.66  [fully developed, constant wall temperature]

Turbulent (Re > 10000):
    Nu = 0.023 × Re^0.8 × Pr^n  [Dittus-Boelter]
    where n = 0.3 for heating
          n = 0.4 for cooling
```

### 4. Valid Ranges (CONDITIONAL)

**Include when:**
- Formula has specific applicability limits
- Parameters must be within certain ranges for accuracy

**Format:**
```python
Valid Ranges
------------
- Reynolds number: 5,000 - 10⁸
- Relative roughness (ε/D): 10⁻⁶ - 0.05
- Accuracy: ±1% vs. Colebrook-White
```

Or:
```python
Valid Range
-----------
273 K ≤ T ≤ 413 K (0-140°C for liquid water)
Accuracy: ±2% for the valid temperature range
```

### 5. Parameters (REQUIRED)
- **Format**: NumPy-style parameter list
- **Type**: Include array dimensions if relevant (e.g., "ndarray (e x 1)")
- **Units**: Always include in square brackets [unit]
- **Details**: Add typical values or ranges if helpful

**Example:**
```python
Parameters
----------
pipe_diameter_m : ndarray
    Pipe diameter [m] for each edge (e x 1)
reynolds : ndarray
    Reynolds number [-] for each edge (e x 1)
pipe_roughness_m : float
    Absolute pipe roughness [m]
    Typical value: 0.02 mm (2×10⁻⁵ m) for steel pipe
    Range: 10⁻⁶ - 0.05 m (EN 13941)
network_type : str
    Network type:
    - 'DH': District heating
    - 'DC': District cooling
```

### 6. Returns (REQUIRED)
- **Format**: Type and description with units
- **Multiple returns**: Separate each return value

**Example:**
```python
Returns
-------
ndarray
    Darcy friction factor [-] for each edge (e x 1)
```

Or with multiple outcomes:
```python
Returns
-------
ndarray
    Pressure loss [Pa] through each edge at each time (t x e)
    Or pressure loss derivative [Pa·s/kg] if loop_type = 1
```

### 7. Raises (CONDITIONAL)
**Include only when:** Function raises specific exceptions for validation

**Format:**
```python
Raises
------
ValueError
    If logarithm argument is invalid in Swamee-Jain calculation
    (indicates extreme pipe roughness or diameter values)
```

### 8. References (REQUIRED for standards-based functions)
- **Format**: `[Tag] Citation`
- **Order**: Most relevant/authoritative first
- **Content**:
  - Journal articles: Author et al. (Year). Title. Journal, Volume, Pages.
  - Standards: Standard: Full standard name
  - Books: Author (Year). Title. Edition. Publisher.

**Example:**
```python
References
----------
[Oppelt2016] Oppelt, T., et al. (2016). Applied Thermal Engineering, 102, 336-345.
[Colebrook1939] Colebrook, C.F. (1939). J. Institution of Civil Engineers.
[White2016] White, F.M. (2016). Fluid Mechanics (8th ed.). McGraw-Hill
[EN13941] EN 13941-1:2019: District heating pipes design standard
```

### 9. Notes (CONDITIONAL)
**Include when:** Essential context needed for understanding

**Use for:**
- Physical interpretation of results
- Important implementation details
- Usage guidance
- Relationship to other functions

**Keep concise:** 2-5 sentences maximum

**Example:**
```python
Notes
-----
The Darcy-Weisbach equation is the fundamental equation for pressure loss
in pipe flow and is valid for all flow regimes (laminar, transition, turbulent).

The loop_type parameter allows this function to be used both in:
1. Direct pressure loss calculation for network branches
2. Iterative network solving using the gradient method
```

## What NOT to Include

❌ **Avoid these sections:**
- `See Also` - Users can grep/search
- `Examples` - Code should be self-explanatory
- `Warnings` - Use Raises section instead
- Implementation history/changelog - Use git
- Author information - Use module docstring
- Overly detailed derivations - Link to references instead

❌ **Avoid in descriptions:**
- Obvious statements ("This parameter is required")
- Implementation details better suited for inline comments
- Marketing language ("powerful", "efficient", "advanced")

## Section Order (Fixed)

The order MUST be:
1. One-line summary
2. Standards Compliance
3. Formula/Flow Regimes/Correlations (if applicable)
4. Valid Ranges (if applicable)
5. Parameters
6. Returns
7. Raises (if applicable)
8. References
9. Notes (if applicable)

## Formatting Rules

### Headers
- Use dashes (----) under headers, matching header length
- Keep consistent indentation (4 spaces)

### Mathematical notation
- Use Unicode symbols: × ≤ ≥ ² ³ ⁰·⁸ π ε ρ ν μ ∂ Δ
- Always include units in square brackets: [Pa], [kg/s], [m]
- Use superscripts for powers: Re⁰·⁸, not Re^0.8 (except in code blocks)

### Lists
- Use dashes (-) for bullet points
- Numbered lists: Use 1., 2., 3.
- Indent continuations by 4 spaces

## Examples by Function Type

### Example 1: Complex Multi-Regime Function
```python
def calc_darcy(pipe_diameter_m, reynolds, pipe_roughness_m):
    """
    Calculate Darcy friction factor using flow regime-appropriate correlations.

    Standards Compliance
    --------------------
    - Colebrook-White equation: Colebrook (1939)
    - Swamee-Jain: Explicit approximation with ±1% accuracy

    Flow Regimes
    ------------
    1. Laminar (Re ≤ 2300):
           f = 64/Re
       [Standard laminar flow correlation]

    2. Transition (2300 < Re ≤ 5000):
           f = 0.316 × Re⁻⁰·²⁵
       [Blasius equation for smooth pipes]

    3. Turbulent (Re > 5000):
           f = 1.325 × [ln(ε/(3.7D) + 5.74/Re⁰·⁹)]⁻²
       [Swamee-Jain explicit equation]

    Valid Ranges (Turbulent)
    -------------------------
    - Reynolds number: 5,000 - 10⁸
    - Relative roughness (ε/D): 10⁻⁶ - 0.05
    - Accuracy: ±1% vs. Colebrook-White

    Parameters
    ----------
    pipe_diameter_m : ndarray
        Pipe diameter [m] for each edge (e x 1)
    reynolds : ndarray
        Reynolds number [-] for each edge (e x 1)
    pipe_roughness_m : float
        Absolute pipe roughness [m]
        Typical value: 0.02 mm (2×10⁻⁵ m) for steel pipe

    Returns
    -------
    ndarray
        Darcy friction factor [-] for each edge (e x 1)

    Raises
    ------
    ValueError
        If logarithm argument is invalid in Swamee-Jain calculation

    References
    ----------
    [Colebrook1939] Colebrook, C.F. (1939). J. Institution of Civil Engineers
    [SwameeJain1976] Swamee, P.K.; Jain, A.K. (1976). J. Hydraulics Division, ASCE
    [Incropera2007] Incropera, F.P., et al. (2007). Fundamentals of Heat and Mass Transfer

    Notes
    -----
    The Swamee-Jain equation provides an explicit solution to the Colebrook-White
    equation, eliminating the need for iterative calculations whilst maintaining
    accuracy within ±1%.

    For transition regime (2300 < Re ≤ 5000), a smooth pipe approximation is used
    as roughness effects are minimal at low Reynolds numbers.
    """
```

### Example 2: Simple Formula Function
```python
def calc_reynolds(mass_flow_rate_kgs, temperature__k, pipe_diameter_m):
    """
    Calculate Reynolds number for internal pipe flow.

    Standards Compliance
    --------------------
    - Standard fluid mechanics definition (Reynolds, 1883)

    Formula
    -------
    Re = 4 × ṁ / (π × D × μ) = 4 × Q / (π × D × ν)  [-]

    where:
        - ṁ: mass flow rate [kg/s]
        - Q: volumetric flow rate [m³/s]
        - D: pipe diameter [m]
        - μ: dynamic viscosity [Pa·s]
        - ν: kinematic viscosity [m²/s]

    Parameters
    ----------
    mass_flow_rate_kgs : ndarray
        Mass flow rate [kg/s]
    temperature__k : ndarray or list
        Fluid temperature [K] (used to calculate viscosity)
    pipe_diameter_m : ndarray
        Pipe diameter [m]

    Returns
    -------
    ndarray
        Reynolds number [-] for each flow condition

    Notes
    -----
    The Reynolds number represents the ratio of inertial forces to viscous forces.
    Flow regimes: Re < 2300 (laminar), 2300 < Re < 5000 (transition), Re > 5000 (turbulent).
    """
```

### Example 3: Property Function
```python
def calc_kinematic_viscosity(temperature):
    """
    Calculate kinematic viscosity of water as function of temperature.

    Formula
    -------
    ν(T) = 2.652623×10⁻⁸ × exp(557.5447/(T-140))  [m²/s]

    Parameters
    ----------
    temperature : ndarray, list, or float
        Water temperature [K]
        Valid range: 273-413 K (0-140°C)

    Returns
    -------
    ndarray or float
        Kinematic viscosity [m²/s]

    Valid Range
    -----------
    273 K ≤ T ≤ 413 K (0-140°C for liquid water)
    Accuracy: ±2% for the valid temperature range

    References
    ----------
    [EngToolbox] Exponential fit to Engineering Toolbox water viscosity data

    Notes
    -----
    Kinematic viscosity (ν) is the ratio of dynamic viscosity (μ) to density (ρ).
    For water, viscosity decreases exponentially with temperature.
    """
```

## Validation Checklist

Use this checklist when writing or reviewing physics function docstrings:

- [ ] One-line summary starts with verb
- [ ] Standards Compliance section present (if standards-based)
- [ ] Standards correctly cited (no ISO 5167 for non-flow-measurement)
- [ ] Formula section included if non-trivial
- [ ] All parameters have types and units
- [ ] Return value has type and units
- [ ] References use proper citation format [Tag] Author (Year)
- [ ] Notes section concise (≤5 sentences)
- [ ] Mathematical notation uses Unicode symbols
- [ ] Section order follows specification
- [ ] All units in square brackets [unit]

## When to Deviate

This specification may be relaxed for:
- Simple utility functions (getters, setters, formatters)
- Internal helper functions (underscore prefix)
- Functions with no physics/engineering content

But physics-based calculations MUST follow this specification.
