import paho.mqtt.client as mqttClient
import time
import random as r
 
def on_connect(client, userdata, flags, rc):
 
    if rc == 0:
 
        print("Connected to broker")
 
        global Connected                #Use global variable
        Connected = True                #Signal connection 
 
    else:
 
        print("Connection failed")
 
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
 
        value = r.uniform(15, 22) 
        print(value)
        client.publish("ado/uoc/temperature",value)
        time.sleep(10)
 
except KeyboardInterrupt:
 
    client.disconnect()
    client.loop_stop()
