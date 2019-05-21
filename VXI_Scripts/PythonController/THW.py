# -*- coding: utf-8 -*-
"""
Created on Fri May 17 13:35:00 2019

@author: Marcus
"""

import visa
import serial

class THW:
    def __init__(self, gpib = 0, serialport = 'com4'):
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
        visa_chunk_size = 102400  # 100 kB of data
        
        #Fast check of device communication
        for dev in [self.Vmeter, self.Imeter, self.DA, self.Relay]:
            dev.timeout = visa_timeout_time #Timeout needs to be long enough for some of the slow devices to respond
            dev.chunk_size = visa_chunk_size #Chunk just needs to be big enough for any/all data transfers
            dev.write("*RST; *CLS") #Reset the device back to its power on state, also clear the status byte used to indicate errors
            print("Device:", dev.query("*IDN?").strip(), flush=True) # Print the identification of the device to check two-way communication
    
        for meter in [self.Vmeter, self.Imeter]:
            meter.write("CAL:LFR 50") #50hz line frequency for the UK
        
        ########### Volt meter configuration setup
        #Configure the volt meter for very high resolution single readings of four wire resistance
        self.Vmeter.write("RES:OCOM ON") #Turn on offset compensation, this tests resistances with current off/on to eliminate thermal offsets
        #self.Vmeter.write("CAL:ZERO:AUTO ON") #Turn on autozero, this halves measurement speed but removes internal DC offset
        #Autozero is not needed when using offset compensation anyway
        #Resolution
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

       
        #self.Vmeter.write("INIT") #Initialise the meter ready to be triggered, causing a trigger
        #self.Vmeter.write("TRIG") #Trigger the meter immediately
        #print(self.Vmeter.query("FETCH?")) #Fetch the result
        #print(self.Vmeter.query("READ?")) #Fetch the result
        #Checking the meter manual, the current supplied ranges from 488mA (256Ohm) to 7.6uA (1048576Ohm) (pg 87)
        #Resolution at 320ms/16 NPLC is 61uOhm for 232Ohm, 488uOhm for 1861 Ohm, and 3.9mOhm for 14894Ohm, 31.2mOhm for 119156Ohm        

        self.checkStatus()
        self.calibrateDA(2)
        self.verifyDA(2)

    def IMeterSlowConf(self):
        '''Setup the current meter for slow but accurate single measurements'''
        self.Imeter.write("*RST")
        self.Imeter.write("CONF:CURR AUTO,MIN") # 50mA range, min/slow resolution (best)
        self.Imeter.write("CAL:ZERO:AUTO ON") # Enable auto-zero
        self.Imeter.write("TRIG:SOUR IMM") # Ready to trigger immediately
        
    def IMeterFastConf(self):
        self.Imeter.write("*RST")
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
        print("DA"+channel+" uncal error (min%%,zero%%,max%%) (%0.3f%%,%0.3f%%,%0.3f%%)" % ((float(minval)/0.024+1)*100,float(zeroval)/0.024*100,(float(maxval)/0.024-1)*100))
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
            try:
                statusbyte = int(dev.query("*STB?"))
            except Exception as e:
                raise Exception("Failed to check",repr(dev), "status byte!")
            if statusbyte != 0:
                raise Exception("Device",repr(dev),"has status byte !=0",statusbyte)
    
    def selftest(self):
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
            

    def VmeterHiResConf(self):
        '''Configures the volt meter for the highest resolution readings'''


        self.Relay.write("SCAN:PORT ABUS")
        self.Relay.write("CLOS (@190, 191)") #Important! close relays of each tree
        
    def VmeterHiSpeedConf(self, long=False):
        '''Configure the Vmeter to take a burst of measurements'''
        #Its possible to read 32k samples at 13khz or more at 12.82kHz
        