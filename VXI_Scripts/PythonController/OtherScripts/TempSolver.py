import numpy as np
from scipy.optimize import fsolve


def f(T, resistivityin):
    return (9.847 * (1 + (0.3963E-2*T) - (0.5389E-6*T**2)) - resistivityin)


dia = 0.0015  # diamter in cm
length = 6.469  # length in cm
area = np.pi * (dia/2)**2
R = 40.22  # resistance of wire
resistivity = (R * 1E6) * (area/length)

print(fsolve(f, 0, resistivity))

Temp = 20

B_l = 0.20351380726728696
A_l = 52.19735983710823
Ro = A_l + (B_l*Temp)

print((B_l/Ro)*1E6)

B_s = 0.14002831760974302
A_s = 35.60142642853265
Ro1 = A_s + (B_s*Temp)
print((B_s/Ro1)*1E6)
