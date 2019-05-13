import visa
import os
import os.path
import csv
import serial
import datetime as dt
import numpy as np
import matplotlib.pyplot as plt
import time
from scipy.optimize import fsolve
import serial.tools.list_ports
from matplotlib.lines import Line2D
import matplotlib.animation as animation
csfont = {'fontname': 'Times New Roman'}

os.chdir("C://Users//asmo9//Desktop//Nanofluids//VXI//PythonController//CalibrationResults")
print(os.getcwd())


TP = []
PT_6 = []
PT_5 = []
PT_4 = []
PT_3 = []
PT_2 = []
PT_1 = []
R_6 = []
R_5 = []
R_4 = []
R_3 = []
R_2 = []
R_1 = []
LW = []
SW = []
t = []

selected_row = []

filename = '04-05-21-14.csv'

with open(filename) as file1:
    readCSV = csv.reader(file1, delimiter=',')
    next(file1)
    for rows in readCSV:
        for num in rows:
            selected_row.append(num)
        if (float(selected_row[1]) > 5):
            SW.append(float(selected_row[1]))
            t.append(float(selected_row[2]))
            LW.append(float(selected_row[3]))
            TP.append(float(selected_row[6]))
            R_6.append(float(selected_row[8]))
            PT_6.append(float(selected_row[9]))
            R_1.append(float(selected_row[11]))
            PT_1.append(float(selected_row[12]))
            R_2.append(float(selected_row[14]))
            PT_2.append(float(selected_row[15]))
            R_3.append(float(selected_row[17]))
            PT_3.append(float(selected_row[18]))
            R_4.append(float(selected_row[20]))
            PT_4.append(float(selected_row[21]))
            R_5.append(float(selected_row[23]))
            PT_5.append(float(selected_row[24]))
        selected_row.clear()
file1.close()


def ThermistorSolve(T, R, Rt):
    R25 = Rt
    return (R25*(9.0014E-1 + (3.87235E-3 * T) + (4.86825E-6 * T**2) + (1.37559E-9 * T**3))) - R


PT_6_cal = []
PT_5_cal = []
PT_3_cal = []
PT_2_cal = []
PT_1_cal = []


for i in range(len(R_6)):
    PT_6_cal.append(fsolve(ThermistorSolve, 0, args=(R_6[i], 1206.323)))

for i in range(len(R_5)):
    PT_5_cal.append(fsolve(ThermistorSolve, 0, args=(R_5[i], 1206.937)))

for i in range(len(R_3)):
    PT_3_cal.append(fsolve(ThermistorSolve, 0, args=(R_3[i], 1197.914)))

for i in range(len(R_2)):
    PT_2_cal.append(fsolve(ThermistorSolve, 0, args=(R_2[i], 1197.202)))

for i in range(len(R_1)):
    PT_1_cal.append(fsolve(ThermistorSolve, 0, args=(R_1[i], 1206.526)))

for i in range(len(t)):
    t[i] = t[i]/(60*60)

print(t)
points = np.arange(len(PT_6))

plt.plot(t, PT_6_cal, 'go', markersize=1, label="PT 6")
#plt.plot(t, PT_6, 'go', markersize=1, label="PT 6")
#plt.plot(t, PT_5, 'bo', markersize=1, label="PT 5")
plt.plot(t, PT_5_cal, 'bo', markersize=1, label="PT 5")
#plt.plot(t, PT_3, 'yo', markersize=1, label="PT 3")
plt.plot(t, PT_3_cal, 'yo', markersize=1, label="PT 3")
#plt.plot(t, PT_2, 'mo', markersize=1, label="PT 2")
plt.plot(t, PT_2_cal, 'mo', markersize=1, label="PT 2")
#plt.plot(t, PT_1, 'ro', markersize=1, label="PT 1")
plt.plot(t, PT_1_cal, 'ro', markersize=1, label="PT 1")
plt.plot(t, TP, 'ko', markersize=1, label="Pt100")
plt.tick_params(axis='y', which='both', direction='in')
plt.legend(loc='best', markerscale=4, prop={'family': 'Times New Roman', 'size': 12})
plt.xlabel('Time (hours)', size=15, **csfont)
plt.ylabel(r'Temperature ($^\circ$C)', size=15, **csfont)
plt.show()

plt.plot(points, LW, "ro", markersize=1, label="Long Wire")
plt.plot(points, SW, "bo", markersize=1, label="Short Wire")
plt.xlabel('Point')
plt.ylabel('Resistance')
plt.legend(loc='best')
plt.ylim(35, 60)
plt.show()

# plt.plot(TP, LW, "bo", markersize=1, label="Long Wire")

del TP[0:400]
del LW[0:400]
del SW[0:400]

# TP = [x+273.15 for x in TP]

plt.plot(TP, LW, "ro", markersize=1, label="Long Wire")
plt.plot(TP, SW, "yo", markersize=1, label="Short Wire")


def linear_fit(x, y):
    meanx = sum(x) / len(x)
    meany = sum(y) / len(y)
    c = sum((xi-meanx)*(yi-meany) for xi, yi in zip(x, y)) / sum((xi-meanx)**2 for xi in x)
    m = meany - c*meanx
    return c, m


y = []
y2 = []

B, A = np.polyfit(TP, LW, 1)
B2, A2 = np.polyfit(TP, SW, 1)

print("Long Wire:")
#print("C " + str(C))
print("B " + str(B))
print("A " + str(A))

print("Short Wire:")
#print("C " + str(C2))
print("B " + str(B2))
print("A " + str(A2))

for i in range(len(TP)):
    y.append(A + (B*TP[i]))  # + (C*(TP[i]**2)))
    y2.append(A2 + (B2*TP[i]))  # + (C2*(TP[i]**2)))

plt.plot(TP, y, "ko", markersize=1)
plt.plot(TP, y2, "ko", markersize=1)

plt.show()
# 91.28E-3, 62.29E
LWperM = [x*((np.pi * ((7.5E-6)**2))/91.28E-3)*1E6 for x in LW]
SWperM = [x*((np.pi * ((7.5E-6)**2))/62.29E-3)*1E6 for x in SW]

Rest = []
for i in range(len(TP)):
    Rest.append(((9.847 * (1 + (0.3963E-2*TP[i]) - (0.5389E-6*(TP[i]**2))))*1E-8)*1E6)

plt.plot(TP, LWperM, "ro", markersize=1, label="Long HW")
plt.plot(TP, SWperM, "bo", markersize=1, label="Short HW")
plt.plot(TP, Rest, "yo", markersize=1, label="NIST")
plt.xticks(fontsize=14, **csfont)
plt.yticks(fontsize=14, **csfont)
plt.xlabel(r'Temperature ($^\circ$C)', size=17, **csfont)
plt.ylabel(r'Resistivity ($\mu \Omega / m$)', size=17, **csfont)
plt.legend(loc='best', prop={'family': 'Times New Roman', 'size': 12})
plt.show()
