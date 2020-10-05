"""Logged-in page routes."""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask import current_app as app
from flask_login import login_required, logout_user

from .assets import compile_main_assets
from .control import get_node_id, get_config_obj, delete_tables_entries, update_config_values, get_wifi_obj, \
    update_wifi_data, get_user_org, get_tokens_obj, get_calib_1_obj, get_calib_2_obj, get_req_calib_1_obj, get_req_calib_2_obj
from .forms import WifiForm
import flaskapp.backend.grafana_interactions as gr
from flaskapp.backend.grafana_bootstrap import load_json
from .mqtt import mqtt_connection, cal_sensor
from config import ConfigFlaskApp, ConfigRPI

MQTT_CONNECTED = False  # global variable for handling mqtt connection
MQTT_SUBSCRIBED = False

# Blueprint Configuration
main_bp = Blueprint('main_bp', __name__,
                    template_folder='templates',
                    static_folder='static')
compile_main_assets(app)

@main_bp.route('/', methods=['GET', 'POST'])
@login_required
def dashboard():
    """
    Node configuration page.
    GET:
    Show active sensors from database, allow enable/disable sensors, show menu options.
    """
    global tokens, client, mqtt_topic, MQTT_CONNECTED, MQTT_SUBSCRIBED
    tokens = get_tokens_obj()

    while not MQTT_CONNECTED:
      MQTT_CONNECTED, client, mqtt_topic = mqtt_connection(tokens)
      mqtt_topic = mqtt_topic + '/control'

    str_current_config = ['checked' if sensor_sr != 0 else '' for sensor_sr in get_config_obj().get_values()]
    # str list of 'checked' if sensor sampling rate is not 0 else '' (checked is passed to html checkbox)

    return render_template('dashboard.jinja2',
                           title='Configuration - ADO',
                           template='dashboard-template',
                           node_id=get_node_id(),
                           s01_state=str_current_config[0],
                           s02_state=str_current_config[1],
                           s03_state=str_current_config[2],
                           s04_state=str_current_config[3],
                           s05_state=str_current_config[4],
                           s06_state=str_current_config[5],
                           s07_state=str_current_config[6],
                           s08_state=str_current_config[7],
                           s09_state=str_current_config[8],
                           s10_state=str_current_config[9])


@main_bp.route('/wifi', methods=['GET', 'POST'])
@login_required
def set_wifi():
    """
    Wifi configuration page.

    GET: Serve Set-wifi page and show current SSID stored.
    POST: If form is valid, add new wifi data (delete previous), show success message.
    """
    wifi_form = WifiForm()

    if get_wifi_obj().active:
        current_wifi_state = 'checked'  # Get current wifi status to be displayed in page
    else:
        current_wifi_state = ''

    if request.method == 'POST' and wifi_form.validate_on_submit():
        # Store Wifi details
        update_wifi_data(wifi_form.ssid.data,
                         wifi_form.password.data)
        flash('New SSID and password stored.')
        return redirect(url_for('main_bp.set_wifi'))

    return render_template('wifi.jinja2',
                           form=wifi_form,
                           title='Configure WiFi - ADO',
                           template='wifi-page',
                           current_ssid=get_wifi_obj().ssid,
                           current_wifi_state=current_wifi_state)


@main_bp.route("/logout")
@login_required
def logout():
    """User log-out."""
    logout_user()
    return redirect(url_for('auth_bp.login'))


@main_bp.route("/delete")
@login_required
def delete():
    """Factory reset. Delete entries one by one for each table (or delete database file?)"""
    # TODO: disconnect thing of channel (backend)
    delete_tables_entries()
    logout_user()
    return redirect(url_for('main_bp.dashboard'))


@main_bp.route('/activatewifi', methods=['POST'])
@login_required
def get_post_js_data_activatewifi():
    """Receives post message from js on-off button to activate wifi."""
    jsdata = request.form['javascript_data']
    if jsdata == 'true':
        activate = 1
    elif jsdata == 'false':
        activate = 0
    else:
        activate = None
    update_wifi_data(activate=activate)
    return jsdata


@main_bp.route('/setsensor', methods=['POST'])
@login_required
def get_post_js_data_setsensor():
    """Receives post message from js on-off button, activates SPECIFIC sensor to default sampling rate."""
    str_sensor_num = request.form['sensor_num']  # Data from js
    state = request.form['box_state']

    sensor_idx = int(str_sensor_num[-2:]) - 1
    new_value = app.config['DEFAULT_SR'] if state == 'true' else 0

    # update rpi db
    update_config_values(sensor_idx, new_value)
    return state

