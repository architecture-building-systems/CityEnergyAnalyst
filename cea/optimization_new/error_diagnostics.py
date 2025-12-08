"""
Error diagnostic utilities for supply system energy carrier mismatches.

Provides detailed error messages and component compatibility analysis when supply system
components cannot generate the required energy carrier for building demands.
"""

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


from cea.optimization_new.containerclasses.energyCarrier import EnergyCarrier


def generate_energy_carrier_mismatch_error(
    supply_system_target,
    component_placement,
    demand_energy_carrier,
    component_codes,
    component_capacity,
    active_component_classes
):
    """
    Generate detailed error message for energy carrier mismatch with diagnostics and suggestions.

    Parameters
    ----------
    supply_system_target : str
        Name of the supply system (e.g., 'xxxx_DH')
    component_placement : str
        Component category ('primary', 'secondary', etc.)
    demand_energy_carrier : str
        Required energy carrier code (e.g., 'T30W')
    component_codes : list[str]
        List of component codes that failed (e.g., ['HP1'])
    component_capacity : dict
        Component capacity information
    active_component_classes : list
        List of active component class definitions

    Returns
    -------
    str
        Formatted error message with diagnostics and suggestions
    """
    demand_ec = EnergyCarrier.from_code(demand_energy_carrier)

    # Analyze each component to understand why it failed
    component_analysis = []
    medium_mismatches = []
    temp_too_low = []
    temp_too_high = []
    unsupported_components = []

    from cea.optimization_new.component import ActiveComponent

    for comp_code in component_codes:
        if comp_code not in ActiveComponent.code_to_class_mapping:
            continue

        comp_class = ActiveComponent.code_to_class_mapping[comp_code]
        try:
            # Try to instantiate to get energy carrier info
            component = comp_class(comp_code, component_placement, component_capacity)
            comp_ec = component.main_energy_carrier

            if comp_ec.type != demand_ec.type:
                component_analysis.append(f"  - {comp_code}: outputs {comp_ec.type} (need {demand_ec.type})")
            elif demand_ec.type == 'thermal':
                if comp_ec.subtype != demand_ec.subtype:
                    medium_mismatches.append({
                        'code': comp_code,
                        'output': comp_ec.code,
                        'output_medium': comp_ec.subtype,
                        'output_temp': comp_ec.mean_qual
                    })
                    component_analysis.append(
                        f"  - {comp_code}: outputs {comp_ec.subtype} at {comp_ec.mean_qual:.0f}°C "
                        f"({comp_ec.code}), need {demand_ec.subtype} ({demand_energy_carrier})"
                    )
                elif comp_ec.mean_qual < demand_ec.mean_qual:
                    temp_too_low.append({
                        'code': comp_code,
                        'output': comp_ec.code,
                        'output_temp': comp_ec.mean_qual
                    })
                    component_analysis.append(
                        f"  - {comp_code}: outputs {demand_ec.subtype} at {comp_ec.mean_qual:.0f}°C "
                        f"({comp_ec.code}), need ≥{demand_ec.mean_qual:.0f}°C ({demand_energy_carrier})"
                    )
                elif comp_ec.mean_qual > demand_ec.mean_qual:
                    # This should work with heat exchanger, but something else failed
                    temp_too_high.append({
                        'code': comp_code,
                        'output': comp_ec.code,
                        'output_temp': comp_ec.mean_qual
                    })
            else:
                component_analysis.append(f"  - {comp_code}: outputs {comp_ec.code}")
        except TypeError:
            # Component has non-standard initialization (e.g., HeatExchanger requires temperature_before/after)
            # This indicates the component type is not supported in this context
            unsupported_components.append(comp_code)
            component_analysis.append(f"  - {comp_code}: unsupported component type for this operation")
        except (ValueError, KeyError) as e:
            component_analysis.append(f"  - {comp_code}: failed to instantiate ({str(e)[:50]})")

    # Build error message
    error_lines = [
        f"\n{'='*70}",
        "ENERGY CARRIER COMPATIBILITY ERROR",
        f"{'='*70}",
        "",
        f"Supply system: {supply_system_target}",
        f"Component placement: {component_placement}",
        f"Required energy carrier: {demand_energy_carrier} ({demand_ec.type}",
    ]

    if demand_ec.type == 'thermal':
        error_lines[-1] += f", {demand_ec.subtype}, {demand_ec.mean_qual:.0f}°C)"
    else:
        error_lines[-1] += ")"

    error_lines.extend([
        f"Peak demand: {component_capacity:.2f} kW",
        "",
        "Component analysis:",
    ])
    error_lines.extend(component_analysis)

    # Provide specific suggestions based on failure mode
    error_lines.extend([
        "",
        f"{'='*70}",
        "DIAGNOSIS & SOLUTIONS",
        f"{'='*70}",
    ])

    if medium_mismatches:
        error_lines.extend([
            "",
            "Issue: MEDIUM MISMATCH",
            f"  Components output {medium_mismatches[0]['output_medium']}, but demand requires {demand_ec.subtype}.",
            "  Different mediums (water/air/brine) cannot be converted with passive components.",
            "",
            "Solutions:",
            f"  1. Use components that output {demand_ec.subtype}:",
        ])

        # Suggest compatible components by searching database
        compatible_components = find_compatible_components(
            demand_ec.subtype, demand_ec.mean_qual, component_placement,
            active_component_classes
        )

        if compatible_components:
            error_lines.append(f"     - Components in your database that output {demand_ec.subtype}:")
            for comp_code, comp_info in compatible_components.items():
                error_lines.append(
                    f"       * {comp_code}: {comp_info['description']} "
                    f"({comp_info['output_temp']:.0f}°C → {comp_info['energy_carrier']})"
                )
            error_lines.extend([
                "",
                "  2. Change SUPPLY assembly to use compatible components:",
                "     - Edit: ASSEMBLIES/SUPPLY/SUPPLY_*",
            ])

            if compatible_components:
                first_compatible = list(compatible_components.keys())[0]
                error_lines.append(f"     - Set primary_components to: {first_compatible} (or any from list above)")
        else:
            error_lines.extend([
                "     - No compatible components found in database!",
                "       You may need to add components to:",
                "       COMPONENTS/CONVERSION/*",
            ])

    elif temp_too_low:
        min_temp_component = min(temp_too_low, key=lambda x: x['output_temp'])
        error_lines.extend([
            "",
            "Issue: TEMPERATURE TOO LOW",
            f"  Components output {min_temp_component['output_temp']:.0f}°C ({min_temp_component['output']}),",
            f"  but demand requires ≥{demand_ec.mean_qual:.0f}°C ({demand_energy_carrier}).",
            "  Cannot heat up passively - need active heating component.",
            "",
            "Solutions:",
            "  1. Use higher-temperature components:",
        ])

        # Find components with temperature >= required
        compatible_hot = find_compatible_components(
            demand_ec.subtype, demand_ec.mean_qual, component_placement,
            active_component_classes
        )

        if compatible_hot:
            error_lines.append(f"     - Components in your database with ≥{demand_ec.mean_qual:.0f}°C output:")
            for comp_code, comp_info in list(compatible_hot.items())[:5]:  # Show top 5
                error_lines.append(
                    f"       * {comp_code}: {comp_info['output_temp']:.0f}°C → {comp_info['energy_carrier']}"
                )
        else:
            error_lines.append(f"     - No components found with ≥{demand_ec.mean_qual:.0f}°C output in database")

        error_lines.extend([
            "",
            "  2. Check if demand temperature is correct:",
            "     - DHW (domestic hot water): typically requires 60°C",
            "     - Space heating: typically 30-40°C for low-temp systems",
            "     - District networks: may aggregate multiple demand types",
        ])

    elif unsupported_components:
        # Component type not supported in this context (e.g., HeatExchanger with special initialization)
        error_lines.extend([
            "",
            "Issue: UNSUPPORTED COMPONENT TYPE",
            f"  Component(s) {', '.join(unsupported_components)} cannot be used in this context.",
            "  These components require special initialisation parameters that are not available",
            "  during automatic system generation.",
            "",
            "Explanation:",
            "  - HeatExchanger (HEX) requires source and sink temperature specifications",
            "  - These passive components need active components to drive them",
            "  - They cannot be used as standalone primary/tertiary components",
            "",
            "Solutions:",
            "  1. Replace unsupported components in SUPPLY assembly:",
            "     - For heat rejection in cooling systems:",
            "       * Use COOLING_TOWERS (CT1, CT2, CT3) instead of HEAT_EXCHANGERS",
            "       * Cooling towers actively reject heat to the environment",
            "     - For district cooling with lake/sea water:",
            "       * Heat exchangers (HEX) are valid but require custom system design",
            "       * Consider using component-based configuration instead of SUPPLY assemblies",
            "",
            "  2. Edit SUPPLY assembly:",
            "     - ASSEMBLIES/SUPPLY/SUPPLY_*",
            f"     - Change tertiary_components from {unsupported_components[0]} to CT1 (or similar)",
            "",
            "  3. Alternative: Use component categories instead of SUPPLY assemblies:",
            "     - Set heat-rejection-components parameter to: COOLING_TOWERS",
            "     - Leave supply-type-cs parameter empty or set to 'Custom'",
        ])

    else:
        # Generic error (capacity, availability, etc.)
        error_lines.extend([
            "",
            "Issue: COMPONENT UNAVAILABLE OR INCOMPATIBLE",
            "  Components may not exist in database or cannot meet capacity requirements.",
            "",
            "Solutions:",
            "  1. Check component database:",
            "     COMPONENTS/CONVERSION/*",
            "     - BOILERS",
            "     - HEAT_PUMPS",
            "     - CHILLERS",
            "",
            "  2. Verify component codes in SUPPLY assembly:",
            "     ASSEMBLIES/SUPPLY/*",
            "",
            "  3. Check system-costs parameters:",
            "     - supply-type-hs, supply-type-cs, supply-type-dhw",
            "     - heating-components, cooling-components",
        ])

    error_lines.extend([
        "",
        f"{'='*70}",
        "For more information, see:",
        "  - ",
        "  - ",
        f"{'='*70}",
    ])

    return "\n".join(error_lines)


