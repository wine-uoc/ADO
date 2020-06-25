"""Receive sampling rates trough control messages, write to db, periodic read of sampling rates from db,
send control message to MainFlux """
import json
import logging
import random
import time

import paho.mqtt.client as mqtt

from config import ConfigRPI
from rpiapp.db_management import get_table_database, check_table_database, update_nodeconfig_table_database
from rpiapp.ini_client import on_connect

MQTT_CONNECTED = False  # global variable for the state
MQTT_SUBSCRIBED = False
LAST_SR_LIST = []
LAST_TIME = time.time()


def do_every(period, f, *args):
    """Periodic scheduling, does not drift in time"""
    def g_tick():
        t = time.time()
        count = 0
        while True:
            count += 1
            yield max(t + count * period - time.time(), 0)

    g = g_tick()
    while True:
        time.sleep(next(g))
        f(*args)


def mqtt_connection(tokens, engine):
    """Connect to broker and subscribe to topic."""
    mqtt_topic = 'channels/' + str(tokens.channel_id)
    client_userdata = {'topic': mqtt_topic + '/control',
                       'engine': engine}
    client = mqtt.Client(client_id=str(tokens.node_id), userdata=client_userdata)

    client.username_pw_set(tokens.thing_id, tokens.thing_key)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_subscribe = on_subscribe

    client.connect_async(host=ConfigRPI.SHORT_SERVER_URL, port=ConfigRPI.SERVER_PORT_MQTT, keepalive=60)
    client.loop_start()
    client.reconnect_delay_set(min_delay=1, max_delay=10)

    # Wait for connection
    global MQTT_CONNECTED
    while not MQTT_CONNECTED:
        time.sleep(1)

    return client, mqtt_topic


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
    print('Subscribed to %s.' % userdata['topic'])
    global MQTT_SUBSCRIBED
    MQTT_SUBSCRIBED = True


def on_message(client, userdata, msg):
    """Callback for received message."""
    print(msg.topic)
    # print("RX1")
    # print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    message = str(msg.payload.decode('UTF-8'))  # message is string now, not json
    print(message)
    message = eval(message)
    if str(message['type']) == 'SET_SR':
        # if message[11:17] == 'SET_SR':  # A naive patch for the issue
        # CAUTION: using message as dict does not work, because messages have different keys, like:
        # [{"bn": "", "n": "Air CO2", "u": "ppm", "v": 30, "t": 1587467662.0718532}]
        # [{"type": "SET_SR", "sensor": "Conductivity", "v": "1", "u": "s", "t": 1587467316.838788}]
        # message = eval(message)  # transform to dictionary
        set_sr(client, userdata['engine'], userdata['topic'], message['sensor'], message['v'], message['u'])
    else:
        print("Received message is not SET_SR type  ")


def set_sr(client, engine, topic, sensor, value, unit):
    """Update db and send the control message to Grafana."""
    print("Setting the SR of the " + str(sensor) + " sensor to " + str(value) + str(unit))
    # Find number of sensor
    magnitudes = ConfigRPI.SENSOR_MAGNITUDES
    for i in range(len(magnitudes)):
        if magnitudes[i] == sensor:
            break

    # Update db
    update_nodeconfig_table_database(engine, i + 1, value)

    # Send control message with new SR for grafana
    data = [{"bn": "", "n": sensor, "u": unit, "v": int(value), "t": time.time()}]
    client.publish(topic, json.dumps(data))


def send_periodic_control(engine, client, mqtt_topic):
    """Send periodic control messages with sampling rates stored in db."""
    global LAST_SR_LIST
    global LAST_TIME
    units = ConfigRPI.SENSOR_UNITS
    magnitudes = ConfigRPI.SENSOR_MAGNITUDES

    # How much time have passed not sending
    time_stamp = time.time()
    passed_time = time_stamp - LAST_TIME

    # Get current SR values in db
    node_config, _ = get_table_database(engine, 'nodeconfig')

    # Get only sampling rates as list
    sampling_rates = list(node_config[1:])

    # 1- Send data if data is sensed:
    # TODO DEMO: sends fake sensor data
    for i in range(len(sampling_rates)):
        sr = sampling_rates[i]
        if sr != 0:
            value = random.gauss(20, 5)
            payload = [{"bn": "", "n": magnitudes[i], "u": units[i], "v": value, "t": time_stamp}]
            client.publish(mqtt_topic + '/messages', json.dumps(payload))

    # 2- Update control state:
    # Compare to the last SR values that were send
    sampling_rates.sort()
    LAST_SR_LIST.sort()
    if sampling_rates != LAST_SR_LIST or passed_time >= 30.:
        # If values have changed, send new
        print(sampling_rates)
        for sensor in range(len(sampling_rates)):
            data = [{"bn": "", "n": magnitudes[sensor], "u": units[sensor], "v": list(node_config[1:])[sensor],
                     "t": time_stamp}]
            client.publish(mqtt_topic + '/control', json.dumps(data))
            time.sleep(0.1)     # 0.1 s * 10 sensors = 1 sec
        LAST_TIME = time_stamp
    else:
        # Do not send
        print(f'Not sending CONTROL, sampling_rates are the same {sampling_rates} and passed time {passed_time} is less than 55s')
    # Unsort them
    LAST_SR_LIST = list(node_config[1:]).copy()


