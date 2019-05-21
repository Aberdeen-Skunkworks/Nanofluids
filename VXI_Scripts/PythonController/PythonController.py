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

#os.chdir("C://Users//asmo9//Desktop//Nanofluids//VXI//PythonController//THW_Results")
print(os.getcwd())

GPIB=0

# set up visa and print avalible resources
rm = visa.ResourceManager()
print("Avaiable resources:")
print(rm.list_resources())

# set up communication with devices
com = rm.open_resource('GPIB'+str(GPIB)+'::9::0::INSTR')
Vmeter = rm.open_resource('GPIB'+str(GPIB)+'::9::23::INSTR')
Imeter = rm.open_resource('GPIB'+str(GPIB)+'::9::3::INSTR')
DA = rm.open_resource('GPIB'+str(GPIB)+'::9::6::INSTR')
Relay = rm.open_resource('GPIB'+str(GPIB)+'::9::4::INSTR')
# Scope = rm.open_resource('ASRL3::INSTR')



timeout_time = 50000  # 20 sec timeout
data_size = 102400  # 100 kB of data

Imeter.timeout = timeout_time
Imeter.chunk_size = data_size
Vmeter.timeout = timeout_time
Vmeter.chunk_size = data_size

Confed = False

def WaitForInput():
    global userinput
    print("")
    print("=============================================")
    print("Control modes:")
    print("(0) = Exit, (1) = Configure Meters, (2) = Bridge Balance, \
 (3) = Run THW, (4) = ... ")
    userinput = input("Enter a command: ")
    print("---------------------------------------------")
    return userinput

