from enum import Enum

class CmdType(Enum):
	read = 0
	config = 1
	actuate = 2

class SensorType(Enum):
	analog = 0
	digital = 1
	spi = 2
	onewire = 3

def create_cmd(cmdtype, sensortype, param_list):
	num_param = len(param_list)
	serialcmd = str(CmdType[cmdtype].value) + str(SensorType[sensortype].value) + str(num_param) + ' ' + str(param_list)#+'\n' 
	return serialcmd

def parse_cmd(command):
	cmdtype = int(command[0])
	pinType = int(command[1])
	pinNb = int(command[5])
	return cmdtype, pinType, pinNb

def get_config(): #this should be info received from user via web
	delay = {}
	serialcmd = {}
	periodicity = {}
	serialcmd[1] = create_cmd("read", "analog", [5])
	serialcmd[2]= create_cmd("read", "digital", [3])
	serialcmd[3] = create_cmd("read", "onewire", [0])

	periodicity[1]=30
	periodicity[2]=30
	periodicity[3]=30

	delay[1] = 0
	delay[2] = delay[1] + 3
	delay[3] = delay[2] + 3

	return delay, serialcmd, periodicity

