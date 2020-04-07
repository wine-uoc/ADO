"""Flask config class."""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker


class Config:
    """
    Set Flask configuration vars.
    https://flask.palletsprojects.com/en/1.1.x/config/
    """

    # General Config
    TESTING = False
    DEBUG = False
    SECRET_KEY = '\xfd{H\_5#y2LF4Q8z\n\xec]/\xfd{H'
    SESSION_COOKIE_NAME = 'my_cookie'

    # ENV Config
    FLASK_ENV = 'development'

    # DB Config
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database/db.sqlite'
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Assets Config
    LESS_BIN = '/usr/local/bin/lessc'
    ASSETS_DEBUG = False
    ASSETS_AUTO_BUILD = True

    # Sensors Config
    DEFAULT_SR = 30
    MAX_NUM_SENSORS_IN_NODE = 10


class ConfigRPI:

    DATABASE_URI = 'sqlite:///HW_code/RPI/flaskapp/database/db.sqlite'

    # Mapping sensor_type <-> sensor position in db
    SENSOR_TYPES = ['onewire', 'i2c', 'i2c', 'analog', 'analog', 'analog', 'digital', 'analog', 'digital', 'analog']
    # note: ambiguous documentation, assuming sensor 11 is digital connected to D3
    SENSOR_PINS = ['0,4', '11,12', '11,12', '0', '1', '2', '1,2', '3,4', '3', '5']
    SENSOR_PARAMS = [[0, 4], ['0xHEX'], ['0xHEX'], [0], [1], [2], [1, 2], [3, 4], [3], [5]]
    # parameters list corresponding to each sensor, to send to A0; should be list os lists (bc createcmd requires list)
    # note: assuming that S1A and S1B are connected to different pins D4 D0 (arqui doc; DS18B20)
    # BUT in A0 code: SplitCommand gets only first parameter of param_list, myArray[i] = obtainArray(fullArray, ',', 0);
    # note 2: how to select in python the two I2C sensors? request hex addresses to A0(scan)? (no code in A0)
    # TODO: define I2C addresses for S2 and S3

    SENSOR_MAGNITUDES = ['Temperature', 'Atmospheric Temperature', 'Light', 'pH', 'Turbidity', 'Oxygen Dissolution',
                         'Flow', 'Conductivity', 'Water Level', 'Air CO2']
    SENSOR_UNITS = ['Cel', 'Cel', 'lux', 'pH', 'NTU', 'mg/L', 'L/min', 'mS/cm', 'ppm', 'ppm']


def check_table_database(engine=None):
    if engine:
        exists = engine.dialect.has_table(engine.connect(), "userdata")
    else:
        engine = create_engine(ConfigRPI.DATABASE_URI, echo=False)  # print(engine.table_names())
        exists = engine.dialect.has_table(engine.connect(), "userdata")
    return engine, exists


def get_table_database(engine, table_name):
    if not engine:
        engine = create_engine(ConfigRPI.DATABASE_URI, echo=False)

    metadata = MetaData(bind=engine)
    metadata.reflect()  # Reflection
    Session = sessionmaker(bind=engine)     # Connection to db
    session = Session()
    table = metadata.tables[table_name]
    query = session.query(table).first()    # Get table (read-only!)
    session.close()
    # engine.dispose()
    return query


def update_table_database(engine, account_token, thing_id, thing_key, channel_id):
    if not engine:
        engine = create_engine(ConfigRPI.DATABASE_URI, echo=False)  # print(engine.table_names())

    # Ask SQLAlchemy to reflect the tables and
    # create the corresponding ORM classes:
    Base = automap_base()
    Base.prepare(engine, reflect=True)

    # This is the ORM class we are interested in:
    table = Base.classes.tokens

    # Create the session, query, update and commit:
    Session = sessionmaker(bind=engine)
    session = Session()
    table_row = session.query(table).first()
    table_row.account_token = account_token
    table_row.thing_id = thing_id
    table_row.thing_key = thing_key
    table_row.channel_id = channel_id
    session.commit()
    session.close()
