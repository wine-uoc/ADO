#!/usr/bin/env python3

"""A MQTT to InfluxDB Bridge

This script receives MQTT data and saves those to InfluxDB.

"""

import re
from typing import NamedTuple

import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient

import time
import json

INFLUXDB_ADDRESS = 'influxdb'
INFLUXDB_USER = 'root'
INFLUXDB_PASSWORD = 'root'
#INFLUXDB_DATABASE = 'ado_db'

MQTT_ADDRESS = 'mosquitto'
MQTT_USER = 'mqttuser'
MQTT_PASSWORD = 'mqttpassword'
MQTT_TOPIC = 'ado/+/+'  
MQTT_REGEX = 'ado/([^/]+)/([^/]+)'
MQTT_CLIENT_ID = 'MQTTInfluxDBBridge'

influxdb_client = InfluxDBClient(INFLUXDB_ADDRESS, 8086, INFLUXDB_USER, INFLUXDB_PASSWORD, None)


class SensorData(NamedTuple):
    location: str
    measurement: str
    value: float



def on_connect(client, userdata, flags, rc):
    """ The callback for when the client receives a CONNACK response from the server."""
    print('Connected with result code ' + str(rc))
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    """The callback for when a PUBLISH message is received from the server."""
    #print(msg.topic + ' ' + str(msg.payload))
    sensor_data = _parse_mqtt_message(msg.topic, msg.payload.decode('utf-8'))
    organization_db = str(sensor_data['organization'])+"_db"  #extract organization info so as to select the corresponding database
    print (organization_db)
    if sensor_data is not None:
        print(sensor_data)
        _look_for_database(organization_db)
        _send_sensor_data_to_influxdb(sensor_data)



def _parse_mqtt_message(topic, payload):
    print("parsing message")
    match = re.match(MQTT_REGEX, topic)
    if match:
        organization = match.group(1) #replacing institution as a tag, with organization as a db
        measurement = match.group(2)
        data = {}
        data['organization'] = organization
        data['measurement'] = measurement
        data['payload'] = payload
        return data
    else:
        return None


def _send_sensor_data_to_influxdb(sensor_data):
    json_body = [
        {
            'measurement': sensor_data['measurement'],
            #'tags': {
             #   'institution': sensor_data['institution'],
            #},
            'fields': json.loads(sensor_data['payload'])
        }
    ]
    influxdb_client.write_points(json_body)


def _look_for_database(organization_database):
    databases = influxdb_client.get_list_database()
    if len(list(filter(lambda x: x['name'] == organization_database, databases))) == 0:
        print('Creating organization database ' + organization_database)
        influxdb_client.create_database(organization_database)
    influxdb_client.switch_database(organization_database)



def main():
    time.sleep(10)

    mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(MQTT_ADDRESS, 1883)
    mqtt_client.loop_forever()


if __name__ == '__main__':
    print('MQTT to InfluxDB bridge')
    main()
