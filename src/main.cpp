#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include "DHT.h"
#include <ArduinoJson.h>
#include "Preferences.h"

#define DHT_PIN 25U
#define DHT_TYPE DHT22
#define SERIALPRINT_ENABLE 1

typedef struct 
{
  float tempOffset;
  float humidityOffset;
} CalibrationData_T;

DHT dht(DHT_PIN, DHT_TYPE);
Preferences Prefs;

const char* ssid = "SWIFT14";
const char* password = "77754321";
const char* uploadServerUrl = "https://192.168.137.1:5000/upload";
const char* calibrationServerUrl = "https://192.168.137.1:5000/api/calibration";


static CalibrationData_T CalibrationData = {0};

static void getNvmCalibrationData(CalibrationData_T *RemotedCalibrationData)
{
  Prefs.begin("calib", false);
  RemotedCalibrationData->tempOffset = Prefs.getFloat("temp_offset");
  RemotedCalibrationData->humidityOffset = Prefs.getFloat("temp_offset");
  Prefs.end();
}

static void saveTemperatureCalibration(float tempOffset)
{
  Prefs.begin("temp_offset", false);
  Prefs.putFloat("temp_offset", tempOffset);
  Prefs.end();
#if SERIALPRINT_ENABLE
  Serial.printf("Successfully save temperature calibration to NVM.\n");
#endif
}

static void saveHumidityCalibration(float humidityOffset)
{
  Prefs.begin("humidityOffset", false);
  Prefs.putFloat("humidityOffset", humidityOffset);
  Prefs.end();
#if SERIALPRINT_ENABLE
  Serial.printf("Successfully save humidity calibration to NVM.\n");
#endif
}

static void fetchCalibration(CalibrationData_T *RemotedCalibrationData)
{
  WiFiClientSecure client;
  client.setInsecure();
  HTTPClient http;
  http.begin(client, calibrationServerUrl);
  int httpCode = http.GET();
  if (httpCode == 200)
  {
    String payload = http.getString();
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, payload);
    if (!error)
    {
      RemotedCalibrationData->tempOffset = doc["temp_offset"].as<float>();
      RemotedCalibrationData->humidityOffset = doc["humidity_offset"].as<float>();
#if SERIALPRINT_ENABLE
      Serial.printf("Calibration loaded: tempOffset=%.2f, humidityOffset=%.2f\n", 
        RemotedCalibrationData->tempOffset, RemotedCalibrationData->humidityOffset);
#endif
    }
    else
    {
#if SERIALPRINT_ENABLE
      Serial.println("Failed to parse JSON");
#endif
    }
  }
  else
  {
#if SERIALPRINT_ENABLE
    Serial.printf("HTTP GET failed, code: %d\n", httpCode);
#endif
  }
  http.end();
}

static void CalibrateSensor(void)
{
  CalibrationData_T RemotedCalibrationData = {0};
  CalibrationData_T NvmCalibrationData = {0};
  fetchCalibration(&RemotedCalibrationData);
  getNvmCalibrationData(&NvmCalibrationData);

  if (RemotedCalibrationData.tempOffset != NvmCalibrationData.tempOffset)
  {
    saveTemperatureCalibration(RemotedCalibrationData.tempOffset);
  }

  if (RemotedCalibrationData.humidityOffset != NvmCalibrationData.humidityOffset)
  {
    saveHumidityCalibration(RemotedCalibrationData.humidityOffset);
  }
  CalibrationData = RemotedCalibrationData;
}


void setup(void) 
{
#if SERIALPRINT_ENABLE
  Serial.begin(115200);
  Serial.println("[INFO] Serial startup successful. ");
#endif

  dht.begin();
#if SERIALPRINT_ENABLE
  Serial.println("[INFO] DHT startup successful.");
#endif
  WiFi.begin(ssid, password);

  uint16_t WiFiTimeout = 0U;
  while((WiFi.status() != WL_CONNECTED) && (WiFiTimeout < 60U))
  {
#if SERIALPRINT_ENABLE
    Serial.println("[INFO] Connecting to WiFi...");
#endif
    WiFiTimeout++;
    delay(1000);
  }

  if (WiFi.status() == WL_CONNECTED)
  {
#if SERIALPRINT_ENABLE
    Serial.println("[INFO] WiFi connect successful.");
#endif
  }
  else
  {
#if SERIALPRINT_ENABLE
    Serial.println("[WARNING] WiFi connect timeout.");
#endif
  }
  CalibrateSensor(); /* Get calibration data. */
}

void loop(void) 
{
  volatile float temperature = dht.readTemperature();
  volatile float humidity = dht.readHumidity();
  if (isnan(temperature) || isnan(humidity))
  {
#if SERIALPRINT_ENABLE
    Serial.println("Error: Failed to read DHT sensor!");
#endif
  }
  else
  {
#if SERIALPRINT_ENABLE
    Serial.printf("Temperature %.1f degree Celcius, Humidity: %.1f %%\n", temperature, humidity);
#endif
      WiFiClientSecure client;
      client.setInsecure();
      HTTPClient http;
      http.begin(client, uploadServerUrl);
    temperature = temperature - CalibrationData.tempOffset;
    humidity = humidity - CalibrationData.humidityOffset;

    http.addHeader("Content-Type", "application/json");
    String json = "{\"temperature\":" + String(temperature) + 
                  ",\"humidity\":" + String(humidity) + "}"; /* {temperature: value, humidity*: value} */

      int httpResponse = http.POST(json);
      http.end();
  }
  delay(2000);
}
