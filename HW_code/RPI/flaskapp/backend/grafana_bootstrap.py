"""Grafana bootstrap."""
import json

import flaskapp.backend.grafana_interactions as gr


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
    print("Bootstrapping grafana ...")

    # User data
    user = {}
    user["name"] = str(name)
    user["email"] = str(email)
    local, at, domain = email.rpartition('@')
    user["login"] = str(local)
    user["password"] = str(password)

    # Org data
    org = str(organization)
    org_database_name = str(channel_id)

    # Grafana data
    # TODO load all files in folder to list
    noti_json = load_json('flaskapp/backend/alert_channels/slack.json')
    num_dashs = 5
    dash_pr_json = load_json('flaskapp/backend/dashboards/principal.json')
    dash_ag_json = load_json('flaskapp/backend/dashboards/agregat.json')
    dash_es_json = load_json('flaskapp/backend/dashboards/estat.json')
    dash_al_json = load_json('flaskapp/backend/dashboards/alertes.json')
    dash_ca_json = load_json('flaskapp/backend/dashboards/calibration.json')

    # --- Provisioning

    # Create new org
    if gr._organization_check(org) == 0:
        # organization not found in grafana
        gr._create_organization(org)
        gr._change_current_organization_to(org)     # switch to org

        # Create datasource
        data_source_id = gr._create_datasource(org_database_name, org_database_name, "admin", "admin")

        # Create alert channels
        gr._create_notification_channels(noti_json)

        # Create dashborads
        dash_ids = []
        dash_ids.append(gr._create_dashboard(dash_pr_json))
        dash_ids.append(gr._create_dashboard(dash_ag_json))
        dash_ids.append(gr._create_dashboard(dash_es_json))
        dash_ids.append(gr._create_dashboard(dash_al_json))
        dash_ids.append(gr._create_dashboard(dash_ca_json))

        # Load preferences
        gr.update_preferences_org(dash_ids[0])
    else:
        gr._change_current_organization_to(org)     # switch to org

    # Create new user
    if gr._user_check(org, user["login"]) == 0:
        # Check if user exists, if not create it
        gr._create_user(user)
        gr._assign_user_to_organization(org, user, "Viewer")    # Editor, Admin
        gr.update_preferences_user(dash_ids[0])     # load user preferences

        # Give db permissions to new user
        # NOTE: Datasource Permissions is now an Enterprise feature
        users = gr._get_all_users_org()
        for usr in users:
            if usr['email'] == str(email):
                gr.add_persmission_datasource(data_source_id, usr['userId'])
                break

        # Star dashboards
        for dash_id in dash_ids:
            gr._star_dashboard(dash_id)

        # Remove created users from default grafana organization, to ensure default screen has the default dashboards
        gr._change_current_organization_to("Main Org.")
        gr._remove_user_from_org(user["login"])

    print("... End of bootstrapping grafana.")
