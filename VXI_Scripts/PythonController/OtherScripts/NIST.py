import numpy as np
import matplotlib.pyplot as plt
import math
from scipy.optimize import fsolve
from scipy import stats
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error, r2_score
csfont = {'fontname': 'Times New Roman'}


Voltage = [5.15612E-4, 1.07951E-3, 1.40795E-3, 1.68155E-3,
           1.84488E-3, 2.00463E-3, 2.1614E-3, 2.2985E-3, 2.43559E-3,
           2.47911E-3, 2.55064E-3, 2.65734E-3, 2.74794E-3, 2.79682E-3,
           2.86418E-3, 2.91842E-3, 2.96074E-3, 3.01201E-3, 3.07459E-3,
           3.16818E-3, 3.16639E-3, 3.16878E-3, 3.23256E-3, 3.31303E-3,
           3.32376E-3, 3.35952E-3, 3.38992E-3, 3.44953E-3, 3.45609E-3,
           3.48649E-3, 3.55206E-3, 3.56219E-3, 3.55087E-3, 3.58603E-3,
           3.64683E-3, 3.6671E-3, 3.6975E-3, 3.69869E-3, 3.73088E-3,
           3.75174E-3, 3.77559E-3, 3.84712E-3, 3.82506E-3, 3.82149E-3,
           3.84414E-3, 3.90017E-3, 3.90673E-3, 3.94309E-3, 3.94249E-3,
           3.95084E-3, 3.96335E-3, 3.99375E-3, 4.04263E-3, 4.03667E-3,
           4.01819E-3, 4.02296E-3, 4.09568E-3, 4.10284E-3, 4.12549E-3,
           4.11595E-3, 4.13562E-3, 4.14874E-3, 4.1696E-3, 4.19344E-3,
           4.22086E-3, 4.20119E-3, 4.19881E-3, 4.24292E-3, 4.26914E-3,
           4.29835E-3, 4.27332E-3, 4.27391E-3, 4.29716E-3, 4.32518E-3,
           4.32994E-3, 4.35677E-3, 4.34485E-3, 4.36571E-3, 4.37644E-3,
           4.39194E-3, 4.42115E-3, 4.4128E-3, 4.40505E-3, 4.41161E-3,
           4.44678E-3, 4.45691E-3, 4.48672E-3, 4.46406E-3, 4.47062E-3,
           4.49268E-3, 4.51115E-3, 4.5499E-3, 4.51712E-3, 4.52248E-3,
           4.52904E-3, 4.55586E-3, 4.55884E-3, 4.60414E-3, 4.58268E-3,
           4.56361E-3, 4.5797E-3, 4.61964E-3, 4.64229E-3, 4.62203E-3,
           4.6107E-3, 4.62262E-3, 4.66494E-3, 4.66316E-3, 4.69475E-3,
           4.68461E-3, 4.67269E-3, 4.68163E-3, 4.72336E-3, 4.72813E-3,
           4.72753E-3, 4.70727E-3, 4.71203E-3, 4.74601E-3, 4.75555E-3,
           4.78476E-3, 4.76211E-3, 4.75078E-3, 4.76866E-3, 4.79847E-3,
           4.79727E-3, 4.81277E-3, 4.80383E-3, 4.82589E-3, 4.82469E-3,
           4.83006E-3, 4.8688E-3, 4.84973E-3, 4.82767E-3, 4.83125E-3,
           4.87357E-3, 4.87834E-3, 4.89265E-3, 4.87476E-3, 4.88669E-3,
           4.89622E-3, 4.90934E-3, 4.94451E-3, 4.91828E-3, 4.90993E-3,
           4.90874E-3, 4.93378E-3, 4.94272E-3, 4.97729E-3, 4.9457E-3,
           4.93199E-3, 4.95404E-3, 4.98444E-3, 4.99637E-3, 4.97789E-3,
           4.97371E-3, 4.9761E-3, 5.0071E-3, 5.0071E-3, 5.03988E-3,
           5.02379E-3, 5.00352E-3, 5.01604E-3, 5.05776E-3, 5.05538E-3,
           5.0524E-3, 5.0369E-3, 5.03392E-3, 5.0673E-3, 5.07624E-3,
           5.10724E-3, 5.07743E-3, 5.0673E-3, 5.08339E-3, 5.10903E-3,
           5.09889E-3, 5.11618E-3, 5.10187E-3, 5.12333E-3, 5.1126E-3,
           5.12452E-3, 5.16387E-3, 5.14062E-3, 5.11618E-3, 5.1275E-3,
           5.17281E-3, 5.16565E-3, 5.17817E-3, 5.15016E-3, 5.16983E-3,
           5.17221E-3, 5.17817E-3, 5.22169E-3, 5.19605E-3, .005174,
           5.1734E-3, 5.20678E-3, 5.21632E-3, 5.23599E-3, 5.20976E-3,
           5.19725E-3, 5.21871E-3, 5.23838E-3, 5.25685E-3, 5.23838E-3,
           5.23063E-3, 5.22407E-3, 5.26222E-3, 5.25924E-3, 5.28725E-3,
           5.26639E-3, 5.2503E-3, 5.25745E-3, 5.28368E-3, 5.29798E-3,
           5.29321E-3, 5.26937E-3, 5.27176E-3, 5.31229E-3, 5.31229E-3,
           5.33434E-3, 5.31169E-3, 5.30514E-3, 5.30514E-3, 5.32838E-3,
           5.32242E-3, 5.34686E-3, 5.32361E-3, 5.3409E-3, 5.33673E-3,
           .005357, 5.38263E-3, 5.35461E-3, 5.33375E-3, 5.34984E-3,
           5.38084E-3, 5.37607E-3, 5.39097E-3, 5.37667E-3, 5.38322E-3,
           5.3862E-3, 5.39157E-3, 5.43866E-3, 5.40766E-3, 5.38322E-3,
           5.37965E-3, 5.41243E-3, 5.42137E-3, 5.43926E-3, 5.41005E-3]

