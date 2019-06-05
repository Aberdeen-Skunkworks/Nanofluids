# -*- coding: utf-8 -*-
"""
Created on Fri May 17 13:35:00 2019

@author: Marcus
"""

import visa
from visa import VisaIOError
import serial
import time
import math
from scipy.optimize import fsolve
import numpy as np
import matplotlib.pyplot as plt
import serial.tools.list_ports
from matplotlib.lines import Line2D
import matplotlib.animation as animation
from scipy.optimize import fsolve


gpib = 0

class Instrument():
    '''This class adds automatic error checking to pyvisa write/query commands and also adds some common VXI/SCPI commands as class methods.'''
    def __init__(self, name, rm, address, full_test, visa_timeout_time=5000, visa_chunk_size=102400, no_check_commands=[]):
        self.name = name
        self.full_test = full_test
        self.no_check_commands = no_check_commands #Commands which lock-up or reset the instrument, so checking for errors doesn't work
        self.resource = rm.open_resource(address)
        #Timeout needs to be long enough for some of the slow devices to respond
        self.resource.timeout = visa_timeout_time
        #Chunk just needs to be big enough for any/all data transfers
        self.resource.chunk_size = visa_chunk_size
        
    def query(self, cmd):
        '''Send a SCPI query and test/capture any instrument errors'''
        retval = None
        try:
            retval = self.resource.query(cmd)
        except Exception as e:
            #If the command fails/timeouts, check for errors
            raise Exception("Instrument Errors: "+self.get_errors()+"\nLeading to "+str(e))
        #If it succeeds, still check for errors
        if cmd not in self.no_check_commands:
            self.check_errors()
        return retval
    
    def write(self, cmd):
        '''Send a SCPI write and test/capture any instrument errors'''
        try:
            self.resource.write(cmd)
        except Exception as e:
            #If the command fails/timeouts, check for errors
            raise Exception("Instrument Errors: "+self.get_errors()+"\nLeading to "+str(e))
        #If it succeeds, still check for errors
        if cmd not in self.no_check_commands:
            self.check_errors()
    
    def get_errors(self):
        '''Get a list of errors of the device, if there's no error return an empty list'''
        errors=[]
        while True:
            try:
                errcode, errstring = self.resource.query("SYSTEM:ERROR?").split(",")
            except VisaIOError as e:
                #If the command fails/timeouts, check for errors
                raise Exception("VisaIOError on "+self.name+"\nLeading to "+str(e))
            errcode = int(errcode)
            if errcode == 0:
                #This isn't an error, all is fine so stop parsing here
                break
            errors.append([errcode, errstring])
        #Finally, we clear the instrument status if its errored
        if len(errors) != 0:
            self.resource.write("*CLS")
        return errors
    
    def check_errors(self):
        '''Checks if the instrument has any errors and, if so, raises an exception'''
        errors = self.get_errors()
        if len(errors) != 0:
            raise Exception(self.name+": Errors "+str(errors))
            
    ######## SCPI command helpers
    def reset(self):
        self.write("*RST")

class CommandModule(Instrument):
    def __init__(self, rm, full_test, visa_timeout_time):
        super().__init__("CommandModule", rm, 'GPIB'+str(gpib)+'::9::0::INSTR', full_test, visa_timeout_time, no_check_commands=["DIAG:BOOT:COLD", "DIAG:BOOT:WARM"])

from enum import Enum, unique

@unique
class MuxChannels(Enum):
    #A/VOLTAGE TREE
    CURRENT_RESISTOR = 0
    SHORT_WIRE = 1
    POTENTIOMETER_1 = 2
    THERMISTOR_6 = 3
    WS_BRIDGE = 4
    LONG_WIRE = 5
    POTENTIOMETER_2 = 6
    RTD_SENSE = 7
    #B/CURRENT/SENSE TREE
    WSB_POWER = 8 
    THERMISTOR_4 = 9 #10K Thermistor
    THERMISTOR_3 = 10
    THERMISTOR_POWER = 11
    THERMISTOR_5 = 12
    THERMISTOR_1 = 13
    THERMISTOR_2 = 14
    RTD_POWER = 15

