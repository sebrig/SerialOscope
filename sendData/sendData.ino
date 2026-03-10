void setup() {
  // put your setup code here, to run once:
  Serial.begin(112500);
}

void loop() {
  // put your main code here, to run repeatedly:
  static char to_send[16] = {0};
  static uint8_t i = 0;

  sprintf( to_send, "%i,%i", i, i);
  Serial.println( to_send );
  
  i++;
  delay(10);
}
