
from scipy.optimize import newton as opt_newton
from math import log


def calc_radiator(Qh, tair, Qh0, tair0, tsh0, trh0):
    nh = 0.3 #radiator constant
    if Qh > 0:
        tair = tair + 273
        tair0 = tair0 + 273
        tsh0 = tsh0 + 273
        trh0 = trh0 + 273
        mCw0 = Qh0 / (tsh0 - trh0)
        # minimum
        LMRT = (tsh0 - trh0) / log((tsh0 - tair0) / (trh0 - tair0))
        k1 = 1 / mCw0

        def fh(x):
            Eq = mCw0 * k2 - Qh0 * (k2 / (log((x + k2 - tair) / (x - tair)) * LMRT)) ** (nh + 1)
            return Eq

        k2 = Qh * k1
        result = opt_newton(fh, trh0, maxiter=100, tol=0.01) - 273
        trh = result.real
        tsh = trh + k2
        mCw = Qh / (tsh - trh) / 1000
    else:
        mCw = 0
        tsh = 0
        trh = 0
    return tsh, trh, mCw