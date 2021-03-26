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
    'residential': 'MULTI_RES',
    'apartments': 'MULTI_RES',
    'dormitory': 'MULTI_RES',
    'terrace': 'MULTI_RES',
    'nursing_home': 'MULTI_RES',
    'social_facility': 'MULTI_RES',
    'house': 'SINGLE_RES',
    'bungalow': 'SINGLE_RES',
    'cabin': 'SINGLE_RES',
    'detached': 'SINGLE_RES',
    'farm': 'SINGLE_RES',
    'ger': 'SINGLE_RES',
    'houseboat': 'SINGLE_RES',
    'semidetached_house': 'SINGLE_RES',
    'static_caravan': 'SINGLE_RES',
    'hotel': 'HOTEL',
    'office': 'OFFICE',
    'civic': 'OFFICE',
    'commercial': 'OFFICE',
    'government': 'OFFICE',
    'bureau_de_change': 'OFFICE',
    'courthouse': 'OFFICE',
    'embassy': 'OFFICE',
    'post_office': 'OFFICE',
    'townhall': 'OFFICE',
    'industrial': 'INDUSTRIAL',
    'retail': 'RETAIL',
    'kiosk': 'RETAIL',
    'bank': 'RETAIL', 'pharmacy':
    'RETAIL', 'marketplace': 'RETAIL',
    'supermarket': 'FOODSTORE',
    'restaurant': 'RESTAURANT',
    'fast_food': 'RESTAURANT',
    'food_court': 'RESTAURANT',
    'bar': 'RESTAURANT',
    'biergarten': 'RESTAURANT',
    'cafe': 'RESTAURANT',
    'ice_cream': 'RESTAURANT',
    'pub': 'RESTAURANT',
    'hospital': 'HOSPITAL',
    'clinic': 'HOSPITAL',
    'dentist': 'HOSPITAL',
    'doctors': 'HOSPITAL',
    'veterinary': 'HOSPITAL',
    'school': 'SCHOOL',
    'kindergarten': 'SCHOOL',
    'childcare': 'SCHOOL',
    'driving_school': 'SCHOOL',
    'language_school': 'SCHOOL',
    'music_school': 'SCHOOL',
    'university': 'UNIVERSITY',
    'college': 'UNIVERSITY',
    'library': 'LIBRARY',
    'toy_library': 'LIBRARY',
    'gym': 'GYM',
    'sports_hall': 'GYM',
    'pavilion': 'GYM',
    'arts_centre': 'MUSEUM',
    'cinema': 'MUSEUM',
    'theatre': 'MUSEUM',
    'parking': 'PARKING',
    'carport': 'PARKING',
    'garage': 'PARKING',
    'garages': 'PARKING',
    'hangar': 'PARKING',
    'bicycle_parking': 'PARKING',
    'charging_station': 'PARKING',
    'motorcycle_parking': 'PARKING',
    'parking_entrance': 'PARKING',
    'parking_space': 'PARKING',
    'taxi': 'PARKING'}
    # most common OSM amenity and building categories according to wiki.openstreetmap.org converted to CEA building
    # use types the "yes" category is excluded so that the default CEA assumption is used instead

OTHER_OSM_CATEGORIES_UNCONDITIONED = ['warehouse', 'roof', 'transportation', 'train_station', 'hut', 'shed', 'service',
                                 'transformer_tower', 'water_tower', 'bridge', 'bus_station', 'ferry_terminal', 'fuel',
                                 'shelter']
    # other unheated use types that don't have a specific CEA use type will be assigned as 'PARKING'
