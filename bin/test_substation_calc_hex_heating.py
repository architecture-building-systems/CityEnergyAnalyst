"""
This file tests to make sure the refactored version of calc_HEX_heating calculates the same values as
the old calc_HEX_heating.
"""
from cea.technologies.substation import *


def main():
    # the first set of values in the lists is taken from a dry-run
    Q_heating_W = [17106.0, 152587.0, 11334.0, 101744.0]
    UA = [21697.9460767, ]
    cc_kWperK = [28306.0, ]
    tci_K = [273.0,]
    tco_K = [289.201, 318.756, 313.744, 302.203]
    thi_K = [306.323, 338.0, 338.0, 315.842]

    for q in Q_heating_W:
        for ua in UA:
            for thi in thi_K:
                for tco in tco_K:
                    for tci in tci_K:
                        for cc in cc_kWperK:
                            old_tho, old_ch = calc_HEX_heating_orig(q, ua, thi, tco, tci, cc)
                            new_tho, new_ch = calc_HEX_heating(q, ua, thi, tco, tci, cc)
                            print('{diff_tco}, {diff_cc} difference for {args}'.format(
                                diff_tco=(old_tho - new_tho), diff_cc=(old_ch - new_ch), args=(q, thi, tco, tci, cc)))

def calc_HEX_heating_orig(Q, UA, thi, tco, tci, cc):
    """
    original version of substation.calc_HEX_cooling before daren & bhargava refactored it.
    """

    if Q > 0:
        dT_primary = tco - tci if tco != tci else 0.0001  # to avoid errors with temperature changes < 0.001
        eff = [0.1, 0]
        Flag = False
        tol = 0.00000001
        while abs((eff[0] - eff[1]) / eff[0]) > tol:
            if Flag == True:
                eff[0] = eff[1]
            else:
                cmin = cc * (dT_primary) / ((thi - tci) * eff[0])
            if cmin < cc:
                ch = cmin
                cmax = cc
            else:
                ch = cmin
                cmax = cmin
                cmin = cc
            cr = cmin / cmax
            NTU = UA / cmin
            eff[1] = calc_shell_HEX(NTU, cr)
            cmin = cc * (dT_primary) / ((thi - tci) * eff[1])
            tho = thi - eff[1] * cmin * (thi - tci) / ch
            Flag = True

        tho = tho - 273
    else:
        tho = 0
        ch = 0
    return np.float(tho), np.float(ch)


if __name__ == '__main__':
    main()