def main_control_sensors():
    global MQTT_SUBSCRIBED

    # Check for a db
    engine, exists = None, False
    while not exists:
        print('Waiting for a database.')
        engine, exists = check_table_database(engine)
        time.sleep(2)

    # Get backend credentials
    tokens_key = None
    while tokens_key is None:
        tokens, _ = get_table_database(engine, 'tokens')
        if tokens:
            tokens_key = tokens.thing_key
            print('Waiting for MQTT credentials.')
        else:
            print('Waiting for node signup.')
        time.sleep(2)

    # # Wait and get again credentials, else: reads db faster than mainflux provides thing key and id
    # del tokens
    # time.sleep(10)
    # tokens, _ = get_table_database(engine, 'tokens')

    # Connect to backend and subscribe to rx control messages
    while not MQTT_SUBSCRIBED:
        client, mqtt_topic = mqtt_connection(tokens, engine)

    # Periodic check on db and control message send
    do_every(ConfigRPI.PERIODIC_CONTROL_SECONDS, send_periodic_control, engine, client, mqtt_topic)

    # do_every(ConfigRPI.PERIODIC_CONTROL_SECONDS, control_sr_function, engine)
    # x = threading.Thread(target=thread_function, args=(engine,))
    # x.start()
    # x.join()
    # with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    #     executor.map(thread_function, [alist]])


if __name__ == "__main__":
    # ASSUMPTION: the script can be called before user registers in flaskapp
    logging.basicConfig(format="%(asctime)s: %(message)s", level=logging.INFO,
                        datefmt="%H:%M:%S")
    main_control_sensors()


# ph = random.gauss(7, 1)
# airco = random.gauss(150, 10)
# temperature = random.gauss(22, 5)
# conductivity = random.gauss(15, 3)
# lux = random.gauss(250, 20)
# flow = random.gauss(20, 4)
#
# #     SENSOR_MAGNITUDES = ['Temperature', 'Light', 'pH', 'Turbidity', 'Flow', 'Conductivity', 'AtmosphericTemp',
# #                          'Oxygen', 'WaterLevel', 'AirCO2']
# #    SENSOR_UNITS = ['Cel', 'lux', 'pH', 'NTU', 'L/min', 'mS/cm', 'Cel', 'mg/L', 'ppm', 'ppm']
# payload3 = [{"bn": "", "n": "Temperature", "u": "C", "v": temperature, "t": time_stamp}]
# payload5 = [{"bn": "", "n": "Light", "u": "lux", "v": lux, "t": time_stamp}]
# payload1 = [{"bn": "", "n": "pH", "u": "ph", "v": ph, "t": time_stamp}]
# payload6 = [{"bn": "", "n": "Flow", "u": "L/min", "v": flow, "t": time_stamp}]
# payload4 = [{"bn": "", "n": "Conductivity", "u": "mS/cm", "v": conductivity, "t": time_stamp}]
# payload2 = [{"bn": "", "n": "AirCO2", "u": "ppm", "v": airco, "t": time_stamp}]
#
# client.publish(mqtt_topic + '/messages', json.dumps(payload1))
# client.publish(mqtt_topic + '/messages', json.dumps(payload2))
# client.publish(mqtt_topic + '/messages', json.dumps(payload3))
# client.publish(mqtt_topic + '/messages', json.dumps(payload4))
# client.publish(mqtt_topic + '/messages', json.dumps(payload5))
# client.publish(mqtt_topic + '/messages', json.dumps(payload6))
#

# def old_control_sr_function(engine):
#     print('hello {} ({:.4f})'.format('asdf',time.time()))
#     # Parameters
#     broker_address = ConfigRPI.SHORT_SERVER_URL
#     port = ConfigRPI.SERVER_PORT_MQTT
#     magnitudes = ConfigRPI.SENSOR_MAGNITUDES
#     units = ConfigRPI.SENSOR_UNITS
#     time_stamp = time.time()
#
#     # Get data from db
#     node_config = get_table_database(engine, 'nodeconfig')
#     tokens = get_table_database(engine, 'tokens')
#
#     # Check that credentials to backend exist
#     if tokens is not None:
#         node_id = tokens.node_id
#         sampling_rates = list(node_config[1:])  # Get only sampling rates ([0] is id, rest are sensors sr)
#         thing_id = tokens.thing_id
#         thing_key = tokens.thing_key
#         channel_id = tokens.channel_id
#
#         # Connect to backend using mqtt
#         client = mqtt.Client('thing' + str(node_id) + ': data publisher')  # create new instance
#         client.username_pw_set(thing_id, thing_key)  # set username and password
#         # Connected = False  # global variable for the state of the connection
#         # client.on_connect = on_connect  # attach function to callback
#         client.connect(broker_address, port=port)  # connect to broker
#         client.loop_start()  # start the loop
#
#         topic = "channels/" + str(channel_id) + "/control/"
#
#         for sensor in range(len(sampling_rates)):
#             data = {}  # json dictionary
#             data = [{"bn": "", "n": magnitudes[sensor], "u": units[sensor], "v": sampling_rates[sensor], "t": time_stamp}]
#             client.publish(topic, json.dumps(data))
#
#         client.disconnect()
#
