"""Config class."""
import os


class ConfigFlaskApp:
    """
    Set Flask configuration vars.
    https://flask.palletsprojects.com/en/1.1.x/config/
    """

    # General Config
    TESTING = False
    DEBUG = False
    # TODO: each node should have a different secret, random create it during deployment and load as env variable
    SECRET_KEY = b'Sl:\x9d\xcc}{\x13\x19\xabuQ\x87\xa7\x91\xa5'     # os.urandom(16)
    SESSION_COOKIE_NAME = str(os.urandom(6))
    PERMANENT_SESSION_LIFETIME = 10*60*60    # seconds

    # ENV Config
    FLASK_ENV = 'production'    # development (to compile new CSS and JS)

    # DB Config
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database/db.sqlite'
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Assets Config
    LESS_BIN = '/usr/local/bin/lessc'
    ASSETS_DEBUG = False
    ASSETS_AUTO_BUILD = True

    # Password storage
    HASH_USER_PASSWORD = True

    # Sensors Config
    DEFAULT_SR = 30
    MAX_NUM_SENSORS_IN_NODE = 10
    REQ_CAL_1 = [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
    REQ_CAL_2 = [0, 0, 1, 0, 0, 0, 0, 0, 0, 0] #pH sensor requiers 2pt cal


class ConfigRPI:
    """
    Set RPI configuration vars.
    """
    # Backend server Mainflux
    SERVER_URL = 'http://localhost'     # 'https://54.171.128.181'
    SHORT_SERVER_URL = 'localhost'
    SERVER_PORT_MQTT = 1883
    print(' Currently configured to connect to localhost MainFlux !!! ')
    # SERVER_URL = 'https://54.171.128.181'
    # SHORT_SERVER_URL = SERVER_URL[8:]

    # Local database
    DATABASE_URI = 'sqlite:///flaskapp/database/db.sqlite'

    # Arduino
    # Mapping sensor type <-> sensor position in db
    SENSOR_TYPES = ['onewire', 'i2c', 'analog', 'analog', 'analog', 'analog', 'digital', 'analog', 'digital', 'analog']
    SENSOR_PINS = ['0', '11,12', '0', '0', '1', '2', '1,2', '3,4', '3', '5']
    SENSOR_PARAMS = [[0], ['0xHEX'], [0, 'cal', 'cal'], [0], [1], [2], [1, 2], [3, 4], [3], [5]]
    # SENSOR_MAGNITUDES = ['Temperature', 'Atmospheric Temperature', 'Light', 'pH', 'Turbidity', 'Oxygen Dissolution',
    #                      'Flow', 'Conductivity', 'Water Level', 'Air CO2']
    # SENSOR_UNITS = ['Cel', 'Cel', 'lux', 'pH', 'NTU', 'mg/L', 'L/min', 'mS/cm', 'ppm', 'ppm']
    SENSOR_MAGNITUDES = ['Temperature', 'Light', 'pH', 'Turbidity', 'Flow', 'Conductivity', 'AtmosphericTemp',
                         'Oxygen', 'WaterLevel', 'AirCO2']
    SENSOR_UNITS = ['Cel', 'lux', 'pH', 'NTU', 'L/min', 'mS/cm', 'Cel', 'mg/L', 'ppm', 'ppm']
    # parameters list corresponding to each sensor, to send to A0; should be list os lists (bc createcmd requires list)
    # note: assuming that S1A and S1B are connected to different pins D4 D0 (arqui doc; DS18B20)
    # BUT in A0 code: SplitCommand gets only first parameter of param_list, myArray[i] = obtainArray(fullArray, ',', 0);
    # note: how to select in python the two I2C sensors? request hex addresses to A0(scan)? (no code in A0)
    # TODO: modify with only sensors that will used for the pilot deployment (this should match the ones in flaskApp)

    # Control messages
    # time period to check on db and send control messages in channel
    PERIODIC_CONTROL_SECONDS = 2
