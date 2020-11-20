#include "main.h"

String inString, remainingstring; //incoming command from RPI
String commandWords[2]; // word1 is command and sensor type; word2 is the array of parameters(max5) 

//int reading; //holds pin reading 

void setup()
{

  digitalWrite(CO2_cal_pin, HIGH); // AirCO2 CALIBRATION happens on LOW
  pinMode(CO2_cal_pin, OUTPUT);

  Serial.begin(9600); //Starting serial communication
  //Serial1.begin(9600); //used for debuging mySerial
  while (!Serial);

  pinPeripheral(2, PIO_SERCOM);   // Assign pins 2 & 3 SERCOM0 functionality for mySerial
  pinPeripheral(3, PIO_SERCOM);   //this serial is for disabling CO2 automatic recalibration
  
  mySerial.begin(9600);
  while (!mySerial);

  analogReadResolution(10);
  sht20.initSHT20();             // Init SHT20 Sensor (Temp & Humidity)
  delay(100);
}



//***read the pins that RPI asked for and send the data in SenML messages
void ProcessReading(int sensortype, String param_list[5])
{
  //reading = 0;
  float value; //holds float value returned by sensor libraries
  value = 500;
  int pin = param_list[0].toInt(); //failure returns zero; could be changed to byte

  if ((pin < 9) and (param_list[0] != "0x40")) {  //valid pin nb  
    if (sensortype == SENSOR_ANALOG){
      value = analogRead(pin);//reading
      //value = 191;      
    } 
    else if (sensortype == SENSOR_DIGITAL)
    {
      //Serial.println("digital read");
      //pinMode(pin, INPUT);
      value = digitalRead(pin);//reading
      //value = 181;
    }
    else if (sensortype == SENSOR_SPI)
    {
      value = 10; //TBD
    } 
    else if (sensortype == SENSOR_ONEWIRE)
    {
     value = OneWireRead(pin);
     //value = 111;
    }
    else if (sensortype == SENSOR_SERIAL) 
    {
    value = 10; //TBD
    }
    else
    {
      value = 888;
    }
    
    HandlePrinting(sensortype, pin, value, "NO"); //no address
  }
  else if (param_list[0] == "0x40") //SEN0227 Temp&Hum sensor
  {  
    if (sensortype == SENSOR_I2C)
    {
        value=500; //test value 
        if (param_list[1] == "T") //Temp
        {
          value =  sht20.readTemperature();
          //value = 151;
        } 
        else if (param_list[1] == "H") //Hum
        {
          value =  sht20.readHumidity();
          //value = 141;
        }
        else
        {
          value = 999;
        }
        HandlePrinting(sensortype, pin, value, "0x40");
    }
  }
  else
  {
    Serial.print(F("Compromized command: array[0] \n")); //safe in case of junk/compromised command
    Serial.flush();
    return;
  } //invalid pin
}

//this function makes sure that we are not running out of RAM
//store the constant part of the strings in Flash
void HandlePrinting(int sensortype, int pin, float value, String addr){
  Serial.print(F("[{\"bn\":\"ArduinoMKR1000\",\"sensorType\":\""));
  Serial.print(sensortype);
  Serial.print(F("\",\"parameter1\":"));
  if (addr == "0x40")
  {
    Serial.print(F("\"0x40\""));
  }
  else if (addr == "NO") //no address
  {
    Serial.print(pin);
  }
  else 
  {
    Serial.print(F("\"PinErr\""));
  }
  Serial.print(F(",\"pinValue\":"));
  Serial.print(value);
  Serial.print(F("}]\n")); //IMPORTANT! DO NOT PUT PRINTLN, AS THE STRING ALREADY CONTAINS \n
  Serial.flush();

}

//***this is for calibration only: send an average of readings instead of a single read
void AverageReading(int sensortype, String param_list[5]){
  int array_sum = 0;
  float avg_reading = 0;
  int Array[ArrayLength];   //Store the sensor readings for calibration; we need multiple in order to average


  if (sensortype == SENSOR_ANALOG)
  {
    int pin = param_list[0].toInt(); // returns zero if conversion is not possible
    if (pin < 7){ //control pin value in case of junk
      for (int i=0; i<ArrayLength; i++) //40samples
      {
        Array[i]=analogRead(pin);
        array_sum = array_sum + Array[i];
        delay(100); //100 miliseconds delay between readings
      }

      avg_reading = array_sum/ArrayLength;
      HandlePrinting(sensortype, pin, avg_reading, "NO"); //no address
    }
    else{
      Serial.print(F("Compromized command: PIN_NB \n")); //safe in case of junk/compromised command
      Serial.flush();
      return;
    }
  }
  else{
    Serial.print(F("Compromized command: STYPE \n")); //safe in case of junk/compromised command
    Serial.flush();
    return;
  }
}
   

