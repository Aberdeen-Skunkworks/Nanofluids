import matplotlib.pyplot as plt
import numpy as np
import math

t = np.linspace(0,10,100)

I = 0.001 #Supply 1mA to the wire
R = 0.98e-7 #Resistivity of platinum ohm per meter at 20*C
q = (I**2)/R #heat flux per meter length of wire
l = 0.0262
K = 1.9e-5
C = 1.781
a = 0.015e-3



DeltaT = (q/(4*np.pi*l)) * np.log((4*K*t)/((a**2)*C))
logt = np.log(t)


plt.plot(logt,DeltaT)
plt.show()
