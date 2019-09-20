# ADO
ADO project repository

## 00-docker-scripts
A docker-compose file to launch influx, grafana, mosquitto and a mqtt forwarder to influxdb.

Run:
```
cd 00-docker-scripts
./0-setenv.sh
sudo ./1-grant-permission.sh
docker-compose up
```

## 01-mosquitto
the folder contains the mqtt broker configuration

## 02-bridge
this is the mqtt forwarder to influxdb in python.

# Other Interesting tools

check grafana cli python library that enables the management of organization. this may be useful when starting new device so we can create a new organization for it. This will enable multitenancy. 
https://pypi.org/project/grafanacli/
