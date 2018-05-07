# example1.py

from pyomo.environ import *
from pyomo.opt import SolverFactory
import numpy as np

# Create a solver
opt = SolverFactory('cplex')

# Define prediction horizon
predictionHorizon = 48

# Define system dimensions
nx = 10
ny = 5
nu = 15
nv = 20
c = 1

x0 = 1

A = 3
B = 2
C = 1
D = 0

# Generate initial state and disturbances
v = np.random.rand(nv, predictionHorizon)  # e.g.solar irradiation

model = ConcreteModel()
model.n = Param(default=nx)
model.x = Var(RangeSet(model.n), within=Reals)
model.y = Var(RangeSet(model.n), within=Reals)
model.u = Var(RangeSet(model.n - 1), within=Reals)
# objective function
def objective_function(model):
    return summation(model.u)

model.o = Objective(rule=objective_function)

# constraints
model.Constraint1 = Constraint(expr=model.x[2] == A*model.x[1] + B*model.u[1])
model.Constraint2 = Constraint(expr=model.y[1] == C*model.x[2] + D*model.u[1])
model.Constraint3 = Constraint(expr=model.x[1] == x0)
model.Constraint4 = Constraint(expr=-1 <= model.y[1] <= 1)
model.Constraint5 = Constraint(expr=model.x[3] == A*model.x[2] + B*model.u[2])
model.Constraint6 = Constraint(expr=model.y[2] == C*model.x[3] + D*model.u[2])

model.Constraint7 = Constraint(expr=model.x[4] == A*model.x[3] + B*model.u[3])
model.Constraint8 = Constraint(expr=model.y[3] == C*model.x[4] + D*model.u[3])


model.Constraint9 = Constraint(expr=model.x[5] == A*model.x[4] + B*model.u[4])
model.Constraint10 = Constraint(expr=model.y[4] == C*model.x[5] + D*model.u[4])

model.Constraint11 = Constraint(expr=model.x[6] == A*model.x[5] + B*model.u[5])
model.Constraint12 = Constraint(expr=model.y[5] == C*model.x[6] + D*model.u[5])

model.Constraint11 = Constraint(expr=model.x[7] == A*model.x[6] + B*model.u[6])
model.Constraint12 = Constraint(expr=model.y[6] == C*model.x[7] + D*model.u[6])

model.Constraint13 = Constraint(expr=model.x[8] == A*model.x[7] + B*model.u[7])
model.Constraint14 = Constraint(expr=model.y[7] == C*model.x[8] + D*model.u[7])

model.Constraint15 = Constraint(expr=model.x[9] == A*model.x[8] + B*model.u[8])
model.Constraint16 = Constraint(expr=model.y[8] == C*model.x[9] + D*model.u[8])

model.Constraint17 = Constraint(expr=model.x[10] == A*model.x[9] + B*model.u[9])
model.Constraint18 = Constraint(expr=model.y[9] == C*model.x[10] + D*model.u[9])

model.Constraint19 = Constraint(expr=-2 <= model.y[2] <= 2)
model.Constraint20 = Constraint(expr=-2 <= model.y[3] <= 2)
model.Constraint21 = Constraint(expr=-2 <= model.y[4] <= 2)
model.Constraint22 = Constraint(expr=-2 <= model.y[5] <= 2)
model.Constraint23 = Constraint(expr=-2 <= model.y[6] <= 2)
model.Constraint24 = Constraint(expr=-2 <= model.y[7] <= 2)
model.Constraint25 = Constraint(expr=-2 <= model.y[8] <= 2)
model.Constraint26 = Constraint(expr=-2 <= model.y[9] <= 2)

model.Constraint27 = Constraint(expr=-100 <= model.u[1] <= 100)
model.Constraint28 = Constraint(expr=-100 <= model.u[2] <= 100)
model.Constraint29 = Constraint(expr=-100 <= model.u[3] <= 100)
model.Constraint30 = Constraint(expr=-100 <= model.u[4] <= 100)
model.Constraint31 = Constraint(expr=-100 <= model.u[5] <= 100)
model.Constraint32 = Constraint(expr=-100 <= model.u[6] <= 100)
model.Constraint33 = Constraint(expr=-100 <= model.u[7] <= 100)
model.Constraint34 = Constraint(expr=-100 <= model.u[8] <= 100)
model.Constraint35 = Constraint(expr=-100 <= model.u[9] <= 100)


# Create a model instance and optimize
instance = model.create_instance()
results = opt.solve(instance)
instance.solutions.store_to(results)
print (results)

