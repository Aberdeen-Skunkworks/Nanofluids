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

os.chdir("C://Users//asmo9//Desktop//Nanofluids//VXI//PythonController//CalibrationResults")
print(os.getcwd())
filename = 'combined2.csv'

with open('04-03-16-28.csv') as file1:
    readCSV = csv.reader(file1, delimiter=',')
    for row in readCSV:
        with open(filename, "a", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
file1.close()
f.close()

with open('04-03-20-19.csv') as file2:
    readCSV = csv.reader(file2, delimiter=',')
    for row in readCSV:
        with open(filename, "a", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

print("done")
