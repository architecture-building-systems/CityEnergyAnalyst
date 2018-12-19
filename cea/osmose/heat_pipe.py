from __future__ import division
import numpy as np
import pandas as pd


def main():
    #T_h_in = np.array([30, 30, 30, 30, 30, 30, 30, 30, 30, 30])
    #w_h = np.array([21.6, 21.6, 21.6, 21.6, 21.6, 21.6, 21.6, 21.6, 21.6, 21.6])
    #T_offcoil = np.array([10.5, 11.1, 11.7, 12.3, 12.9, 13.5, 14.1, 14.7, 15.3, 15.9])
    #w_offcoil = np.array([7.84, 8.17, 8.51, 8.86, 9.22, 9.60, 9.99, 10.39, 10.81, 11.24])
    T_h_in = np.array([18, 18, 18])
    w_h = np.array([13.76, 13.76, 13.76])
    T_offcoil = np.array([8.1, 8.75, 13.73])
    w_offcoil = np.array([6.66, 6.96, 9.89])

    T_c_in = T_offcoil
    w_c = w_offcoil
    eff_heatpipe = 0.4
    T_h_out = T_h_in - (T_h_in - T_c_in) * eff_heatpipe
    dh_coil = calc_h_from_T_w(T_h_in, w_h) - calc_h_from_T_w(T_c_in, w_c)
    dh_coil_hp = calc_h_from_T_w(T_h_out, w_h) - calc_h_from_T_w(T_c_in, w_c)
    h_c_out = calc_h_from_T_w(T_h_in, w_h) - calc_h_from_T_w(T_h_out, w_h) + calc_h_from_T_w(T_c_in, w_c)
    T_c_out = calc_T_from_h_w(h_c_out, w_c)

    print 'dh_coil\n',dh_coil
    print 'T_h_out\n',T_h_out
    print 'T_offcoil\n',T_offcoil
    print 'h_offcoil\n', calc_h_from_T_w(T_c_in, w_c)
    print 'dh_coil_hp\n',dh_coil_hp
    print 'T_c_out\n',T_c_out
    print 'h_c_out\n',h_c_out
    return np.nan


def calc_h_from_T_w(T_C, w_gperkg):
    c_air = 1.007
    c_vapor = 1.84 / 1000
    h_fg = 2501 / 1000
    h_kJperkg = (c_air * T_C - 0.0026) + w_gperkg * (h_fg + c_vapor * T_C)
    return h_kJperkg


def calc_T_from_h_w(h_kJperkg, w_gperkg):
    c_air = 1.007
    c_vapor = 1.84 / 1000
    h_fg = 2501 / 1000
    # h = (c_air * T_C - 0.0026) + w_gperkg * h_fg + w_gperkg * c_vapor * T_C)
    T_C = (h_kJperkg + 0.0026 - w_gperkg * h_fg) / (c_air + w_gperkg * c_vapor)
    return T_C


if __name__ == '__main__':
    main()
