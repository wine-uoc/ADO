# this is sending data over ubuntu serial to arduino main serial (not gpio to gpio)
import logging
import os
import threading
import time

import serial

from rpiapp import arduino_publish_data, arduino_commands, ini_client
from rpiapp.db_management import check_table_database

CmdType = arduino_commands.CmdType
SensorType = arduino_commands.SensorType


def create_threads(ser):
    serialcmd, periodicity = arduino_commands.get_config()
    size = len(serialcmd)  # number of configs we have
    for i in range(1, size + 1):
        # timer is given by expressing a delay
        t = threading.Timer(1, TransmitThread, (ser, serialcmd[i], periodicity[i]))  # all sensors send data at startup
        t.setName(str(i))
        t.start()
        t.join()


def TransmitThread(ser, serialcmd, periodicity):
    global no_answer_pending
    global tx_lock
    # debug messages; get thread name and get the lock
    logging.debug('executing thread %s', threading.currentThread().getName())
    threadname = threading.currentThread().getName()
    logging.debug('Waiting for lock')
    tx_lock.acquire()
    logging.debug('Acquired lock')
    # schedule this thread corresponding to its periodicity, with the same name it has now
    now = time.time()
    tx = threading.Timer(periodicity, TransmitThread, (ser, serialcmd, periodicity))
    tx.setName(threadname)
    tx.start()
    # expect an answer from A0 after sending the serial message
    no_answer_pending = False
    logging.debug('%s', serialcmd)
    ser.write(serialcmd.encode('utf-8'))
    # create the RX thread; use join() to start right now
    r = threading.Timer(1, ReceiveThread, (ser, serialcmd))
    r.setName('RX Thread')
    r.start()
    r.join()


def ReceiveThread(ser, serialcmd):
    global no_answer_pending, client, topic

    # debug messages
    logging.debug('executing thread %s', threading.currentThread().getName())
    logging.debug('%s', serialcmd)
    cmdtype, pinType, pinNb = arduino_commands.parse_cmd(serialcmd)
    logging.debug('pinType %s', pinType)
    logging.debug('pinNb %s', pinNb)
    # set a timeout for waiting for serial
    # wait until receiving valid answer
    timeout = time.time() + 15
    while no_answer_pending == False and time.time() < timeout:
        if ser.inWaiting() > 0:
            logging.debug("manage answer")
            response = ser.readline()
            response = response.decode('utf-8')
            logging.debug("%s", str(response))
            if arduino_publish_data.valid_data(response, pinType, pinNb):
                no_answer_pending = True
                # if (item["pinType"]) == str(SensorType["onewire"].value):
                if pinType == int(SensorType["onewire"].value):
                    arduino_publish_data.pack_data_onewire(response, client, topic)
                    tx_lock.release()
                else:
                    tx_lock.release()
            else:
                logging.debug("RX data does not correspond to the last command sent, checking again the serial")

    if no_answer_pending == False:  # still no answer received, release lock
        tx_lock.release()
    print(time.time(), " End RX processing")


def main():
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")

    logging.debug("####################### Initializing mqtt broker for client #######################")
    client, topic = ini_client.initialize_client()

    logging.debug("####################### Setting serial interface #######################")
    ser = serial.Serial(port='/dev/ttyACM0', baudrate=9600)

    logging.debug("####################### Creating TX_lock #######################")
    tx_lock = threading.Lock()

    # Wait until table exists in db
    # ASSUMPTION: the script can be called before user registers in flaskapp
    engine, exists = None, False
    while not exists:
        engine, exists = check_table_database(engine)
        time.sleep(1)  # seconds

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
    #   rpi reboot

    # print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    try:  # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(2)
            logging.debug('loop')
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        # scheduler.shutdown()
        os.exit()
