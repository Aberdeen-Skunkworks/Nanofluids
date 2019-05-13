import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.optimize import fsolve

os.chdir("C://Users//asmo9//Desktop//Nanofluids//VXI//PythonController//THW_Results")
print(os.getcwd())

VMtime = []
voltage = []
current = []
Voltage_Threshold = 0.01
Current_Threshold = 0.0002
# ------------------------VM time------------------------------------

VMfile = open("vtime.txt", "r")
VMtime = VMfile.readlines()
VMfile.close()

# VMtimelst = VMtime[0].split(' ,')
VMtimelst = []

for i in range(len(VMtime)):
    VMtimelst.append(VMtime[i].replace("\n", ""))


VMtimelst = [i for i in VMtimelst if i != '0']
del VMtimelst[-1]

print(VMtimelst)

for i in range(len(VMtimelst)):
    if (VMtimelst[i] == 0):
        VMtimelst.pop([i])

VMtimelst = list(map(int, VMtimelst))

# Micro to milli
for i in range(len(VMtimelst)):
    VMtimelst[i] = VMtimelst[i]/1000


# -------------------------Voltage-------------------------------------

Vfile = open("voltage.txt", "r")
for line in Vfile:
    values = line.split(",")
    for num in values:
        voltage.append(num)
Vfile.close()

voltagelst = list(map(float, voltage))
voltage1 = []

for num in voltagelst:
    if (num > Voltage_Threshold):
        voltage1.append(num)
    else:
        VMtimelst.pop(0)

if (len(VMtimelst) != len(voltage1)):
    print("Voltage and time list do not match!")

# --------------------Current---------------------------------

Ifile = open("current.txt", "r")
for line in Ifile:
    values = line.split(",")
    for num in values:
        current.append(num)
Ifile.close()

currentlst = list(map(float, current))
current1 = []
for num in currentlst:
    if (num > Current_Threshold):
        current1.append(num)


def Average(lst):
    return sum(lst) / len(lst)


AvgCurrent = Average(current1)


# ---------------------------- Plot ----------------------------------
VMtime1 = []
voltage2 = []
for i in range(len(VMtimelst)):
    if (VMtimelst[i] < 100000):
        VMtime1.append(VMtimelst[i])
        voltage2.append(voltage1[i])

resistance = []
for i in range(len(voltage1)):
    resistance.append(voltage1[i]/AvgCurrent)

# MY OWN CALIBRATION
Temp = []
for n in range(len(resistance)):
    x = (resistance[n] - 34.811)/0.1361
    Temp.append(x)

dia = 0.0015  # diamter in cm
length = 6.469  # length in cm
area = np.pi * (dia/2)**2

resistivity = []
for i in range(len(resistance)):
    resistivity.append((resistance[i] * 1E6) * (area/length))


# def f(T, i):
#    return (9.847 * (1 + (0.3963E-2*T) - (0.5389E-6*T**2)) - resistivity[i])


#Temp = []
# for n in range(len(resistivity)):
#    x = fsolve(f, 0, n)  # 0 is inital guess, n is iterable argument
#    Temp.append(x)

DeltaT = []
VMtime2 = []
VMtime2ms = []
for n in range(len(Temp)):
    if (n == 0):
        continue
    else:
        # ok so since the D/A is not ideal i have to reference the VMtime to
        # the first value of VMtime in the list, after the threshold
        # so esstially we are saying that the experiment starts at the first
        # resonable multimeter measurement. which is not quite accurate
        result = Temp[0] - Temp[n]
        VMtime2.append(np.log((np.abs(VMtimelst[0] - VMtimelst[n]))))
        DeltaT.append(np.abs(result))

# eyeball the linear regime
DeltaT2 = []
VMtime3 = []
for i in range(len(DeltaT)):
    if (i > 0 and i < 8):  # 0,8
        DeltaT2.append(DeltaT[i])
        VMtime3.append(VMtime2[i])


def linear_fit(x, y):
    meanx = sum(x) / len(x)
    meany = sum(y) / len(y)
    c = sum((xi-meanx)*(yi-meany) for xi, yi in zip(x, y)) / sum((xi-meanx)**2 for xi in x)
    m = meany - c*meanx
    return c, m


y = []
slope, intercept = linear_fit(VMtime3, DeltaT2)
for j in range(len(VMtime3)):
    y.append(slope*VMtime3[j] + intercept)
