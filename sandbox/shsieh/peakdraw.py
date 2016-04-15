import numpy as np




mww = np.random.rand(8760)
mww_0= mww.max()
n0=0
# Calculate the storage size according to peak draw.
for k in range(8760):
    if mww_0-0.05 <= mww[k] <= mww_0:     # find the peak draw
        N=n0+1               # N is the duration of peak draw
        V= mww_0*N
        n0=N

print(N)
print(V)
print(mww_0)
print(mww)