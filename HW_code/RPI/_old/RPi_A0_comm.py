import sched
import threading
import serial
import time
import json
import RPi.GPIO as GPIO
from enum import Enum

class CmdType(Enum):
	read = 0
	config = 1
	actuate = 2

class SensorType(Enum):
	analog = 0
	digital = 1
	spi = 2

def mycallback(channel) :
	global no_answer_pending
	no_answer_pending = False
	print (time.time(), " interrupted")
	global now = time.time()

def create_cmd(cmdtype, sensortype, param_list):
	num_param = len(param_list)
	serialcmd = str(CmdType[cmdtype].value) + str(SensorType[sensortype].value) + str(num_param) + ' ' + str(param_list)
	return serialcmd

def TransmitThread(ser, serialcmd):
	print (time.time(), ' ', serialcmd)
	GPIO.output(10,1) #it should interrupt arduino and make it listen
	GPIO.output(10,0)
	ser.write(serialcmd.encode('utf-8'))

def ReceiveThread(ser, serialcmd):
		print (time.time(), " The serial cmd transmitted was : ", serialcmd)
		global no_answer_pending
		global received_answer
		if ser.inWaiting()>0:
			received_answer=True
			no_answer_pending =True
			print("manage answer")
			response = ser.readline()
			response = response.decode('utf-8')
			print (str(response))
			if len(response)>2:
				data = json.loads(response) #a SenML list
				for item in data:
                        		print (item)
                        		print (item["pinType"])
                        		print (item["pinNb"])
                        		print (item["pinValue"])
			else:
				print("no content in the answer") #only the new line character
			print (time.time(), " End RX processing")


def main():
	print ("Setting GPIOs")
	scheduler = sched.scheduler(time.time, time.sleep)
	ser = serial.Serial(
        	port='/dev/serial0',
        	baudrate=9600)
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)             # choose BCM or BOARD
	GPIO.setup(10, GPIO.OUT)           # set GPIO10 as an output
	GPIO.setup(9, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #incoming interrupt from arduino;default voltage=0
	GPIO.add_event_detect(9, GPIO.RISING, callback=mycallback, bouncetime=300)

	no_answer_pending = True
	received_answer=False

	print ("Setting Schedules")

	now = time.time()
	print (now)
	serialcmd1 = create_cmd("read", "analog", [5])
	serialcmd2 = create_cmd("read", "digital", [3])
	serialcmd3 = create_cmd("read", "spi", [3, 2, 1])

	e1 = scheduler.enter(5, 1, TransmitThread, (ser, serialcmd1,))
	e2 = scheduler.enter(5, 2, TransmitThread, (ser, serialcmd2,))
	e3 = scheduler.enter(10, 1, TransmitThread, (ser, serialcmd3,))

	re1 = scheduler.enter(10, 1, ReceiveThread, (ser, serialcmd1,))  
	re2 = scheduler.enter(7, 2, ReceiveThread, (ser, serialcmd2,))
	re3 = scheduler.enter(12, 1,ReceiveThread, (ser, serialcmd3,))
	#e2 = scheduler.enter(7, 1, ReceiveThread, (serialcmd,)) #priority 2, to execute after TX

	t = threading.Thread(target = scheduler.run)
	t.start()
	t.join()

	print ("End of script")

if __name__ == "__main__":
	print ("Scheduling Commands for Arduino")
	main()
