"""Database models."""
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash, safe_str_cmp

from . import db


class User(UserMixin, db.Model):
    """User account model."""
    __tablename__ = 'userdata'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer,
                   primary_key=True)
    name = db.Column(db.String(100),
                     nullable=False,
                     unique=False)
    org = db.Column(db.String(100),
                    nullable=False,
                    unique=False)
    email = db.Column(db.String(40),
                      nullable=False,
                      unique=True)
    password = db.Column(db.String(200),
                         nullable=False,
                         unique=False)

    def set_password(self, password, hash_it):
        """Create hashed (or not) password."""
        if hash_it:
            password = generate_password_hash(password, method='sha256')
        self.password = password

    def check_password(self, password, hash_it):
        """Check hashed (or not) password."""
        if hash_it:
            return check_password_hash(self.password, password)
        else:
            return safe_str_cmp(self.password, password)

    def __repr__(self):
        return '<User {}>'.format(self.name)


class NodeConfig(UserMixin, db.Model):
    """Node state model.
    - Each column represents a sensor in the node
        if 0: sensor will not be used
        if > 0: sensor will be used with sampling rate = Integer
    """
    __tablename__ = 'nodeconfig'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.String(40), primary_key=True)     # Associated to email (unique)
    s01 = db.Column(db.Integer, nullable=False, unique=False)
    s02 = db.Column(db.Integer, nullable=False, unique=False)
    s03 = db.Column(db.Integer, nullable=False, unique=False)
    s04 = db.Column(db.Integer, nullable=False, unique=False)
    s05 = db.Column(db.Integer, nullable=False, unique=False)
    s06 = db.Column(db.Integer, nullable=False, unique=False)
    s07 = db.Column(db.Integer, nullable=False, unique=False)
    s08 = db.Column(db.Integer, nullable=False, unique=False)
    s09 = db.Column(db.Integer, nullable=False, unique=False)
    s10 = db.Column(db.Integer, nullable=False, unique=False)

    def set_values(self, a_list):
        """Set values."""
        self.s01, self.s02, self.s03, self.s04, self.s05, self.s06, self.s07, self.s08, self.s09, self.s10 = a_list

    def get_values(self):
        """Get values as a list."""
        return [self.s01, self.s02, self.s03, self.s04, self.s05, self.s06, self.s07, self.s08, self.s09, self.s10]


class Wifi(UserMixin, db.Model):
    """WiFi table model.
    active: defines use of SSId stored to connect to Inet {0: if Ethernet 1: if Wifi}
    """
    __tablename__ = 'wifidata'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.String(40), primary_key=True)     # Associated to email (unique)
    ssid = db.Column(db.String(100),
                     nullable=False,
                     unique=False)          # False bc another user account can use same network
    password = db.Column(db.String(200),
                         nullable=True,
                         unique=False)     # Handle networks w/o pw
    active = db.Column(db.Integer,
                       nullable=False,
                       unique=False)

    def set_password(self, password, hash_it=False):
        """Create hashed (or not) password."""
        if hash_it:
            password = generate_password_hash(password, method='sha256')
        self.password = password

    def activate(self):
        """Set active state"""
        self.active = 1

    def deactivate(self):
        """Set deactive state"""
        self.active = 0


class Tokens(UserMixin, db.Model):
    """Tokens table model."""
    __tablename__ = 'tokens'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.String(40), primary_key=True)     # Associated to email (unique)
    node_id = db.Column(db.Integer,                     # Stores unique node id
                        nullable=False,
                        unique=True)
    account_token = db.Column(db.String(200),
                              nullable=True,            # Nullabes bc info comes from MainFlux
                              unique=True)
    thing_id = db.Column(db.String(100),
                         nullable=True,
                         unique=True)
    thing_key = db.Column(db.String(100),
                          nullable=True,
                          unique=True)
    channel_id = db.Column(db.String(100),
                           nullable=True,
                           unique=True)

    # import json
    # with open('HW_code/RPI/tokens.txt') as f:
    #     json_tokens = json.load(f)
    # node_token = json_tokens['account_token']
