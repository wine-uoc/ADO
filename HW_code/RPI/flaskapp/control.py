"""Database control functions."""
from flask import current_app as app
from flask_login import current_user

from .models import db, User, NodeConfig, Wifi, Tokens, Calibration_1, Calibration_2, Requires_Cal_1, Requires_Cal_2
from .utils import create_node_name, delete_entries


def delete_tables_entries():
    """Delete entries of each table in db."""
    delete_entries(Wifi.query.all())
    delete_entries(NodeConfig.query.all())
    delete_entries(Tokens.query.all())
    delete_entries(User.query.all())
    delete_entries(Calibration_1.query.all())
    delete_entries(Calibration_2.query.all())
    delete_entries(Requires_Cal_1.query.all())
    delete_entries(Requires_Cal_2.query.all())
    db.session.commit()


def update_config_values(sensor_idx, value):
    """Replace value of sensor ('sensor_idx+'1) with 'value'"""
    node_config = get_config_obj()
    new_config = node_config.get_values()
    new_config[sensor_idx] = value
    node_config.set_values(new_config)
    db.session.commit()


def update_wifi_data(ssid=None, password=None, activate=None):
    """Set new SSID and password for wifi."""
    wifi = Wifi.query.filter_by(id=current_user.email).first()
    if ssid and password:
        wifi.ssid = ssid
        wifi.set_password(password, hash_it=False)
    if activate == 1:
        wifi.activate()
    elif activate == 0:
        wifi.deactivate()
    db.session.commit()


def update_tokens_values(account_token, thing_id, thing_key, channel_id):
    """Add values to table.'"""
    tokens = get_tokens_obj()
    tokens.account_token = account_token
    tokens.thing_id = thing_id
    tokens.thing_key = thing_key
    tokens.channel_id = channel_id
    db.session.commit()


def get_config_obj():
    """Query to db to get current node config. object."""
    return NodeConfig.query.filter_by(id=current_user.email).first()


def get_wifi_obj():
    """Query to db to get current wifi status."""
    return Wifi.query.filter_by(id=current_user.email).first()


def get_tokens_obj():
    """Query to db to get current tokens table obj."""
    return Tokens.query.filter_by(id=current_user.email).first()


def get_node_id():
    """Query to db to get the unique node id."""
    return Tokens.query.filter_by(id=current_user.email).first().node_id

def get_user_org():
    """Query to db to get the user organization name."""
    existing_user = User.query.first()
    if existing_user is None:
        return 0
    else:
        return existing_user.org


def validate_user(email, password):
    """Validate user pass against db."""
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password=password, hash_it=app.config['HASH_USER_PASSWORD']):
        return user
    else:
        return None


def sign_up_database(name, org, email, password):
    """
    Given user input in sign up form, initializes all tables of the database
    NOTE: WiFi password is currently stored in plain text (needed for Raspbian)

    :param name: user input in sign form
    :param org:
    :param email:
    :param password:
    :return: error msg, object of class User if new user else None
    """
    # Check if user does not exists and the node has not been registered yet to another account
    # existing_user = User.query.filter_by(email=email).first()
    existing_user = User.query.first()
    if existing_user is None:
        user = User(name=name, org=org, email=email)    # userdata table
        user.set_password(password, hash_it=app.config['HASH_USER_PASSWORD'])

        node_config = NodeConfig(id=email)              # nodeconfig table associated to email
        node_config.set_values([0] * app.config['MAX_NUM_SENSORS_IN_NODE'])   # All sampling rates to 0 (disabled)

        wifi = Wifi(id=email, ssid='')                  # wifidata table associated to email
        wifi.set_password(password, hash_it=False)      # Store-hashed option off
        wifi.deactivate()  # Use ethernet by default

        tokens = Tokens(id=email, node_id=create_node_name())   # tokens table associated to email

        calibration1 = Calibration_1(id=email)              # calibration table associated to email
        calibration1.set_values([0] * app.config['MAX_NUM_SENSORS_IN_NODE'])   # All 1-pt calibration values set to 0 (disabled)
        
        calibration2 = Calibration_2(id=email)              # calibration table associated to email
        calibration2.set_values([0] * app.config['MAX_NUM_SENSORS_IN_NODE'])   # All 2-pt calibration values set to 0 (disabled)
        
        #loads flags from config file
        #flag = 1 for the sensors that require calibration before using
        req_cal_1 = Requires_Cal_1(id=email)              # flag table associated to email
        req_cal_1.set_values(app.config['REQ_CAL_1'])   # All flag values set to 0 (disabled calibration)
        
        req_cal_2 = Requires_Cal_2(id=email)              # flag table associated to email
        req_cal_2.set_values(app.config['REQ_CAL_2'])   # All flag values set to 0 (disabled calibration)
        
        db.session.add(user)                            # Commit changes
        db.session.add(node_config)
        db.session.add(wifi)
        db.session.add(tokens)
        db.session.add(calibration1)
        db.session.add(calibration2)
        db.session.add(req_cal_1)
        db.session.add(req_cal_2)
        db.session.commit()
        return False, user, tokens.node_id
    else:
        # already exists an account associated to this node
        if existing_user.email == email:
            # email taken
            error_msg = 'This node is already registered with that email address. Log in to configure it.'
            return error_msg, None, None
        else:
            # node registered to other account
            error_msg = 'This node is linked to: {}! To link it to another account, log in and reset the ' \
                        'node to factory settings.'.format(existing_user.email)
            return error_msg, None, None
