"""
Simplified formatting for baseline costs output.

Summary file: Only aggregated totals
Detailed file: All components with full information
"""

import pandas as pd


def format_output_simplified(merged_results, locator):
    """
    Format results into simplified summary and comprehensive detailed files.

    Summary file: Only aggregated totals (no per-service columns)
    Detailed file: All components, energy carriers, and piping with service info

    :param merged_results: Merged results from all network types
    :param locator: InputLocator instance
    :return: (summary_df, detailed_df) tuple of DataFrames
    """
    # Read demand to get building list and GFA
    demand = pd.read_csv(locator.get_total_demand())

    summary_rows = []
    detailed_rows = []

    # Sort results: buildings first (B*), then networks (N*)
    sorted_identifiers = sorted(merged_results.keys(),
                                key=lambda x: (x.startswith('N'), x))

    for identifier in sorted_identifiers:
        network_data = merged_results[identifier]

        # Check if this is a network or a building
        is_network = network_data.get('DH', {}).get('is_network', False) or \
                     network_data.get('DC', {}).get('is_network', False)

        # Get GFA
        if is_network:
            # Network: sum GFA from all buildings
            buildings_in_network = network_data.get('DH', {}).get('buildings') or \
                                 network_data.get('DC', {}).get('buildings', [])
            total_gfa = 0.0
            for building in buildings_in_network:
                building_demand = demand[demand['name'] == building.identifier]
                if not building_demand.empty:
                    total_gfa += building_demand.iloc[0]['GFA_m2']

            # Remove _DC or _DH suffix from network name
            display_name = identifier.replace('_DC', '').replace('_DH', '')
        else:
            # Building: get GFA from demand
            building_demand = demand[demand['name'] == identifier]
            if building_demand.empty:
                print(f"Warning: Building {identifier} not found in demand, skipping.")
                continue
            total_gfa = building_demand.iloc[0]['GFA_m2']
            display_name = identifier

        # Initialize cost accumulators for summary
        summary = {
            'name': display_name,
            'GFA_m2': total_gfa,
            'Capex_total_USD': 0.0,
            'Capex_a_USD': 0.0,
            'Opex_fixed_a_USD': 0.0,
            'Opex_var_a_USD': 0.0,
            'Opex_a_USD': 0.0,
            'TAC_USD': 0.0,
            # Scale breakdowns (building vs district)
            'Capex_total_building_scale_USD': 0.0,
            'Capex_total_district_scale_USD': 0.0,
            'Capex_a_building_scale_USD': 0.0,
            'Capex_a_district_scale_USD': 0.0,
            'Opex_a_building_scale_USD': 0.0,
            'Opex_a_district_scale_USD': 0.0,
        }

        # Process costs from each network type (DH, DC, or standalone)
        for network_type, data in network_data.items():
            if 'costs' not in data:
                continue

            # Determine display network_type for detailed rows
            if is_network:
                display_network_type = network_type
            else:
                display_network_type = ''

            # Process each service's costs
            for service_name, service_costs in data['costs'].items():
                scale = service_costs['scale']

                # Accumulate to summary
                summary['Capex_total_USD'] += service_costs['capex_total_USD']
                summary['Capex_a_USD'] += service_costs['capex_a_USD']
                summary['Opex_fixed_a_USD'] += service_costs['opex_a_fixed_USD']
                summary['Opex_var_a_USD'] += service_costs['opex_a_var_USD']
                summary['Opex_a_USD'] += service_costs['opex_a_USD']
                summary['TAC_USD'] += service_costs['TAC_USD']

                # Accumulate scale breakdowns
                if scale == 'BUILDING':
                    summary['Capex_total_building_scale_USD'] += service_costs['capex_total_USD']
                    summary['Capex_a_building_scale_USD'] += service_costs['capex_a_USD']
                    summary['Opex_a_building_scale_USD'] += service_costs['opex_a_USD']
                elif scale == 'DISTRICT':
                    summary['Capex_total_district_scale_USD'] += service_costs['capex_total_USD']
                    summary['Capex_a_district_scale_USD'] += service_costs['capex_a_USD']
                    summary['Opex_a_district_scale_USD'] += service_costs['opex_a_USD']
                # Note: CITY scale removed - not commonly used and can be added back if needed

                # Add physical components to detailed output
                for comp in service_costs['components']:
                    detailed_rows.append({
                        'name': display_name,
                        'network_type': display_network_type,
                        'service': service_name,
                        'code': comp['code'],
                        'capacity_kW': comp['capacity_kW'],
                        'placement': comp['placement'],
                        'capex_total_USD': comp['capex_total_USD'],
                        'capex_a_USD': comp['capex_a_USD'],
                        'opex_fixed_a_USD': comp['opex_fixed_a_USD'],
                        'opex_var_a_USD': 0.0,  # Components don't have variable costs
                        'scale': scale
                    })

                # Add energy costs to detailed output
                for energy_cost in service_costs.get('energy_costs', []):
                    detailed_rows.append({
                        'name': display_name,
                        'network_type': display_network_type,
                        'service': service_name,
                        'code': energy_cost['carrier'],  # e.g., E230AC, NATURALGAS
                        'capacity_kW': 0.0,  # N/A for energy carriers
                        'placement': 'energy_carrier',
                        'capex_total_USD': 0.0,
                        'capex_a_USD': 0.0,
                        'opex_fixed_a_USD': 0.0,
                        'opex_var_a_USD': energy_cost['opex_a_var_USD'],
                        'scale': scale
                    })

            # Add network piping costs to detailed output
            if is_network and 'piping_cost_annual' in data and data['piping_cost_annual'] > 0:
                piping_cost_annual = data['piping_cost_annual']
                piping_cost_total = data.get('piping_cost_total', 0.0)

                # Add to summary totals
                summary['Capex_total_USD'] += piping_cost_total
                summary['Capex_a_USD'] += piping_cost_annual
                summary['TAC_USD'] += piping_cost_annual
                summary['Capex_total_district_scale_USD'] += piping_cost_total
                summary['Capex_a_district_scale_USD'] += piping_cost_annual

                # Add to detailed
                detailed_rows.append({
                    'name': display_name,
                    'network_type': network_type,
                    'service': f'{network_type}_network',
                    'code': 'PIPES',
                    'capacity_kW': 0.0,
                    'placement': 'distribution',
                    'capex_total_USD': piping_cost_total,
                    'capex_a_USD': piping_cost_annual,
                    'opex_fixed_a_USD': 0.0,
                    'opex_var_a_USD': 0.0,
                    'scale': 'DISTRICT'
                })

        # Add zero-cost placeholder for buildings with no costs
        if not is_network and summary['TAC_USD'] == 0.0:
            detailed_rows.append({
                'name': display_name,
                'network_type': '',
                'service': 'NONE',
                'code': 'NONE',
                'capacity_kW': 0.0,
                'placement': 'NONE',
                'capex_total_USD': 0.0,
                'capex_a_USD': 0.0,
                'opex_fixed_a_USD': 0.0,
                'opex_var_a_USD': 0.0,
                'scale': 'BUILDING'
            })

        summary_rows.append(summary)

    summary_df = pd.DataFrame(summary_rows)
    detailed_df = pd.DataFrame(detailed_rows)

    return summary_df, detailed_df
