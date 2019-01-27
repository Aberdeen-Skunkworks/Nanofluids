import numpy as np

l = 6.45 #length of platinum wire in cm (taken from eagle)
d =  0.00015 #diameter of wire in cm
R = 37.721354 #resistance of wire

#find resistivity of wire p
#
r = np.roots([-5.3065E-6, 0.039025, 10])

print(r)
