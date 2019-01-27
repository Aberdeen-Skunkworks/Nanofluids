import matplotlib.pyplot as plt
import numpy as np
from matplotlib import rc

rc('font', **{'family':'serif','serif':['Palatino']})
rc('text', usetex=True)
plt.rcParams.update({'font.size': 14})

o = np.linspace(0, 1, 256, endpoint=True) #Vol fraction
kp = 10
kf = 1

Par = 1 + o*((kp/kf)-1) #series limit kf/k
Ser = 1 + (o * (((kp/kf)-1)/((kp/kf)-o*(kp/kf-1)))) #parralel limit k/kf


MaxLow = (1 + (( 3 * o * (kp-kf))/((3*kf) + ((1-o)*(kp-kf)))))
MaxUp = (kp/kf)*(1 - ((3*(1 - o)*(kp - kf))/((3*kp) - o * (kp - kf))))
BLow = (kp - kf)/(kp + (2*kf))
BUp = (kf - kp)/(kf + (2*kp))
#MaxLow = (1 + (2 * BLow *o))/(1 - (BLow * o))
#MaxUp = (kp*((1 + (2 * BUp * (1 - o)))/(1 - (BUp * (1 - o)))))/kf

plt.plot(o, Par, label = "Parralel Limit", color = 'black')
plt.plot(o, Ser, label = "Series Limit", color = 'black', linestyle = 'dashed')
plt.plot(o, MaxLow, label = "Lower Maxwell Limit", color = 'red', linestyle = 'dashed')
plt.plot(o, MaxUp, label = "Upper Maxwell Limit", color = 'red')

plt.legend()
plt.xlabel('$\phi$')
plt.ylabel('$\lambda_{eff}$/$\lambda_f$')

#plt.xlim(0,1)
#plt.ylim(0,kp)

plt.show()
