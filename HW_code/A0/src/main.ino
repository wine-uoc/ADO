#include "main.h"

String inString, remainingstring; //incoming command from RPI
String commandWords[2]; // word1 is command and sensor type; word2 is the array of parameters(max5) 
String myArray[5]; //holds each of command parameters (max 5)

int Array[ArrayLength];   //Store the sensor readings for calibration; we need multiple in order to average
int reading; //holds pin reading 
float value; //holds float value returned by sensor libraries
String SenMLdata; //data to be printed on serial




void setup()
{

  digitalWrite(CO2_cal_pin, HIGH); // AirCO2 CALIBRATION happens on LOW
  pinMode(CO2_cal_pin, OUTPUT);

  Serial.begin(9600); //Starting serial communication
  //Serial1.begin(9600); //used for debuging mySerial
  while (!Serial);

  pinPeripheral(2, PIO_SERCOM);   // Assign pins 2 & 3 SERCOM0 functionality for mySerial
  pinPeripheral(3, PIO_SERCOM);   
  
  mySerial.begin(9600);
  while (!mySerial);

  analogReadResolution(10);
  sht20.initSHT20();             // Init SHT20 Sensor
  delay(100);
}




void ProcessReading(int sensortype, String param_list[5])
{
  SenMLdata = "\n";
  reading = 0;
  value = 0;

  if (sensortype == SENSOR_ANALOG)
  {
    int pin = param_list[0].toInt();
    reading = analogRead(pin);
    SenMLdata = "[{\"bn\":\"ArduinoMKR1000\",\"sensorType\":\"" + String(sensortype) + "\",\"parameter1\":" + String(pin) + ",\"pinValue\":" + String(reading) + "}]\n";
    Serial.print(SenMLdata); //IMPORTANT! DO NOT PUT PRINTLN, AS THE STRING ALREADY CONTAINS \n
  }
  else if (sensortype == SENSOR_DIGITAL)
  {
    //Serial.println("digital read");
    pinMode(param_list[0].toInt(), INPUT);
    reading = digitalRead(param_list[0].toInt());
    //Serial.println(reading);
    SenMLdata = "[{\"bn\":\"ArduinoMKR1000\",\"sensorType\":\"" + String(sensortype) + "\",\"parameter1\":" + String(param_list[0]) + ",\"pinValue\":" + String(reading) + "}]\n";
    Serial.print(SenMLdata); //IMPORTANT! DO NOT PUT PRINTLN, AS THE STRING ALREADY CONTAINS \n
  }
  else if (sensortype == SENSOR_SPI)
  {//TBD
    value = 10;
    SenMLdata = "[{\"bn\":\"ArduinoMKR1000\",\"sensorType\":\"" + String(sensortype) + "\",\"parameter1\":" + String(param_list[0]) + ",\"pinValue\":" + String(value) + "}]\n";
    Serial.print(SenMLdata); //IMPORTANT! DO NOT PUT PRINTLN, AS THE STRING ALREADY CONTAINS \n
  }
  else if (sensortype == SENSOR_ONEWIRE)
  {
    value = 5;
    value = OneWireRead(param_list[0].toInt());
    SenMLdata = "[{\"bn\":\"ArduinoMKR1000\",\"sensorType\":\"" + String(sensortype) + "\",\"parameter1\":" + String(param_list[0]) + ",\"pinValue\":" + String(value) + "}]\n";
    Serial.print(SenMLdata); //IMPORTANT! DO NOT PUT PRINTLN, AS THE STRING ALREADY CONTAINS \n
  }
  else if (sensortype == SENSOR_I2C)
  {
    if (String(param_list[0]) == "0x40") //SEN0227 Temp&Hum sensor
    {
      value=500; //test value 
      if (String(param_list[1]) == "T") //Temp
      {
       value =  sht20.readTemperature();
      } 
      else if (String(param_list[1]) == "H") //Hum
      {
       value =  sht20.readHumidity();
      }
      SenMLdata = "[{\"bn\":\"ArduinoMKR1000\",\"sensorType\":\"" + String(sensortype) + "\",\"parameter1\":\"" + String(param_list[0]) + "\",\"pinValue\":" + String(value) + "}]\n";
      Serial.print(SenMLdata); //IMPORTANT! DO NOT PUT PRINTLN, AS THE STRING ALREADY CONTAINS \n
    }
  }
  else if (sensortype == SENSOR_SERIAL){
  //TBD 
    value = 10;
    SenMLdata = "[{\"bn\":\"ArduinoMKR1000\",\"sensorType\":\"" + String(0) + "\",\"parameter1\":" + String(value) + ",\"pinValue\":" + String(0) + "}]\n";
    Serial.print(SenMLdata);
  } 
}

void AverageReading(int sensortype, String param_list[5]){
  SenMLdata = "\n";
  int array_sum = 0;
  float avg_reading = 0;

  if (sensortype == SENSOR_ANALOG)
  {
    int pin = param_list[0].toInt();
    for (int i=0; i<ArrayLength; i++) //40samples
    {
      Array[i]=analogRead(pin);
      array_sum = array_sum + Array[i];
      delay(100); //100 miliseconds delay between readings
    }

    avg_reading = array_sum/ArrayLength;
    SenMLdata = "[{\"bn\":\"ArduinoMKR1000-CALIBRATION\",\"sensorType\":\"" + String(sensortype) + "\",\"parameter1\":" + String(pin) + ",\"pinValue\":" + String(avg_reading) + "}]\n";
    Serial.print(SenMLdata); //IMPORTANT! DO NOT PUT PRINTLN, AS THE STRING ALREADY CONTAINS \n
  }
}

void SplitCommand(String command, String fullArray)
{
  int ctype, stype, num_param;
  memset(myArray, 0, sizeof(myArray));
  
  ctype = command.charAt(0) - '0';     //cmdtype; extarct ASCII for zero
  stype = command.charAt(1) - '0';     //sensortype
  num_param = command.charAt(2) - '0'; //param list size

  remainingstring = fullArray; //the array of parameters "a,b,c]" or "a]"
  //Serial.println(cmdtype);
  //Serial.println(num_param);
  for (int i = 0; i < num_param; i++)
  {
    myArray[i] = obtainArray(fullArray, ',', 0);
    remainingstring = fullArray.substring(myArray[i].length() + 1, fullArray.length()); //skip the comma; old:2
    fullArray = remainingstring;
  }

  //*****process READ/CALIBRATE command****
  if (ctype == CMD_READ) 
    ProcessReading(stype, myArray);
  else if (ctype == CMD_CALIBRATE)
  { 
    if (String(myArray[1]) == "CO2")
      CalibrateCO2(myArray[0]); //myArray[0] holds pin nb
    else 
      AverageReading(stype, myArray);
  }

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
  if (Serial.available() > 0)
  {
    while (Serial.available() > 0)
    {
      inString = Serial.readString();
    }
    //Serial.println(inString);

    commandWords[0] = obtainArray(inString, ' ', 0);                //get first word containing CmdType, SensorType, Num_param
    remainingstring = inString.substring(5, inString.length() - 1); //index 0 to length-1
    commandWords[1] = obtainArray(remainingstring, ']', 0);         //extract the remaining string containing the list of parameters
    SplitCommand(commandWords[0], commandWords[1]);                 //analyze command and parameters
  }
  delay(100);
}
