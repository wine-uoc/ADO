# this is sending data over ubuntu serial to arduino main serial (not gpio to gpio)
import logging
import os
import threading
import time
import json

import serial
from rpiapp import arduino_publish_data, arduino_commands, ini_client
from rpiapp.db_management import check_table_database, get_table_database, update_calibration_1_table_database, update_calibration_2_table_database
from rpiapp.periodic_control_sensors import set_sr
import paho.mqtt.client as mqtt
from config import ConfigRPI


CmdType = arduino_commands.CmdType
SensorType = arduino_commands.SensorType

MQTT_CONNECTED = False  # global variable for the state
MQTT_SUBSCRIBED = False
latest_thread = ['1','2','3','4', '5', '6', '7', '8', '9', '10'] #the name of the latest created thread. position corresponds to sensor index
old_name_available=[1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

def create_threads(ser):
    global latest_thread
    serialcmd, periodicity, magnitudes = arduino_commands.get_config()
    size = len(serialcmd)  # number of configs we have
    for i in range(size):
        if periodicity[i+1] != 0:
            periodicity[i+1] = 60 #force SR to 60
    print('The set of commands is ', serialcmd)
    print('NB of threads is '+ str(size))
    print('periodicity of each thread is ', periodicity)
    print('name of each sensor is ', magnitudes)
    for i in range(1, size + 1):
        # timer is given by expressing a delay
        t = threading.Timer(1, TransmitThread, (ser, serialcmd[i], periodicity[i], magnitudes[i]))  # all sensors send data at startup
        position = arduino_publish_data.get_sensor_index(magnitudes[i])
        name = str(position+1)
        latest_thread[position]=name
        old_name_available[position] = 0 #block this name
        t.setName(name)
        t.start()
        t.join()



def TransmitThread(ser, serialcmd, periodicity, magnitude):
    global no_answer_pending
    global tx_lock
    global old_name_available

    # debug messages; get thread name and get the lock
    #print("TX trying to acquire lock")
    tx_lock.acquire()

    logging.debug('executing thread %s', threading.currentThread().getName())
    # expect an answer from A0 after sending the serial message
    no_answer_pending = False

    # schedule this thread corresponding to its periodicity, with the same name it has now
    now = time.time()
    threadname = threading.currentThread().getName()
    index = arduino_publish_data.get_sensor_index(magnitude)


    if keepalive_thread(magnitude, threadname):
        try:
            ser.write(serialcmd.encode('utf-8')) 
        
            tx = threading.Timer(periodicity, TransmitThread, (ser, serialcmd, periodicity, magnitude))
            threadname =reset_thread_name(threadname, index)
            tx.setName(threadname)
            tx.start()
        
            # create the RX thread; use join() to start right now
            r = threading.Timer(1, ReceiveThread, (ser, serialcmd, magnitude))
            r.setName('RX Thread')
            r.start()
            r.join()
    
        except OSError as e:
            try:
                new_ser = reestablish_serial(ser)
                #attempt writing again
                new_ser.write(serialcmd.encode('utf-8'))

                tx = threading.Timer(periodicity, TransmitThread, (new_ser, serialcmd, periodicity, magnitude))
                threadname =reset_thread_name(threadname, index)
                tx.setName(threadname)
                tx.start()

                # create the RX thread; use join() to start right now
                r = threading.Timer(1, ReceiveThread, (new_ser, serialcmd, magnitude))
                r.setName('RX Thread')
                r.start()
                r.join()

            except:
                # reschedule TX and release lock
                tx = threading.Timer(periodicity, TransmitThread, (ser, serialcmd, periodicity, magnitude))
                threadname =reset_thread_name(threadname, index)
                tx.setName(threadname)
                tx.start()
                tx_lock.release()

    else:
        print("++++ killing thread: ", threadname) #kill thread and release lock
        if threadname == str(index+1): #first name will be available again
            old_name_available[index] = 1   
        tx_lock.release()

  





def ReceiveThread(ser, serialcmd, magnitude):
    global no_answer_pending, client, topic, engine

    try:
        logging.debug('executing thread %s', threading.currentThread().getName())
        cmdtype, sensorType, parameter1 = arduino_commands.parse_cmd(serialcmd)
        # set a timeout for waiting for serial
        # wait until receiving valid answer
        timeout = time.time() + 15
        while no_answer_pending == False and time.time() < timeout:
            if ser.inWaiting() > 0:
                response = ser.readline()
                response = response.decode('utf-8')
                if arduino_publish_data.valid_data(response, sensorType, parameter1):
                    no_answer_pending = True
                    arduino_publish_data.publish_data(magnitude,response, client, topic, engine)
                else:
                    logging.debug("RX data does not correspond to the last command sent, checking again the serial")

        print(time.time(), " End RX processing")
        tx_lock.release()
    except:
        print("##### bad PROCESSING")
        tx_lock.release()


def CalibrationThread(ser, serialcmd, index, engine, db): #not periodic, index 0 to 9
    global no_answer_pending
    global tx_lock
    if db =='1':
        arduino_publish_data.update_req_cal_1_table_database(engine, index+1, 1) #reset to requires cal
    else:
        arduino_publish_data.update_req_cal_2_table_database(engine, index+1, 1) #reset to requires cal

    print("CAL trying to acquire lock")
    tx_lock.acquire()

    threadname = threading.currentThread().getName()
    logging.debug('executing thread %s', threadname)

    # expect an answer from A0 after sending the serial message
    no_answer_pending = False
    try:
        ser.write(serialcmd.encode('utf-8'))
        # create the RX thread; use join() to start right now
        r = threading.Timer(1, SetCalibrationDBThread, (ser, serialcmd, index, engine, db))
        r.setName('RX CAL Thread')
        r.start()
        r.join()
    except OSError as e: 
        try:
            ser = reestablish_serial(ser)
            #attempt writing again
            ser.write(serialcmd.encode('utf-8'))
            r = threading.Timer(1, SetCalibrationDBThread, (ser, serialcmd, index, engine, db))
            r.setName('RX CAL Thread')
            r.start()
            r.join()
        except:
            tx_lock.release() #in case serial fails
     


def SetCalibrationDBThread(ser, serialcmd, index, engine, db):
    global no_answer_pending, client, topic

    try:
        logging.debug('executing thread %s', threading.currentThread().getName())
        cmdtype, sensorType, parameter1 = arduino_commands.parse_cmd(serialcmd)
        logging.debug('SENT CMD %s', serialcmd)
        # set a timeout for waiting for serial
        # wait until receiving valid answer
        timeout = time.time() + 15
        while no_answer_pending == False and time.time() < timeout:
            if ser.inWaiting() > 0:
                response = ser.readline()
                response = response.decode('utf-8')
                logging.debug("%s", str(response))
                if arduino_publish_data.valid_data(response, sensorType, parameter1):
                    no_answer_pending = True
                    idx_sensor = index + 1
                    data = json.loads(response)
                    value = data[0]['pinValue'] #there should be only one item in data

                    arduino_publish_data.HandleCalibration(engine, db, value, idx_sensor)
                else:
                    logging.debug("RX data does not correspond to the last command sent, checking again the serial")

        print(time.time(), " End CAL RX processing")
        tx_lock.release()
    except:
        print("##### bad PROCESSING")
        tx_lock.release()        


def reestablish_serial(serial_port):
    flag = 0 
    if serial_port.isOpen():
        serial_port.close()
    try:    
        ser = serial.Serial(port='/dev/ttyACM0', baudrate=9600)
        flag = 1
        print("connected to ACM0")
    except:
        try:
            ser = serial.Serial(port='/dev/ttyACM1', baudrate=9600)
            flag = 1
            print("connected to ACM1")
        except:
            ser = None
            print("connected to nothing")
    return ser

def keepalive_thread(magnitude, threadname):
    global latest_thread
    
    index = arduino_publish_data.get_sensor_index(magnitude)
    if threadname == latest_thread[index]: #this is the latest created thread for this sensor
        return True
    else:
        return False #this is an old thread for this sensor

def reset_thread_name(threadname, index):
    global old_name_available, latest_thread
    
    if old_name_available[index] == 1: 
        threadname = str(index+1)
        latest_thread[index] = threadname
        old_name_available[index] = 0
    return threadname

############################# MQTT FUNCTIONS ##################################################
def mqtt_connection_0(tokens, engine, serial):
    """Connect to broker and subscribe to topic."""
    mqtt_topic = 'channels/' + str(tokens.channel_id)
    client_userdata = {'topic': mqtt_topic + '/control',
                       'engine': engine, 'serial':serial}

    # avoid deadlock by nop-ing socket control callback stubs
    mqtt.Client._call_socket_register_write = lambda _self: None
    mqtt.Client._call_socket_unregister_write = lambda _self, _sock=None: None
   
    client = mqtt.Client(client_id=str(tokens.node_id), userdata=client_userdata)

    client.username_pw_set(tokens.thing_id, tokens.thing_key)
    client.on_connect = on_connect
    client.on_message = on_message_0
    client.on_subscribe = on_subscribe
    client.on_diconnect = on_disconnect
    client.on_log = on_log

    client.connect_async(host=ConfigRPI.SHORT_SERVER_URL, port=ConfigRPI.SERVER_PORT_MQTT, keepalive=60)
    client.loop_start()
    client.reconnect_delay_set(min_delay=1, max_delay=10)

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

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection.")

def on_log(client, userdata, level, buf):
    if level == MQTT_LOG_WARNING or level == MQTT_LOG_ERR:
        print(buf)


def on_subscribe(client, userdata, mid, granted_qos):
    """Callback for subscribed message."""
    print('Subscribed to %s.' % userdata['topic'])
    global MQTT_SUBSCRIBED
    MQTT_SUBSCRIBED = True


def on_message_0(client, userdata, msg):
    global latest_thread
    """Callback for received message."""
    #print(msg.topic)
    # print("RX1")
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    rx_data = str(msg.payload.decode('UTF-8'))  # message is string now, not json
    message = json.loads(rx_data) #message to json
    print ("***************************************")
    print(message)
    if str(message['type']) == 'SET_SR':
        print("Set Sr message")
            # if message[11:17] == 'SET_SR':  # A naive patch for the issue
            # CAUTION: using message as dict, because messages have different keys, like:
            # [{"bn": "", "n": "Air CO2", "u": "ppm", "v": 30, "t": 1587467662.0718532}]
            # [{"type": "SET_SR", "sensor": "Conductivity", "v": "1", "u": "s", "t": 1587467316.838788}]
            # message = eval(message)  # transform to dictionary
        magnitude = message['sensor']
        SR = int(message['v'])
        new_thread_needed, index = set_sr(client, userdata['engine'], userdata['topic'], magnitude, SR, message['u'])
        if new_thread_needed == 1:
            print("creating new thread")
            
            #create read command
            cmd_type = 'read'  
            sensor_type = ConfigRPI.SENSOR_TYPES[index]
            sensor_params = ConfigRPI.SENSOR_PARAMS[index]
            serialcmd = arduino_commands.create_cmd(cmd_type, sensor_type, sensor_params)
            print(serialcmd)
            print(SR)
            print(magnitude)

            #create thread
            t = threading.Timer(1, TransmitThread, (userdata['serial'], serialcmd, SR, magnitude))
            old_thread = int(latest_thread[index]) #catch the latest thread name for this sensor
            if old_name_available[index] == 1: #this thread was not created at startup in flaskapp config page
                new_thread = str(old_thread)
            else:
                new_thread = str(old_thread+10) #linear translation to make sure we don't duplicate names
            print("****** new thread name: ", new_thread)
            #update latest threadname for this sensor    
            latest_thread[index] = new_thread
            t.setName(new_thread)
            t.start()
            t.join()


        else:
            print("threads stay the same")



    elif str(message['type']) == 'CAL':
        print("**** CAL the", message['n'], "sensor")
        sensor = str(message['n'])
        db_to_use = str(message['v']) #indicates in which calibration db to save the data
        magnitudes = ConfigRPI.SENSOR_MAGNITUDES
        for i in range(len(magnitudes)):
            if magnitudes[i] == sensor:
                break
        # Create command for A0
        cmd_type = 'calibrate'#'read'  
        sensor_type = ConfigRPI.SENSOR_TYPES[i]
        sensor_params = ConfigRPI.SENSOR_PARAMS[i]
        serialcmd = arduino_commands.create_cmd(cmd_type, sensor_type, sensor_params)

        #create calibration thread; use join() to wait for this thread to finish
        r = threading.Timer(1, CalibrationThread, (userdata['serial'], serialcmd, i, userdata['engine'], db_to_use))
        r.setName('CAL Thread')
        r.start()
        r.join()
            
    else:
        print("Received message is not of known type  ")

def main():
    global tx_lock, client, topic, engine
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")

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

    #initialize serial
    ser = serial.Serial(port='/dev/ttyACM0', baudrate=9600)

    # Connect to backend and subscribe to rx control topic
    global MQTT_CONNECTED 
    MQTT_CONNECTED= False
    while not MQTT_CONNECTED:
        MQTT_CONNECTED, client, mqtt_topic = mqtt_connection_0(tokens, engine, ser)
    
    # save the messages topic too
    topic = mqtt_topic + "/messages" 

    #logging.debug("####################### Initializing mqtt broker for client #######################")
    #client, topic = ini_client.initialize_client()

    logging.debug("####################### Creating TX_lock #######################")
    tx_lock = threading.Lock()

    # Wait until table exists in db
    # ASSUMPTION: the script can be called before user registers in flaskapp
    # engine, exists = None, False
    # while not exists:
    #     engine, exists = check_table_database(engine)
    #    time.sleep(1)  # seconds

    logging.debug('####################### Creating Command Threads #######################')
    create_threads(ser)

    logging.debug("####################### Running periodic threads #######################")

    # TODO:
    #  	que pasa si el usuario anade otro sensor mas adelante, se cancelan todos los threads (this)
    #   que pasa si usuario modifica config en grafana
    #   check db periodically (now is checked only when thread happens)
    #   error handling to grafana reading error if x3 reset or error message
    #   reset A0 from rpi
    #   firm udpdate rpi and A0
    #   status message to grafana (https://grafana.com/grafana/plugins/flant-statusmap-panel, auto install in docker
    #   handle rpi reboot

    # print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    try:  # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(2)
            logging.debug('loop')
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        # scheduler.shutdown()
        os.exit()
