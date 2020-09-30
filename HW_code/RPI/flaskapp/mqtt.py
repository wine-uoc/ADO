#handles the mqtt connection for asking rpi for data from arduino
import paho.mqtt.client as mqtt
from config import ConfigRPI
import time
import json


MQTT_CONNECTED = False  # global variable for the state
MQTT_SUBSCRIBED = False


def mqtt_connection(tokens):
    """Connect to broker and subscribe to topic."""
    mqtt_topic = 'channels/' + str(tokens.channel_id)
    client_userdata = {'topic': mqtt_topic + '/control'}
    #connect using flask_id, to not interfere with node
    client = mqtt.Client(client_id=str(tokens.flask_id), userdata=client_userdata)

    client.username_pw_set(tokens.flask_id, tokens.flask_key)
    client.on_connect = on_connect
    #client.on_message = on_message
    client.on_subscribe = on_subscribe

    client.connect_async(host=ConfigRPI.SHORT_SERVER_URL, port=ConfigRPI.SERVER_PORT_MQTT, keepalive=60)
    client.loop_start()

    # Wait for connection
    global MQTT_CONNECTED
    while not MQTT_CONNECTED:
        time.sleep(1)

    return MQTT_CONNECTED, client, mqtt_topic


def on_connect(client, userdata, flags, rc):
    """The callback for when the client receives a CONNACK response from the server."""
    # The value of rc indicates success or not:
    # 0: Connection successful 1: Connection refused - incorrect protocol version 2: Connection refused - invalid
    # client identifier 3: Connection refused - server unavailable 4: Connection refused - bad username or password
    # 5: Connection refused - not authorised 6-255: Currently unused.
    print("Trying to connect to broker. Result code: " + str(rc))
    if rc == 0:
        print("Connected.")
        global MQTT_CONNECTED
        MQTT_CONNECTED = True
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(userdata['topic'])


def on_subscribe(client, userdata, mid, granted_qos):
    """Callback for subscribed message."""
    print('Subscribed to %s.' % userdata['topic'])
    global MQTT_SUBSCRIBED
    MQTT_SUBSCRIBED = True

def cal_sensor(client, topic, sensor, db_to_use):
    """Send the control message to RPI to ask arduino for data."""
    """sensor holds the sensor name; param is what we calibrate, e.g 4 for pH 4"""
    print("******Calibrating the " + str(sensor) + " sensor, to be stored in db ", str(db_to_use))
    # Find number of sensor
    #magnitudes = ConfigRPI.SENSOR_MAGNITUDES
    #for i in range(len(magnitudes)):
    #    if magnitudes[i] == sensor:
    #        break
    # Update db
    #update_nodeconfig_table_database(engine, i + 1, value)

    # Send control message to rpiapp
    #{"type": "SET_SR", "sensor":sensor_name, "v":selectedvalue, "u":"s", "t":timestamp}
    timestamp = time.time()
    data = [{"type": "CAL", "n": sensor, "v": db_to_use, "t": timestamp}]

    #data = [{"type": "SET_SR", "sensor":sensor, "v":28, "u":"s", "t":timestamp}]
    client.publish(topic, json.dumps(data))
	


