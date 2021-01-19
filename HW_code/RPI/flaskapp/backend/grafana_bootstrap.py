"""Grafana bootstrap."""
import json
from config import ConfigRPI
import requests
host = ConfigRPI.SERVER_URL 
ssl_flag = ConfigRPI.SSL_FLAG #true or false in config 

def load_json(path):
    with open(path) as f:
        data_json = json.load(f)
    return data_json


def bootstrap(name, organization, email, password, channel_id):
    """
    This method is only accessed if organization not registered yet in Grafana
    :param name:
    :param organization:
    :param email:
    :param password:
    :param channel_id:
    :return:
    """
    """ POST to /control/grafana to register user"""
    # RESPONSE TO POST:
    # response.json()['status']= success/ Error when...

    url = host + '/control/grafana'
    data = {
        "email": str(email),
        "password": str(password),
        "name": str(name),
        "organization": str(organization),
        "channel_id": str(channel_id)
    }
    headers = {"Content-Type": 'application/json'}
    return requests.post(url, json=data, headers=headers, verify=ssl_flag)
