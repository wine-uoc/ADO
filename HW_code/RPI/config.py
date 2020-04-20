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
    # TODO: each node should have a different secret, read from db if exists else random create it and store it in db
    SECRET_KEY = b'Sl:\x9d\xcc}{\x13\x19\xabuQ\x87\xa7\x91\xa5'     # os.urandom(16)
    SESSION_COOKIE_NAME = str(os.urandom(6))
    PERMANENT_SESSION_LIFETIME = 60*10    # seconds

    # ENV Config
    FLASK_ENV = 'production'

    # DB Config
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database/db.sqlite'
    SQLALCHEMY_ECHO = False
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
    SENSOR_TYPES = ['onewire', 'i2c', 'i2c', 'analog', 'analog', 'analog', 'digital', 'analog', 'digital', 'analog']
    SENSOR_PINS = ['0,4', '11,12', '11,12', '0', '1', '2', '1,2', '3,4', '3', '5']
    SENSOR_PARAMS = [[0, 4], ['0xHEX'], ['0xHEX'], [0], [1], [2], [1, 2], [3, 4], [3], [5]]
    SENSOR_MAGNITUDES = ['Temperature', 'Atmospheric Temperature', 'Light', 'pH', 'Turbidity', 'Oxygen Dissolution',
                         'Flow', 'Conductivity', 'Water Level', 'Air CO2']
    SENSOR_UNITS = ['Cel', 'Cel', 'lux', 'pH', 'NTU', 'mg/L', 'L/min', 'mS/cm', 'ppm', 'ppm']
    # parameters list corresponding to each sensor, to send to A0; should be list os lists (bc createcmd requires list)
    # note: assuming that S1A and S1B are connected to different pins D4 D0 (arqui doc; DS18B20)
    # BUT in A0 code: SplitCommand gets only first parameter of param_list, myArray[i] = obtainArray(fullArray, ',', 0);
    # note: how to select in python the two I2C sensors? request hex addresses to A0(scan)? (no code in A0)
    # TODO: define I2C addresses for S2 and S3

    # Control messages
    PERIODIC_CONTROL_SECONDS = 10