def driveChannels():
        return {
            MuxChannels.CURRENT_RESISTOR : MuxChannels.WSB_POWER,
            MuxChannels.SHORT_WIRE : MuxChannels.WSB_POWER,
            MuxChannels.WS_BRIDGE : MuxChannels.WSB_POWER,
            MuxChannels.LONG_WIRE : MuxChannels.WSB_POWER,
            MuxChannels.POTENTIOMETER_1 : MuxChannels.WSB_POWER,
            MuxChannels.POTENTIOMETER_2 : MuxChannels.WSB_POWER,
            MuxChannels.THERMISTOR_1 : MuxChannels.THERMISTOR_POWER,
            MuxChannels.THERMISTOR_2 : MuxChannels.THERMISTOR_POWER,
            MuxChannels.THERMISTOR_3 : MuxChannels.THERMISTOR_POWER,
            MuxChannels.THERMISTOR_4 : MuxChannels.THERMISTOR_POWER,
            MuxChannels.THERMISTOR_5 : MuxChannels.THERMISTOR_POWER,
            MuxChannels.THERMISTOR_6 : MuxChannels.THERMISTOR_POWER,
            MuxChannels.RTD_SENSE : MuxChannels.RTD_POWER,
            }

class RelayMux(Instrument):
    def __init__(self, rm, full_test, visa_timeout_time):
        super().__init__("RelayMux", rm, 'GPIB'+str(gpib)+'::9::4::INSTR', full_test, visa_timeout_time)
    
    def getClosedRelays(self):
        closed = list(map(int, self.query("CLOSE? (@100:115,190,191,192)").strip().split(',')))
        return closed
    
    def closeRelays(self, channels):
        self.write("CLOS (@"+",".join(map(str, channels))+")")
        
    def isTrueFourWire(self, sense):
        '''Returns true if the mux channels can be driven in 4 wire mode'''
        if not 0 <= sense.value <= 15:
            raise Exception(str(sense)+" is not a valid channel number")
        if sense not in driveChannels():
            raise Exception(str(sense)+" has no allocated drive channel on the mux")
        drive = driveChannels()[sense]
        
        return sense.value <= 7 and drive.value >= 8
    
    def twowire_channels(self, sense):
        if not 0 <= sense.value <= 15:
            raise Exception(str(sense)+" is not a valid channel number")

        channels = [100+sense.value]
        if sense.value < 8: #Sense channel is in A tree
            channels.append(190) # Enable the AT Tree Switch to link A tree with meter H L
        else: #Sense channel is in B tree
            channels.append(192) # Enable the AT2 Tree Switch to link B tree with meter H L
        return channels
    
    def fourwire_channels(self, sense):
        if sense not in driveChannels():
            raise Exception(str(sense)+" has no allocated drive channel on the mux")
        
        drive = driveChannels()[sense]

        if not 8 <= drive.value <= 15:
            raise Exception(str(drive)+" is not in the B tree, cannot use it as a drive line!")

        return self.twowire_channels(sense)+[100+drive.value, 191] #191 is the BT Tree switch
    
    def twowire(self, sense):
        self.closeRelays(self.twowire_channels(sense))        
        
    def fourwire(self, sense):
        self.closeRelays(self.fourwire_channels(sense))
        
