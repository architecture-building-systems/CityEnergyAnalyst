

import scipy
import scipy.optimize as sopt

def calc_Hcoil2(Qh, tasup, tare, Qh0, tare_0, tasup_0, tsh0, trh0, wr, ws, ma0, ma, Cpa, LMRT0, UA0, mCw0, Qhsf):
    if Qh > 0 and ma > 0:
        AUa = UA0 * (ma / ma0) ** 0.77
        NTUc = AUa / (ma * Cpa * 1000)
        ec = 1 - scipy.exp(-NTUc)
        tc = (tare - tasup + tasup * ec) / ec  # contact temperature of coil

        # minimum
        LMRT = (tsh0 - trh0) / scipy.log((tsh0 - tc) / (trh0 - tc))
        k1 = 1 / mCw0

        def fh(x):
            Eq = mCw0 * k2 - Qh0 * (k2 / (scipy.log((x + k2 - tc) / (x - tc)) * LMRT))
            return Eq

        k2 = Qh * k1
        result = sopt.newton(fh, trh0, maxiter=100, tol=0.01) - 273
        trh = result.real
        tsh = trh + k2
        mcphs = Qhsf / (tsh - trh) / 1000
    else:
        tsh = trh = mcphs = 0
    return tsh, trh, mcphs

def calc_Ccoil2(Qc, tasup, tare, Qc0, tare_0, tasup_0, tsc0, trc0, wr, ws, ma0, ma, Cpa, LMRT0, UA0, mCw0, Qcsf):
    # Water cooling coil for temperature control
    if Qc < 0 and ma > 0:
        AUa = UA0 * (ma / ma0) ** 0.77
        NTUc = AUa / (ma * Cpa * 1000)
        ec = 1 - scipy.exp(-NTUc)
        tc = (tare - tasup + tasup * ec) / ec  # contact temperature of coil

        def fh(x):
            TD1 = tc - (k2 + x)
            TD2 = tc - x
            LMRT = (TD2 - TD1) / scipy.log(TD2 / TD1)
            Eq = mCw0 * k2 - Qc0 * (LMRT / LMRT0)
            return Eq

        k2 = -Qc / mCw0
        result = sopt.newton(fh, trc0, maxiter=100, tol=0.01) - 273
        tsc = result.real
        trc = tsc + k2

        # Control system check - close to optimal flow
        min_AT = 5  # Its equal to 10% of the mass flowrate
        tsc_min = 7  # to consider coolest source possible
        trc_max = 17
        tsc_max = 12
        AT = tsc - trc
        if AT < min_AT:
            if tsc < tsc_min:
                tsc = tsc_min
                trc = tsc_min + min_AT
            if tsc > tsc_max:
                tsc = tsc_max
                trc = tsc_max + min_AT
            else:
                trc = tsc + min_AT
        elif tsc > tsc_max or trc > trc_max or tsc < tsc_min:
            trc = trc_max
            tsc = tsc_max

        mcpcs = Qcsf / (tsc - trc) / 1000
    else:
        tsc = trc = mcpcs = 0
    return tsc, trc, mcpcs
