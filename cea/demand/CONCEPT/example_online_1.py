# -*- coding: utf-8 -*-
"""
Created on Thu Mar 31 17:03 2017
@author: Igor Yamamoto
"""
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal
from cvxopt import matrix, solvers


class SystemModel(object):
    def __init__(self, ny, nu, H):
        self.ny = ny
        self.nu = nu
        self.H = np.array(H)

    def step_response(self, X0=None, T=None, N=None):
        def fun(X02=None, T2=None, N2=None):
            def fun2(sys):
                return signal.step(sys, X02, T2, N2)

            return fun2

        fun3 = fun(X0, T, N)
        step_with_time = list(map(fun3, self.H))
        return np.array([s[1] for s in step_with_time])


class GPCController(object):
    def __init__(self, system, Ts, p, m, Q, R, du_min, du_max):
        self.system = system
        self.Ts = Ts
        self.nu = system.nu
        self.ny = system.ny
        self.p = p
        self.m = m
        self.Q = Q
        self.R = R
        self.du_min = du_min
        self.du_max = du_max
        self.G = self.initialize_G()
        AB = self.create_AB()
        self.A_til = AB[0]
        self.B = AB[1]

    def create_matrix_G(self, g, p, m):
        g = np.append(g[:p], np.zeros(m - 1))
        G = np.array([])
        for i in range(p):
            G = np.append(G, [g[i - j] for j in range(m)])
        return np.resize(G, (p, m))

    def initialize_G(self):
        T = np.array(range(1, 200, self.Ts))
        g11, g12, g21, g22 = ethylene.step_response(T=T)
        G11 = self.create_matrix_G(g11, p, m)
        G12 = self.create_matrix_G(g12, p, m)
        G21 = self.create_matrix_G(g21, p, m)
        G22 = self.create_matrix_G(g22, p, m)
        G1 = np.hstack((G11, G12))
        G2 = np.hstack((G21, G22))
        G = np.vstack((G1, G2))
        return G

    def create_AB(self):
        Bm11 = np.array([-0.19])
        Am11 = np.array([1, -1])
        Am11_til = np.convolve(Am11, [1, -1])

        Bm12 = np.array([-0.08498])
        Am12 = np.array([1, -0.95])
        Am12_til = np.convolve(Am12, [1, -1])

        Bm21 = np.array([-0.02362])
        Am21 = np.array([1, -0.969])
        Am21_til = np.convolve(Am21, [1, -1])

        Bm22 = np.array([0.235])
        Am22 = np.array([1, -1])
        Am22_til = np.convolve(Am22, [1, -1])
        return [[Am11_til, Am12_til, Am21_til, Am22_til],
                [Bm11, Bm12, Bm21, Bm22]]

    def calculate_control(self, w, **kwargs):
        dm = 0
        y11_f = np.zeros(self.p)
        y12_f = np.zeros(self.p)
        y21_f = np.zeros(self.p)
        y22_f = np.zeros(self.p)
        # Free Response
        du1, du2 = kwargs['current_du']
        du1_f, du2_f = kwargs['du_past']
        y11_aux, y12_aux, y21_aux, y22_aux = kwargs['y_past']
        for j in range(p):
            if j <= dm:
                du1_f = du1
                du2_f = du2
            else:
                du1_f = du2_f = np.array(0)
            y11_f[j] = -y11_aux.dot(self.A_til[0][1:]) + du1_f.dot(self.B[0])
            y12_f[j] = -y12_aux.dot(self.A_til[1][1:]) + du2_f.dot(self.B[1])
            y21_f[j] = -y21_aux.dot(self.A_til[2][1:]) + du1_f.dot(self.B[2])
            y22_f[j] = -y22_aux.dot(self.A_til[3][1:]) + du2_f.dot(self.B[3])
            y11_aux = np.append(y11_f[j], y11_aux[:-1])
            y12_aux = np.append(y12_f[j], y12_aux[:-1])
            y21_aux = np.append(y21_f[j], y21_aux[:-1])
            y22_aux = np.append(y22_f[j], y22_aux[:-1])
        f = np.append(y11_f + y12_f, y21_f + y22_f)
        # Solver Inputs
        H = matrix((2 * (self.G.T.dot(self.Q).dot(self.G) + self.R)).tolist())
        q = matrix((2 * self.G.T.dot(self.Q).dot(f - w)).tolist())
        A = matrix(np.hstack((np.eye(self.nu * self.m), -1 * np.eye(self.nu * self.m))).tolist())
        b = matrix([self.du_max] * self.nu * self.m + [-self.du_min] * self.nu * self.m)
        # Solve
        sol = solvers.qp(P=H, q=q, G=A, h=b)
        dup = list(sol['x'])
        s = sol['status']
        j = sol['primal objective']
        return dup, j, s


