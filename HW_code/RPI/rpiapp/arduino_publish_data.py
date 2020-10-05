"""
TODO
"""
import json
import logging
import time
from config import ConfigRPI
from rpiapp.arduino_commands import CmdType, SensorType
from rpiapp.db_management import get_table_database, update_req_cal_1_table_database, update_req_cal_2_table_database, update_calibration_1_table_database, update_calibration_2_table_database

isCalibrated = [0,0,0,0,0,0,0,0,0,0] #flag for each sensor
_kvalue = 1

def reset_iscalibrated_flags(idx_sensor):
    global isCalibrated
    isCalibrated[idx_sensor] = 0


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

        #handle calibration db
        temperature = 22 #to do, import real value
        sensor_index = get_sensor_index(name) + 1 #index 1 to 10, to extract from calibration table
        if sensor_index < 10:
            idx_sensor_str = 's0' + str(sensor_index)
        else:
            idx_sensor_str = 's' + str(sensor_index)

        db1_row,_ = get_table_database(engine,"calibration_1")
        db2_row,_ = get_table_database(engine,"calibration_2")
        #constructing the payload for mainflux
        #for some sensors, special payload construction is needed, to use the calibration values
        #********************************************
        if name == "pH":
            neutralVoltage = getattr(db1_row, idx_sensor_str) #*5000/1024 #mV @ 5
            acidVoltage = getattr(db2_row, idx_sensor_str)#*5000/1024#mV @ 5V
            #todo: neutral voltage check between 1322-1678
            # value/1024*5000?
            print ("neutral, ", neutralVoltage)
            print("acid, ", acidVoltage) 
            try:
                ph =  readPH_library(value, temperature, neutralVoltage, acidVoltage)
                value = ph
            except:#division by zero
                print("division by zero")
        #***********************************************
        elif name == "Turbidity":
            try:
                #attention! voltage reading is artificially shifted to 5V from 3.3V
                value = readTurbidity(value) 
            except:
                print("error in turbidity computation")
        #************************************************
        elif name == "Conductivity1": #add if calibrated flag
            print("pinvalue: ", value)
            voltage = value/1024*5000
            print("voltage:", voltage)
            global _kvalueLow, _kvalueHigh
            _kvalueLow = getattr(db1_row, idx_sensor_str)
            _kvalueHigh = getattr(db2_row, idx_sensor_str)
            #if isCalibrated[sensor_index-1] == 1: #switch to 0-9 indexes
             #   print("sensor is calibrated")
            #else:
            #    HandleCalibration(engine, name, voltage, db1_row, db2_row, idx_sensor_str, sensor_index, temperature)
            value = readEC(voltage, temperature)
        #***********************************************
            

        payload = [{"bn": "", "n": name, "u": unit, "v": value, "t": timestamp}]
        print(payload)
        client.publish(topic, json.dumps(payload))



def readPH_library(voltage, temperature, neutralVoltage, acidVoltage):
    slope = (7.0-4.0)/((neutralVoltage-1500.0)/3.0 - (acidVoltage-1500.0)/3.0)  
    #two point: (_neutralVoltage,7.0),(_acidVoltage,4.0)
    intercept =  7.0 - slope*(neutralVoltage-1500.0)/3.0
    phValue = slope*(voltage-1500.0)/3.0+intercept;  
    #y = k*x + b
    return phValue

def readTurbidity(reading):
    #from dfrobot wiki page
    #transform reading 0-1023 to voltage 0-5V
    #reading is 0-3.3V
    voltage = reading * 5/1024 # converts reading to 5V value
    #voltage3.3 = reading * 3.3/1024 #maximum pin input is 3.3V
    #voltage5 = voltage3.3 * 5/3.3
    NTU = -1120.4*(voltage**2) + 5742.3*voltage -4352.9
    return NTU 

def readEC(voltage,temperature):
    global _kvalue, _kvalueHigh, _kvalueLow
    rawEC = 1000*voltage/820.0/200.0
    valueTemp = rawEC * _kvalue
    if(valueTemp > 2.5):
        _kvalue = _kvalueHigh
    elif(valueTemp < 2.0):
        _kvalue = _kvalueLow
    value = rawEC * _kvalue
    value = value / (1.0+0.0185*(temperature-25.0))
    print("Voltage:", voltage)
    print("EC:",value)
    return value

def get_sensor_index(name):
    sensor_list = ConfigRPI.SENSOR_MAGNITUDES
    for i in range(len(sensor_list)):
        if sensor_list[i] == name:
            break
    return i

def HandleCalibration(engine, db, value, sensor_index, temperature):
    global _kvalue, _kvalueLow, _kvalueHigh, isCalibrated
    flag1 = 0
    flag2 = 0

    name = ConfigRPI.SENSOR_MAGNITUDES[sensor_index-1]
    if name == "Conductivity1":
        #read cal db\
        print("*******************Handling calibration********************")
        voltage = value *5000/1024
        if db == '1':
            dbname= "calibration_1"
            db_index = 1
        else:
            dbname= "calibration_2"
            db_index = 2

        if sensor_index < 10:
            idx_sensor_str = 's0' + str(sensor_index)
        else:
            idx_sensor_str = 's' + str(sensor_index)
    
            
        print ("db value:", voltage)
        rawEC = 1000*voltage/820.0/200.0 
        print("rawEC:", rawEC)
        if (rawEC>0.9 and rawEC<2): #Buffer Solution:1.413us/cm
            compECsolution = 1.413*(1.0+0.0185*(temperature-25.0))
            KValueTemp = 820.0*200.0*compECsolution/1000.0/voltage
            round(KValueTemp,2)
            _kvalueLow = KValueTemp 
            print ("kLOW:",_kvalueLow)
            update_req_cal_1_table_database(engine, sensor_index, 0) #cal not needed anymore
            flag1 = 1
        elif (rawEC>9 and rawEC<16.8): #Buffer Solution:12.88ms/cm
            compECsolution = 12.88*(1.0+0.0185*(temperature-25.0))
            KValueTemp = 820.0*200.0*compECsolution/1000.0/voltage
            _kvalueHigh = KValueTemp
            print("kHIGH:",_kvalueHigh)
            update_req_cal_2_table_database(engine, sensor_index, 0)
            flag2 = 1
        else:
            if db_index == 1:
                update_req_cal_1_table_database(engine, sensor_index, 1)
            elif db_index == 2:
                update_req_cal_2_table_database(engine, sensor_index, 1)
            print ("error with calibration values, setting db:", db_index ,"flag to retake measurement")
                #to do: flag a database for check_cal fc in flaskapp

        if flag1 == 1 or flag2 == 1: #this function will be called once for a db, and once again for the other
            print ("value is updated")
            if db_index == 1:
                update_req_cal_1_table_database(engine, sensor_index, 0) #cal not needed anymore for this db
                update_calibration_1_table_database(engine, sensor_index, _kvalueLow) #1 to 10
            elif db_index == 2:
                update_req_cal_2_table_database(engine, sensor_index, 0)
                update_calibration_2_table_database(engine, sensor_index, _kvalueHigh) #1 to 10
            #isCalibrated[sensor_index-1] = 1 # 0 to 9 indexes
        else:
            print ("_kvalueLow and _kvalueHigh were not updated correctly")
            #here we should set a flag for flaskapp

    else: #other sensor than conductivity1
        if db == '1':
            update_calibration_1_table_database(engine, sensor_index, value) #1 to 10
        else:
            update_calibration_2_table_database(engine, sensor_index, value)
        
