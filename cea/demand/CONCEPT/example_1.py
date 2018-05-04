from __future__ import division
from pyomo.environ import *
from pyomo.opt import SolverFactory
import numpy as np

model = ConcreteModel()

c = 1

x0 = 1

A = 3
B = 2
C = 1
D = 0

model.x = Var([1,2,3])
model.y = Var([1,2])
model.u = Var([1,2])

model.Constraint1 = Constraint(expr = model.x[2] == A*model.x[1] + B*model.u[1])
model.Constraint2 = Constraint(expr = model.y[1] == C*model.x[2] + D*model.u[1])
model.Constraint3 = Constraint(expr = model.x[1] == x0)
model.Constraint4 = Constraint(expr = -1 <= model.y[1] <= 1)

model.Constraint5 = Constraint(expr = model.x[3] == A*model.x[2] + B*model.u[2])
model.Constraint6 = Constraint(expr = model.y[2] == C*model.x[3] + D*model.u[2])


model.OBJ = Objective(expr=c*model.u[1])

opt = SolverFactory('cplex')

results = opt.solve(model)
model.display()

x_value1 = np.array(model.x)
print(x_value1)

x_value2 = np.array(model.x[1].value)
print(x_value2)