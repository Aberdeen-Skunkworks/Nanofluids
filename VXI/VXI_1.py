import visa
import matplotlib.pyplot as plt
import time
import serial

#set up visa and print avalible resources
rm = visa.ResourceManager()
print(rm.list_resources())

#set up communication with devices
com = rm.open_resource('GPIB1::9::0::INSTR')
Vmeter = rm.open_resource('GPIB1::9::5::INSTR')
Imeter = rm.open_resource('GPIB1::9::3::INSTR')

Imeter.timeout = 20000 #20 sec time out
Imeter.chunk_size = 15000 #visa chunck size 150Kilobytes
Vmeter.timeout = 20000
Vmeter.chunk_size = 15000


#clear and reset devices
Vmeter.write("*RST; *CLS")
Imeter.write("*RST; *CLS")

#configure the V meter for speed
Vmeter.write("CONF:VOLT:DC 1.5,MAX")
print("Voltage Res = " + Vmeter.query("VOLT:RES?"))
print("Voltage Range = " + Vmeter.query("VOLT:RANG?"))
Vmeter.write("CAL:ZERO:AUTO OFF")
Vmeter.write("TRIG:SOUR EXT")
print("Voltage Trigger Source = " + Vmeter.query("TRIG:SOUR?"))
Vmeter.write("TRIG:SLOP NEG") #deflaut set by RST, but just making sure
print("Voltage Trigger Slope = " + Vmeter.query("TRIG:SLOP?"))
Vmeter.write("SENS:VOLT:NPLC 0.1") #no option for 0.2
print("Voltage NPLC Cycle = " + Vmeter.query("SENS:VOLT:NPLC?"))
Vmeter.write("SENS:VOLT:APER MIN")
print("Voltage Aperature = " + Vmeter.query("SENS:VOLT:APER?"))
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


#Wait for trigger state for meters
Imeter.write("INIT")
Vmeter.write("INIT")

time.sleep(2)

ser.write(b'1')

start = time.time()
Vresult = Vmeter.query("FETC?")
Iresult = Imeter.query("FETC?")
end = time.time()

print(Iresult)
print(Vresult)

file = open("current.txt","w")
file.write(Iresult)
file.close()

file = open("voltage.txt","w")
file.write(Vresult)
file.close()

print(end - start)
