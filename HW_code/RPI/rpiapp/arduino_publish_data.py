"""
TODO
"""
import json
import logging
import time


def valid_data(response, pinType, pinNb):
    if len(response) > 2:
        data = json.loads(response)  # a SenML list
        for item in data:  # normally only one item
            if int(item["pinType"]) == int(pinType) and int(item["pinNb"]) == int(pinNb):
                logging.debug('pinType and pinNb checks')
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
