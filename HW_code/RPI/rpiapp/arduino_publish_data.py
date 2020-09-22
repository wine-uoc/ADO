"""
TODO
"""
import json
import logging
import time
from config import ConfigRPI
from rpiapp.arduino_commands import CmdType, SensorType

def valid_data(response, sensorType, parameter1):
    if len(response) > 2:
        print(response)
        data = json.loads(response)  # a SenML list
        for item in data:  # normally only one item
            try:
                if int(item["sensorType"]) == int(sensorType) and int(item["parameter1"]) == int(parameter1):
                    logging.debug('sensorType and parameter checks')
                    return True
                else:
                    logging.debug('Received data does not correspond to the last sent command')
            except ValueError:
                # it was a string, not int
                logging.debug('parameter is a string')
                if int(item["sensorType"]) == int(sensorType) and str(item["parameter1"]) == str(parameter1):
                    logging.debug('sensorType and parameter checks')
                    return True
                else:
                    logging.debug('Received data does not correspond to the last sent command')

    else:
        logging.debug('Data length is too small')
        return False


def pack_data_onewire(response, client, topic):
    global tx_lock

    data = json.loads(response)  # a SenML list
    for item in data:
        logging.debug("####################### packing data #######################")
        timestamp = time.time()
        value = item['pinValue']
        bn = item['bn']
        name = "Temperature"
        unit = "C"
        payload = [{"bn": "", "n": name, "u": unit, "v": value, "t": timestamp}]
        print(payload)
        client.publish(topic, json.dumps(payload))

def publish_data(magnitude,response, client, topic):
    global tx_lock

    data = json.loads(response)  # a SenML list
    for item in data: #normally there is only one item
        logging.debug("####################### publishing data to mainflux #######################")
        timestamp = time.time()
        # extract read value and hardware name from arduino answer 
        value = item['pinValue']
        bn = item['bn']
        name = magnitude
        unit = [i for (i, v) in zip(ConfigRPI.SENSOR_UNITS, ConfigRPI.SENSOR_MAGNITUDES) if v == name][0]
        #constructing the payload for mainflux
        payload = [{"bn": "", "n": name, "u": unit, "v": value, "t": timestamp}]
        print(payload)
        client.publish(topic, json.dumps(payload))
