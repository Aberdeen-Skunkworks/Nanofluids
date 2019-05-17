import visa
import serial


class TransientHeatedWire:
    
    COM_CODE = "GPIB0::9::0::INSTR"
    VOLT_METER_CODE = "GPIB0::9::23::INSTR"
    CURRENT_METER_CODE = "GPIB0::9::3::INSTR"
    RELAY_CODE = "GPIB0::9::6::INSTR"
    DA_CODE = "GPIB0::9::4::INSTR"
    
    def __init__(self):
        self.rm = visa.ResourceManager()
        print("Available resources:")
        print(self.rm.list_resources())
        
        self.com = self.rm.open_resource(self.COM_CODE)
        self.Vmeter = self.rm.open_resource(self.VOLT_METER_CODE)
        self.Imeter = self.rm.open_resource(self.CURRENT_METER_CODE)
        self.DA = self.rm.open_resource(self.DA_CODE)
        self.Relay = self.rm.open_resource(self.RELAY_CODE)
        
        #self.ser = serial.Serial("com1")
        
        for p in range(101):
            try:
                self.ser = serial.Serial("com{}".format(p), 9600, timeout=20) 
                print("port: com {} found!".format(p))
                break
            except:
                continue
            
    def __del__(self):
        print("deconstruct")
        #print(self.ser)
        print(self.com)
        self.ser.close()