t = np.arange(0, 755, 3.02)
t2 = np.delete(t, 0)
print(len(t2))
print(len(Voltage))
logt = np.log(t2)


Vs = 6
P = 33.595

R_1 = 100.00
R_2 = 100.00
R_3 = 5.9738
R_4 = 53.4878

A_L = -9.065472
B_L = 0.3534445
C_L = -0.5923443E-4
D_L = -1.401463E-3

A_S = -4.346459
B_S = 0.1740251
C_S = -0.2831553E-4
D_S = -6.565822E-4


def f(T, i):
    R_S = A_S + (B_S * T) + (C_S * T**2) + (D_S * P)
    R_L = A_L + (B_L * T) + (C_L * T**2) + (D_L * P)
    # return ((((R_3 + A_L + (B_L * T) + (C_L * T**2) + (D_L * P))/(R_3 + A_L + (B_L * T) + (C_L * T**2) + (D_L * P) + R_1)) - ((R_2) / (R_4 + A_S + (B_S * T) * (C_S * T**2) + (D_S * P) + R_2)))*(Vs/2)) - Voltage[i]
    return ((((R_4 + R_S)/(R_3 + R_L + R_4 + R_S)) - ((R_2)/(R_1 + R_2)))*(Vs)) + Voltage[i]


Temp = []
DeltaT = [0]

for n in range(len(Voltage)):
    x = fsolve(f, 0, n)  # 0 is inital guess, n is iterable argument
    Temp.append(x)
print("Temp:")
for i in range(len(Temp)):
    print(Temp[i]-273)

for n in range(len(Temp)):
    if n == 0:
        continue
    else:
        result = Temp[n] - Temp[0]
        DeltaT.append(result)

C = 1.781  # euler constant
rho_plat = 21425  # kg/m^3
cp_plat = 150  # j/(kgK)
rho_air = 1.2047  # kg/m^3
lambda_air = 0.025596  # w/mK
lambda_plat = 71.6  # W/mK
radius = (12.7E-6)/2  # m
cp_air = 1.0061  # j/kgK
q = 0.81285
Thermal_Diffusivity_air = lambda_air/(rho_air*cp_air)
Thermal_Diffusivity_plat = lambda_plat/(rho_plat*cp_plat)

DeltaT_ideal = (q/(4*np.pi*lambda_air)) * \
    np.log((4*Thermal_Diffusivity_air*(t2/1000))/((radius**2)*C))

DeltaT_cor = (q/(4*np.pi*lambda_air)) * (0.1E-6/radius) * (DeltaT_ideal/Temp[0])

# for i in range(len(DeltaT)):
#DeltaT = DeltaT + DeltaT_cor


def linear_fit(x, y):
    meanx = sum(x) / len(x)
    meany = sum(y) / len(y)
    c = sum((xi-meanx)*(yi-meany) for xi, yi in zip(x, y)) / sum((xi-meanx)**2 for xi in x)
    m = meany - c*meanx
    return c, m


slope, intercept = linear_fit(logt, DeltaT)
print(slope)
# slope, intercept, r_value, p_value, std_err = stats.linregress(logt, DeltaT)
y = slope*logt + intercept

# regr = linear_model.LinearRegression()
# regr.fit(logt, DeltaT)
# DeltaT_pred = regr.predict(logt)


y_digi = 0.384*logt + 0.8382

print(Temp[2])

fig = plt.figure()
ax1 = fig.add_subplot(1, 2, 1)
ax2 = fig.add_subplot(1, 2, 2)

ax1.plot(t2, Voltage, marker="o", color="black", linestyle="", markersize=1)
ax2.plot(logt, DeltaT, marker="o", color="black", linestyle="", markersize=1)
ax2.plot(logt, y, color="black", linestyle="--", linewidth=1, label="Evaluated Line")
ax2.plot(logt, y_digi, color="red", linestyle="--", linewidth=1, label="Digitised NIST Line")
ax1.set_title("(a)", fontsize=15, **csfont)
ax2.set_title("(b)", fontsize=15, **csfont)
#ax2.set_xlim([3.2, 7.2])
#ax2.set_ylim([2.0, 3.6])


ax1.set_xlabel(r't (ms)', fontsize=15, **csfont)
ax1.set_ylabel(r'Bridge Voltage (mV)', fontsize=15, **csfont)

ax2.legend()
ax2.set_xlabel(r'ln(t) (ms)', fontsize=15, **csfont)
ax2.set_ylabel(r'$\Delta$T', fontsize=15, **csfont)
plt.show()
