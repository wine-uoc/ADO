#include <OneWire.h>
#include <stdlib.h>
#include "DFRobot_SHT20.h"
#include <Arduino.h>                              // required before wiring_private.h
#include <wiring_private.h>
#include <Wire.h>

#define MAX_NUM_SENSORS 14
#define ArrayLength  40    //times of collection for calibration

//debug flag. Set to 1 to print debug traces
#define DEBUG 1 
#define CO2_cal_pin  (4ul)
// Serial pin and pad definitions (in Arduino files Variant.h & Variant.cpp)
#define PIN_SERIAL_RX       (3ul)                // Pin description number for PIO_SERCOM on D3
#define PIN_SERIAL_TX       (2ul)                // Pin description number for PIO_SERCOM on D2
#define PAD_SERIAL_TX       (UART_TX_PAD_2)      // SERCOM pad 2 TX
#define PAD_SERIAL_RX       (SERCOM_RX_PAD_3)    // SERCOM pad 3 RX

// Instantiate the extra Serial class
Uart mySerial(&sercom0, PIN_SERIAL_RX, PIN_SERIAL_TX, PAD_SERIAL_RX, PAD_SERIAL_TX);



DFRobot_SHT20    sht20;
String disable_autocal = "0xFF 0x01 0x79 0x00 0x00 0x00 0x00 0x00";



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
float OneWireRead(int one_pin);
void CalibrateCO2(String pinNB);
String obtainArray(String data, char separator, int index);
void SERCOM0_Handler();
