import paho.mqtt.client as mqttClient
import time
import random as r
import json
 
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
 
client = mqttClient.Client(clientID)               #create new instance
client.username_pw_set(user, password=password)    #set username and password
client.on_connect= on_connect                      #attach function to callback
client.connect(broker_address, port=port)          #connect to broker
 
client.loop_start()        #start the loop
 
while Connected != True:    #Wait for connection
    time.sleep(0.1)
 
try:
    while True:
        for node_id in range(3):
            data['nodeid'] = node_id
            data['temperature'] = r.uniform(15, 22)
            data['ph'] = r.uniform(1, 14)
            data['do'] = r.uniform(100, 200)
            data['conductivity'] = r.uniform(10, 20)
            data['lux'] = r.uniform(100, 400)
            data['flow'] = r.uniform(1, 40) #l/min
            print(data)
            client.publish("ado/uoc/sensors",json.dumps(data))
            time.sleep(2)
 
except KeyboardInterrupt:
    print("bye bye")
    client.disconnect()
    client.loop_stop()
