from grafana_api.grafana_face import GrafanaFace
import json
import requests
#login to the grafana api through the library
grafana_api = GrafanaFace(auth=('admin','admin'), host= '54.171.128.181', port=3001)
host= 'http://admin:admin@54.171.128.181:3001'
# ORGANIZATIONS 
def _organization_check(organization): #checks if org exists or not in order to create it
	orgs = grafana_api.organizations.list_organization()
	for i in range(len(orgs)):
		if str(organization) in orgs[i]['name']:
			print ("organization already created")
			return 1
	return 0

def _create_organization(organization):
	url=host + '/api/orgs'
	data={
		"name":organization,
	}
	headers={"Content-Type": 'application/json'}
	response = requests.post(url, json=data,headers=headers)
	print (response.text)

def _get_current_organization():
	url=host + '/api/org/'
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
	url=host + '/api/user/using/' + str(org_id)
	headers={"Content-Type": 'application/json'}
	response = requests.post(url, headers=headers)
	print (response.text)
	print("current organization is now ", new_organization)

def _delete_organization(org_name):
	org_id = _get_organization_id(org_name)
	if org_id != 0:
		print ("deleting organization..", org_name)
		url= host + '/api/orgs/' + str(org_id)
		headers={"Content-Type": 'application/json'}
		response = requests.delete(url, headers=headers)
		print (response.text)
	else:
		print("organization does not exist")


# USERS 

def _get_all_users(): #returns all users of the selected organization
	url=host + '/api/org/users'
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
	url=host + '/api/admin/users'
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
	url=host + '/api/orgs/'+ str(org_id)+ '/users'
	data={
		"loginOrEmail": user["login"],
		"role": str(role),
		
	}
	headers={"Content-Type": 'application/json'}
	response = requests.post(url, json=data,headers=headers)
	print (response.text)

def _get_global_user_id(user_login): #without switching to org
	url=host + '/api/users/lookup?loginOrEmail=' + str(user_login)
	headers={"Content-Type": 'application/json'}
	response = requests.get(url, headers=headers)
	print (response.text)
	user_data = response.json()
	if 'id' not in user_data: #user does not exists
		print("no such user")
		return 0
	else:
		print(user_data['id'])
		return user_data['id']


def _delete_user(user_login):
	print ("deleting user .. ", user_login)
	user_id = _get_global_user_id(user_login)
	if user_id != 0:
		url = host + '/api/admin/users/' + str(user_id)
		headers={"Content-Type": 'application/json'}
		response = requests.delete(url, headers=headers)
		print (response.text)

def _remove_user_from_org(user_login):
	print ("removing user from current organization .. ", user_login)
	user_id = _get_global_user_id(user_login)
	if user_id != 0:
		url = host + '/api/org/users/' + str(user_id)
		headers={"Content-Type": 'application/json'}
		response = requests.delete(url, headers=headers)
		print (response.text)

# DATASOURCES
def _create_datasource(name, database, admin_name, admin_pass):
	url=host + '/api/datasources'
	data={
		"name":name,
		"type":"influxdb",
		"url":"http://influxdb:8086",
		"access":"proxy", #vs direct/proxy
		"password": "mainflux",#admin_pass,
		"user": "mainflux",#admin_name,
		"database": database,
		"httpMode": "GET"  #very important field!!!

	}
	headers={"Content-Type": 'application/json'}
	response = requests.post(url, json=data,headers=headers)
	print (response.text)


def _delete_datasource(datasource_name):
	url=host + "/api/datasources/name/" + str(datasource_name)
	headers={"Content-Type": 'application/json'}
	response = requests.delete(url, headers=headers)
	print (response.text)

# DASHBOARDS

def _create_dashboard(name):
	url=host + "/api/dashboards/db"
	headers={"Content-Type": 'application/json'}
	data = {
		"dashboard": {
			"id": None, #for new dashboard
			"uid": None,
			"title": name,
			"tags": [ "templated" ],
			"timezone": "browser",
			"schemaVersion": 16,
			"version": 0,
		},
		"folderId": 0,
		"overwrite": False #new dashboard
		}
	response = requests.post(url, json=data,headers=headers)
	print (response.text)

