#-----------------
# Florian Mueller
# December 2014
#-----------------



import numpy
import scipy.io



class Data:



    scalarFields = []
    indexFields  = []



    def __init__(self):

        self.c = dict()
        self.c['zeroBasedIndexing'] = True



    def setFromMat(self,matPath):

        self.c = scipy.io.loadmat(matPath)
        for field in self.scalarFields:
            self.c[field] = self.c[field][0,0]
        if (not self.c['zeroBasedIndexing']):
            for field in self.indexFields:
                self.c[field] = self.c[field]-1
            self.c['zeroBasedIndexing'] = True



    def writeToMat(self,matPath):

        scipy.io.savemat(matPath,self.c,oned_as='column')


    
    # for testing only    
    def writeToTerminal(self):

        for field in self.c.keys():
            print field+' = '
            print self.c[field]
