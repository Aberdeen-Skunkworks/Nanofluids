# -*- coding: utf-8 -*-
"""
Created on Fri May 17 13:35:00 2019

@author: Marcus
"""

import visa
import serial
import time
import math
from scipy.optimize import fsolve

class THW:
    def __init__(self, reset_rack = False, full_test = False, gpib = 0, serialport = 'com4'):
        self.ser = serial.Serial(serialport, 9600, timeout=2)
        self.ser.write(b'0')
        self.ser.close()
        
        '''Initialises the VXI device communication and sets the default parameters'''
        self.rm = visa.ResourceManager()
        # set up communication with devices
        #E1406A command module
        self.com = self.rm.open_resource('GPIB'+str(gpib)+'::9::0::INSTR')
        #E1411B 5.5 digit multimeter
        self.Vmeter = self.rm.open_resource('GPIB'+str(gpib)+'::9::23::INSTR')
        #E1412A 6.5 digit multimeter
        self.Imeter = self.rm.open_resource('GPIB'+str(gpib)+'::9::3::INSTR')
        #E1328A Digital analogue converter
        self.DA = self.rm.open_resource('GPIB'+str(gpib)+'::9::6::INSTR')
        #E1345A Relay mux
        self.Relay = self.rm.open_resource('GPIB'+str(gpib)+'::9::4::INSTR')
        
        visa_timeout_time = 5000  # 5 sec timeout
        if full_test:
            visa_timeout_time = 20000  # 20 sec timeout, needed for meter self test!
        visa_chunk_size = 102400  # 100 kB of data
        
        #Setup communication
        for dev in [self.Vmeter, self.Imeter, self.DA, self.Relay]:
            dev.timeout = visa_timeout_time #Timeout needs to be long enough for some of the slow devices to respond
            dev.chunk_size = visa_chunk_size #Chunk just needs to be big enough for any/all data transfers
 
        #Force the rack to reset itself (useful if the meters have become locked up due to misuse)
        if reset_rack:
            print("Resetting VXI rack....wait 10s for them to come back")
            self.com.write("DIAG:BOOT:COLD")
            time.sleep(10)
    
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
        # Now we can check the voltmeter is wired correctly
        
        # find temp of cell and wires
        # 
        # Thermistor 1, 2, 3, 5,6 is  TFPT0805L1201FV TFPT0805 Linear 120x10^1=1200 Ohm ?F=+-1% V #Lead-free 1000pcs
        # Thermistor 4 is TFPT1206L1002FV TFPT1206 Linear 100*10^2=10k Ohm ?F=+-1% V #Lead-free 1000pcs
        #http://www.vishay.com/docs/33017/tfpt.pdf 
        def ThermistorSolve(T, R, Rref=1206.323):  # PT_6
            return Rref*(9.0014E-1 + (3.87235E-3 * T) + (4.86825E-6 * T**2) + (1.37559E-9 * T**3)) - R
       
        def ThermistorT(R, Rref=1206.323):
            return 28.54 * (R/Rref)**3 - 158.5*(R/Rref)**2 + 474.8 * (R/Rref) - 319.85
        #Get the table of ratio tolerances digitized
        
        #Our probe is this
        #https://uk.rs-online.com/web/p/platinum-resistance-temperature-sensors/2364299/?relevancy-data=636F3D3126696E3D4931384E525353746F636B4E756D626572266C753D656E266D6D3D6D61746368616C6C26706D3D5E2828282872737C5253295B205D3F293F285C647B337D5B5C2D5C735D3F5C647B332C347D5B705061415D3F29297C283235285C647B387D7C5C647B317D5C2D5C647B377D2929292426706F3D3126736E3D592673723D2673743D52535F53544F434B5F4E554D4245522677633D4E4F4E45267573743D32333634323939267374613D3233363432393926&searchHistory=%7B%22enabled%22%3Atrue%7D
        #1/5th DIN PT100 +-0.06C at 0C (in accordance with IEC 751)
        #This means the alpha is 0.00385 
        #Following the notes at http://educypedia.karadimov.info/library/c15_136.pdf
        #We can use the Callendar-Van Dusen expression to calculate T
        def RTD_Solve(ProbeRES):
            A = 3.908E-3
            B = -5.775E-7
            #C = -4.183E-12
            Ro = 100
            Temp = ((-Ro*A)+math.sqrt(Ro**2 * A**2 - 4 * Ro * B * (Ro - ProbeRES)))  / (2*Ro*B)
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
        
        #Voltage tree
        ##R_current - CH 0
        ##Short_HW_sense - CH 1
        ##POT_1 - CH 2
        #PT_6 - CH 3
        ##WB_sense - CH 4
        ##Long_HW_Sense - CH 5
        ##POT_2 - CH 6
        #RTD_Probe_Sense - CH 7
        
        #Current tree
        #WB_Power - CH 8
        #PT_4 - CH 9
        #PT_3 - CH 10
        #PT_Power - CH 11
        #PT_5 - CH 12
        #PT_1 - CH 13
        #PT_2 - CH 14
        #RTD_Probe_Power - CH 15
        
        for i,chan in enumerate([[113,111,191,192], [114,111,191,192], [110,111,191,192], [109,111,191,192], [112,111,191,192], [103,111,190,191]]):
            val = self.FourWire(chan)
            ThermistorTemp = fsolve(ThermistorSolve, 0, float(val))[0]
            print("Thermistor",i," R=",val," Temp:", ThermistorTemp, " Temp2:", ThermistorT(val, 1200.0))
        
        val = self.FourWire([107, 115, 190, 191])
        RTD_Temp = RTD_Solve(val)
        print("PT100 probe R=",val,"temp:", RTD_Temp)
        
        val = self.FourWire([101, 108, 190, 191])
        Short_HW_Temp = fsolve(Short_HW_Solve, 0, float(val))[0]
        print("Short HW Temp:", Short_HW_Temp)
        
        val = self.FourWire([105, 108, 190, 191])
        Long_HW_Temp = fsolve(Long_HW_Solve, 0, float(val))[0]
        print("Long HW Temp:", Long_HW_Temp) 
        
    def FourWire(self, channels):
        #Close 90 (AT Tree Switch) and 91 (BT Tree Switch) of card 1. This connects the trees to the analogue bus in 4 wire mode
        self.Relay.write("CLOS (@"+",".join(map(str,channels))+")")
        #print(self.Relay.query("CLOSE? (@100:115,190,191,192)").strip())
        #print(channels)
        #time.sleep(0.02)
        # Load the four wire resistance measurement, add a delay for the meters and take the reading
        self.Vmeter.write("*RST")
        self.Vmeter.write("*RCL 0")
        #self.Vmeter.write("TRIG:DELAY 0.2;:TRIG:SOURCE HOLD;") #Tell the meter be triggered immediately when INITialise'd        
        #self.Vmeter.write("TRIG:DELAY 0.2")
        #self.Vmeter.write("TRIG:SOURCE HOLD")
        #self.Vmeter.write("INIT")
        #self.Vmeter.write("TRIG")
        #Resistance = float(self.Vmeter.query("FETCH?"))
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
        
    def IMeterFastConf(self):
        self.Imeter.write("*RST")
        self.Imeter.write("CAL:LFR 50") #50hz line frequency for the UK
        self.Imeter.write("CONF:CURR 0.05,MAX") # 50mA range, max/fast resolution (worst) (should be 0.02 NPLC, so 2.5kHz)
        self.Imeter.write("CAL:ZERO:AUTO OFF") # Disable auto-zero
        self.Imeter.write("SAMP:COUN 500")
        self.Imeter.write("TRIG:SOUR EXT")
        self.Imeter.write("TRIG:SLOP NEG")
        
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
            
        