class Simulation(object):
    def __init__(self, controller, real_system=None):
        self.controller = controller
        if real_system:
            self.real_system = real_system
        else:
            self.real_system = controller.system

    def run(self, tsim):
        # Real Process
        Br11 = 1 * np.array([-0.19])
        Ar11 = np.array([1, -1])
        Br12 = 1 * np.array([-0.08498])
        Ar12 = np.array([1, -0.95])
        Br21 = 1 * np.array([-0.02362])
        Ar21 = np.array([1, -0.969])
        Br22 = 1 * np.array([0.235])
        Ar22 = np.array([1, -1])
        na11 = len(Ar11)
        na12 = len(Ar12)
        na21 = len(Ar21)
        na22 = len(Ar22)
        nb = 1
        # Reference and Disturbance Signals
        w1 = np.array([1] * int(tsim / 4) + [1] * int(tsim / 4) + [1] * int(tsim / 4) + [1] * int(tsim / 4 + p))
        w2 = np.array([1] * int(tsim / 4) + [1] * int(tsim / 4) + [1] * int(tsim / 4) + [1] * int(tsim / 4 + p))
        # a1 = list(0.0125*np.arange(int(tsim/2)))
        # b1 = [1.25]*int(tsim/4)
        # c1 = list(b1-0.025*np.arange(int(tsim/4)))
        # c1.reverse()
        # d1 = [1.25]*int(tsim/2+p)
        # w1 = np.array(a1+d1)

        # a1 = list(0.01*np.arange(int(tsim/2)))
        # b1 = [1]*int(tsim/4)
        # c1 = list(b1-0.02*np.arange(int(tsim/4)))
        # c1.reverse()
        # d1 = [1]*int(tsim/2+p)
        # w2 = np.array(a1+d1)

        # Initialization
        y11 = 0 * np.ones(tsim + 1)
        y12 = 0 * np.ones(tsim + 1)
        y21 = 0 * np.ones(tsim + 1)
        y22 = 0 * np.ones(tsim + 1)
        u1 = np.zeros(tsim + 1)
        u2 = np.zeros(tsim + 1)
        du1 = np.zeros(tsim + 1)
        du2 = np.zeros(tsim + 1)
        y11_past = 0 * np.ones(na11)
        y12_past = 0 * np.ones(na12)
        y21_past = 0 * np.ones(na21)
        y22_past = 0 * np.ones(na22)
        u1_past = np.zeros(nb)
        u2_past = np.zeros(nb)

        J = np.zeros(tsim)
        Status = [''] * tsim
        # Control Loop
        for k in range(1, tsim + 1):
            y11[k] = -Ar11[1:].dot(y11_past[:-1]) + Br11.dot(u1_past)
            y12[k] = -Ar12[1:].dot(y12_past[:-1]) + Br12.dot(u2_past)
            y21[k] = -Ar21[1:].dot(y21_past[:-1]) + Br21.dot(u1_past)
            y22[k] = -Ar22[1:].dot(y22_past[:-1]) + Br22.dot(u2_past)

            # Select references for the current horizon
            w = np.append(w1[k:k + p], w2[k:k + p])

            du_past = np.array([du1[k - 1], du2[k - 1]])
            y_past = [y11_past, y12_past, y21_past, y22_past]
            current_du = [np.array([du1[k]]), np.array([du2[k]])]
            dup, j, s = self.controller.calculate_control(w,
                                                          du_past=du_past,
                                                          y_past=y_past,
                                                          current_du=current_du)

            du1[k] = dup[0]
            du2[k] = dup[m]
            u1[k] = u1[k - 1] + du1[k]
            u2[k] = u2[k - 1] + du2[k]

            u1_past = np.append(u1[k], u1_past[:-1])
            u2_past = np.append(u2[k], u2_past[:-1])
            y11_past = np.append(y11[k], y11_past[:-1])
            y12_past = np.append(y12[k], y12_past[:-1])
            y21_past = np.append(y21[k], y21_past[:-1])
            y22_past = np.append(y22[k], y22_past[:-1])

            J[k - 1] = abs(j)
            Status[k - 1] = s
            # Teste
        plt.clf()
        plt.plot(w1[:-p], ':', label='Target y1')
        plt.plot(w2[:-p], ':', label='Target y2')
        plt.plot(y11 + y12, label='y1')
        plt.plot(y21 + y22, label='y2')
        plt.plot(u1, '--', label='u1')
        plt.plot(u2, '--', label='u2')
        plt.legend(loc=0, fontsize='small')
        plt.xlabel('sample time (k)')
        plt.show()
        # plt.savefig('sim8.png')
        return J, Status


if __name__ == '__main__':
    nu = 2  # number of inputs
    ny = 2  # number of outputs
    h11 = signal.TransferFunction([-0.19], [1, 0])
    h12 = signal.TransferFunction([-1.7], [19.5, 1])
    h21 = signal.TransferFunction([-0.763], [31.8, 1])
    h22 = signal.TransferFunction([0.235], [1, 0])
    ethylene = SystemModel(2, 2, [h11, h12, h21, h22])

    p = 10  # prediction horizon
    m = 3  # control horizon
    Q = 1 * np.eye(p * ny)
    R = 10 * np.eye(m * nu)
    du_max = 0.2
    du_min = -0.2
    Ts = 1
    controller = GPCController(ethylene, Ts, p, m, Q, R, du_min, du_max)

    real_h11 = signal.TransferFunction([-0.19], [1, 0])
    real_h12 = signal.TransferFunction([-1.7], [19.5, 1])
    real_h21 = signal.TransferFunction([-0.763], [31.8, 1])
    real_h22 = signal.TransferFunction([0.235], [1, 0])
    real_ethylene = SystemModel(2, 2, [real_h11, real_h12, real_h21, real_h22])

    solvers.options['show_progress'] = False
    tsim = 100
    sim = Simulation(controller)
    J, S = sim.run(tsim)
    # plt.plot(J)