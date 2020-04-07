import time

import grafana_users as grafana
import requests
import urllib3

from config import get_table_database, update_table_database, check_table_database

host = 'https://54.171.128.181'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# create user account
def create_account(email, password):
	url=host+'/users'
	data={
		"email":str(email),
		"password": str(password)
	}
	headers={"Content-Type": 'application/json'}
	response = requests.post(url, json=data, headers=headers, verify=False)
	#print (response.text)


def get_account_token(email, password):
	url=host+'/tokens'
	data={
		"email":str(email),
		"password": str(password)
	}
	headers={"Content-Type": 'application/json'}
	response = requests.post(url, json=data, headers=headers, verify=False)
	#print (response.text)
	token = response.json()['token']
	#print (token)
	return token 

def create_thing(account_token, thing_name, thing_type):
	url=host+'/things'
	data={
		"name": str(thing_name),
		"type": str(thing_type)
	}
	headers={"Content-Type": 'application/json', "Authorization": str(account_token)}
	response = requests.post(url, json=data, headers=headers, verify=False)
	#print (response.text)

def return_thing_id(account_token, thing_name):
	url=host+'/things'
	headers={"Authorization": str(account_token)}
	response = requests.get(url,headers=headers, verify=False)
	#print (response.text)
	response= response.json()
	things_list = response["things"]
	for i in range(len(things_list)):
		if things_list[i]['name'] == str(thing_name):
			#print("found it")
			thing_id = things_list[i]['id']
			return thing_id
	
	print('thing not here')
	return 0

def return_thing_key(account_token, thing_name):
	url=host+'/things'
	headers={"Authorization": str(account_token)}
	response = requests.get(url, headers=headers, verify=False)
	#print (response.text)
	response = response.json()
	things_list = response["things"]
	for i in range(len(things_list)):
		if things_list[i]['name'] == str(thing_name):
			#print("found it")
			thing_key = things_list[i]['key']
			return thing_key
		
	print('thing not here')
	return 0

def create_channel(account_token, channel_name):
	url=host+'/channels'
	data={
		"name": str(channel_name)
	}
	headers={"Content-Type": 'application/json', "Authorization": str(account_token)}
	response = requests.post(url, json=data, headers=headers, verify=False)
	print (response.text)

def return_channel_id(account_token, channel_name):
	url=host+'/channels'
	headers={"Authorization": str(account_token)}
	response = requests.get(url,headers=headers, verify=False)
	#print (response.text)
	response= response.json()
	channels_list = response["channels"]
	for i in range(len(channels_list)):
		if channels_list[i]['name'] == str(channel_name):
			#print("found it")
			channel_id = channels_list[i]['id']
			return channel_id
		
	print('channel not here')
	return 0


def connect_to_channel(account_token, channel_id, thing_id):
	url=host+'/channels/'+ str(channel_id)+ '/things/'+ str(thing_id)
	headers={"Authorization": str(account_token)}
	response = requests.put(url, headers=headers, verify=False)
	#print (response.text)

def attempt_sending_message(channel_id, thing_key):
	url=host+'/http/channels/'+ str(channel_id) + '/messages'
	headers={"Content-Type": 'application/senml+json', "Authorization": str(thing_key)}
	data = [
			{
				"bn":"some-base-name:",
				"bt":1.276020076001e+09,
				"bu":"A",
				"bver":5,
				"n":"voltage",
				"u":"V",
				"v":120.1
			}, 
			{
				"n":"current",
				"t":-5,
				"v":1.2
			},
			{
				"n":"current",
				"t":-4,
				"v":1.3
			}
			]
	response = requests.post(url, json = data,headers=headers, verify=False)
	print (response.text)

def get_messages_on_channel(channel_id, thing_key):
	url=host+':8905/channels/'+ str(channel_id) + '/messages'
	headers={"Authorization": str(thing_key)}
	response = requests.get(url, headers=headers, verify=False)
	print (response.text)


def main():
	# ASSUMPTION: the script can be called before user registration in flaskapp
	# Wait until table exists in db
	engine, exists = None, False
	while not exists:
		engine, exists = check_table_database(engine)
		time.sleep(1)  # seconds

	user = get_table_database(engine, 'userdata')
	tokens = get_table_database(engine, 'tokens')

	# Get data from db
	name = user.name
	organization = user.org
	email = user.email
	password = user.password
	node_name = 'node' + str(tokens.node_id)

	create_account(email, password)
	account_token = get_account_token(email, password)

	create_thing(account_token, node_name, "device")
	thing_id = return_thing_id(account_token, node_name)
	thing_key = return_thing_key(account_token, node_name)

	create_channel(account_token, "comm_channel")
	channel_id = return_channel_id(account_token, "comm_channel")
	connect_to_channel(account_token, channel_id, thing_id)

	grafana.bootstrap(name, organization, email, password, channel_id)
	print("accounts and objects created, exporting variables")

	# dictionary = {}
	# dictionary['account_token'] = account_token
	# dictionary['thing_id'] = thing_id
	# dictionary['thing_key'] = thing_key
	# # dictionary['thing2_id'] = thing2_id
	# # dictionary['thing2_key'] = thing2_key
	# dictionary['channel_id'] = channel_id
	# f = open('tokens.txt', 'w')
	# f.write(json.dumps(dictionary))
	# f.close()

	# Load from txt for testing, so no need to connect to mainflux
	dictionary = eval(open("./HW_code/RPI/tokens.txt").read())
	print(dictionary)
	account_token = dictionary['account_token']
	thing_id = dictionary['thing1_id']
	thing_key = dictionary['thing1_key']
	channel_id = dictionary['channel_id']

	# Add tokens to database
	update_table_database(engine, account_token, thing_id, thing_key, channel_id)


if __name__ == '__main__':
	print('Trying to create user account')
	main()

