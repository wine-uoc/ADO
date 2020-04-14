"""Grafana bootstrap."""
import json

import flaskapp.backend.grafana_interactions as gr


def bootstrap(name, organization, email, password, channel_id):
    user = {}
    print("Bootstrapping grafana")
    user["name"] = str(name)
    user["email"] = str(email)
    local, at, domain = email.rpartition('@')
    user["login"] = str(local)
    user["password"] = str(password)
    with open('flaskapp/backend/dashboard.json') as f:
        dash_json = json.load(f)
    org = str(organization)
    org_database_name = str(channel_id)

    print("******checking if organization exists")
    if gr._organization_check(org) == 0:  # organization not found in grafana
        print(org, "..organization not found in grafana, creating it ...")
        gr._create_organization(org)
    else:
        print(org, "..already exists")

    print("******switch to created organization and create datasource")
    gr._change_current_organization_to(org)
    gr._create_datasource(org_database_name, org_database_name, "admin", "admin")

    print("******creating default organization dashboard")
    org_dashboard_name = str(org) + '_default_dashboard'
    gr._create_dashboard(org_dashboard_name)
    print("******updating default organization dashboard")
    org_dashboard_uid = gr._get_dashboard_uid(org_dashboard_name)
    gr._update_dashboard(dash_json, org_dashboard_name, org_dashboard_uid)

    print("******Adding users as editors")
    if (gr._user_check(org, user["login"]) == 0):  # check if user exists, if not create it
        print("user not found in this organization, it needs to be created and assigned")
        gr._create_user(user)
        gr._assign_user_to_organization(org, user, "Editor")
    else:
        print("username ", user["login"], " already exists in this organization")
    # remove the created users from the default grafana organization, to ensure default screen has the default dashboards
    print("removing user from Main Org.")
    gr._change_current_organization_to("Main Org.")
    gr._remove_user_from_org(user["login"])