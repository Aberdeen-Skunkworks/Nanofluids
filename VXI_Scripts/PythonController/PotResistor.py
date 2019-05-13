import visa
import time
# set up visa and print avalible resources
rm = visa.ResourceManager()
print("Avaiable resources:")
print(rm.list_resources())
Rmeter = rm.open_resource('GPIB1::9::3::INSTR')
Rmeter.timeout = 10000

Rmeter.write("*RST; *CLS")
Rmeter.write("CAL:LFR 50")
Rmeter.write("CONF:FRES 100,DEF")
Rmeter.write("TRIG:SOUR BUS")
Rmeter.write("FRES:NPLC 10")

print("Configuration: " + Rmeter.query("CONF?"))
print("Trig Source: " + Rmeter.query("TRIG:SOUR?"))
print("Range: " + Rmeter.query("FRES:RANG?"))
print("Res: " + Rmeter.query("FRES:RES?"))
print("NPLC: " + Rmeter.query("FRES:NPLC?"))
print("Aper: " + Rmeter.query("FRES:APER?"))

while True:
    print("-")
    Rmeter.write("INIT")
    Rmeter.write("*TRG")
    print(float(Rmeter.query("FETC?")))


# POT 3 - avg 100.004 ohms
# POT 4 - avg 100.017
