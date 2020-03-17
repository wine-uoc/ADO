void setup() {
Serial1.begin(9600);   
Serial.begin(9600); //Starting serial communication
}
  
void loop() {
  analogReadResolution(10);
  Serial.print("ADC 10-bit (default) : ");
  Serial.println(analogRead(A0));

  // change the resolution to 12 bits and read A0
  analogReadResolution(12);
  Serial.print(", 12-bit : ");
  PH= analogRead(A0);
  Serial.println(PH);


  SenMLdata= "[{\"bn\":\"ArduinoMKR1000\",\"n\":\"PH\",\"u\":\"None\",\"v\":"+String(PH)+"}, {\"bn\":\"ArduinoMKR1000\",\"n\":\"inventedTemp\",\"u\":\"Cel\",\"v\":22}]";
  
  Serial.println(SenMLdata);
  Serial1.println(SenMLdata);
  
  delay (5000);

}
