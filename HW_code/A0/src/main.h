
#define MAX_NUM_SENSORS 14


//debug flag. Set to 1 to print debug traces
#define DEBUG 1 

/* Types of Commands */

enum CmdType {
  CMD_READ    = 0,
  CMD_CONFIG  = 1,
  CMD_ACTUATE = 2,
  CMD_CALIBRATE = 3  
};

/* Types of Sensors */

enum SensorType{
  SENSOR_ANALOG  = 0,
  SENSOR_DIGITAL = 1,
  SENSOR_SPI     = 2,
  SENSOR_ONEWIRE = 3,
  SENSOR_I2C = 4,
  SENSOR_SERIAL = 5
};


//function prototypes