class THW:
    def __init__(self, reset_rack = False, full_test = False, serialport = 'com4', skip_cal=False):
        #Set the teensy to its default state
        self.ser = serial.Serial(serialport, 9600, timeout=2)
        self.ser.write(b'0')
        self.ser.close()
        
        self.rm = visa.ResourceManager()

        visa_timeout_time = 5000  # 5 sec timeout
        if full_test:
            visa_timeout_time = 20000  # 20 sec timeout, needed for meter self test!
            
        
        # set up communication with devices
        #E1406A command module
        self.com = CommandModule(self.rm, full_test, visa_timeout_time)
        #E1411B 5.5 digit multimeter
        self.Vmeter = Instrument("VMeter", self.rm, 'GPIB'+str(gpib)+'::9::23::INSTR', full_test, visa_timeout_time, no_check_commands=["INIT"])
        #E1412A 6.5 digit multimeter
        self.Imeter = Instrument("IMeter", self.rm, 'GPIB'+str(gpib)+'::9::3::INSTR', full_test, visa_timeout_time, no_check_commands=["INIT"])
        #E1328A Digital analogue converter
        self.DA = Instrument("DA", self.rm, 'GPIB'+str(gpib)+'::9::6::INSTR', full_test, visa_timeout_time)
        #E1345A Relay mux
        self.Relay = RelayMux(self.rm, full_test, visa_timeout_time)
        
 
        #Force the rack to reset itself (useful if the meters have become locked up due to misuse)
        if reset_rack:
            print("Resetting VXI rack....wait 10s for them to come back")
            self.com.write("DIAG:BOOT:COLD")
            time.sleep(10)
            print("Wait complete, continuing")
    
        if full_test:
            self.VXIselftest()
            for dev in [self.Vmeter, self.Imeter, self.DA, self.Relay]:
                dev.write("*RST; *CLS") #Reset the device back to its power on state, also clear the status byte used to indicate errors
        
        ########### Volt meter configuration setup
        # We store the two volt meter modes in the meter itself
        #Configure the volt meter for very high resolution single readings of four wire resistance
        self.Vmeter.write("*RST") # Reset to power-on configuration again
        self.Vmeter.write("CAL:LFR 50") #50hz line frequency for the UK
        self.Vmeter.write("RES:OCOM ON") #Turn on offset compensation, this tests resistances with current off/on to eliminate thermal offsets
        #self.Vmeter.write("CAL:ZERO:AUTO ON") #Turn on autozero, this halves measurement speed but removes internal DC offset
        #Autozero is not needed when using offset compensation anyway
        #Resolution
        #Checking the meter manual, the current supplied ranges from 488uA (256Ohm) to 7.6uA (1048576Ohm) (pg 87)
        #Note that the manual incorrectly states 488mA, but the datasheet states 488uA or 11.5V.
        #Resolution at 320ms/16 NPLC is 61uOhm for 232Ohm, 488uOhm for 1861 Ohm, and 3.9mOhm for 14894Ohm, 31.2mOhm for 119156Ohm
        self.Vmeter.write("CONF:FRES AUTO,MIN") #Configure meter for the auto ranging, minimum resolution (best is min)
        #self.Vmeter.write("CONF:RES AUTO,MIN") #Configure meter for the auto ranging, minimum resolution (best is min)
        #AUTO range increases measurement time by 150ms but guarantees the best range is used
        #self.Vmeter.write("RES:NPLC 16") #16 NLPC
        #self.Vmeter.write("RES:APER 3.2E-01")  # 320ms aperature
        #It is only required to set either the NLPC, aperature, or resolution (in the CONF command). Setting either one of these sets the other three
        #E.g. this will return 16 
        #print(self.Vmeter.query('RES:NPLC?'))
        self.Vmeter.write("TRIG:SOUR IMM") #Tell the meter be triggered immediately when INITialise'd
        self.Vmeter.write("*SAV 0") #  Save this as setup 0
        
        # configure the V meter for speedy bursts of measurements
        self.Vmeter.write("*RST") # Reset to power-on configuration again
        self.Vmeter.write("CAL:LFR 50")  #Set the line frequenc
        self.Vmeter.write("CONF:VOLT:DC 10, MAX") #Fixed voltage range, max resolution (worst possible, but fastest)
        self.Vmeter.write("CAL:ZERO:AUTO OFF") #Disable auto zero
        self.Vmeter.write("SAMP:COUN 500") #Take 500 samples
        self.Vmeter.write("SAMP:SOUR TIM") #Use the internal timer to drive the sampling
        self.Vmeter.write("SAMP:TIM MIN")  #At the fastest timing possible (76us)
        self.Vmeter.write("TRIG:SOUR EXT")
        self.Vmeter.write("TRIG:SLOP NEG") 
        self.Vmeter.write("*SAV 1") #Save as setup 1

        self.checkStatus()
        
        #Now we calibrate the DA supply
        if not skip_cal:
            self.calibrateDA(2)
            if full_test:
                self.verifyDA(2)
            self.checkStatus()
    
    
    def ReadSenseR(self):
        self.ser = serial.Serial('com4', 9600, timeout=2)
        #Switch the wire on instead of the dummy load
        self.IMeterSlowConf()
        self.ser.write(b'4')
        self.DA.write("CURR2 0.0") #Put 0mA through the wires
        self.Relay.write("CLOS (@100,190)")
        self.Vmeter.write("*RST")
        self.Vmeter.write("*RCL 0")
        self.Vmeter.write("CAL:ZERO:AUTO ON")
        self.Vmeter.write("CONF:VOLT:DC AUTO,MIN")
        time.sleep(0.001)
        I0 = float(self.Imeter.query("READ?").strip())
        V0=float(self.Vmeter.query("READ?"))
        print("Voffset=",V0,"Icurr=",I0)
        self.DA.write("CURR2 0.001") #Put 1mA through the wires
        time.sleep(0.001)
        IR = float(self.Imeter.query("READ?").strip())
        VR=float(self.Vmeter.query("READ?"))
        print("Vcurr=",VR,"Icurr=",IR)
        print("R=",(VR-V0)/(IR-I0))
        self.Relay.write("*RST")
        self.ser.write(b'0')
        self.ser.close()

        self.checkStatus()
        
    def Temptest(self):
        # Thermistor 1, 2, 3, 5,6 is  TFPT0805L1201FV TFPT0805 Linear 120x10^1=1200 Ohm ?F=+-1% V #Lead-free 1000pcs
        # Thermistor 4 is TFPT1206L1002FV TFPT1206 Linear 100*10^2=10k Ohm ?F=+-1% V #Lead-free 1000pcs
        #http://www.vishay.com/docs/33017/tfpt.pdf 
        def Thermistor_TtoR(T, Rref=1200):  # PT_6
            return Rref*(9.0014E-1 + (3.87235E-3 * T) + (4.86825E-6 * T**2) + (1.37559E-9 * T**3))
       
        def Thermistor_RtoT(R, Rref=1206.323):
            return 28.54 * (R/Rref)**3 - 158.5*(R/Rref)**2 + 474.8 * (R/Rref) - 319.85
        #Get the table of ratio tolerances digitized
        
        def Thermistor_tol(T):
            if 12 <= T <= 40:
                return 0.005
            elif 0 <= T <= 55:
                return 0.01
            elif -20 <= T <= 85:
                return 0.02
            elif -40 <= T <= 125:
                return 0.03
            elif -55 <= T <= 150:
                return 0.04
            else:
                raise Exception("Out of range")
        
        #Our probe is this
        #https://uk.rs-online.com/web/p/platinum-resistance-temperature-sensors/2364299/?relevancy-data=636F3D3126696E3D4931384E525353746F636B4E756D626572266C753D656E266D6D3D6D61746368616C6C26706D3D5E2828282872737C5253295B205D3F293F285C647B337D5B5C2D5C735D3F5C647B332C347D5B705061415D3F29297C283235285C647B387D7C5C647B317D5C2D5C647B377D2929292426706F3D3126736E3D592673723D2673743D52535F53544F434B5F4E554D4245522677633D4E4F4E45267573743D32333634323939267374613D3233363432393926&searchHistory=%7B%22enabled%22%3Atrue%7D
        #1/5th DIN PT100 +-0.06C at 0C (in accordance with IEC 751)
        #This means the alpha is 0.00385 
        #Following the notes at http://educypedia.karadimov.info/library/c15_136.pdf
        #We can use the Callendar-Van Dusen expression to calculate T
        #
        # Here's a definition via the ITS-90 versus the IPTS-68
        #http://www.code10.info/index.php%3Foption%3Dcom_content%26view%3Darticle%26id%3D82:measuring-temperature-platinum-resistance-thermometers%26catid%3D60:temperature%26Itemid%3D83
        def RTD_RtoT(R, R0=100):
            A = 3.9083E-3
            B = -5.775E-7
            C = -4.183E-12
            Temp = (-R0 * A + math.sqrt(R0**2 * A**2 - 4 * R0 * B * (R0 - R)))  / (2 * R0 * B)
            return Temp
        
        #Our wire lengths are 89.50mm and 60.50mm from pad end to pad end, and 0.015mm diameter
        #Short and Long resistances per length should be within 2% (pg 463 NIST THW)
        #More callendar-Van Dusen equations
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

        sources = [
                (MuxChannels.THERMISTOR_1, lambda R : Thermistor_RtoT(R, Rref=1200.0)),
                (MuxChannels.THERMISTOR_2, lambda R : Thermistor_RtoT(R, Rref=1200.0)),
                (MuxChannels.THERMISTOR_3, lambda R : Thermistor_RtoT(R, Rref=1200.0)),
                (MuxChannels.THERMISTOR_4, lambda R : Thermistor_RtoT(R, Rref=10000.0)),
                (MuxChannels.THERMISTOR_5, lambda R : Thermistor_RtoT(R, Rref=1200.0)),
                (MuxChannels.THERMISTOR_6, lambda R : Thermistor_RtoT(R, Rref=1200.0)),
                (MuxChannels.RTD_SENSE, RTD_RtoT),
                (MuxChannels.SHORT_WIRE, lambda R : fsolve(lambda T : 35.62074654189631 + 0.1385312594407914811 * T + 2.861284460413907e-05 * T**2 - R, 0)[0]),
                (MuxChannels.LONG_WIRE, lambda R :  fsolve(lambda T : 52.235976794620974 + 0.2005214939916926 * T + 5.719122779371328e-05 * T**2 - R, 0)[0])
                ]
        
        
        log = open("T.log", "a+")
        print("# Time", file=log, sep="", end=",") #print header
        for muxchan, RtoT in sources:
            print(muxchan," Resistance", file=log, sep="", end=",")
            print(muxchan," T", file=log, sep="", end=",")
        print("",file=log, sep="", end="\n")
        log.close()
        
        while True:
            log = open("T.log", "a+")
            print(time.strftime("%X %x"), file=log, sep="", end=",")
            for muxchan, RtoT in sources:
                R = self.FourWire(muxchan)
                print(repr(R),repr(RtoT(R)), file=log, sep=",", end=",")
                if muxchan == MuxChannels.RTD_SENSE:
                    print(time.strftime("%X %x"), sep="", end=",")
                    print(repr(R), repr(RtoT(R)), sep=",")
            print("",file=log, sep="", end="\n")
            log.close()
        #val = self.FourWire(MuxChannels.SHORT_WIRE)
        #Short_HW_Temp = fsolve(Short_HW_Solve, 0, float(val))[0]
        #print("Short HW R=",val,"Temp:", Short_HW_Temp)
        
        #val = self.FourWire(MuxChannels.LONG_WIRE)
        #Long_HW_Temp = fsolve(Long_HW_Solve, 0, float(val))[0]
        #print("Long HW R=",val,"Temp:", Long_HW_Temp) 
        
    def FourWire(self, muxchan):
        self.Relay.fourwire(muxchan)
        # Load the four wire resistance measurement, add a delay for the meters and take the reading
        self.Vmeter.write("*RST")
        self.Vmeter.write("*RCL 0")
        Resistance = float(self.Vmeter.query("READ?"))
        self.checkStatus()
        self.Relay.write("*RST")
        return Resistance

    def IMeterSlowConf(self):
        '''Setup the current meter for slow but accurate single measurements'''
        self.Imeter.write("*RST")
        self.Imeter.write("CAL:LFR 50") #50hz line frequency for the UK
        self.Imeter.write("CONF:CURR AUTO,MIN") # 50mA range, min/slow resolution (best)
        self.Imeter.write("CAL:ZERO:AUTO ON") # Enable auto-zero
        self.Imeter.write("TRIG:SOUR IMM") # Ready to trigger immediately
        
    def IMeterFastConf(self, currentrange):
        self.Imeter.write("*RST")
        self.Imeter.write("CAL:LFR 50") #50hz line frequency for the UK
        self.Imeter.write("CONF:CURR "+str(currentrange)+",MAX") # 50mA range, max/fast resolution (worst) (should be 0.02 NPLC, so 2.5kHz)
        self.Imeter.write("CAL:ZERO:AUTO OFF") # Disable auto-zero
        self.Imeter.write("SAMP:COUN 500")
        self.Imeter.write("TRIG:SOUR EXT")
        
    def calibrateDA(self, channel=2):
        '''Calibrate the output of the DA channel in current mode'''
        channel = str(channel)
        print("Calibrating DA channel "+channel)
        
        #Check the channel is configured for current
        if self.DA.query("SOURCE:FUNCTION?").strip() != "CURR":
            raise Exception("Channel "+channel+" of the DA is not configured for current output!")

        #We want the current meter to be as accurate as possible
        self.IMeterSlowConf()
        # set up the DA into uncalibrated mode, then measure its min max and zero values
        self.DA.write("CAL"+channel+":STAT OFF") # Disable calibration until its done
        self.DA.write("CURR"+channel+" MIN")  # Measure the minimum value
        minval = self.Imeter.query("READ?").strip()
        self.DA.write("CURR"+channel+" DEF")  # Measure the zero value
        zeroval = self.Imeter.query("READ?").strip()
        self.DA.write("CURR"+channel+" MAX")  # Measure max value
        maxval = self.Imeter.query("READ?").strip()        
        self.DA.write("CURR"+channel+" DEF")  # Disable the current again
        #print("DA"+channel+" uncal error (min%%,zero%%,max%%) (%0.3f%%,%0.3f%%,%0.3f%%)" % ((float(minval)/0.024+1)*100,float(zeroval)/0.024*100,(float(maxval)/0.024-1)*100))
        #Tell the DA the values so it can internally calibrate
        self.DA.write("CAL"+channel+":CURR "+minval+","+zeroval+","+maxval)
        self.DA.write("CAL"+channel+":STAT ON") #Enable calibration

    def verifyDA(self, channel=2):
        '''Verify the output of the channel is within 24 hour specs (0.05% of output + 7uA)'''
        channel = str(channel)
        print("Verifying DA channel "+channel+" in specs")
        self.IMeterSlowConf()
        #Now verify calibration is within specifications
        self.DA.write("CURR"+channel+" MIN")  # Measure the minimum value
        minval = float(self.Imeter.query("READ?").strip())
        self.DA.write("CURR"+channel+" DEF")  # Measure the zero value
        zeroval = float(self.Imeter.query("READ?").strip())
        self.DA.write("CURR"+channel+" MAX")  # Measure max value
        maxval = float(self.Imeter.query("READ?").strip())
        self.DA.write("CURR"+channel+" DEF")  # Disable the current again
        
        print("DA"+channel+" cal error (min%%,zero%%,max%%) (%0.3f%%,%0.3f%%,%0.3f%%)" % ((float(minval)/0.02184+1)*100,float(zeroval)/0.02184*100,(float(maxval)/0.02184-1)*100))
        if abs(minval+0.02184) > 0.0005*0.02184+7e-6:
            raise Exception("DA Channel "+channel+" min value is out of spec!")
        if abs(maxval-0.02184) > 0.0005*0.02184+7e-6:
            raise Exception("DA Channel "+channel+" max value is out of spec!")
        if abs(zeroval) > 7e-6:
            raise Exception("DA Channel "+channel+" zero value is out of spec!")
        
    def checkStatus(self):
        '''Checks the status bytes of every VXI device to see if any are in an error state'''
        for dev in [self.Vmeter, self.Imeter, self.DA, self.Relay]:
            errcode,errstring = dev.query("SYSTEM:ERROR?").split(",")
            if int(errcode) != 0:
                raise Exception("Device",repr(dev),"has errcode",errcode," ",errstring)
    
    def VXIselftest(self):
        '''Runs the built-in self test for each VXI device to check its ok'''
        print("Testing devices ")
        for dev in [self.Vmeter, self.Imeter, self.DA, self.Relay]:
            print("Device:", dev.query("*IDN?").strip(),"...",end="")
            try:
                result = int(dev.query("*TST?"))
            except Exception as e:
                raise Exception("Failed to obtain device,",repr(dev),", status.", e)
            if result != 0:
                raise Exception("Device ", repr(dev), "returned failed test")
            print("OK!")
    
    def runSingleWireTest(self, current, sensechan):
        self.Relay.twowire(sensechan)

        self.DA.write("CURR2 "+str(current))  # Disable the current again

        self.Vmeter.write("*RST") # Reset to power-on configuration again
        self.Vmeter.write("CAL:LFR 50")  #Set the line frequenc
        self.Vmeter.write("CONF:VOLT:DC 1, MAX") #Fixed voltage range, max resolution (worst possible, but fastest)
        self.Vmeter.write("CAL:ZERO:AUTO OFF") #Disable auto zero
        self.Vmeter.write("SAMP:COUN 500") #Take 500 samples
        self.Vmeter.write("SAMP:SOUR TIM") #Use the internal timer to drive the sampling
        self.Vmeter.write("SAMP:TIM MIN")  #At the fastest timing possible (76us)
        self.Vmeter.write("TRIG:SOUR EXT")
        self.Vmeter.write("TRIG:SLOP NEG")
        self.Vmeter.write("INIT")
        self.IMeterFastConf(current)
        self.Imeter.write("INIT")

        result_array = []
        VMtime = []
        IMtime = []
        GetStatus = []
        print("Sleeping 1 second to let the DA output stabilise")
        time.sleep(1)
        print("Triggering the run")
        #Clear out what's been sent by the teensy already
        self.ser = serial.Serial('com4', 9600, timeout=2)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.ser.write(b'1')
        
        print("Gathering Meter Data...")
        Vquery = self.Vmeter.query("FETC?")
        Iquery = self.Imeter.query("FETC?")
        voltage = -np.array(list(map(float, Vquery.split(','))))
        current = np.array(list(map(float, Iquery.split(','))))
        
        self.Relay.write("*RST")
        
        print("Meters Queried. Reading back data from the teensy")

        def readTeensy():
            raw_result = self.ser.readline()
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
        self.ser.close()        
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
        