"""
Symbolic Aggregate approximation (SAX) in python.
Based on the paper "A Symbolic Representation of Time Series, with Implications for Streaming Algorithms"
by J. Lin,  E, Keogh,  S. Lonardi & B. Chiu. 2003.

Adapted from work og N. Hoffman published under MIT license. The original
code can be found in https://github.com/nphoff/saxpy

The MIT License (MIT)
Copyright (c) 2013 Nathan Hoffman
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions
of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
from __future__ import division

import math
import scipy.stats as stats
import numpy as np

__author__ = "Nathan Hoffman"
__copyright__ = "Copyright (c) 2013 Nathan Hoffman"
__credits__ = ["Nathan Hoffman", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class SAX(object):
    """
    This class is for computing common things with the Symbolic
    Aggregate approXimation method.  In short, this translates
    a series of data to a string, which can then be compared with other
    such strings using a lookup table.
    """

    def __init__(self, word_size=8, alphabet_size=7, epsilon=1e-6):

        if alphabet_size < 3:
            raise "Error: The Alphabet Size Is Too Small"
        self.aOffset = ord('a')
        self.word_size = word_size
        self.alphabet_size = alphabet_size
        self.eps = epsilon
        self.beta = list(stats.norm().ppf(np.linspace(0.01, 0.99, self.alphabet_size + 1))[1:-1])
        self.build_letter_compare_dict()
        self.scaling_factor = 1

    def to_letter_representation(self, x):
        """
        Function takes a series of data, x, and transforms it to a string representation
        """
        (paaX, indices) = self.to_PAA(self.normalize(x))
        self.scaling_factor = np.sqrt((len(x) * 1.0) / (self.word_size * 1.0))
        return self.alphabetize(paaX), indices

    def normalize(self, x):
        """
        Function will normalize an array (give it a mean of 0, and a
        standard deviation of 1) unless it's standard deviation is below
        epsilon, in which case it returns an array of zeros the length
        of the original array.
        """
        X = np.asanyarray(x)
        if X.std() < self.eps:
            return [0 for entry in X]
        return (X - X.mean()) / X.std()

    def to_PAA(self, x):
        """
        Function performs Piecewise Aggregate Approximation on data set, reducing
        the dimension of the dataset x to w discrete levels. returns the reduced
        dimension data set, as well as the indicies corresponding to the original
        data for each reduced dimension
        """
        n = len(x)
        stepFloat = n / float(self.word_size)
        step = int(math.ceil(stepFloat))
        frame_start = 0
        approximation = []
        indices = []
        i = 0
        while frame_start <= n - step:
            thisFrame = np.array(x[frame_start:int(frame_start + step)])
            approximation.append(np.mean(thisFrame))
            indices.append((frame_start, int(frame_start + step)))
            i += 1
            frame_start = int(i * stepFloat)
        return (np.array(approximation), indices)

    def alphabetize(self, paaX):
        """
        Converts the Piecewise Aggregate Approximation of x to a series of letters.
        """
        alphabetizedX = ''
        for i in range(0, len(paaX)):
            letterFound = False
            for j in range(0, len(self.beta)):
                if paaX[i] < self.beta[j]:
                    alphabetizedX += chr(self.aOffset + j)
                    letterFound = True
                    break
            if not letterFound:
                alphabetizedX += chr(self.aOffset + len(self.beta))
        return alphabetizedX

    def compare_strings(self, sA, sB):
        """
        Compares two strings based on individual letter distance
        Requires that both strings are the same length
        """
        if len(sA) != len(sB):
            raise "Error: String Are Different Length"
        list_letters_a = [x for x in sA]
        list_letters_b = [x for x in sB]
        mindist = 0.0
        for i in range(0, len(list_letters_a)):
            mindist += self.compare_letters(list_letters_a[i], list_letters_b[i]) ** 2
        mindist = self.scaling_factor * np.sqrt(mindist)
        return mindist

    def compare_letters(self, la, lb):
        """
        Compare two letters based on letter distance return distance between
        """
        return self.compareDict[la + lb]

    def build_letter_compare_dict(self):
        """
        Builds up the lookup table to determine numeric distance between two letters
        given an alphabet size.  Entries for both 'ab' and 'ba' will be created
        and will have identical values.
        """

        number_rep = range(0, int(self.alphabet_size))
        letters = [chr(x + self.aOffset) for x in number_rep]
        self.compareDict = {}
        for i in range(0, len(letters)):
            for j in range(0, len(letters)):
                if np.abs(number_rep[i] - number_rep[j]) <= 1:
                    self.compareDict[letters[i] + letters[j]] = 0
                else:
                    high_num = np.max([number_rep[i], number_rep[j]]) - 1
                    low_num = np.min([number_rep[i], number_rep[j]])
                    self.compareDict[letters[i] + letters[j]] = self.beta[high_num] - self.beta[low_num]

    def sliding_window(self, x, num_subsequences=None, overlapping_fraction=None):
        if not num_subsequences:
            num_subsequences = 20
        self.window_size = int(len(x) / num_subsequences)
        if not overlapping_fraction:
            overlapping_fraction = 0.9
        overlap = self.window_size * overlapping_fraction
        move_size = int(self.window_size - overlap)
        if move_size < 1:
            raise " Error: Overlap Specified Is Not Smaller Than WindowSize"
        ptr = 0
        n = len(x)
        windowIndices = []
        stringRep = []
        while ptr < n - self.window_size + 1:
            thisSubRange = x[ptr:ptr + self.window_size]
            (thisStringRep, indices) = self.to_letter_representation(thisSubRange)
            stringRep.append(thisStringRep)
            windowIndices.append((ptr, ptr + self.window_size))
            ptr += move_size
        return (stringRep, windowIndices)

    def batch_compare(self, xStrings, refString):
        return [self.compare_strings(x, refString) for x in xStrings]

    def set_scaling_factor(self, scalingFactor):
        self.scaling_factor = scalingFactor

    def set_window_size(self, windowSize):
        self.window_size = windowSize
