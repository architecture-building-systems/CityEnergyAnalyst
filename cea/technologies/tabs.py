
import scipy
import scipy.optimize as sopt

def calc_TABSH(Qh, tair, Qh0, tair0, tsh0, trh0, nh):
    if Qh > 0:
        tair0 = tair0 + 273
        tsh0 = tsh0 + 273
        trh0 = trh0 + 273
        mCw0 = Qh0 / (tsh0 - trh0)
        # minimum
        LMRT = (tsh0 - trh0) / scipy.log((tsh0 - tair0) / (trh0 - tair0))
        k1 = 1 / mCw0

        def fh(x):
            Eq = mCw0 * k2 - Qh0 * (k2 / (scipy.log((x + k2 - tair) / (x - tair)) * LMRT)) ** (nh + 1)
            return Eq

        k2 = Qh * k1
        tair = tair + 273
        result = sopt.newton(fh, trh0, maxiter=1000, tol=0.1) - 273
        trh = result.real
        tsh = trh + k2

        # Control system check
        # min_AT = 2 # Its equal to 10% of the mass flowrate
        # trh_min = tair + 1 - 273
        # tsh_min = trh_min + min_AT
        # AT = (tsh - trh)
        # if AT < min_AT:
        #    if trh <= trh_min or tsh <= tsh_min:
        #        trh = trh_min
        #        tsh = tsh_min
        #    if tsh > tsh_min:
        #        trh = tsh - min_AT
        mCw = Qh / (tsh - trh) / 1000
    else:
        mCw = 0
        tsh = 0
        trh = 0
    return tsh, trh, mCw