//*** the received command from rpi is separated into ctype, stype and parameters array
void SplitCommand(String command, String fullArray)
{
  int ctype, stype, num_param;
  String myArray[5]; //holds each of command parameters (max 5)

  //memset(myArray, 0, sizeof(myArray));
  
  ctype = command.charAt(0) - '0';     //cmdtype; extarct ASCII for zero
  stype = command.charAt(1) - '0';     //sensortype
  num_param = command.charAt(2) - '0'; //param list size

  remainingstring = fullArray; //the array of parameters "a,b,c]" or "a]"
  //Serial.println(cmdtype);
  //Serial.println(num_param);

  if ((num_param == 1) or (num_param == 2)){ //the only possible values
    for (int i = 0; i < num_param; i++)
    {
      myArray[i] = obtainArray(fullArray, ',', 0);
      remainingstring = fullArray.substring(myArray[i].length() + 1, fullArray.length()); //skip the comma; old:2
      fullArray = remainingstring;
    }
  }
  else 
  {
    Serial.print(F("Compromized command: NUM_PARAM \n")); //safe in case of junk/compromised command
    Serial.flush();
    return;
  }


  //*****process READ/CALIBRATE command****
  if (ctype == CMD_READ)
  {
    //Serial.print("\n"); 
    ProcessReading(stype, myArray);
  }
  else if (ctype == CMD_CALIBRATE)
  { 
    if (myArray[1] == "CO2")
    {
      CalibrateCO2(myArray[0]); //myArray[0] holds pin nb, but it is only used for rpi serial confirmation
    }
    else 
    {
      AverageReading(stype, myArray);
    }
  }
  else
  {
    Serial.print(F("Unrecognized command: CTYPE \n")); //safe in case of junk/compromised command
    Serial.flush();
  }

}


//*** handle the new serial interface created especially for the CO2 sensor
void SERCOM0_Handler()    // Interrupt handler for SERCOM2
{
  mySerial.IrqHandler();
}


//***extracts symbol separated values from string
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


//*** read the one wire sensor
float OneWireRead(int one_pin)
{
   //returns the temperature from one DS18S20 in DEG Celsius
  OneWire ds(one_pin);
  byte data[12];
  byte addr[8];

  if ( !ds.search(addr)) {
      //no more sensors on chain, reset search
      ds.reset_search();
      return -1000;
  }

  if ( OneWire::crc8( addr, 7) != addr[7]) {
      //Serial.println("CRC is not valid!");
      return -1000;
  }

  if ( addr[0] != 0x10 && addr[0] != 0x28) {
      //Serial.print("Device is not recognized");
      return -1000;
  }

  ds.reset();
  ds.select(addr);
  ds.write(0x44,1); // start conversion, with parasite power on at the end

  byte present = ds.reset();
  ds.select(addr);
  ds.write(0xBE); // Read Scratchpad


  for (int i = 0; i < 9; i++) { // we need 9 bytes
    data[i] = ds.read();
  }

  ds.reset_search();

  byte MSB = data[1];
  byte LSB = data[0];

  float tempRead = ((MSB << 8) | LSB); //using two's compliment
  float TemperatureSum = tempRead / 16;

  return TemperatureSum;
}

//*** calibrate CO2 by putting pin to GND and disable autocalibration
void CalibrateCO2(String pinNB){
  digitalWrite(CO2_cal_pin, LOW); // CALIBRATION happens on LOW, min 7 seconds
  delay(8000);
  digitalWrite(CO2_cal_pin, HIGH);
  delay(1000);
  mySerial.print(disable_autocal); //disable autocalibration
  delay(1000);
  //PRINT ANYTHING ON THE SERIAL for confirmation
  //extract ASCII for zero
  HandlePrinting(0, pinNB.charAt(0)- '0', 0, "NO");
}


void loop()
{
  //testing mySerial, Serial1 and Serial
  /*Serial.println("Starting");
  CalibrateCO2("A5"); 
  while (Serial1.available()) {
    Serial.print(char(Serial1.read()));
  }
  Serial.println("");*/

  //original code following:
  //Serial.setTimeout(10000); //defaults to 1000ms
  if (Serial.available() > 0)
  {
    while (Serial.available() > 0)
    {
      inString = Serial.readString();
      Serial.print(F("Waiting serial "));
    }
      //Serial.println(inString);
    if (inString[inString.length()-1] == '\n') //make sure string is correctly terminated
    {
      Serial.print(inString); //pingpong
    //cmd: abc [p,q,r]
      commandWords[0] = obtainArray(inString, ' ', 0);                //get first word containing CmdType, SensorType, Num_param
      remainingstring = inString.substring(5, inString.length() - 1 -1 ); //index 0 to length-1-1, to exclude termination character
      commandWords[1] = obtainArray(remainingstring, ']', 0);         //extract the remaining string containing the list of parameters
      SplitCommand(commandWords[0], commandWords[1]);                 //analyze command and parameters
    }
    else
    {
      Serial.print(F("Not OK\n"));
      Serial.flush();
    } 

  }

  
  delay(100);
}
