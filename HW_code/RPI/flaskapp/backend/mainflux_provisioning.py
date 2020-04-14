"""MainFlux bootstrap and provisioning."""
import requests
import urllib3

import flaskapp.backend.grafana_bootstrap as grafana
from config import ConfigRPI
from ..control import get_node_id, update_tokens_values

host = ConfigRPI.SERVER_URL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# create user account
def create_account(email, password):
    url = host + '/users'
    data = {
        "email": str(email),
        "password": str(password)
    }
    headers = {"Content-Type": 'application/json'}
    response = requests.post(url, json=data, headers=headers, verify=False)


def get_account_token(email, password):
    url = host + '/tokens'
    data = {
        "email": str(email),
        "password": str(password)
    }
    headers = {"Content-Type": 'application/json'}
    response = requests.post(url, json=data, headers=headers, verify=False)
    # print (response.text)
    token = response.json()['token']
    # print (token)
    return token


def create_thing(account_token, thing_name, thing_type):
    url = host + '/things'
    data = {
        "name": str(thing_name),
        "type": str(thing_type)
    }
    headers = {"Content-Type": 'application/json', "Authorization": str(account_token)}
    response = requests.post(url, json=data, headers=headers, verify=False)


# TODO: code repeats in the next three methods
def return_thing_id(account_token, thing_name):
    url = host + '/things'
    headers = {"Authorization": str(account_token)}
    response = requests.get(url, headers=headers, verify=False)
    # print (response.text)
    response = response.json()
    things_list = response["things"]
    for i in range(len(things_list)):
        if things_list[i]['name'] == str(thing_name):
            # print("found it")
            thing_id = things_list[i]['id']
            return thing_id

    print('thing not here')
    return 0


def return_thing_key(account_token, thing_name):
    url = host + '/things'
    headers = {"Authorization": str(account_token)}
    response = requests.get(url, headers=headers, verify=False)
    # print (response.text)
    response = response.json()
    things_list = response["things"]
    for i in range(len(things_list)):
        if things_list[i]['name'] == str(thing_name):
            # print("found it")
            thing_key = things_list[i]['key']
            return thing_key

    print('thing not here')
    return 0


def return_channel_id(account_token, channel_name):
    url = host + '/channels'
    headers = {"Authorization": str(account_token)}
    response = requests.get(url, headers=headers, verify=False)
    # print (response.text)
    response = response.json()
    channels_list = response["channels"]
    for i in range(len(channels_list)):
        if channels_list[i]['name'] == str(channel_name):
            # print("found it")
            channel_id = channels_list[i]['id']
            return channel_id

    print('channel not here')
    return 0


def create_channel(account_token, channel_name):
    url = host + '/channels'
    data = {
        "name": str(channel_name)
    }
    headers = {"Content-Type": 'application/json', "Authorization": str(account_token)}
    response = requests.post(url, json=data, headers=headers, verify=False)
    print(response.text)


def connect_to_channel(account_token, channel_id, thing_id):
    url = host + '/channels/' + str(channel_id) + '/things/' + str(thing_id)
    headers = {"Authorization": str(account_token)}
    response = requests.put(url, headers=headers, verify=False)
    # print (response.text)


def attempt_sending_message(channel_id, thing_key):
    url = host + '/http/channels/' + str(channel_id) + '/messages'
    headers = {"Content-Type": 'application/senml+json', "Authorization": str(thing_key)}
    data = [
        {
            "bn": "some-base-name:",
            "bt": 1.276020076001e+09,
            "bu": "A",
            "bver": 5,
            "n": "voltage",
            "u": "V",
            "v": 120.1
        },
        {
            "n": "current",
            "t": -5,
            "v": 1.2
        },
        {
            "n": "current",
            "t": -4,
            "v": 1.3
        }
    ]
    response = requests.post(url, json=data, headers=headers, verify=False)
    print(response.text)


def get_messages_on_channel(channel_id, thing_key):
    url = host + ':8905/channels/' + str(channel_id) + '/messages'
    headers = {"Authorization": str(thing_key)}
    response = requests.get(url, headers=headers, verify=False)
    print(response.text)


def register_node(name, organization, email, password):
    """
    Create account and register the node to mainflux and grafana
    NOTE: This method is called only ONCE when user signs up on web page
    TODO:
      - check if account already exists in MainFlux
      - if user account already exists: associate node to its account
      - Token should be stored in backend, thus things and channel created there: Use the Mainflux backend service or not
    :return: True if provisioning OK
    """
    # +++ OLD; now this method its inside flaskapp context +++
    # # Wait until table exists in db
    # # ASSUMPTION: the script can be called before user registration in flaskapp
    # engine, exists = None, False
    # while not exists:
    #     engine, exists = check_table_database(engine)
    #     time.sleep(1)  # seconds
    # # Get data from db -> no need, passing data as arguments
    # user = get_table_database(engine, 'userdata')
    # name = user.name
    # organization = user.org
    # email = user.email
    # password = user.password

    # Get node id generated by node
    node_id = get_node_id()
    node_name = 'node ' + str(node_id)

    registration_ok = False

    # ONLY for TESTING: Load tokens from txt file, so no need to connect to mainflux (user already was created)
    if True:
        try:
            create_account(email, password)
            account_token = get_account_token(email, password)

            create_thing(account_token, "node 1", "device")
            thing1_id = return_thing_id(account_token, "node 1")
            thing1_key = return_thing_key(account_token, "node 1")

            create_thing(account_token, "app", "application")
            thing2_id = return_thing_id(account_token, "app")
            thing2_key = return_thing_key(account_token, "app")
            create_channel(account_token, "comm_channel")
            channel_id = return_channel_id(account_token, "comm_channel")

            connect_to_channel(account_token, channel_id, thing1_id)
            connect_to_channel(account_token, channel_id, thing2_id)

            # Add tokens to rpi database
            update_tokens_values(account_token, thing1_id, thing1_key, channel_id)

            # Try to create Grafana account
            grafana.bootstrap(name, organization, email, password, channel_id)
            print("accounts and objects created, exporting variables")

            registration_ok = True

            import json
            dictionary = {}
            dictionary['account_token'] = account_token
            dictionary['thing1_id'] = thing1_id
            dictionary['thing1_key'] = thing1_key
            dictionary['thing2_id'] = thing2_id
            dictionary['thing2_key'] = thing2_key
            dictionary['channel_id'] = channel_id
            f = open('tokens.txt', 'w')
            f.write(json.dumps(dictionary))
            f.close()

        except:
            registration_ok = False
    else:
        dictionary = eval(open("tokens.txt").read())
        account_token = dictionary['account_token']
        thing_id = dictionary['thing1_id']
        thing_key = dictionary['thing1_key']
        channel_id = dictionary['channel_id']

        # Add tokens to rpi database
        update_tokens_values(account_token, thing_id, thing_key, channel_id)

        registration_ok = True

    return registration_ok
