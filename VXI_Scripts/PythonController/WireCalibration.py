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

os.chdir("./CalibrationResults")
print(os.getcwd())

# ser = serial.Serial('com4', 9600, timeout=1)

# set up visa and print avalible resources
rm = visa.ResourceManager()
print("Avaiable resources:")
print(rm.list_resources())

# set up communication with devices
com = rm.open_resource('GPIB0::9::0::INSTR')
Vmeter = rm.open_resource('GPIB0::9::23::INSTR')
Imeter = rm.open_resource('GPIB0::9::3::INSTR')
DA = rm.open_resource('GPIB0::9::6::INSTR')
Relay = rm.open_resource('GPIB0::9::4::INSTR')
# Scope = rm.open_resource('ASRL3::INSTR')

timeout_time = 20000  # 20 sec timeout
data_size = 102400  # 100 kB of data

Imeter.timeout = timeout_time
Imeter.chunk_size = data_size
Vmeter.timeout = timeout_time
Vmeter.chunk_size = data_size


def RTD(ProbeRES):
    A = 3.908E-3
    B = -5.775E-7
    C = -4.183E-12
    Ro = 100
    Temp = ((-1*Ro*A)+np.sqrt(((Ro**2) * (A**2)) - (4 * Ro * B * (Ro - ProbeRES)))) / (2*Ro*B)
    print(Temp)
    return Temp


def RunMeter():
    time.sleep(0.015)  # GIVE RELAYS TIME
    Vmeter.write("INIT")
    Vmeter.write("TRIG")
    return Vmeter.query("FETC?")


def FourWire(CH1, CH2):
    Relay.write("CLOS (@%s,%s)" % (CH1, CH2))
    Resistance = RunMeter()
    Relay.write("OPEN (@%s,%s)" % (CH1, CH2))
    return Resistance


def Thermistor_4W(CH1):
    Relay.write("CLOS (@%s)" % (CH1))
    Resistance = RunMeter()
    Relay.write("OPEN (@%s)" % (CH1))
    return Resistance


def Short_HW_4W():
    Relay.write("CLOS (@101, 108)")  # Short HW
    Resistance_short_wire = RunMeter()
    Relay.write("OPEN (@101, 108)")
    return Resistance_short_wire


def Long_HW_4W():
    Relay.write("CLOS (@105, 108)")
    Resistance_long_wire = RunMeter()
    Relay.write("OPEN (@105, 108)")
    return Resistance_long_wire


def WaitForInput():
    global userinput
    print("")
    print("=============================================")
    print("Control modes:")
    print("(0) = Break Loop, (1) = Configure Meter/Relay, (2) = Start Calibration,\
 (3) = Get Calibration Timing, (4) = ... ")
    userinput = input("Enter a command: ")
    print("---------------------------------------------")
    return userinput


def ThermistorSolve(T, R):
    R25 = 1200
    return (R25*(9.0014E-1 + (3.87235E-3 * T) + (4.86825E-6 * T**2) + (1.37559E-9 * T**3))) - R


def ThermistorSolveP(T, R):
    R25 = 10000
    return (R25*(9.0014E-1 + (3.87235E-3 * T) + (4.86825E-6 * T**2) + (1.37559E-9 * T**3))) - R


def TempProbeSolve(T, R):
    RO = 100
    A = 3.908E-3
    B = -5.775E-7
    C = -4.183E-12
    return (RO*(1 + (A * T) + (B * T**2) - (100 * C * T**3) + (C * T**4))) - R


count = 0
x_len = 30
y1_range = [38, 50]
y2_range = [55, 70]
y3_range = [18, 50]
y4_range = [18, 50]

# Create figure for plotting
fig = plt.figure()
ax1 = fig.add_subplot(3, 3, 1)
ax2 = fig.add_subplot(3, 3, 2)
ax3 = fig.add_subplot(3, 3, 3)
ax4 = fig.add_subplot(3, 3, 4)
ax5 = fig.add_subplot(3, 3, 5)
ax6 = fig.add_subplot(3, 3, 6)
ax7 = fig.add_subplot(3, 3, 7)
ax8 = fig.add_subplot(3, 3, 8)
ax9 = fig.add_subplot(3, 3, 9)

xs = list(range(0, x_len))

y1 = [0] * x_len
ax1.set_ylim(y1_range)