def find_compatible_components(
    required_subtype,
    required_temp,
    component_placement,
    active_component_classes
):
    """
    Find components in the database that output the required medium and can satisfy temperature.

    Parameters
    ----------
    required_subtype : str
        Required medium ('water', 'air', 'brine')
    required_temp : float
        Required temperature in °C (or None for non-thermal)
    component_placement : str
        Component category ('primary', 'secondary', 'tertiary')
    active_component_classes : list
        List of active component class definitions

    Returns
    -------
    dict
        Dictionary of compatible components: {code: {description, output_temp, energy_carrier}}
        Sorted by temperature closeness to requirement
    """
    from cea.optimization_new.component import ActiveComponent

    if not ActiveComponent.code_to_class_mapping:
        return {}

    compatible = {}

    # Get relevant component classes based on component_placement
    for comp_class in active_component_classes:
        # Get all component codes for this class
        if hasattr(comp_class, '_available_component_data') and comp_class._available_component_data is not None:
            component_codes = comp_class._available_component_data['code'].unique()

            for code in component_codes:
                try:
                    # Try to instantiate with small capacity to check output
                    component = comp_class(code, component_placement, 100)  # 100 kW test capacity
                    comp_ec = component.main_energy_carrier

                    # Check if medium matches
                    if comp_ec.type == 'thermal' and comp_ec.subtype == required_subtype:
                        # For heating: component must output >= required temperature
                        # (higher temps can be cooled down via heat exchanger)
                        if required_temp is None or comp_ec.mean_qual >= required_temp:
                            compatible[code] = {
                                'description': component._model_data.get('description', [''])[0] if hasattr(component, '_model_data') else '',
                                'output_temp': comp_ec.mean_qual,
                                'energy_carrier': comp_ec.code
                            }
                except (ValueError, KeyError, IndexError):
                    # Component instantiation failed, skip it
                    continue

    # Sort by temperature (closest to required first)
    if required_temp and compatible:
        compatible = dict(sorted(
            compatible.items(),
            key=lambda x: abs(x[1]['output_temp'] - required_temp)
        ))

    return compatible
