/*
  WiFiSwitch.ino

  Switch an AC power socket via web.

  Circuit: connect an AC relay to [Gnd, 5V, and] SWITCH_PIN. Easy.

  * http://<IP>/arduino/webserver/ for "GUI".
  * http://<IP>/arduino/digital/1 to turn AC switch on.
  * http://<IP>/arduino/digital/0 to turn AC switch off.

  Note: works only with Arduino Uno WiFi Developer Edition.
*/

#include <Wire.h>
#include <UnoWiFiDevEd.h>

#define SWITCH_PIN 13
int state = LOW;

void setup() {
  pinMode(SWITCH_PIN, OUTPUT);
  digitalWrite(SWITCH_PIN, state);
  Wifi.begin();
  Wifi.println("Web Server is up");
}
void loop() {

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
    DoSwitch(client);
  }
}

void WebServer(WifiData client) {

  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: text/html");
  client.println("Connection: close");
  client.println();
  client.println("<html>");

  client.println("<head><title>WiFiSwitch</title></head>");
  client.print("<body>");
  client.print("<h3>Switch is ");
  client.print(state? "on": "off");
  client.println("</h3>");
  
  client.println("<a href='/arduino/digital/1'>On</a>");
  client.println("<a href='/arduino/digital/0'>Off</a>");
  client.println("</html>");
  client.print(DELIMITER); // very important to end the communication !!!

}

void DoSwitch(WifiData client) {
  int value = client.parseInt();
  digitalWrite(SWITCH_PIN, value);
  state = value;
  client.println("HTTP/1.1 303 See Other");
  client.println("Location: /arduino/webserver\n");
}
