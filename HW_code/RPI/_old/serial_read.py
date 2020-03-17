import serial
import time
import json

ser = serial.Serial(
        port='/dev/serial0', 
        baudrate=9600)

buffer = ""

while 1:
        try:
                response = ser.readline()
                response = response.decode('utf-8')
                print (str(response))
                data = json.loads(response) #a SenML list
                for item in data:
                        print (item)
                        print (item["n"])
                        print (item["u"])
                        print (item["v"])
                buffer = ""
        except json.JSONDecodeError:
                print ("Error : try to parse an incomplete message")

