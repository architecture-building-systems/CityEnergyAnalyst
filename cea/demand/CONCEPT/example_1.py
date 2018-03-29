# coding=utf-8
"""
Analytical energy demand model algorithm
"""
from __future__ import division

import multiprocessing as mp
import os

import pandas as pd
import numpy as np
import random

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def MPC_trial_example_1(predictionHorizon, nx, ny, nu, nv):

    c = np.ones((1, predictionHorizon))

    # MPC Setup: Get Model
    # Generate model matrices
    A = np.random.rand(nx, nx) - 0.5
    Bu = np.random.rand(nx, nu) - 0.5
    Bv = np.random.rand(nx, nv) - 0.5
    C = np.eye(ny,nx)
    Du = np.zeros((ny, nu))
    Dv = np.zeros((ny, nv))

    # Generate initial state and disturbances
    x0 = np.random.rand(nx, 1)
    v = np.random.rand(nv, predictionHorizon) # e.g.solar irradiation

    # Define constraints
    umax = 100 * np.ones((nu, predictionHorizon))
    umin = -100 * np.ones((nu, predictionHorizon))
    ymax = 2 * np.ones((ny, predictionHorizon + 1))
    ymin = -2 * np.ones((ny, predictionHorizon + 1))

    return 0


if __name__ == '__main__':

    # Settings
    # Define prediction horizon
    predictionHorizon = 10

    # Define system dimensions
    nx = 10
    ny = 5
    nu = 15
    nv = 20
    MPC_trial_example_1(predictionHorizon, nx, ny, nu, nv)
