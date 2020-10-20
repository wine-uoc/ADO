#include <stdlib.h>
#include <OneWire.h>
#include "DFRobot_SHT20.h"
#include <Arduino.h>                              // required before wiring_private.h
#include <wiring_private.h>
#include <Wire.h>

#define MAX_NUM_SENSORS 14
#define ArrayLength  40    //times of collection for calibration

//debug flag. Set to 1 to print debug traces
#define DEBUG 1 
#define CO2_cal_pin  (5ul)
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
void SERCOM0_Handler()    // Interrupt handler for SERCOM2
{
  mySerial.IrqHandler();
}

String obtainArray(String data, char separator, int index)
{
  int found = 0;
  int strIndex[] = {0, -1};
  int maxIndex = data.length() - 1;
  for (int i = 0; i <= maxIndex && found <= index; i++)
  {
    if (data.charAt(i) == separator || i == maxIndex)
    {
      found++;
      strIndex[0] = strIndex[1] + 1;
      strIndex[1] = (i == maxIndex) ? i + 1 : i;
    }
  }
  return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}

float OneWireRead(int one_pin)
{
  OneWire ds(one_pin);
  byte data[12];
  byte addr[8];

  if (!ds.search(addr))
  {
    //no more sensors on chain, reset search
    ds.reset_search();
    return -1000;
  }

  if (OneWire::crc8(addr, 7) != addr[7])
  {
    //Serial.println("CRC is not valid!");
    return -1000;
  }

  if (addr[0] != 0x10 && addr[0] != 0x28)
  {
    //Serial.print("Device is not recognized");
    return -1000;
  }

  ds.reset();
  ds.select(addr);
  ds.write(0x44, 1); // start conversion, with parasite power on at the end

  //byte present = ds.reset();
  ds.select(addr);
  ds.write(0xBE); // Read Scratchpad

  for (int i = 0; i < 9; i++)
  { // we need 9 bytes
    data[i] = ds.read();
  }

  ds.reset_search();

  byte MSB = data[1];
  byte LSB = data[0];

  float Read = ((MSB << 8) | LSB); //using two's compliment
  float Sum = Read / 16;

  return Sum;
}

void CalibrateCO2(String pinNB){
  String answer = "\n";
  digitalWrite(CO2_cal_pin, LOW); // CALIBRATION happens on LOW, min 7 seconds
  delay(8000);
  digitalWrite(CO2_cal_pin, HIGH);
  delay(1000);
  mySerial.print(disable_autocal); //disable autocalibration
  delay(1000);
  //PRINT ANYTHING ON THE SERIAL for confirmation
  answer = "[{\"bn\":\"ArduinoMKR1000-CO2-CAL\",\"sensorType\":\"" + String(0) + "\",\"parameter1\":" + pinNB + ",\"pinValue\":" + String(0) + "}]\n";
  Serial.print(answer);

}