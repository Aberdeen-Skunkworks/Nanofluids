import os
import visa
import serial
import numpy as np
import matplotlib.pyplot as plt
import time
import serial.tools.list_ports
from matplotlib.lines import Line2D
import matplotlib.animation as animation
from scipy.optimize import fsolve

os.chdir("C://Users//asmo9//Desktop//Nanofluids//VXI//PythonController//THW_Results")
print(os.getcwd())

ser = serial.Serial('com4', 9600, timeout=20)

# set up visa and print avalible resources
rm = visa.ResourceManager()
print("Avaiable resources:")
print(rm.list_resources())

# set up communication with devices
com = rm.open_resource('GPIB1::9::0::INSTR')
Vmeter = rm.open_resource('GPIB1::9::23::INSTR')
Imeter = rm.open_resource('GPIB1::9::3::INSTR')
DA = rm.open_resource('GPIB1::9::6::INSTR')
Relay = rm.open_resource('GPIB1::9::4::INSTR')
# Scope = rm.open_resource('ASRL3::INSTR')

timeout_time = 50000  # 20 sec timeout
data_size = 102400  # 100 kB of data

Imeter.timeout = timeout_time
Imeter.chunk_size = data_size
Vmeter.timeout = timeout_time
Vmeter.chunk_size = data_size

Confed = False


def ThermistorSolve(T, R):  # PT_6
    R25 = 1206.323
    return (R25*(9.0014E-1 + (3.87235E-3 * T) + (4.86825E-6 * T**2) + (1.37559E-9 * T**3))) - R


def WaitForInput():
    global userinput
    print("")
    print("=============================================")
    print("Control modes:")
    print("(0) = Break Loop, (1) = Configure Meters, (2) = Bridge Balance, \
 (3) = Run THW, (4) = ... ")
    userinput = input("Enter a command: ")
    print("---------------------------------------------")
    return userinput


WaitForInput()

