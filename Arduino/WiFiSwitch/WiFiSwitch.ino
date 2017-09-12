/*
  WiFiSwitch.ino

  Switch an AC power socket via web [or serial].
  Note: works only with Arduino Uno WiFi Developer Edition.
  
  Circuit: connect an AC relay to [Gnd, 5V, and] SWITCH_PIN. Easy.

  Control via WiFi:
  
  * http://<IP>/arduino/webserver/ for "GUI".
  * http://<IP>/arduino/digital/1 to turn AC switch on.
  * http://<IP>/arduino/digital/0 to turn AC switch off.

  Control via serial (9600 bd):
  
  * send '1' to turn AC switch on
  * send any other char to turn AC switch on

*/

#include <Wire.h>
#include <UnoWiFiDevEd.h>

#define SWITCH_PIN 12
int state = LOW;

void setup() {
  pinMode(SWITCH_PIN, OUTPUT);
  digitalWrite(SWITCH_PIN, state);
  Serial.begin(9600);
  Wifi.begin();
  Wifi.println("Web Server is up");
}
void loop() {
  if (Serial.available()) {
    DoSwitch(Serial.read()=='1');
    Serial.flush();
  }
  while (Wifi.available()) {
    process(Wifi);
  }
  delay(50);
}

void process(WifiData client) {
  // read the command
  String command = client.readStringUntil('/');

  // commands have to be "webserver" or "digital" ?!?
  // weird firmware
  if (command == "webserver") {
    WebServer(client);
  } else if (command == "digital") {
    DoSwitch(client.parseInt());
    client.println(F("HTTP/1.1 303 See Other"));
    client.println(F("Location: /arduino/webserver\n"));
  }
}

void WebServer(WifiData client) {

  client.println(F("HTTP/1.1 200 OK"));
  client.println(F("Content-Type: text/html"));
  client.println(F("Connection: close"));
  client.println();
  client.println(F("<html>"));

  client.println(F("<head><title>WiFiSwitch</title></head>"));
  client.print(F("<body>"));
  client.print(F("<h3>Switch is "));
  client.print(state? F("on"): F("off"));
  client.println(F("</h3>"));
  
  client.println(F("<a href='/arduino/digital/1'>On</a>"));
  client.println(F("<a href='/arduino/digital/0'>Off</a>"));
  client.println(F("</html>"));
  client.print(DELIMITER); // very important to end the communication !!!

}

void DoSwitch(int value) {
  if (value!=state) {
    digitalWrite(SWITCH_PIN, value);
    state = value;
    //Serial.write(state? "On\n": "Off\n");
  }
}
