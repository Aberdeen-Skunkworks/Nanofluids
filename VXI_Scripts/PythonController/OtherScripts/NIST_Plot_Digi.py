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

os.chdir("C://Users//asmo9//Desktop//Nanofluids//VXI//PythonController")

x = []
y = []
row = []
with open("PlotDigitiser.csv") as file1:
    readCSV = csv.reader(file1, delimiter=',')
    next(file1)
    for rows in readCSV:
        for num in rows:
            row.append(num)
        x.append(float(row[0]))
        y.append(float(row[1]))
        row.clear()

B, A = np.polyfit(x, y, 1)
y2 = []
for i in range(len(x)):
    y2.append(A + (B*x[i]))  # + (C*(TP[i]**2)))


plt.plot(x, y, "bo", markersize=4, label="Digitised Data")
plt.plot(x, y2, "g--", linewidth=1,  label="Data Fit")
plt.xticks(fontsize=14, **csfont)
plt.yticks(fontsize=14, **csfont)
plt.xlabel(r'ln(t), t in ms', size=17, **csfont)
plt.ylabel(r'$\Delta$ T', size=17, **csfont)
plt.legend(loc='best', prop={'family': 'Times New Roman', 'size': 12})
plt.show()
