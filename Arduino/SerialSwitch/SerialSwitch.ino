/* Simulate WifiSwitch (in serial mode) on a bare `duino */
#define SWITCH_PIN 13 // on-board pin-13 led emulates relay
int state = LOW;

void setup() {
  pinMode(SWITCH_PIN, OUTPUT);
  digitalWrite(SWITCH_PIN, state);
  Serial.begin(9600);
}
void loop() {
  if (Serial.available()) {
    DoSwitch(Serial.read()=='1');
    Serial.flush();
  }
  delay(50);
}

void DoSwitch(int value) {
  if (value!=state) {
    digitalWrite(SWITCH_PIN, value);
    state = value;
    //Serial.write(state? "On\n": "Off\n");
  }
}
