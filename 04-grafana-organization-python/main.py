from grafana_api.grafana_face import GrafanaFace
import json

import requests


def createUser():
    url='http://admin:wine4ever@localhost:3000/api/admin/users'
    data='''{
      "name":"Xavi",
      "email":"xvilajosana@uoc.edu",
      "login":"xvilajosana",
      "password":"patata"
    }'''
    headers={"Content-Type": 'application/json'}
    response = requests.post(url, data=data,headers=headers)
    print (response.text)



#login to the grafana api through the library

#grafana_api = GrafanaFace(auth='eyJrIjoiWHYyYUh2MWNrT1E0RjU3NHhUcjFzSUdwSmJ5eVpwY2siLCJuIjoiYWRtaW5rZXkiLCJpZCI6MX0=', port=3000)
grafana_api = GrafanaFace(auth=('admin','wine4ever'), port=3000)

#grafana_api.admin.delete_user('xvilajosana')

#user['name'] = "Xavi Vilajosana"
#user['email'] = "xvilajosana@uoc.edu"
#user['login'] = "xvilajosana"
#user['password'] = "patata"
#user['role'] = "Admin"

#print(user)
#print(json.dumps(user))

#id = grafana_api.admin.create_user(str(json.dumps(user)))
#id = grafana_api.admin.create_user(user)

#us=grafana_api.users.get_user(id)

#print(us)
#create an organization
organizationnew = {}
organizationnew['name'] = "UOC5"

orgs = grafana_api.organizations.list_organization()
print(orgs)

idorg= grafana_api.organization.create_organization(organizationnew)
orgs = grafana_api.organizations.list_organization()
print(orgs)
print(idorg)

if (idorg['message'] in 'Organization created'):
    print('deleting org')
    grafana_api.organizations.delete_organization(idorg['orgId'])

orgs = grafana_api.organizations.list_organization()
print(orgs)


#add user to organization