y2 = [0] * x_len
ax2.set_ylim(y2_range)

y3 = [0] * x_len
ax3.set_ylim(y3_range)

y4 = [0] * x_len
ax4.set_ylim(y4_range)

y5 = [0] * x_len
ax5.set_ylim(y4_range)

y6 = [0] * x_len
ax6.set_ylim(y4_range)

y7 = [0] * x_len
ax7.set_ylim(y4_range)

y8 = [0] * x_len
ax8.set_ylim(y4_range)

y9 = [0] * x_len
ax9.set_ylim(y4_range)

# Create a blank line. We will update the line in animate
line1, = ax1.plot(xs, y1)
line2, = ax2.plot(xs, y2)
line3, = ax3.plot(xs, y3)
line4, = ax4.plot(xs, y4)
line5, = ax5.plot(xs, y5)
line6, = ax6.plot(xs, y6)
line7, = ax7.plot(xs, y7)
line8, = ax8.plot(xs, y8)
line9, = ax9.plot(xs, y9)
# plt.title('Short Wire')
# plt.xlabel('Samples')
# plt.ylabel('Resistance')

# This function is called periodically from FuncAnimation


def animate(i, y1, y2, y3, y4, y5, y6, y7, y8, y9):
    start = time.time()
    global count

    # Read Resistance from multimeter
    val = float(Short_HW_4W())

    x1 = dt.datetime.now().strftime('%H:%M:%S.%f')
    y1.append(val)

    # Limit y list to set number of items
    y1 = y1[-x_len:]

    # Update line with new Y values
    line1.set_ydata(y1)
    print(val)
    val2 = float(Long_HW_4W())
    x2 = dt.datetime.now().strftime('%H:%M:%S.%f')
    y2.append(val2)
    y2 = y2[-x_len:]
    line2.set_ydata(y2)
    print(val2)
    val3 = float(FourWire(107, 115))  # Temp_Probe
    x3 = dt.datetime.now().strftime('%H:%M:%S.%f')
    Temp3 = fsolve(TempProbeSolve, 0, val3)
    y3.append(Temp3)
    y3 = y3[-x_len:]
    line3.set_ydata(y3)

    Relay.write("CLOS (@111)")

    val4 = float(Thermistor_4W(103))  # PT_6
    x4 = dt.datetime.now().strftime('%H:%M:%S.%f')
    Temp4 = fsolve(ThermistorSolve, 0, val4)
    y4.append(Temp4)
    y4 = y4[-x_len:]
    line4.set_ydata(y4)

    Relay.write("OPEN (@190)")
    Relay.write("CLOS (@192)")

    val5 = float(Thermistor_4W(113))  # PT_1
    x5 = dt.datetime.now().strftime('%H:%M:%S.%f')
    Temp5 = fsolve(ThermistorSolve, 0, val5)
    y5.append(Temp5)
    y5 = y5[-x_len:]
    line5.set_ydata(y5)

    val6 = float(Thermistor_4W(114))  # PT_2
    x6 = dt.datetime.now().strftime('%H:%M:%S.%f')
    Temp6 = fsolve(ThermistorSolve, 0, val6)
    y6.append(Temp6)
    y6 = y6[-x_len:]
    line6.set_ydata(y6)

    val7 = float(Thermistor_4W(110))  # PT_3
    x7 = dt.datetime.now().strftime('%H:%M:%S.%f')
    Temp7 = fsolve(ThermistorSolve, 0, val7)
    y7.append(Temp7)
    y7 = y7[-x_len:]
    line7.set_ydata(y7)

    val8 = float(Thermistor_4W(109))  # PT_4 PERCISE
    x8 = dt.datetime.now().strftime('%H:%M:%S.%f')
    Temp8 = fsolve(ThermistorSolveP, 0, val8)
    y8.append(Temp8)
    y8 = y8[-x_len:]
    line8.set_ydata(y8)

    val9 = float(Thermistor_4W(112))  # PT_5
    x9 = dt.datetime.now().strftime('%H:%M:%S.%f')
    Temp9 = fsolve(ThermistorSolve, 0, val9)
    y9.append(Temp9)
    y9 = y9[-x_len:]
    line9.set_ydata(y9)

    Relay.write("OPEN (@111)")
    Relay.write("CLOS (@190)")
    Relay.write("OPEN (@192)")

    with open(filename, "a", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([count, val, x1, val2, x2,
                         val3, Temp3[0], x3, val4, Temp4[0], x4,
                         val5, Temp5[0], x5, val6, Temp6[0], x6,
                         val7, Temp7[0], x7, val8, Temp8[0], x8,
                         val9, Temp9[0], x9])

    count += 1
    end = time.time()

    print(end - start)

    return line1, line2, line3, line4, line5, line6, line7, line8, line9,


WaitForInput()

while True:
    if (userinput == ("0")):
        print("Breaking...")
        break
    if(userinput == ("1")):

        print(Vmeter.query("*IDN?"))
        print(Relay.query("*IDN?"))

        Vmeter.write("*RST; *CLS")
        Vmeter.write("CAL:LFR 50")
        Vmeter.write("CONF:FRES 1861,DEF")
        Vmeter.write("TRIG:SOUR HOLD")
        Vmeter.write("RES:OCOM ON")
        Vmeter.write("CAL:ZERO:AUTO ON")
        Vmeter.write("RES:APER 3.2E-01")  # 320ms
        Vmeter.write("RES:NPLC 16")

        print("Meter settings:")

        print("Configuration: " + Vmeter.query("CONF?"))
        print("Trig Source: " + Vmeter.query("TRIG:SOUR?"))
        print("Range: " + Vmeter.query("RES:RANG?"))
        print("Res: " + Vmeter.query("RES:RES?"))
        print("NPLC: " + Vmeter.query("RES:NPLC?"))
        print("Aper: " + Vmeter.query("RES:APER?"))
        print("Compensated: " + Vmeter.query("RES:OCOM?"))

        print("-------")

        Relay.write("*RST; *CLS")
        Relay.write("SCAN:PORT ABUS")
        print(Relay.query("*OPC?"))
        WaitForInput()

    if(userinput == ("2")):
        # 190 connects CH00-CH07, 192 connects CH08-CH15 - 4W Sens
        # 191 connects CH08-CH15 - 4W Current
        initalrow = ['#', 'SW', 'SW (t)', 'LW', 'LW (t)',
                     'TP (ohm)', 'Temp Probe (*C)', 'TP (t)',
                     'PT_6 (ohm)', 'PT_6 (*C)', 'PT_6 (t)',
                     'PT_1 (ohm)', 'PT_1 (*C)', 'PT_1 (t)',
                     'PT_2 (ohm)', 'PT_2 (*C)', 'PT_2 (t)',
                     'PT_3 (ohm)', 'PT_3 (*C)', 'PT_3 (t)',
                     'PT_4 (ohm)', 'PT_4 (*C)', 'PT_4 (t)',
                     'PT_5 (ohm)', 'PT_5 (*C)', 'PT_5 (t)']
        filename = dt.datetime.now().strftime('%m-%d-%H-%M.csv')
        with open(filename, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(initalrow)
        f.close()
        Relay.write("CLOS (@190, 191)")
        ani = animation.FuncAnimation(fig, animate, fargs=(
            y1, y2, y3, y4, y5, y6, y7, y8, y9), interval=17500, blit=True)
        plt.show()
        f.close()
        print("exiting calibration mode")
        break

    if(userinput == ("3")):
        # 190 connects CH00-CH07, 192 connects CH08-CH15 - 4W Sens
        # 191 connects CH08-CH15 - 4W Current
        start = time.time()
        Relay.write("CLOS (@190, 191)")
        # print(float(Short_HW_4W()))
        print(float(Long_HW_4W()))
        #print(float(FourWire(107, 115)))
        # Relay.write("CLOS (@111)")  # thermistor current
        # print(float(Thermistor_4W(103)))  # PT_6
        #Relay.write("OPEN (@190)")
        #Relay.write("CLOS (@192)")
        # print(float(Thermistor_4W(112)))  # PT_5
        # print(float(Thermistor_4W(113)))  # PT_1
        # print(float(Thermistor_4W(114)))  # PT_2
        # print(float(Thermistor_4W(110)))  # PT_3
        # print(float(Thermistor_4W(109)))  # PT_4
        end = time.time()
        #print(end - start)
        #print("+0.2 for plot?")
        break

    if(userinput == ("4")):
        RunMeter()
        Relay.write("CLOS (@109,111,192,191)")
        print(RunMeter())
        break

WaitForInput()
