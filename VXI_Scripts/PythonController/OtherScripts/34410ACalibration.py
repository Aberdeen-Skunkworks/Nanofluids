import visa
rm = visa.ResourceManager()
rm.list_resources()
print(rm.list_resources())

meter = rm.open_resource("USB0::2391::1543::MY47002455::0::INSTR")

print(meter.query("*IDN?"))
