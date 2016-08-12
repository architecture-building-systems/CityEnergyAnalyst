"""
=====================================
Main routine for Network optimization
=====================================

"""
from __future__ import division


class ntwFeatures(object):
    def __init__(self):
        self.pipesCosts_DHN = 58310     # CHF
        self.pipesCosts_DCN = 64017     # CHF
        self.DeltaP_DHN = 77743         # Pa
        self.DeltaP_DCN = 77743         # Pa

def ntwMain2():
    # WARNING : linearization on the complete network of SQ Data
    ntwFeat = ntwFeatures()
    ntwFeat.pipesCosts_DHN = 58682
    ntwFeat.pipesCosts_DCN = 64017
    ntwFeat.DeltaP_DHN = 77158
    ntwFeat.DeltaP_DCN = 86938
    
    return ntwFeat
