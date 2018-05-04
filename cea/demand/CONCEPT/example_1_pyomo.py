from __future__ import division
from pyomo.environ import *
from pyomo.opt import SolverFactory
import numpy as np

model = ConcreteModel()

# Settings
# Define prediction horizon
predictionHorizon = 10

# Define system dimensions
nx = 10
ny = 5
nu = 15
nv = 20

c = np.ones((1, predictionHorizon))

# MPC Setup: Get Model
# Generate model matrices
A = np.random.rand(nx, nx) - 0.5
Bu = np.random.rand(nx, nu) - 0.5
Bv = np.random.rand(nx, nv) - 0.5
C = np.eye(ny, nx)
Du = np.zeros((ny, nu))
Dv = np.zeros((ny, nv))

# Generate initial state and disturbances
x0 = np.random.rand(nx, 1)
v = np.random.rand(nv, predictionHorizon)  # e.g.solar irradiation

# Define constraints
umax = 100 * np.ones((nu, predictionHorizon))
umin = -100 * np.ones((nu, predictionHorizon))
ymax = 2 * np.ones((ny, predictionHorizon + 1))
ymin = -2 * np.ones((ny, predictionHorizon + 1))

c = 1

x0 = 1

A = 3
B = 2
C = 1
D = 0

model.x = Var([nx, predictionHorizon + 1])
model.u = Var([nu, predictionHorizon])
model.y = Var([ny, predictionHorizon + 1])

# for i in range(predictionHorizon):
#     Constraint =

model.Constraint1 = Constraint(expr=model.x[2] == A*model.x[1] + B*model.u[1])
model.Constraint2 = Constraint(expr=model.y[1] == C*model.x[2] + D*model.u[1])
model.Constraint3 = Constraint(expr=model.x[1] == x0)
model.Constraint4 = Constraint(expr=-1 <= model.y[1] <= 1)

model.Constraint5 = Constraint(expr=model.x[3] == A*model.x[2] + B*model.u[2])
model.Constraint6 = Constraint(expr=model.y[2] == C*model.x[3] + D*model.u[2])
model.Constraint7 = Constraint(expr=model.x[2] == x0)
model.Constraint8 = Constraint(expr=-1 <= model.y[2] <= 1)

model.Constraint9 = Constraint(expr=model.x[4] == A*model.x[3] + B*model.u[3])
model.Constraint10 = Constraint(expr=model.y[3] == C*model.x[4] + D*model.u[3])
model.Constraint11 = Constraint(expr=model.x[3] == x0)
model.Constraint12 = Constraint(expr=-1 <= model.y[3] <= 1)

model.OBJ = Objective(expr=c*model.u[1])

opt = SolverFactory('cplex')

results = opt.solve(model)
model.display()

x_value1 = np.array(model.x)
print(x_value1)

x_value2 = np.array(model.x[1].value)
print(x_value2)