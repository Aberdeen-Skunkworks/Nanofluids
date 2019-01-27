import visa
rm = visa.ResourceManager('C:\Program Files\IVI Foundation\VISA\Win64\ktvisa\ktbin')
print(rm.list_resources())
