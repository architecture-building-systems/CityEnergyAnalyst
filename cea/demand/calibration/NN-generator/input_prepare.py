# coding=utf-8
"""
Input matrix script creates matrix of input parameters for the NN out of CEA
"""
from __future__ import division
import numpy as np

__author__ = ""
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def prep_NN_delay(NN_input,NN_target,NN_delays):
    input1=NN_input
    target1=NN_target
    nS, nF = input1.shape
    nSS, nT = target1.shape
    nD=NN_delays
    aD=nD+1
    input_matrix_features=np.zeros((nS+nD, aD*nF))
    rowsF, colsF=input_matrix_features.shape
    input_matrix_targets=np.zeros((nS+nD, aD*nT))
    rowsFF, ColsFF = input_matrix_targets.shape

    i=1
    while i<aD+1:
        j=i-1
        aS=nS+j
        m1=(i*nF)-(nF)
        m2=(i*nF)
        n1=(i*nT)-(nT)
        n2=(i*nT)
        input_matrix_features[j:aS, m1:m2]=input1
        input_matrix_targets[j:aS, n1:n2]=target1
        i=i+1

    trimmed_inputn = input_matrix_features[aD:nS,:]
    trimmed_inputt = input_matrix_targets[aD:nS, 2:]
    NN_input_ready=np.concatenate([trimmed_inputn, trimmed_inputt], axis=1)
    NN_target_ready=target1[aD:nS,:]

    return NN_input_ready, NN_target_ready

