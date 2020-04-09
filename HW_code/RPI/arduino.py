"""Arduino <-> Grafana bridge application."""
from arduinoapp.RPi_command_manager import main

if __name__ == "__main__":
    main()


# TODO:
#  - get sampling rate values from Grafana
#  - update local database using grafana sampling rate values
