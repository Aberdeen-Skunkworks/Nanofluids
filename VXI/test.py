import visa
import serial
import matplotlib.pyplot as plt
import time
import serial.tools.list_ports

VM_Array = []
VM_Time_Array = []
IM_Time_Array = []
IM_Array = []

ser = serial.Serial('com3', 9600, timeout = 20)

#set up visa and print avalible resources
rm = visa.ResourceManager()
print("Avaiable resources:")
print(rm.list_resources())

#set up communication with devices
com = rm.open_resource('GPIB1::9::0::INSTR')
Vmeter = rm.open_resource('GPIB1::9::5::INSTR')
Imeter = rm.open_resource('GPIB1::9::3::INSTR')

timeout_time = 20000 #20 sec timeout
data_size = 102400 #100 kB of data

Imeter.timeout = timeout_time
Imeter.chunk_size = data_size #visa chunck size 150Kilobytes
Vmeter.timeout = timeout_time
Vmeter.chunk_size = data_size

def WaitForInput():
    global userinput
    print("")
    print("=============================================")
    print("Control modes:")
    print("(0) = Break Loop, (1) = Configure Meters, (2) = Start THW,\
 (3) = THW Test 1, (4) = THW Test 2")
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

        #clear and reset devices
        Vmeter.write("*RST; *CLS")
        Imeter.write("*RST; *CLS")

        #configure the V meter for speed
        Vmeter.write("CONF:VOLT:DC 1.5,MAX")
        print("Voltage Res = " + Vmeter.query("VOLT:RES?"))
        print("Voltage Range = " + Vmeter.query("VOLT:RANG?"))
        Vmeter.write("CAL:ZERO:AUTO OFF")
        Vmeter.write("TRIG:SOUR EXT")
        Vmeter.write("TRIG:SLOP NEG") #deflaut set by RST, but just making sure
        Vmeter.write("SENS:VOLT:NPLC 0.1") #no option for 0.2
        Vmeter.write("SENS:VOLT:APER MIN")
        Vmeter.write("SAMP:COUN 500")

        #configure the I meter for speed
        Imeter.write("CAL:ZERO:AUTO OFF")
        Imeter.write("CONF:CURR 0.1,MAX")
        print("Current Res = " + Imeter.query("CURR:RES?"))
        print("Current Range = " + Imeter.query("CURR:RANG?"))
        Imeter.write("CURR:DC:APER MIN")
        print("Current Aperature = " + Imeter.query("CURR:DC:APER?"))
        Imeter.write("CURR:DC:NPLC 0.2")
        print("Current NPLC Cycle = " + Imeter.query("CURR:DC:NPLC?"))
        Imeter.write("TRIG:SOUR EXT")
        print("Current Trigger Source = " + Imeter.query("TRIG:SOUR?"))
        Imeter.write("SAMP:COUN 500")
        WaitForInput()

    elif (userinput == ("2")):
        result_array = []

        #Wait for trigger state for meters
        Imeter.write("INIT")
        Vmeter.write("INIT")

        time.sleep(1)

        ser.write(b'1')

        start = time.time()
        Vresult = Vmeter.query("FETC?")
        Iresult = Imeter.query("FETC?")
        end = time.time()

        while True:
            raw_result = ser.readline()
            if raw_result:
                result_array.append(raw_result)
            else:
                break
        ser.close()

        Array_Location_VM_Time = 0
        Array_Location_VM = 0
        Array_Location_IM_Time = 0
        Array_Location_IM = 0

        for i in range(len(result_array)):
            result_array[i] = result_array[i].decode('utf-8')
            result_array[i] = result_array[i].replace("\r\n","")

            if result_array[i] == "VM_Time_Array":
                Array_Location_VM_Time = i

            elif result_array[i] == "VM_Array":
                Array_Location_VM = i

            elif result_array[i] == "IM_Time_Array":
                Array_Location_IM_Time = i

            elif result_array[i] == "IM_Array":
                Array_Location_IM = i

            else:
                continue

        print(len(result_array))
        print(result_array)

        for x in range(Array_Location_VM_Time + 1, Array_Location_VM):
            VM_Time_Array.append(result_array[x])
        for x in range(Array_Location_VM  + 1, Array_Location_IM_Time):
            VM_Array.append(result_array[x])
        for x in range(Array_Location_IM_Time + 1, Array_Location_IM):
            IM_Time_Array.append(result_array[x])
        for x in range(Array_Location_IM + 1, len(result_array)):
            IM_Array.append(result_array[x])

        print("VM_Time_Array")
        print(len(VM_Time_Array))
        print(VM_Time_Array)

        print("")
        print("VM_Array")
        print(len(VM_Array))
        print(VM_Array)

        print("")
        print("IM_Time_Array")
        print(len(IM_Time_Array))
        print(IM_Time_Array)

        print("")
        print("IM_Array")
        print(len(IM_Array))
        print(IM_Array)

        print(Iresult)
        print(Vresult)

        file = open("current.txt","w")
        file.write(Iresult)
        file.close()

        file = open("voltage.txt","w")
        file.write(Vresult)
        file.close()

        print(end - start)

        plt.figure(1)
        plt.subplot(211)
        plt.plot(VM_Time_Array, VM_Array)

        plt.subplot(212)
        plt.plot(IM_Time_Array, IM_Array)
        plt.show()


    elif (userinput == ("3")):
        ser.write(b'3')
        WaitForInput()

    elif (userinput == ("4")):
        ser.write(b'3')
        WaitForInput()

    else:
        print(userinput + " is an invalid command.")
        WaitForInput()
