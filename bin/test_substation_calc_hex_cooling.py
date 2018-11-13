"""
This file tests to make sure the refactored version of calc_HEX_cooling calculates the same values as
the old calc_HEX_cooling.
"""
from cea.technologies.substation import *


def main():
    # the first set of values in the lists is taken from a dry-run
    Q_cooling_W = [0.0, 1000.0, 1234.0, 246.0, 1049.0, 1019.0]
    UA = [72493.5189434, ]
    ch_kWperK = [0.0, 1.0, 2.0, 100.0, 28.0, 118.0, 113.0]
    thi_K = [271.0, 251.0, 291.0, 255.0, 295.0, 289.3, 289.4, 289.5]
    tho_K = [273.0, 253.0, 293.0, 280.5, 280.5, 280.5]
    tci_K = [239.0, 249.0, 259.0, 278.5, 278.5, 278.5]

    for q in Q_cooling_W:
        for ua in UA:
            for thi in thi_K:
                for tho in tho_K:
                    for tci in tci_K:
                        for ch in ch_kWperK:
                            if thi - tho < 0.0 or thi - tci < 0.0:
                                # would set cmin negative...
                                continue
                            old_tco, old_cc = calc_HEX_cooling_orig(q, ua, thi, tho, tci, ch)
                            new_tco, new_cc = calc_HEX_cooling(q, ua, thi, tho, tci, ch)
                            print('{diff_tco}, {diff_cc} difference for {args}'.format(
                                diff_tco=(old_tco - new_tco), diff_cc=(old_cc - new_cc), args=(q, thi, tho, tci, ch)))

def calc_HEX_cooling_orig(Q, UA, thi, tho, tci, ch):
    """
    original version of substation.calc_HEX_cooling before daren & bhargava refactored it.
    """

    if ch > 0 and thi != tho:
        eff = [0.1, 0]
        Flag = False
        tol = 0.00000001
        while abs((eff[0] - eff[1]) / eff[0]) > tol:
            if Flag == True:
                eff[0] = eff[1]
            else:
                cmin = ch * (thi - tho) / ((thi - tci) * eff[0])
            if cmin < 0:
                raise ValueError('cmin is negative!!!', 'Q:', Q, 'UA:', UA, 'thi:', thi, 'tho:', tho, 'tci:', tci,
                                 'ch:', ch, 'eff[0]:', eff[0])
            elif cmin < ch:
                cc = cmin
                cmax = ch
            else:
                cc = cmin
                cmax = cc
                cmin = ch
            cr = cmin / cmax
            NTU = UA / cmin
            eff[1] = calc_plate_HEX(NTU, cr)
            cmin = ch * (thi - tho) / ((thi - tci) * eff[1])
            tco = tci + eff[1] * cmin * (thi - tci) / cc
            Flag = True

        cc = Q / abs(tci - tco)
        tco = tco - 273
    else:
        tco = 0
        cc = 0
    return np.float(tco), np.float(cc)


if __name__ == '__main__':
    main()
