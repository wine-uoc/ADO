import json
import grafana_interactions as gr

UOC_user_list = {}
UOC_user_list[0] = {}
UOC_user_list[0]["name"] = "uoc1"
UOC_user_list[0]["email"] = "uoc1@test.com"
UOC_user_list[0]["login"] = "uoc1"
UOC_user_list[0]["password"] = "uoc1"

UOC_user_list[1] = {}
UOC_user_list[1]["name"] = "uoc2"
UOC_user_list[1]["email"] = "uoc2@test.com"
UOC_user_list[1]["login"] = "uoc2"
UOC_user_list[1]["password"] = "uoc2"

UPC_user_list = {}
UPC_user_list[0] = {}
UPC_user_list[0]["name"] = "upc1"
UPC_user_list[0]["email"] = "upc1@test.com"
UPC_user_list[0]["login"] = "upc1"
UPC_user_list[0]["password"] = "upc1"

UPC_user_list[1] = {}
UPC_user_list[1] ["name"] = "upc2"
UPC_user_list[1] ["email"] = "upc2@test.com"
UPC_user_list[1] ["login"] = "upc2"
UPC_user_list[1] ["password"] = "upc2"


def main():
	organization_list = ['UOC','UPC']
	#create organizations and create their datasources and default databases
	for org in organization_list:

		print("******checking if organization exists")
		if gr._organization_check(org) == 0: #organization not found in grafana
			print (org, "..organization not found in grafana, creating it ...")
			gr._create_organization(org)
		else:
			print (org, "..already exists")

		print("******switch to created organization and create datasource")
		gr._change_current_organization_to(org)
		org_database_name = str(org)+ '_db'
		gr._create_datasource(org_database_name, org_database_name, "admin", "admin")

		print("******creating default organization dashboard")
		org_dashboard_name = str(org)+'_default_dashboard'
		gr._create_dashboard(org_dashboard_name)
		org_dashboard_uid=gr._get_dashboard_uid(org_dashboard_name)
		gr._update_dashboard(org_dashboard_name, org_dashboard_uid, org_database_name, "raw", "temperature", "node_1", "flow", "raw", "ph")

	
		print("******Adding users as editors")		
		current_user_list = eval(org+"_user_list")
		for i in range(len(current_user_list)):
			if (gr._user_check(org, current_user_list[i]["login"]) == 0):#check if user exists, if not create it
				print ("user not found in this organization, it needs to be created and assigned")
				gr._create_user(current_user_list[i])
				gr._assign_user_to_organization(org, current_user_list[i], "Editor")
			else:
				print ("username ", current_user_list[i]["login"], " already exists in this organization")
	#remove the created users from the default grafana organization, to ensure default screen has the default dashboards
	gr._change_current_organization_to("Main Org.")
	for org in organization_list:
		current_user_list = eval(org+"_user_list")
		for i in range(len(current_user_list)):
			gr._remove_user_from_org(current_user_list[i]["login"])


if __name__ == '__main__':
    print('Managing organizations in Grafana')
    main()


