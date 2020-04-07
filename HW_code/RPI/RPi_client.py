import time

import paho.mqtt.client as mqttClient

from config import get_table_database


def initialize_client():
	global Connected
	global topic
	global client

	# dictionary = eval(open("tokens.txt").read())
	# print(dictionary)
	# thing_id = dictionary["thing1_id"]
	# thing_key = dictionary["thing1_key"]
	# channel_id = dictionary["channel_id"]
	tokens = get_table_database(None, 'tokens')
	thing_id = tokens.thing_id
	thing_key = tokens.thing_key
	channel_id = tokens.channel_id

	# TODO: load this from file
	broker_address = "54.171.128.181"
	port = 1883
	clientID = "thing1: data publisher"

	client = mqttClient.Client(clientID)               #create new instance
	client.username_pw_set(thing_id, thing_key)    #set username and password

	Connected = False   #global variable for the state of the connection
	client.on_connect = on_connect                      #attach function to callback
	client.connect(broker_address, port=port)          #connect to broker

	topic = "channels/" + str(channel_id) + "/messages"
	data = {} #json dictionary

	client.loop_start()        #start the loop
	while Connected != True:    #Wait for connection
		time.sleep(0.1)
	return client, topic


def on_connect(client, userdata, flags, rc):
	if rc == 0:
		print("Connected to broker")
		global Connected                #Use global variable
		Connected = True                #Signal connection 
	else:
		print("Connection failed")