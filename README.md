# ADO
ADO project repository

## HW_code
Contains code for handling communication of sensor data between RPi and Arduino. RPi sends commands to A0 demanding
 data and after checking data validity, it pushes it to Mainflux, using the user credentials.

### A0
Load the A0_command_manager.ino on Arduino MKR1000. It will wait for serial commands from RPI, parse them and immediately
 send an answer (containing the requested data) to RPi.

### RPi
Run RPi_command_manager.py. It will handle mqtt connection with mainflux, serial comm configuration with A0, command
 configuration (sensors, pins, periodicity) and it will create separate threads for each command. The threads share a lock, 
to ensure that commands are sent in the correct order to A0, and that no commands happen simultaneously. The lock is released 
after having received an answer from A0.  

RPi_client.py: handles mqtt connection to Mainflux

tokens.txt: contains user credentials for things

RPi_commands.py: creates commands for A0

RPi_publish_data.py: checks data validity (data received from A0) and pushes it to mainflux, as a SenML message.

