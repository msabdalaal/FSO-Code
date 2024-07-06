int irpin = 7;
bool receiving = false;
float bitDuration = 300;
unsigned char recived_byte = 0;

void setup() {
  Serial.begin(2000000);
  pinMode(irpin, INPUT);
}

void loop() {
  if (receiving) {
    recived_byte = 0;  // Reset the received byte
    // Read each bit of the byte
    for (int i = 0; i < 8; i++) {
      recived_byte = (recived_byte << 1) | !digitalRead(irpin);  // Read the bit and shift into position
      // Serial.print(!digitalRead(irpin));
      delayMicroseconds(bitDuration);  // Wait for the next bit
    }
    receiving = false;  // Reset the receiving flag

    if (recived_byte != 0) {
      char receivedChar = (char)recived_byte;  // Convert to character
      Serial.print(receivedChar);  // Print the received character
    }
  } else if (!digitalRead(irpin) == LOW) {
    // Detect start bit (LOW signal)
    receiving = true;  // Set the receiving flag
    
    delayMicroseconds(bitDuration * 3.7);  // Wait to the middle of the first data bit
  }
}

