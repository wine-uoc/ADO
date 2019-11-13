import paho.mqtt.client as mqttClient
import time
import random as r
import json
import copy
 
def on_connect(client, userdata, flags, rc):
 
    if rc == 0:
 
        print("Connected to broker")
 
        global Connected                #Use global variable
        Connected = True                #Signal connection 
 
    else:
 
        print("Connection failed")
 
data = {} #json dictionary

Connected = False   #global variable for the state of the connection
 
broker_address= "localhost"
port = 1883
user = "mqttuser"
password = "mqttpassword"
clientID = "datagenerator" 
organizations = ["UOC", "UPC"] #organizations will have their data stored in different databases
nb_org_nodes = [3, 5] #number of nodes each organization has
 
client = mqttClient.Client(clientID)               #create new instance
client.username_pw_set(user, password=password)    #set username and password
client.on_connect= on_connect                      #attach function to callback
client.connect(broker_address, port=port)          #connect to broker
 
client.loop_start()        #start the loop
 
while Connected != True:    #Wait for connection
    time.sleep(0.1)
 
try:
    while True:
    	for org in organizations:
    		topic = "ado/"+ str(org)
    		print (org)
    		ind = organizations.index(org)
    		nodes = nb_org_nodes[ind]
    		print (nodes, " nodes")
    		for node_id in range(nodes):
        		raw_topic = topic + "/raw" 
        		node_topic = topic + "/node_" + str(node_id)
        		data['nodeid'] = node_id
        		data['temperature'] = r.uniform(15, 22)
        		data['ph'] = r.uniform(1, 14)
        		data['do'] = r.uniform(100, 200)
        		data['conductivity'] = r.uniform(10, 20)
        		data['lux'] = r.uniform(100, 400)
        		data['flow'] = r.uniform(1, 40) #l/min
        		print(data)
        		data_per_node = copy.deepcopy(data)
        		del data_per_node['nodeid']
        		print(data_per_node)
        		client.publish(raw_topic,json.dumps(data)) #raw topic includes data for all nodes
        		client.publish(node_topic,json.dumps(data_per_node)) #node topic includes data only for a specific node
        		time.sleep(2)
 
except KeyboardInterrupt:
    print("bye bye")
    client.disconnect()
    client.loop_stop()