@main_bp.route('/upgrade', methods=['GET','POST'])
@login_required
def dashboard_upgrade():
  # TODO load all files from server or github for updated versions
    #noti_json = load_json('flaskapp/backend/alert_channels/slack.json')
    try:
      num_dashs = 4
      dash_pr_json = load_json('flaskapp/backend/dashboards/principal.json')
      dash_ag_json = load_json('flaskapp/backend/dashboards/agregat.json')
      dash_es_json = load_json('flaskapp/backend/dashboards/estat.json')
      dash_al_json = load_json('flaskapp/backend/dashboards/alertes.json')

      organization = get_user_org()
      gr._change_current_organization_to(organization)

      # Create dashborads, rewrite flag is true --> existing dashs are updated
      dash_ids = []
      dash_ids.append(gr._create_dashboard(dash_pr_json))
      dash_ids.append(gr._create_dashboard(dash_ag_json))
      dash_ids.append(gr._create_dashboard(dash_es_json))
      dash_ids.append(gr._create_dashboard(dash_al_json))

      # Load preferences
      gr.update_preferences_org(dash_ids[0])
      flash('Dashboard has been upgraded to the last version')
    except:
      flash('Something went wrong, Try again later')
    return redirect(url_for('auth_bp.login'))
    

@main_bp.route('/calibration', methods=['GET'])
@login_required
def start_calibration():
    """it should proceed with calibrating the specific sensor"""
    str_sensor_idx = str(request.args.get('sensor_index'))
    print(str_sensor_idx)
    sensor_idx = int(str_sensor_idx[-2:]) - 1 #name goes from 1 to 10, but index from 0 to 9
    sensor_name = ConfigRPI.SENSOR_MAGNITUDES[sensor_idx]
    text1 = " Wash the probe with distilled water,\
               then absorb the residual water-drops with paper.\
               Insert the probe into the standard buffer solution of"
    text2 = ", stir gently, for a few seconds. Then press the button below."
    if sensor_name == 'pH':
      ph7 = " 7.0"
      ph4 = " 4.0"
      message1 = "1) "+ text1 + str(ph7) + text2
      message2 = "2) "+ text1 + str(ph4) + text2
      button1 = "Record pH 7.0"
      button2 = "Record pH 4.0"
    elif sensor_name == 'Conductivity1':
      cd1 = " 1413us/cm"
      cd2 = " 12.88ms/cm"
      message1 = "1) "+ text1 + str(cd1) + text2
      message2 = "2) "+ text1 + str(cd2) + text2
      button1 = "Record" + str(cd1)
      button2 = "Record" + str(cd2)
    else:
      message1= "not implemented"
      message2= "not implemented"
      button1= "not implemented"
      button2= "not implemented"

  #render template with variables: sensor name, sensor message, button text
    return render_template('calibration.jinja2', title= "ADO- Sensor Calibration",
                             sensor_name= sensor_name, message1=message1, message2=message2,
                              button1=button1, button2=button2, template='dashboard-template')


@main_bp.route('/sendcontrol', methods=['POST'])
@login_required
def cal_sendcontrol():
    """sends message in control topic, to ask arduino to acquire data"""
    #create control message
    sensor = str(request.form['sensor']) 
    print(sensor)
    db_to_use = str(request.form['db_to_use'])
    print(db_to_use)
    cal_sensor(client, mqtt_topic, sensor, db_to_use)
    return sensor


@main_bp.route('/calcheck', methods=['POST'])
@login_required
def cal_check():
    """checks if calibration databases are full"""
    sensor = str(request.form['sensor']) 
    db1_values = get_req_calib_1_obj().get_values()
    db2_values = get_req_calib_2_obj().get_values()
    print(db1_values)
    print(db2_values)
    #find sensor index i
    magnitudes = ConfigRPI.SENSOR_MAGNITUDES
    for i in range(len(magnitudes)):  #starts with 0
      if magnitudes[i] == sensor:
        break

    if db1_values[i] == 0 and db2_values[i] == 0 : #calib not required anymore
      message = "calibration database is correctly updated"
      return message
    elif db1_values[i] ==1 and  db2_values[i] == 0:
      message = "Please retake the first measurement"
      return message
    elif db1_values[i] ==0 and  db2_values[i] == 1:
      message = "Please retake the second measurement"
      return message
    else:
      message = "Please retake both measurements"
      return message