while True:
    WaitForInput()
    if (userinput == ("0")):
        print("Breaking...")
        break
    elif (userinput == ("1")):
        ser = serial.Serial('com4', 9600, timeout=2)
        ser.write(b'0')
        ser.close()

        # find temp of cell and wires
        def ThermistorSolve(T, R):  # PT_6
            R25 = 1206.323
            return (R25*(9.0014E-1 + (3.87235E-3 * T) + (4.86825E-6 * T**2) + (1.37559E-9 * T**3))) - R
       
        def RTD_Solve(ProbeRES):
            A = 3.908E-3
            B = -5.775E-7
            C = -4.183E-12
            Ro = 100
            Temp = ((-1*Ro*A)+np.sqrt(((Ro**2) * (A**2)) - (4 * Ro * B * (Ro - ProbeRES)))) / (2*Ro*B)
            return Temp
        
        def Long_HW_Solve(Temp, Res):
            C_l = 5.719122779371328e-05
            B_l = 0.2005214939916926
            A_l = 52.235976794620974
            return (A_l + (B_l*Temp) + (C_l*(Temp**2)))- Res
        
        def Short_HW_Solve(Temp, Res):
            C_s = 2.861284460413907e-05
            B_s = 0.1385312594407914811
            A_s = 35.62074654189631
            return (A_s + (B_s*Temp) + (C_s*(Temp**2))) - Res
        
        def RunMeter():
            time.sleep(0.02)  # GIVE RELAYS TIME
            Vmeter.write("INIT")
            Vmeter.write("TRIG")
            return Vmeter.query("FETC?")
        
        def FourWire(CH1, CH2):
            Relay.write("CLOS (@%s,%s)" % (CH1, CH2))
            Resistance = RunMeter()
            Relay.write("OPEN (@%s,%s)" % (CH1, CH2))
            return Resistance
        
        #Configure the volt meter for very high resolution readings
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
        Relay.write("CLOS (@190, 191)") #Important! close relays of each tree
        
        val = FourWire(111, 103)
        ThermistorTemp = fsolve(ThermistorSolve, 0, float(val))
        print("Thermistor Temp:", ThermistorTemp)
        
        val = FourWire(107, 115)
        RTD_Temp = RTD_Solve(float(val))
        print("PT100 Temp:", RTD_Temp)
        
        val = FourWire(108, 101)
        Short_HW_Temp = fsolve(Short_HW_Solve, 0, float(val))
        print("Short HW Temp:", Short_HW_Temp)
        
        val = FourWire(108, 105)
        Long_HW_Temp = fsolve(Long_HW_Solve, 0, float(val))
        print("Long HW Temp:", Long_HW_Temp)
        
        #Configure modules for experiment 
        
        # set up the DA
        DA.write("*RST")
        DA.write("CAL2:STAT OFF")
        DA.write("CURR2 0.015")

        # set up the relay
        Relay.write("*RST; *CLS")
        Relay.write("SCAN:PORT ABUS")
        Relay.write("CLOS (@105, 190)")
        time.sleep(0.02)

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
        Vmeter.write("CONF:VOLT:DC 10, DEF")
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
            DA.write("CURR2 0.001")

            Relay.write("*RST; *CLS")
            Relay.write("SCAN:PORT ABUS")
            Relay.write("CLOS (@104, 190)")

            ser = serial.Serial('com4', 9600, timeout=2)
            ser.write(b'3')
            ser.close()
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
        
        #Clear out what's been sent by the teensy already
        ser = serial.Serial('com4', 9600, timeout=2)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.write(b'1')

        print("Gathering Meter Data...")
        Vquery = Vmeter.query("FETC?")
        Iquery = Imeter.query("FETC?")
        voltage = -np.array(list(map(float, Vquery.split(','))))
        current = np.array(list(map(float, Iquery.split(','))))
        
        print("Meters Queried. Reading back data from the teensy")

        def readTeensy():
            raw_result = ser.readline()
            if not raw_result:
                raise Exception("Failed to receive reply from teensy")
            return raw_result.decode('utf-8').replace("\r\n", "").strip()
        
        def readTeensyExpect(expected):
            reply = readTeensy()
            if reply != expected:     
                raise Exception("Got unexpected teensy reply, expecting \"",expected,"\" but got \"", reply,"\"")

        readTeensyExpect("PowerTimeStart")
        PowerTimeStart = float(readTeensy())/1000
        print("Power Time Start:", PowerTimeStart)

        readTeensyExpect("PowerTime")
        PowerTime = float(readTeensy())/1000
        print("Power Time:", PowerTime)

        
        def loadTeensyArray(numreadings):
            array = []
            for i in range(numreadings):
                reply = readTeensy()
                try:
                    value = float(reply)/1000
                except:
                    raise Exception("Expecting value but got ",repr(reply))
                array.append(value)
            return array
    
        readTeensyExpect("VMReadings")
        VMreadings = int(readTeensy())
        print("VMReadings:", VMreadings)
        print("Parsing voltage measurement times")
        readTeensyExpect("VMtime")
        VMtime = loadTeensyArray(VMreadings)

        readTeensyExpect("IMReadings")
        IMreadings = int(readTeensy())
        print("VMReadings:", IMreadings)
        print("Parsing current measurement times")
        readTeensyExpect("IMtime")
        IMtime = loadTeensyArray(IMreadings)        
        ser.close()        
        print("Teensy Data Recived and Sorted...")

        print("VM Time Array")
        print(len(VMtime))

        print("IM Time Array")
        print(len(IMtime))

        def writeArray(filename, array):
            open(filename, "w").write(','.join(map(lambda x : repr(x), array)))
        writeArray("vtime.txt", VMtime)
        writeArray("itime.txt", IMtime)
        writeArray("current.txt", current)
        writeArray("voltage.txt", voltage)

        print("Writing to files Completed... plotting")

        if True:
            fig = plt.figure()
            ax1 = fig.add_subplot(1, 2, 1)
            ax2 = fig.add_subplot(2, 2, 4)
            ax = fig.add_subplot(2, 2, 2)

            for i in VMtime:
                ax.plot([i, i], [0, 1], 'b', lw=0.1)

            for j in IMtime:
                ax.plot([j,j], [0, 2], 'y', lw=0.1)

            ax.plot([PowerTime+PowerTimeStart, PowerTime+PowerTimeStart], [0, 3], 'r', lw=1)
            ax.plot([PowerTimeStart, PowerTime+PowerTimeStart], [3, 3], 'r', lw=1)
            ax.plot([PowerTimeStart, PowerTimeStart], [0, 3], 'r', lw=1)

            ax1.plot(VMtime, voltage, marker="o", linestyle="", markersize=1)
            ax2.plot(IMtime, current, marker="o", linestyle="", markersize=1)

            ax.set_yticklabels([])
            ax.set_xticklabels([])

            #ax1.set_ylim([-0.1,1])
            
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
    elif (userinput == ("4")):
        pass
