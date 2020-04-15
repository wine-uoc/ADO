"""MainFlux bootstrap and provisioning."""
import requests
import urllib3

import flaskapp.backend.grafana_bootstrap as grafana
from config import ConfigRPI
from ..control import update_tokens_values

host = ConfigRPI.SERVER_URL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def create_account(email, password):
    """ POST to /users to register user"""
    # RESPONSE TO POST:
    # print(response.reason)
    # print(response.status_code)
    # print(response.ok)
    # print(response.text)
    # if user exists:
    #   Conflict
    #   409
    #   False
    #   {"error":"Save user to DB failed"}
    # if user does not exit:
    #   Created
    #   201
    #   True

    url = host + '/users'
    data = {
        "email": str(email),
        "password": str(password)
    }
    headers = {"Content-Type": 'application/json'}
    return requests.post(url, json=data, headers=headers, verify=False)


def get_account_token(email, password):
    """ POST to /tokens to get token or create token of user"""
    url = host + '/tokens'
    data = {
        "email": str(email),
        "password": str(password)
    }
    headers = {"Content-Type": 'application/json'}
    # response = requests.post(url, json=data, headers=headers, verify=False)
    # token = response.json()['token']
    return requests.post(url, json=data, headers=headers, verify=False)


def create_thing(account_token, thing_name, thing_type):
    url = host + '/things'
    data = {
        "name": str(thing_name),
        "type": str(thing_type)
    }
    headers = {"Content-Type": 'application/json', "Authorization": str(account_token)}
    return requests.post(url, json=data, headers=headers, verify=False)


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
    return requests.post(url, json=data, headers=headers, verify=False)


def connect_to_channel(account_token, channel_id, thing_id):
    url = host + '/channels/' + str(channel_id) + '/things/' + str(thing_id)
    headers = {"Authorization": str(account_token)}
    return requests.put(url, headers=headers, verify=False)


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


def register_node_backend(name, organization, email, password, node_id):
    """
    Node registration to backend and user account creation.
    Assumption: node is not registered to the email provided
    Check if account exist
        if yes: log in, get token, register node (create thing), get channel
        if no: create account, get token, register node (create thing), create app thing, get channel, bootstrap grafana
    NOTE: This method is called only ONCE when user signs up on web page
    TODO:
      - Token should be stored in backend, thus things and channel created there (Mainflux boostrap service)
      - Currently, token is stored in db in case rpi restarts (needed to connect to channel)
    :return: None if provisioning OK else error message
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

    error_msg = False
    node_name = str(node_id) + '_device'
    node_app_name = str(node_id) + '_app'
    channel_name = 'comm_channel'  # unique for each organization

    # Triple check: account exists, email and pw OK
    response_c1 = create_account(email, password)
    response_c2 = get_account_token(email, password)
    # new account -> c1 true c2 true
    # email ok and pw ok + account exists -> c1 false, c2 true
    # email ok and pw wrong + account exists -> c1 false, c2 false

    if not response_c1.ok and response_c2.ok:
        # print('Backend account exists, registering node.')
        # token exists, thus account too
        token = get_account_token(email, password).json()['token']

        # register node to account (create thing)
        _ = create_thing(token, node_name, "device")
        thing_id = return_thing_id(token, node_name)
        thing_key = return_thing_key(token, node_name)

        # connect to the existing channel
        channel_id = return_channel_id(token, channel_name)
        _ = connect_to_channel(token, channel_id, thing_id)

        # store backend credentials to rpi database
        update_tokens_values(token, thing_id, thing_key, channel_id)

    if response_c1.ok and response_c2.ok:
        # print('Backend account DOES NOT exist, creating account, channel, registering node.')
        # token does not exist, thus account neither > create account first
        _ = create_account(email, password)

        # get account token
        token = get_account_token(email, password).json()['token']

        # create and register node to account (create thing)
        _ = create_thing(token, node_name, 'device')
        thing_id = return_thing_id(token, node_name)
        thing_key = return_thing_key(token, node_name)

        # create app
        # TODO: why app?
        _ = create_thing(token, node_app_name, 'application')
        thing2_id = return_thing_id(token, node_app_name)
        thing2_key = return_thing_key(token, node_app_name)

        # create and connect to new channel
        _ = create_channel(token, channel_name)
        channel_id = return_channel_id(token, channel_name)
        response = connect_to_channel(token, channel_id, thing_id)

        # boostrap grafana
        if response.ok:
            grafana.bootstrap(name, organization, email, password, channel_id)

        # store backend credentials to rpi database
        update_tokens_values(token, thing_id, thing_key, channel_id)

    if not response_c1.ok and not response_c2.ok:
        # Account exists in ADO, but password does not match.
        error_msg = 'Incorrect password, cannot register the node to that account.'

    return error_msg