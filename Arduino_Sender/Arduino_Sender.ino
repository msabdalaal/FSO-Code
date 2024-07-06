const int laserPin = 4;  // Pin connected to the laser
short bitDuration = 300;

void setup() {
  // Initialize the laser pin as an output
  pinMode(laserPin, OUTPUT);
  digitalWrite(laserPin, HIGH);
  // Initialize the serial communication
  Serial.begin(2000000);
}

void loop() {
  // Check if any data is available to read from the serial port
  if (Serial.available() > 0) {
    // Read the incoming byte
    char incomingByte = Serial.read();

    sendByteAsBits(incomingByte);
  }
}

void sendByteAsBits(char byte) {

  // Send start bit (LOW)
  digitalWrite(laserPin, LOW);
  delayMicroseconds(bitDuration*3);
  
  // Send each bit of the byte
  for (int i = 7; i >= 0; i--) {
    bool bitValue = bitRead(byte, i);
    digitalWrite(laserPin, bitValue ? HIGH : LOW);
    delayMicroseconds(bitDuration);
    // Serial.print(bitValue);
  }

  // Send stop bit (HIGH)
  digitalWrite(laserPin, HIGH);
  delayMicroseconds(bitDuration*2);
}
