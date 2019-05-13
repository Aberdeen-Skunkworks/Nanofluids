import os
import visa
import serial
import numpy as np
import matplotlib.pyplot as plt
import time
import serial.tools.list_ports
from matplotlib.lines import Line2D

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

timeout_time = 20000  # 20 sec timeout
data_size = 102400  # 100 kB of data

Imeter.timeout = timeout_time
Imeter.chunk_size = data_size
Vmeter.timeout = timeout_time
Vmeter.chunk_size = data_size


def WaitForInput():
    global userinput
    print("")
    print("=============================================")
    print("Control modes:")
    print("(0) = Break Loop, (1) = Configure Meters, (2) = Start THW,\
 (3) = THW Test 1, (4) = ... ")
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

        # clear and reset devices
        Vmeter.write("*RST; *CLS")
        Imeter.write("*RST; *CLS")

        # configure the V meter for speed
        Vmeter.write("CAL:LFR MIN")
        print("Volt meter Line Frequency = " + Vmeter.query("CAL:LFR?"))
        Vmeter.write("CONF:VOLT:DC 0.016, DEF")
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
        Imeter.write("CAL:ZERO:AUTO OFF")
        Imeter.write("CONF:CURR 0.05,MAX")
        print("Current Res = " + Imeter.query("CURR:RES?"))
        print("Current Range = " + Imeter.query("CURR:RANG?"))
        # Imeter.write("CURR:DC:APER MIN")
        print("Current Aperature = " + Imeter.query("CURR:DC:APER?"))
        Imeter.write("CURR:DC:NPLC 0.2")
        print("Current NPLC Cycle = " + Imeter.query("CURR:DC:NPLC?"))
        Imeter.write("TRIG:SOUR EXT")
        print("Current Trigger Source = " + Imeter.query("TRIG:SOUR?"))
        Imeter.write("SAMP:COUN 500")
        WaitForInput()

        # configure D/A
        DA.write("CAL1:STAT OFF")
        DA.write("CAL2:STAT OFF")
        # print("D/A Channel 1 = " + DA.query("CAL1:STAT?"))
        # print("D/A Channel 2 = " + DA.query("CAL2:STAT?"))

    elif (userinput == ("2")):
        print("Started...")
        result_array = []
        VMtime = []
        IMtime = []

        # measure the intial resistance of the wire using a very small current

        # Wait for trigger state for meters
        Imeter.write("INIT")
        Vmeter.write("INIT")

        time.sleep(1)

        GetStatus = []

        ser.write(b'1')
        DA.write("CURR1 0.001")

        while True:
            print("Powering...")
            GetStatus = ser.readline()
            if GetStatus:
                break

        DA.write("CURR1 DEF")
        DA.write("CURR2 DEF")

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

        for i in range(len(result_array)):
            result_array[i] = result_array[i].decode('utf-8')
            result_array[i] = result_array[i].replace("\r\n", "")

            if result_array[i] == "PowerTime":
                Array_Location_PowerTime = i

            elif result_array[i] == "VMtime":
                Array_Location_VMtime = i

            elif result_array[i] == "IMtime":
                Array_Location_IMtime = i

            else:
                continue

        PowerTime = result_array[Array_Location_PowerTime + 1]

        for x in range(Array_Location_VMtime + 1, Array_Location_IMtime):
            VMtime.append(result_array[x])

        for y in range(Array_Location_IMtime + 1, len(result_array)):
            IMtime.append(result_array[y])

        print("Teensy Data Recived and Sorted...")

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
                VMtime[i] = float(VMtime[i])

            for i in range(len(IMtime)):
                IMtime[i] = float(IMtime[i])

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

            PowerTime = float(PowerTime)

            ax.plot([PowerTime, PowerTime], [0, 3], 'r', lw=2)
            ax.plot([0, PowerTime], [3, 3], 'r', lw=2)

            ax1.plot(VMtime, voltage, marker="o", linestyle="", markersize=1)
            ax2.plot(IMtime, current, marker="o", linestyle="", markersize=1)

            ax.set_yticklabels([])
            ax.set_xticklabels([])

            ax.set_xlabel('Time (microseconds)')
            ax.set_ylabel('')
            ax1.set_xlabel('Time (microseconds)')
            ax1.set_ylabel('Voltage (V)')
            ax2.set_xlabel('Time (microseconds)')
            ax2.set_ylabel('Current (I)')

            custom_lines = [Line2D([0], [0], color='r', lw=4),
                            Line2D([0], [0], color='y', lw=4),
                            Line2D([0], [0], color='b', lw=4)]

            ax.legend(custom_lines, ['Power Time', 'Current Trigger', 'Voltage\
 Trigger'])

            plt.show()

        else:
            WaitForInput()

        WaitForInput()

    elif(userinput == ("3")):
        ser.write(b'3')
        WaitForInput()

    elif(userinput == ("4")):

        WaitForInput()

    else:
        print(userinput + " is an invalid command.")
        WaitForInput()