while True:
    if (userinput == ("0")):
        print("Breaking...")
        break

    elif (userinput == ("1")):

        print("Conf meter")
        ser.write(b'0')
        # four wire resistance measure POT3 and POT4
        POT3 = 100.03
        POT4 = 100.01

        # find temp cell to find wire resistance
        Vmeter.write("*RST; *CLS")
        Vmeter.write("CAL:LFR 50")
        Vmeter.write("CONF:FRES 1861,DEF")
        Vmeter.write("TRIG:SOUR HOLD")
        Vmeter.write("RES:OCOM ON")
        Vmeter.write("CAL:ZERO:AUTO ON")
        Vmeter.write("RES:APER 3.2E-01")  # 320ms
        Vmeter.write("RES:NPLC 16")

        Relay.write("*RST; *CLS")
        Relay.write("SCAN:PORT ABUS")
        Relay.write("CLOS (@190, 191, 111, 103)")
        time.sleep(0.2)

        Vmeter.write("INIT")
        Vmeter.write("TRIG")
        val = Vmeter.query("FETC?")
        print(float(val))
        Temp = fsolve(ThermistorSolve, 0, float(val))
        print(Temp)

        # resistance of wires
        C_l = 5.719122779371328e-05
        B_l = 0.2005214939916926
        A_l = 52.235976794620974
        LW = A_l + (B_l*Temp) + (C_l*(Temp**2))
        print(LW)

        C_s = 2.861284460413907e-05
        B_s = 0.1385312594407914811
        A_s = 35.62074654189631
        SW = A_s + (B_s*Temp) + (C_s*(Temp**2))
        print(SW)

        POT1 = POT3 - LW
        POT2 = POT4 - SW

        print(POT1)
        print(POT2)

        print("done calc")

        # set up the DA
        DA.write("*RST")
        DA.write("CAL2:STAT OFF")
        DA.write("VOLT2 6")

        # set up the relay
        Relay.write("*RST; *CLS")
        Relay.write("SCAN:PORT ABUS")
        Relay.write("CLOS (@104, 190)")
        time.sleep(0.5)

        # compensate for thermo electric effect
        # Vmeter.write("INIT")
        # Vmeter.write("TRIG")
        # val = Vmeter.query("FETC?")
        # it's so small

        # clear and reset devices
        Vmeter.write("*RST; *CLS")
        Imeter.write("*RST; *CLS")

        # configure the V meter for speed
        Vmeter.write("CAL:LFR MIN")
        print("Volt meter Line Frequency = " + Vmeter.query("CAL:LFR?"))
        Vmeter.write("CONF:VOLT:DC 0.002, DEF")
        print("Voltage Res = " + Vmeter.query("VOLT:RES?"))
        print("Voltage Range = " + Vmeter.query("VOLT:RANG?"))
        Vmeter.write("CAL:ZERO:AUTO ON")
        Vmeter.write("TRIG:SOUR EXT")
        print("Voltage Trigger Source = " + Vmeter.query("TRIG:SOUR?"))
        Vmeter.write("TRIG:SLOP NEG")  # deflaut set by RST
        print("Voltage Trigger Slope = " + Vmeter.query("TRIG:SLOP?"))
        Vmeter.write("SENS:VOLT:NPLC 0.005")  # no option for 0.2
        print("Voltage NPLC Cycle = " + Vmeter.query("SENS:VOLT:NPLC?"))
        # Vmeter.write("SENS:VOLT:APER MIN")
        # print("Voltage Aperature = " + Vmeter.query("SENS:VOLT:APER?"))
        Vmeter.write("SAMP:COUN 500")

        # configure the I meter for speed
        Imeter.write("CAL:ZERO:AUTO ON")
        Imeter.write("CONF:CURR 0.05,MAX")
        print("Current Res = " + Imeter.query("CURR:RES?"))
        print("Current Range = " + Imeter.query("CURR:RANG?"))
        # Imeter.write("CURR:DC:APER MIN")
        print("Current Aperature = " + Imeter.query("CURR:DC:APER?"))
        Imeter.write("CURR:DC:NPLC 0.02")
        print("Current NPLC Cycle = " + Imeter.query("CURR:DC:NPLC?"))
        Imeter.write("TRIG:SOUR EXT")
        print("Current Trigger Source = " + Imeter.query("TRIG:SOUR?"))
        Imeter.write("SAMP:COUN 500")
        WaitForInput()

    elif (userinput == ("2")):
        if (Confed is False):

            Vmeter.write("*RST; *CLS")
            Vmeter.write("CAL:LFR 50")
            Vmeter.write("CONF:VOLT:DC 0.1,DEF")
            Vmeter.write("TRIG:SOUR HOLD")
            Vmeter.write("VOLT:NPLC 16")

            print("Meter settings:")

            print("Configuration: " + Vmeter.query("CONF?"))
            print("Trig Source: " + Vmeter.query("TRIG:SOUR?"))
            print("Range: " + Vmeter.query("VOLT:RANG?"))
            print("Res: " + Vmeter.query("VOLT:RES?"))
            print("NPLC: " + Vmeter.query("VOLT:NPLC?"))
            print("Aper: " + Vmeter.query("VOLT:APER?"))

            print("-------")

            Imeter.write("*RST; *CLS")
            Imeter.write("CONF:CURR:DC 0.05,DEF")
            Imeter.write("TRIG:SOUR BUS")
            Imeter.write("CURR:DC:NPLC 1")

            DA.write("*RST")
            DA.write("CAL2:STAT OFF")
            DA.write("VOLT2 0.2")

            Relay.write("*RST; *CLS")
            Relay.write("SCAN:PORT ABUS")
            Relay.write("CLOS (@104, 190)")

            ser.write(b'3')
            time.sleep(0.1)
            print("Ready")

        Confed = True
        Vmeter.write("INIT")
        Vmeter.write("TRIG")
        val = Vmeter.query("FETC?")
        print(float(val))

    elif (userinput == ("3")):

        print("Started...")
        Imeter.write("INIT")
        Vmeter.write("INIT")
        time.sleep(1)
        result_array = []
        VMtime = []
        IMtime = []
        GetStatus = []

        ser.write(b'1')

        while True:
            print("Powering...")
            GetStatus = ser.readline()
            if GetStatus:
                break

        print("Gathering Meter Data...")
        Vresult = Vmeter.query("FETC?")
        Iresult = Imeter.query("FETC?")

        print("Meters Queried...")

        while True:
            raw_result = ser.readline()
            if raw_result:
                result_array.append(raw_result)
            else:
                break
        ser.close()

        print("Raw Result Recived...")
        print("Total length:")
        print(len(result_array))

        Array_Location_VMtime = 0
        Array_Location_IMtime = 0
        Array_Location_PowerTime = 0
        Array_Location_PowerTimeStart = 0

        for i in range(len(result_array)):
            result_array[i] = result_array[i].decode('utf-8')
            result_array[i] = result_array[i].replace("\r\n", "")

            if result_array[i] == "PowerTimeStart":
                Array_Location_PowerTimeStart = i

            elif result_array[i] == "PowerTime":
                Array_Location_PowerTime = i

            elif result_array[i] == "VMtime":
                Array_Location_VMtime = i

            elif result_array[i] == "IMtime":
                Array_Location_IMtime = i

            else:
                continue

        PowerTimeStart = result_array[Array_Location_PowerTimeStart + 1]
        PowerTime = result_array[Array_Location_PowerTime + 1]

        for x in range(Array_Location_VMtime + 1, Array_Location_IMtime):
            VMtime.append(result_array[x])

        for y in range(Array_Location_IMtime + 1, len(result_array)):
            IMtime.append(result_array[y])

        print("Teensy Data Recived and Sorted...")

        print("Power Time Start:")
        print(PowerTimeStart)

        print("Power Time:")
        print(PowerTime)

        print("VM Time Array")
        print(len(VMtime))

        print("IM Time Array")
        print(len(IMtime))

        with open("vtime.txt", "w") as VMfile:
            for values in VMtime:
                VMfile.write("%s ," % values)
            VMfile.close()

        with open("itime.txt", "w") as IMfile:
            for values in IMtime:
                IMfile.write("%s ," % values)
            IMfile.close()

        Ifile = open("current.txt", "w")
        Ifile.write(Iresult)
        Ifile.close()

        Vfile = open("voltage.txt", "w")
        Vfile.write(Vresult)
        Vfile.close()

        print("Writing to files Completed... ")

        plotinput = input("Plot? (1: Yes): ")

        if (plotinput == ("1")):

            voltage = []
            current = []

            Vfile = open("voltage.txt", "r")
            for line in Vfile:
                values = line.split(",")
                for num in values:
                    voltage.append(num)
            Vfile.close()

            Ifile = open("current.txt", "r")
            for line in Ifile:
                values = line.split(",")
                for num in values:
                    current.append(num)
            Ifile.close()

            VMtime = [i for i in VMtime if i != '0']
            IMtime = [i for i in IMtime if i != '0']

            for i in range(len(VMtime)):
                VMtime[i] = float(VMtime[i])/1000

            for i in range(len(IMtime)):
                IMtime[i] = float(IMtime[i])/1000

            for i in range(len(voltage)):
                voltage[i] = float(voltage[i])

            for i in range(len(current)):
                current[i] = float(current[i])

            fig = plt.figure()
            ax1 = fig.add_subplot(1, 2, 1)
            ax2 = fig.add_subplot(2, 2, 4)
            ax = fig.add_subplot(2, 2, 2)

            for i in range(len(VMtime)):
                ax.plot([VMtime[i], VMtime[i]], [0, 1], 'b', lw=0.1)

            for j in range(len(IMtime)):
                ax.plot([IMtime[j], IMtime[j]], [0, 2], 'y', lw=0.1)

            PowerTimeStart = float(PowerTimeStart)/1000
            PowerTime = float(PowerTime)/1000

            ax.plot([PowerTime+PowerTimeStart, PowerTime+PowerTimeStart], [0, 3], 'r', lw=1)
            ax.plot([PowerTimeStart, PowerTime+PowerTimeStart], [3, 3], 'r', lw=1)
            ax.plot([PowerTimeStart, PowerTimeStart], [0, 3], 'r', lw=1)

            ax1.plot(VMtime, voltage, marker="o", linestyle="", markersize=1)
            ax2.plot(IMtime, current, marker="o", linestyle="", markersize=1)

            ax.set_yticklabels([])
            ax.set_xticklabels([])

            ax.set_xlabel('Time (ms)')
            ax.set_ylabel('')
            ax1.set_xlabel('Time (ms)')
            ax1.set_ylabel('Voltage (V)')
            ax2.set_xlabel('Time (ms)')
            ax2.set_ylabel('Current (I)')

            custom_lines = [Line2D([0], [0], color='r', lw=4),
                            Line2D([0], [0], color='y', lw=4),
                            Line2D([0], [0], color='b', lw=4)]

            ax.legend(custom_lines, ['Power Time', 'IM Complete', 'VM\
 Complete'])

            plt.show()

        else:
            WaitForInput()

        WaitForInput()
        break

    elif (userinput == ("4")):
        if (Confed is False):
            DA.write("*RST")
            DA.write("CAL1:STAT OFF")
            DA.write("CAL2:STAT OFF")
            DA.write("VOLT2 5")

        Confed = True

        print("confed")
        time.sleep(1)
