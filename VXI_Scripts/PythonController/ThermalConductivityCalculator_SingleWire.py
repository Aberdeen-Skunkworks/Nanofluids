import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.optimize import fsolve

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(CURRENT_DIR)
print(os.getcwd())

VMtime = []
voltage = []
current = []
Voltage_Threshold = 0.7
Current_Threshold = 0.01
# ------------------------VM time------------------------------------

VMtime = list(map(float, open("vtime.txt", "r").read().split(",")))
voltage = list(map(float, open("voltage.txt", "r").read().split(",")))
if len(VMtime) != len(voltage):
    raise Exception("Length mismatch!")

voltage = list(filter(lambda x : x[1] < Voltage_Threshold, zip(VMtime, voltage)))
# --------------------Current---------------------------------

currentRaw = map(float, open("current.txt", "r").read().split(","))
currentRaw = list(filter(lambda I : I > Current_Threshold, currentRaw))
AvgCurrent = sum(currentRaw) / len(currentRaw)

# -------------------plot------------------------
resistance = []
for t,V in voltage:
    resistance.append((t, V / AvgCurrent))

def TempSolve(T, R):  # PT_6
    C_l = 5.719122779371328e-05
    B_l = 0.2005214939916926
    A_l = 52.235976794620974
    return (A_l + (B_l * T) + (C_l * T**2)) - R


print(resistance)
Temp = [(t, fsolve(TempSolve, 0, R)) for t, R in resistance]
Temp0 = 20.69166168 #WHAT IS THIS? Starting temperature?

DeltaT = [T - Temp[0][1] for t,T in Temp]
VMtimeLog = [np.log(t - Temp[0][0]) for t,T in Temp]

# ryrball linear regime
DeltaT_eyed = []
VMtimeLog_eyed = []
for i in range(len(DeltaT)):
    if (i > 10 and i < 100):  # 0,8
        DeltaT_eyed.append(DeltaT[i])
        VMtimeLog_eyed.append(VMtimeLog[i])

slope, intercept = np.polyfit(VMtimeLog_eyed, DeltaT_eyed, 1)

avgResistance = sum(map(lambda x : x[1], resistance)) / len(resistance)
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


#ax1.set_title("(a)", fontsize=15, **csfont)

print("Tempo" + str(Temp[0]))
print("AvgCurrent" + str(AvgCurrent))
print("q" + str(q))
print("slope" + str(slope))
print("therm" + str(experiment_lambda))
plt.show()
