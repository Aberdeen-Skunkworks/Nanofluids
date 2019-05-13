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
Voltage_Threshold = 0.89
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
    voltageRaw[i] = float(voltageRaw[i])

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

# -------------------plot------------------------
resistance = []
for i in range(len(voltage)):
    resistance.append(voltage[i]/AvgCurrent)


def TempSolve(T, R):  # PT_6
    C_l = 5.719122779371328e-05
    B_l = 0.2005214939916926
    A_l = 52.235976794620974
    return (A_l + (B_l * T) + (C_l * T**2)) - R


print(resistance)
Temp = []
for n in range(len(resistance)):
    x = fsolve(TempSolve, 0, resistance[n])
    Temp.append(x)

Temp0 = 20.69166168

DeltaT = []
VMtimeLog = []

for i in range(len(Temp)):
    result = Temp[i] - Temp0
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

avgResistance = Average(resistance)
length = 91.28E-3
q = ((AvgCurrent**2)*avgResistance)/(length)


C = 1.781  # euler constant
rho_plat = 21425.0  # kg/m^3
cp_plat = 150.0  # j/(kgK)
rho_air = 1.2047  # kg/m^3
lambda_air = 0.025596  # w/mK
lambda_plat = 71.6  # W/mK
radius = 7.5E-6  # m
cp_air = 1.0061  # j/kgK
area = np.pi * (radius)**2

real_slope = (4*np.pi*lambda_air) / q
y = []
y2 = []
y3 = []
y4 = []

for i in range(len(VMtimeLog_eyed)):
    y.append(slope*VMtimeLog_eyed[i] + intercept)
    y2.append(real_slope*VMtimeLog_eyed[i])

for i in range(len(VMtimeLog)):
    y3.append((q/(area*rho_plat*cp_plat))*(np.exp(VMtimeLog[i])/1000))

experiment_lambda = (q / (4*np.pi)) * slope

Thermal_Diffusivity_air = lambda_air/(rho_air*cp_air)
Thermal_Diffusivity_plat = lambda_plat/(rho_plat*cp_plat)

Cor1 = []

for i in range(len(DeltaT)):
    DeltaT_ideal = (q/(4*np.pi*lambda_air)) * \
        np.log((4*Thermal_Diffusivity_air*(np.exp(VMtimeLog[i])/1000))/((radius**2)*C))

    Cor1.append(DeltaT[i] + ((radius**2)*(((rho_plat*cp_plat)-(rho_air*cp_air)) /
                                          (2*lambda_air*(np.exp(VMtimeLog[i])/1000))) * DeltaT_ideal) -
                ((q/(4*np.pi*lambda_air)) * ((radius**2)/(4*Thermal_Diffusivity_air*(np.exp(VMtimeLog[i])/1000)))
                 * (2 - (Thermal_Diffusivity_air/Thermal_Diffusivity_plat))))

error = []

for i in range(len(Cor1)):
    if (i > 10 and i < 100):
        error.append(((Cor1[i]-DeltaT[i])/DeltaT[i])*100)

print(error)

fig = plt.figure()

csfont = {'fontname': 'Times New Roman'}

#ax1 = fig.add_subplot(1, 2, 1)
#ax2 = fig.add_subplot(2, 2, 2)
#ax3 = fig.add_subplot(1, 2, 2)
ax4 = fig.add_subplot(1, 1, 1)

#ax1.plot(VMtime, voltage, marker="o", color="black", linestyle="", markersize=1)
#ax1.set_xlabel(r't (ms)', fontsize=18, **csfont)
#ax1.set_ylabel(r'Voltage (V)', fontsize=18, **csfont)


#ax2.plot(VMtime, resistance, marker="o", linestyle="", markersize=1)
#ax2.set_xlabel(r'$t$ (ms)')
#ax2.set_ylabel(r'Resistance ($\Omega$)')

#ax3.plot(VMtime, Temp, marker="o", linestyle="", markersize=1)
#ax3.set_xlabel(r'$t$ (ms)')
#ax3.set_ylabel(r'Temperature ($^\circ$C)')

ax4.plot(VMtimeLog, DeltaT, marker="o", color="black", linestyle="", markersize=1)
ax4.plot(VMtimeLog_eyed, y, color="red", linestyle="--", linewidth=2,
         label=r'Linear fit | $\lambda$ = %.4f W/mK' % (experiment_lambda))
# ax4.plot(VMtimeLog_eyed, y2, label=r'Theoretical: I = ? | q = ? | slope = %0.2f | $\lambda_{air}$ = %.4f W/mK' % (
# real_slope, lambda_air))
ax4.plot(VMtimeLog, Cor1, marker="o", color="green",
         linestyle="", markersize=1, label=r"Finite $C_p$ correction")
ax4.plot(VMtimeLog, y3, label="Upper heat transfer limit")
ax4.set_xlabel(r'ln(t) (t in ms)', fontsize=19, **csfont)
ax4.set_ylabel(r'$\Delta$ T (T in $^\circ$C)', fontsize=19, **csfont)
plt.legend(loc='best',  prop={'family': 'Times New Roman', 'size': 15}, markerscale=5)
#plt.legend(loc='lower right', bbox_to_anchor=(1.2, 1), shadow=True, ncol=1)

# ax1.xaxis.set_tick_params(labelsize=14)
# ax1.yaxis.set_tick_params(labelsize=14)

ax4.xaxis.set_tick_params(labelsize=14)
ax4.yaxis.set_tick_params(labelsize=14)

ax4.set_ylim([2.5, 7.2])

#ax1.set_title("(a)", fontsize=15, **csfont)

print("Tempo" + str(Temp[0]))
print("AvgCurrent" + str(AvgCurrent))
print("q" + str(q))
print("slope" + str(slope))
print("therm" + str(experiment_lambda))
plt.show()
