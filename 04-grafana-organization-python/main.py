from grafana_api.grafana_face import GrafanaFace
import json

import requests

#login to the grafana api through the library
grafana_api = GrafanaFace(auth=('admin','admin'), port=3000)


def _organization_check(organization):
	orgs = grafana_api.organizations.list_organization()
	for i in range(len(orgs)):
		if str(organization) in orgs[i]['name']:
			print ("organization already created")
			return 1
	return 0

def _create_organization(organization):
	url='http://admin:admin@localhost:3000/api/orgs'
	data={
		"name":organization,
	}
	headers={"Content-Type": 'application/json'}
	response = requests.post(url, json=data,headers=headers)
	print (response.text)


def _get_current_organization():
	url='http://admin:admin@localhost:3000/api/org/'
	response = requests.get(url)
	organization_details = response.json()
	print(organization_details["name"])
	return str(organization_details["name"])

def _get_organization_id(organization_name):
	orgs = grafana_api.organizations.list_organization()
	print (orgs)
	for i in range(len(orgs)):
		if str(organization_name) in orgs[i]['name']:
			return orgs[i]['id']
	return 0 #there is no organization ID zero in grafana


def _change_current_organization_to(new_organization):
	org_id = _get_organization_id(new_organization)
	print ('organization id ', org_id)
	url='http://admin:admin@localhost:3000/api/user/using/' + str(org_id)
	headers={"Content-Type": 'application/json'}
	response = requests.post(url, headers=headers)
	print (response.text)
	print("current organization is now ", new_organization)

def _get_all_users(): #returns all users of the selected organization
	url='http://admin:admin@localhost:3000/api/org/users'
	response = requests.get(url)
	user_list = response.json()
	for i in range(len(user_list)):
		print(user_list[i]['login'])
	return user_list

def _user_check(user_org, user):
	#switch to user_org
	_change_current_organization_to(user_org)
	user_list = _get_all_users()
	for i in range(len(user_list)):
		if user_list[i]['login'] == user:
			return user_list[i]['userId']
	return 0 #user not found


def _create_user(user): #creates it and does not assign it to anything
	print("****************************************")
	url='http://admin:admin@localhost:3000/api/admin/users'
	data={
		"name": user["name"],
		"email": user["email"],
		"login":  user["login"],
		"password": user["password"],
	}
	headers={"Content-Type": 'application/json'}
	response = requests.post(url, json=data,headers=headers)
	print (response.text)

def _assign_user_to_organization(organization, user, role):
	org_id=_get_organization_id(organization)
	url='http://admin:admin@localhost:3000/api/orgs/'+ str(org_id)+ '/users'
	data={
		"loginOrEmail": user["login"],
		"role": str(role),
		
	}
	headers={"Content-Type": 'application/json'}
	response = requests.post(url, json=data,headers=headers)
	print (response.text)



def main():
	organization_list = ['UOC', 'UPC', 'testing']

	for org in organization_list:
		if _organization_check(org) == 0: #organization not found in grafana
			print ("organization not found in grafana, creating it ...")
			_create_organization(org)

	current_organization = 'UOC'
	
	if (_get_current_organization() != current_organization):
		print ("need to switch organization to ", current_organization)
		_change_current_organization_to(current_organization)
	else:
		print ("current organization is already selected")


	#current_user = 'test2' #this should be complete info with email, name, login and password
	user = {}
	user["name"] = "PythonUser"
	user["email"] = "python@test.com"
	user["login"] = "python_login"
	user["password"] = "password"
	if (_user_check(current_organization, user["login"]) == 0):#check if user exists, if not create it
		print ("user not found in this organization, it needs to be created and assigned")
		_create_user(user)
		_assign_user_to_organization(current_organization, user, "Viewer")
	else:
		print ("username ", user["login"], " already exists in this organization")



if __name__ == '__main__':
    print('Managing organizations in Grafana')
    main()


