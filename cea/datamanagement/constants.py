# -*- coding: utf-8 -*-
"""
This file contains the constants used in the data management tools
"""




__author__ = "Martin Mosteiro-Romero"
__copyright__ = "Copyright 2021, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Martin Mosteiro-Romero"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# OSM building category converters
OSM_BUILDING_CATEGORIES = {
    'apartments': 'MULTI_RES', 'dormitory': 'MULTI_RES', 'residential': 'MULTI_RES', 'terrace': 'MULTI_RES',
    'house': 'SINGLE_RES', 'bungalow': 'SINGLE_RES', 'cabin': 'SINGLE_RES', 'detached': 'SINGLE_RES',
    'farm': 'SINGLE_RES', 'ger': 'SINGLE_RES', 'houseboat': 'SINGLE_RES', 'semidetached_house': 'SINGLE_RES',
    'static_caravan': 'SINGLE_RES',
    'hotel': 'HOTEL',
    'office': 'OFFICE', 'civic': 'OFFICE', 'commercial': 'OFFICE', 'government': 'OFFICE',
    'industrial': 'INDUSTRIAL',
    'retail': 'RETAIL', 'kiosk': 'RETAIL',
    'supermarket': 'FOODSTORE',
    'hospital': 'HOSPITAL',
    'school': 'SCHOOL', 'kindergarten': 'SCHOOL',
    'university': 'UNIVERSITY', 'college': 'UNIVERSITY',
    'sports_hall': 'GYM', 'pavilion': 'GYM',
    'parking': 'PARKING', 'carport': 'PARKING', 'garage': 'PARKING', 'garages': 'PARKING', 'hangar': 'PARKING'}
    # most common OSM building categories according to wiki.openstreetmap.org converted to CEA building use types
    # the "yes" category is excluded so that the default CEA assumption is used instead

OTHER_UNHEATED_OSM_CATEGORIES = ['warehouse', 'roof', 'transportation', 'train_station', 'hut', 'shed', 'service',
                                 'transformer_tower', 'water_tower', 'bridge']
    # other unheated use types that don't have a specific CEA use type will be assigned as 'PARKING'