def _update_dashboard(name, id, datasource_name, measurement1, parameter1, measurement2, parameter2, measurement3, parameter3):
	#future versions: add time intervals too
	url=host + "/api/dashboards/db"
	headers={"Content-Type": 'application/json'}
	data = {
	  "dashboard": {
	    "id": id,
	    "title": name,
	    "panels": [
	    {
	          "aliasColors": {},
	          "bars": False,
	          "dashLength": 10,
	          "dashes": False,
	          "datasource": datasource_name,
	          "fill": 1,
	          "fillGradient": 0,
	          "gridPos": {
	            "h": 8,
	            "w": 12,
	            "x": 0,
	            "y": 0
	          },
	          "id": 6,
	          "legend": {
	            "avg": False,
	            "current": False,
	            "max": False,
	            "min": False,
	            "show": True,
	            "total": False,
	            "values": False
	          },
	          "lines": True,
	          "linewidth": 1,
	          "nullPointMode": "null",
	          "options": {
	            "dataLinks": []
	          },
	          "percentage": False,
	          "pointradius": 2,
	          "points": False,
	          "renderer": "flot",
	          "seriesOverrides": [],
	          "spaceLength": 10,
	          "stack": False,
	          "steppedLine": False,
	          "targets": [
	            {
	              "groupBy": [],
	              "measurement": measurement1,
	              "orderByTime": "ASC",
	              "policy": "default",
	              "refId": "A",
	              "resultFormat": "time_series",
	              "select": [
	                [
	                  {
	                    "params": [
	                      "value"
	                    ],
	                    "type": "field"
	                  }
	                ]
	              ],
	              "tags": [
	               {
	                 "key": "name",
	                 "operator": "=",
	                 "value": parameter1
	               }
	              ]
	            }
	          ],
	          "thresholds": [],
	          "timeFrom": None,
	          "timeRegions": [],
	          "timeShift": None,
	          "title": str(measurement1)+ " "+ str(parameter1) ,
	          "tooltip": {
	            "shared": True,
	            "sort": 0,
	            "value_type": "individual"
	          },
	          "type": "graph",
	          "xaxis": {
	            "buckets": None,
	            "mode": "time",
	            "name": None,
	            "show": True,
	            "values": []
	          },
	          "yaxes": [
	            {
	              "format": "short",
	              "label": None,
	              "logBase": 1,
	              "max": None,
	              "min": None,
	              "show": True
	            },
	            {
	              "format": "short",
	              "label": None,
	              "logBase": 1,
	              "max": None,
	              "min": None,
	              "show": True
	            }
	          ],
	          "yaxis": {
	            "align": False,
	            "alignLevel": None
	          }
	        },
	        {
	          "aliasColors": {},
	          "bars": False,
	          "dashLength": 10,
	          "dashes": False,
	          "datasource": datasource_name,
	          "fill": 1,
	          "fillGradient": 0,
	          "gridPos": {
	            "h": 8,
	            "w": 12,
	            "x": 0,
	            "y": 8
	          },
	          "id": 4,
	          "legend": {
	            "avg": False,
	            "current": False,
	            "max": False,
	            "min": False,
	            "show": True,
	            "total": False,
	            "values": False
	          },
	          "lines": True,
	          "linewidth": 1,
	          "nullPointMode": "null",
	          "options": {
	            "dataLinks": []
	          },
	          "percentage": False,
	          "pointradius": 2,
	          "points": False,
	          "renderer": "flot",
	          "seriesOverrides": [],
	          "spaceLength": 10,
	          "stack": False,
	          "steppedLine": False,
	          "targets": [
	            {
	              "groupBy": [],
	              "measurement": measurement2,
	              "orderByTime": "ASC",
	              "policy": "default",
	              "refId": "A",
	              "resultFormat": "time_series",
	              "select": [
	                [
	                  {
	                    "params": [
	                      "value"
	                    ],
	                    "type": "field"
	                  }
	                ]
	              ],
	              "tags": [
	               {
	                 "key": "name",
	                 "operator": "=",
	                 "value": parameter2
	               }
	              ]
	            }
	          ],
	          "thresholds": [],
	          "timeFrom": None,
	          "timeRegions": [],
	          "timeShift": None,
	          "title":  str(measurement2)+ " "+ str(parameter2),
	          "tooltip": {
	            "shared": True,
	            "sort": 0,
	            "value_type": "individual"
	          },
	          "type": "graph",
	          "xaxis": {
	            "buckets": None,
	            "mode": "time",
	            "name": None,
	            "show": True,
	            "values": []
	          },
	          "yaxes": [
	            {
	              "format": "short",
	              "label": None,
	              "logBase": 1,
	              "max": None,
	              "min": None,
	              "show": True
	            },
	            {
	              "format": "short",
	              "label": None,
	              "logBase": 1,
	              "max": None,
	              "min": None,
	              "show": True
	            }
	          ],
	          "yaxis": {
	            "align": False,
	            "alignLevel": None
	          }
	        },	    

	      {
	        "aliasColors": {},
	        "bars": False,
	        "dashLength": 10,
	        "dashes": False,
	        "datasource": datasource_name,
	        "fill": 1,
	        "fillGradient": 0,
	        "gridPos": {
	          "h": 9,
	          "w": 12,
	          "x": 0,
	          "y": 0
	        },
	        "id": 2,
	        "legend": {
	          "avg": False,
	          "current": False,
	          "max": False,
	          "min": False,
	          "show": True,
	          "total": False,
	          "values": False
	        },
	        "lines": True,
	        "linewidth": 1,
	        "nullPointMode": "null",
	        "options": {
	          "dataLinks": []
	        },
	        "percentage": False,
	        "pointradius": 2,
	        "points": False,
	        "renderer": "flot",
	        "seriesOverrides": [],
	        "spaceLength": 10,
	        "stack": False,
	        "steppedLine": False,
	        "targets": [
	          {
	            "groupBy": [],
	            "measurement": measurement3,
	            "orderByTime": "ASC",
	            "policy": "default",
	            "refId": "A",
	            "resultFormat": "time_series",
	            "select": [
	              [
	                {
	                  "params": [
	                    "value"
	                  ],
	                  "type": "field"
	                }
	              ]
	            ],
	            "tags": [
	             {
	                 "key": "name",
	                 "operator": "=",
	                 "value": parameter3
	               }
	            ]
	          }
	        ],
	        "thresholds": [],
	        "timeFrom": None,
	        "timeRegions": [],
	        "timeShift": None,
	        "title": str(measurement3)+ ' ' +str(parameter3),
	        "tooltip": {
	          "shared": True,
	          "sort": 0,
	          "value_type": "individual"
	        },
	        "type": "graph",
	        "xaxis": {
	          "buckets": None,
	          "mode": "time",
	          "name": None,
	          "show": True,
	          "values": []
	        },
	        "yaxes": [
	          {
	            "format": "short",
	            "label": None,
	            "logBase": 1,
	            "max": None,
	            "min": None,
	            "show": True
	          },
	          {
	            "format": "short",
	            "label": None,
	            "logBase": 1,
	            "max": None,
	            "min": None,
	            "show": True
	          }
	        ],
	        "yaxis": {
	          "align": False,
	          "alignLevel": None
	        }
	      }
	    ],
	    "refresh": False,
	    "schemaVersion": 19,
	    "style": "dark",
	    "tags": [],
	    "templating": {
	      "list": []
	    },
	    "time": {
	      "from": "now-24h",
	      "to": "now"
	    },
	    "timepicker": {
	      "refresh_intervals": [
	        "5s",
	        "10s",
	        "30s",
	        "1m",
	        "5m",
	        "15m",
	        "30m",
	        "1h",
	        "2h",
	        "1d"
	      ]
	    },
	    
	  },
	  "folderId": 0,
	  "overwrite": True #dashboard exists
	}
	response = requests.post(url, json=data,headers=headers)
	print (response.text)

def _get_dashboard_uid(dash_title):
	url= host + "/api/search?folderIds=0&query=&starred=false"
	headers={"Content-Type": 'application/json'}
	response = requests.get(url, headers=headers)
	#print (response.text)
	dash_list = response.json()
	for i in range(len(dash_list)):
		if dash_list[i]['title'] == dash_title:
			return dash_list[i]['uid']
	return 0 #user not found

def _get_dashboard_json(dash_title, org):
	_change_current_organization_to(org)
	dash_uid = _get_dashboard_uid(dash_title)
	if dash_uid != 0:
		url= host + "/api/dashboards/uid/" + str(dash_uid)
		headers={"Content-Type": 'application/json'}
		response = requests.get(url, headers=headers)

		data = response.json()
		print("************************************")
		print (data['dashboard']['panels'])
	else:
		print("get dash json not working")

def _delete_dashboard(dash_title):
	dash_uid=_get_dashboard_uid(dash_title)
	if dash_uid != 0:
		print ("deleting dashboard ...", dash_title)
		url= host + "/api/dashboards/uid/" + str(dash_uid)
		headers={"Content-Type": 'application/json'}
		response = requests.delete(url, headers=headers)
		print (response.text)
	else:
		print("dashboard does not exist")
