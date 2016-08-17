import numpy as np


mww = np.array([30, 800, 890, 934, 843, 888, 234, 21, 34, 53])
mww_0= mww.max()
i = np.argmax(mww)
n0 = 1
# Calculate the storage size according to peak draw.
for k in range(10):
    if mww_0-0.1*mww_0 <= mww[k] <= mww_0+0.1*mww_0:     # find the peak draw
        N=n0+1               # N is the duration of peak draw
        V= mww_0*N
        n0=N

peakdraw = mww_0
j = i
k = i
while mww_0-0.1*mww_0 <= mww[j-1] <= mww_0+0.1*mww_0:
    peakdraw = peakdraw + mww[j-1]
    j = j-1
    while mww_0-0.1*mww_0 <= mww[k+1] <= mww_0+0.1*mww_0:
        peakdraw = peakdraw + mww[k+1]
        k = k+1
n = k - j + 1

