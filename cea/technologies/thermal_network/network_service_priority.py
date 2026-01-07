"""
District Heating Service Priority Logic

Extracts service priority from plant node type to determine network temperature strategy.

For DH networks with multiple services (e.g., space heating + DHW), the plant type defines
which service determines the network temperature and which services use local boosters.

Example:
- PLANT_hs_ww: space heating priority → low-temp network (26-45°C), boosters for DHW
- PLANT_ww_hs: DHW priority → high-temp network (65°C), direct DHW supply
"""

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def get_itemised_dh_services_from_plant_type(plant_type):
    """
    Extract DH service priority list from plant node type.

    Reuses logic from network layout to parse plant type string into service priority list.

    :param plant_type: Plant node type string (e.g., 'PLANT_hs_ww', 'PLANT_ww')
    :return: List of services in priority order, or None for legacy behavior
    :rtype: list or None

    Examples:
        'PLANT_hs_ww' → ['space_heating', 'dhw'] (space heating priority)
        'PLANT_ww_hs' → ['dhw', 'space_heating'] (DHW priority)
        'PLANT_ww' → ['dhw']
        'PLANT' → None (legacy: max of all temps)
    """
    from cea.technologies.network_layout.plant_node_operations import get_services_from_plant_type

    services, is_legacy = get_services_from_plant_type(plant_type)

    if is_legacy:
        # Legacy plant type (e.g., 'PLANT') - trigger max temperature behavior
        return None
    else:
        # Modern plant type with service priority
        return services


def get_heating_systems_for_network_temp(itemised_dh_services, all_heating_systems):
    """
    Determine which heating systems should be used for network temperature calculation.

    When service priority is defined, only the PRIMARY service determines network temp.
    Other services use local boosters to reach their required temperatures.

    :param itemised_dh_services: Service priority list from plant type, or None
    :param all_heating_systems: All available heating systems ['aru', 'ahu', 'shu', 'ww']
    :return: List of heating systems to consider for network temperature
    :rtype: list

    Examples:
        itemised_dh_services=['space_heating', 'dhw'] → ['aru', 'ahu', 'shu'] (only space heating)
        itemised_dh_services=['dhw'] → ['ww'] (only DHW)
        itemised_dh_services=None → ['aru', 'ahu', 'shu', 'ww'] (legacy: all systems)
    """
    if itemised_dh_services is not None and len(itemised_dh_services) > 0:
        # Use only PRIMARY service for network temp calculation
        primary_service = itemised_dh_services[0]

        if primary_service == 'space_heating':
            # Network temp based on space heating only
            # DHW will use boosters to reach 60°C
            return ['aru', 'ahu', 'shu']
        elif primary_service == 'dhw':
            # Network temp based on DHW only (65°C)
            # Space heating served directly (network hotter than needed)
            return ['ww']
        else:
            # Unknown primary service, use all (conservative)
            return all_heating_systems
    else:
        # Legacy mode: network temp = max of ALL services
        return all_heating_systems