print("Slope")

print(slope)
print("AvgCurrent")
print(AvgCurrent)

avgResistance = (resistance[0] + resistance[100])/2

q = ((AvgCurrent**2)*avgResistance)/(length/100)
print(q)

# https://theengineeringmindset.com/properties-of-air-at-atmospheric-pressure/

C = 1.781  # euler constant
rho_plat = 21425  # kg/m^3
cp_plat = 150  # j/(kgK)
rho_air = 1.2047  # kg/m^3
lambda_air = 0.025596  # w/mK
lambda_plat = 71.6  # W/mK
radius = 7.5E-6  # m
cp_air = 1.0061  # j/kgK

# finite heat capacity correction

Predicted_Gradient = (4*np.pi*lambda_air) / q

experiment_lambda = (q / (4*np.pi)) * slope

print("Predicted Gradient")
print(Predicted_Gradient)

Predicted_DeltaT = [n*Predicted_Gradient for n in VMtime3]

list1 = (q/(area*rho_plat*cp_plat))*np.exp(VMtime2)

C = 1.781  # euler constant
rho_plat = 21425  # kg/m^3
cp_plat = 150  # j/(kgK)
rho_air = 1.2047  # kg/m^3
lambda_air = 0.025596  # w/mK
lambda_plat = 71.6  # W/mK
radius = 7.5E-6  # m
cp_air = 1.0061  # j/kgK

Thermal_Diffusivity_air = lambda_air/(rho_air*cp_air)
Thermal_Diffusivity_plat = lambda_plat/(rho_plat*cp_plat)

DeltaT_ideal = (q/(4*np.pi*lambda_air)) * \
    np.log((4*Thermal_Diffusivity_air*(np.exp(VMtime2)/1000))/((radius**2)*C))

# exp(VMtime2)/1000 creates normal time in seconds

Cor1 = DeltaT + ((radius**2)*(((rho_plat*cp_plat)-(rho_air*cp_air)) /
                              (2*lambda_air*(np.exp(VMtime2)/1000))) * DeltaT_ideal) - \
    ((q/(4*np.pi*lambda_air)) * ((radius**2)/(4*Thermal_Diffusivity_air*(np.exp(VMtime2)/1000)))
     * (2 - (Thermal_Diffusivity_air/Thermal_Diffusivity_plat)))

# for i in range(len(VMtime2)):
#    list.append((q/rho_plat*cp_plat)*np.exp(np.log(VMtime2[i])))

fig = plt.figure()

ax1 = fig.add_subplot(2, 2, 1)
ax2 = fig.add_subplot(2, 2, 2)
ax3 = fig.add_subplot(2, 2, 3)
ax4 = fig.add_subplot(2, 2, 4)

print(q)

ax4.plot(VMtime2, DeltaT, marker="o", linestyle="", markersize=1)
ax4.plot(VMtime3, y, label=r'Experimental: I = %.4f | q = %.4f | slope = %.2f | $\lambda$ = %.4f' %
         (AvgCurrent, q, slope, experiment_lambda))
ax4.plot(VMtime3, Predicted_DeltaT, label=r'Theoretical: I = ? | q = ? | slope = %0.2f | $\lambda_{air}$ = %.4f' % (
    Predicted_Gradient, lambda_air))
ax4.plot(VMtime2, Cor1, label="DeltaT Correction")
ax4.plot(VMtime2, list1, label="Upper heat transfer limit")
#ax4.plot(VMtime2, list2)
ax4.set_xlabel(r'$ln(t)$ (ms)')
ax4.set_ylabel(r'$\Delta$ T ($^\circ$C)')

ax3.plot(VMtimelst, Temp, marker="o", linestyle="", markersize=1)
ax3.set_xlabel(r'$t$ (ms)')
ax3.set_ylabel(r'Temperature ($^\circ$C)')

ax2.plot(VMtimelst, resistance, marker="o", linestyle="", markersize=1)
ax2.set_xlabel(r'$t$ (ms)')
ax2.set_ylabel(r'Resistance ($\Omega$)')

ax1.plot(VMtimelst, voltage1, marker="o", linestyle="", markersize=1)
ax1.set_xlabel(r'$t$ (ms)')
ax1.set_ylabel(r'Voltage ($V$)')

plt.legend(loc='lower right', bbox_to_anchor=(1.2, 1), shadow=True, ncol=1)
plt.show()
