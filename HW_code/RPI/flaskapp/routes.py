"""Logged-in page routes."""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask import current_app as app
from flask_login import login_required, logout_user

from .assets import compile_main_assets
from .control import get_node_id, get_config_obj, delete_tables_entries, update_config_values, get_wifi_obj, \
    update_wifi_data, get_user_org, get_tokens_obj, get_calib_1_obj, get_calib_2_obj
from .forms import WifiForm
import flaskapp.backend.grafana_interactions as gr
from flaskapp.backend.grafana_bootstrap import load_json
from .mqtt import mqtt_connection, cal_sensor
from config import ConfigFlaskApp, ConfigRPI


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
    global tokens, client, mqtt_topic
    tokens = get_tokens_obj()
    client, mqtt_topic = mqtt_connection(tokens)
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
    

@main_bp.route('/calibration', methods=['GET','POST'])
@login_required
def start_calibration():
    """Receives post message from js push button, it should proceed with calibrating the specific sensor"""
   # str_sensor_num = request.form['sensor_num']  # Data from js
    #sensor_idx = int(str_sensor_num[-2:]) - 1
   # sensor_name = read from config


    # update rpi db
    #update_config_values(sensor_idx, new_value)
    return render_template('calibration.jinja2',title='Sensor Calibration - ADO',
                           template='dashboard-template')


@main_bp.route('/sendcontrol', methods=['POST'])
@login_required
def cal_sendcontrol():
    """sends message in control topic, to ask arduino to acquire data"""
    #create control message
    sensor = str(request.form['sensor']) 
    db_to_use = str(request.form['db_to_use'])
    cal_sensor(client, mqtt_topic, sensor, db_to_use)
    return sensor


@main_bp.route('/calcheck', methods=['POST'])
@login_required
def cal_check():
    """checks if calibration databases are full"""
    sensor = str(request.form['sensor']) 
    db1_values = get_calib_1_obj().get_values()
    db2_values = get_calib_2_obj().get_values()
    print(db2_values)
    #find sensor index i
    magnitudes = ConfigRPI.SENSOR_MAGNITUDES
    for i in range(len(magnitudes)):  #starts with 0
      if magnitudes[i] == sensor:
        break

    if db1_values[i] != 0.0 and db2_values[i] != 0.0 :
      message = "calibration database is correctly updated"
      return message
    else:
      message = "One of the values seems to be missing, please restart the calibration process"
      return message