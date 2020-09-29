"""
TODO
"""
import json
import logging
import time
from config import ConfigRPI
from rpiapp.arduino_commands import CmdType, SensorType
from rpiapp.db_management import get_table_database

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

def publish_data(magnitude,response, client, topic, engine):
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
        #for pH, special payload construction is needed, to use the calibration values
        if name == "pH":
            temperature = 25 #there is no temp compensation in dfrobot library code
            ph_index = get_sensor_index(name) + 1 #index 1 to 10
            if ph_index < 10:
                idx_sensor_str = 's0' + str(ph_index)
            else:
                idx_sensor_str = 's' + str(ph_index)

            neutral_row,_=get_table_database(engine,"calibration_1")
            neutralVoltage = getattr(neutral_row, idx_sensor_str)

            acid_row,_=get_table_database(engine,"calibration_2")
            acidVoltage = getattr(acid_row, idx_sensor_str)

            #todo: neutral voltage check between 1322-1678
            # value/1024*5000?
            #todo handle division by zero in readPH
            print ("neutral, ", neutralVoltage)
            print("acid, ", acidVoltage) 
            ph =  readPH(value, temperature, neutralVoltage, acidVoltage)
            value = ph

        payload = [{"bn": "", "n": name, "u": unit, "v": value, "t": timestamp}]
        print(payload)
        client.publish(topic, json.dumps(payload))



def readPH(voltage, temperature, neutralVoltage, acidVoltage):
    slope = (7.0-4.0)/((neutralVoltage-1500.0)/3.0 - (acidVoltage-1500.0)/3.0)  
    #two point: (_neutralVoltage,7.0),(_acidVoltage,4.0)
    intercept =  7.0 - slope*(neutralVoltage-1500.0)/3.0
    phValue = slope*(voltage-1500.0)/3.0+intercept;  
    #y = k*x + b
    return phValue

def get_sensor_index(name):
    sensor_list = ConfigRPI.SENSOR_MAGNITUDES
    for i in range(len(sensor_list)):
        if sensor_list[i] == name:
            break
    return i