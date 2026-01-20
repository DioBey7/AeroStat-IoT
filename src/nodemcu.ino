#include <DHT.h>
#include <ArduinoJson.h>

#define DHTPIN 4
#define DHTTYPE DHT22
#define LED_PIN 2

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);
  dht.begin();
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "LED_ON") {
      digitalWrite(LED_PIN, LOW);
    } else if (command == "LED_OFF") {
      digitalWrite(LED_PIN, HIGH);
    }
  }

  static unsigned long lastTime = 0;
  unsigned long currentTime = millis();
  
  if (currentTime - lastTime > 2000) {
    lastTime = currentTime;
    
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();

    if (!isnan(humidity) && !isnan(temperature)) {
      StaticJsonDocument<200> doc;
      doc["temp"] = temperature;
      doc["hum"] = humidity;
      serializeJson(doc, Serial);
      Serial.println(); 
    }
  }
}