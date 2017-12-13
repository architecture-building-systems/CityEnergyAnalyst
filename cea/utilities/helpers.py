# -*- coding: utf-8 -*-
"""
Some helper functions that could be useful
"""

from __future__ import division
import numpy as np


def sind(angle):
    """
    Calculates sine function with input in degree.

    :param angle: angle in degree
    :type angle: float
    :return: sine of the angle
    :rtype: float

    Author: Shanshan Hsieh, 27/04/2017
    """
    return np.sin(np.radians(angle))


def cosd(angle):
    """
    Calculates cosine function with input in degree.

    :param angle: angle in degree
    :type angle: float
    :return: cosine of the angle
    :rtype: float

    Author: Shanshan Hsieh, 27/04/2017
    """
    return np.cos(np.radians(angle))


def tand(angle):
    """
    Calculates tangent function with input in degree.

    :param angle: angle in degree
    :type angle: float
    :return: tan of the angle
    :rtype: float

    Author: Shanshan Hsieh, 27/04/2017
    """
    return np.tan(np.radians(angle))
