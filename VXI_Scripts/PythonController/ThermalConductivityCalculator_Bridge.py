import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.optimize import fsolve

os.chdir("C://Users//asmo9//Desktop//Nanofluids//VXI//PythonController//Bridge")
print(os.getcwd())

VMtime = []
voltage = []
current = []
Voltage_Threshold = 0.002
Current_Threshold = 0.01
# ------------------------VM time------------------------------------

VMtimeRaw = []

VMfile = open("vtime.txt", "r")
for line in VMfile:
    values = line.split(" ,")
    for num in values:
        VMtime.append(num)
VMfile.close()
del VMtime[-1]

# VMtimelst = VMtime[0].split(' ,')

for i in range(len(VMtime)):
    VMtime[i] = int(VMtime[i])


VMtime = [i for i in VMtime if i != 0]


# Micro to milli
for i in range(len(VMtime)):
    VMtime[i] = VMtime[i]/1000


# -------------------------Voltage-------------------------------------
voltageRaw = []

Vfile = open("voltage.txt", "r")
for line in Vfile:
    values = line.split(",")
    for num in values:
        voltageRaw.append(num)
Vfile.close()

for i in range(len(voltageRaw)):
    voltageRaw[i] = float(voltageRaw[i]) * -1

for i in range(len(voltageRaw)):
    if (voltageRaw[i] > Voltage_Threshold):
        voltage.append(voltageRaw[i])
    else:
        del VMtime[i]

if (len(VMtime) != len(voltage)):
    print("Voltage and time list do not match!")

# --------------------Current---------------------------------
currentRaw = []

Ifile = open("current.txt", "r")
for line in Ifile:
    values = line.split(",")
    for num in values:
        currentRaw.append(num)
Ifile.close()

for i in range(len(currentRaw)):
    currentRaw[i] = float(currentRaw[i])

for num in currentRaw:
    if (num > Current_Threshold):
        current.append(num)


def Average(lst):
    return sum(lst) / len(lst)


AvgCurrent = Average(current)
print(AvgCurrent)


def f(T, i):
    R_3 = 100 - 56.4693
    R_4 = 100 - 38.5418
    R_1 = 100
    R_2 = 100
    C_L = 5.719122779371328e-05
    B_L = 0.2005214939916926
    A_L = 52.235976794620974
    C_S = 2.861284460413907e-05
    B_S = 0.1385312594407914811
    A_S = 35.62074654189631
    R_S = A_S + (B_S * T) + (C_S * T**2)
    R_L = A_L + (B_L * T) + (C_L * T**2)
    # return ((((R_3 + A_L + (B_L * T) + (C_L * T**2) + (D_L * P))/(R_3 + A_L + (B_L * T) + (C_L * T**2) + (D_L * P) + R_1)) - ((R_2) / (R_4 + A_S + (B_S * T) * (C_S * T**2) + (D_S * P) + R_2)))*(Vs/2)) - Voltage[i]
    return ((((R_4 + R_S)/(R_3 + R_L + R_4 + R_S)) - ((R_2)/(R_1 + R_2)))*((AvgCurrent * 200))) + voltage[i]


DeltaT = []
Temp = []
VMtimeLog = []

for n in range(len(voltage)):
    x = fsolve(f, 0, n)  # 0 is inital guess, n is iterable argument
    Temp.append(x)

for i in range(len(Temp)):
    result = Temp[i] - Temp[0]
    VMtimeLog.append(np.log(VMtime[i] - VMtime[0]))
    DeltaT.append(result)

# ryrball linear regime
DeltaT_eyed = []
VMtimeLog_eyed = []
for i in range(len(DeltaT)):
    if (i > 10 and i < 100):  # 0,8
        DeltaT_eyed.append(DeltaT[i])
        VMtimeLog_eyed.append(VMtimeLog[i])

slope, intercept = np.polyfit(VMtimeLog_eyed, DeltaT_eyed, 1)

length = 91.28E-3
q = ((AvgCurrent**2)*56.4693)/(length)

y = []
for i in range(len(VMtimeLog_eyed)):
    y.append(slope*VMtimeLog_eyed[i] + intercept)

experiment_lambda = (q / (4*np.pi)) * slope

print(q)

fig = plt.figure()

csfont = {'fontname': 'Times New Roman'}

ax1 = fig.add_subplot(1, 2, 1)
ax2 = fig.add_subplot(1, 2, 2)


ax1.plot(VMtime, voltage, marker="o", color="black", linestyle="", markersize=1)
ax2.plot(VMtimeLog, DeltaT, marker="o", color="black", linestyle="", markersize=1)
ax2.plot(VMtimeLog_eyed, y, color="red", linestyle="--", linewidth=2,
         label=r'Linear fit | $\lambda$ = %.4f W/mK' % (experiment_lambda))
ax2.set_xlabel(r'ln(t) (t in ms)', fontsize=19, **csfont)
ax2.set_ylabel(r'$\Delta$ T (T in $^\circ$C)', fontsize=19, **csfont)
plt.legend(loc='best',  prop={'family': 'Times New Roman', 'size': 15}, markerscale=5)
#plt.legend(loc='lower right', bbox_to_anchor=(1.2, 1), shadow=True, ncol=1)

ax1.xaxis.set_tick_params(labelsize=14)
ax1.yaxis.set_tick_params(labelsize=14)

ax2.xaxis.set_tick_params(labelsize=14)
ax2.yaxis.set_tick_params(labelsize=14)

ax1.set_title("(a)", fontsize=18, **csfont)
ax2.set_title("(b)", fontsize=18, **csfont)
ax1.set_xlabel(r't (ms)', fontsize=18, **csfont)
ax1.set_ylabel(r'Voltage (V)', fontsize=18, **csfont)

plt.legend(loc='best',  prop={'family': 'Times New Roman', 'size': 15}, markerscale=5)
plt.show()
