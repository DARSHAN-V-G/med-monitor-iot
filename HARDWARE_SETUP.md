# Hardware Setup Guide: ESP32 + ThingSpeak

This guide explains how to configure ThingSpeak and write the Arduino C code for the ESP32 to communicate with the Med Monitor backend.

---

## 1. ThingSpeak Setup

Follow these steps to create a compatible data channel:

1.  **Sign In**: Go to [ThingSpeak.com](https://thingspeak.com/) and log in.
2.  **New Channel**: Click **Channels > My Channels > New Channel**.
3.  **Channel Settings**:
    *   **Name**: `Med Monitor RFID Scans`
    *   **Field 1**: `event` (Values: `present` or `absent`)
    *   **Field 2**: `tag_uid` (The RFID Hex ID)
    *   **Field 3**: `medicine_id` (Internal ID, e.g., `medicine_001`)
4.  **Save**: Scroll down and click **Save Channel**.
5.  **API Keys**:
    *   Go to the **API Keys** tab.
    *   Copy the **Write API Key** (used by the ESP32 to send data).
    *   Copy the **Read API Key** (provide this to the Python team for the backend).
    *   Copy the **Channel ID** (located at the top of the page).

---

## 2. Data Format Requirements

The backend expects data in the following format. Ensure your code sends these exact strings:

| Field | Key | Expected Value | Example |
|---|---|---|---|
| **Field 1** | `event` | `present` (picked up) or `absent` (placed back) | `present` |
| **Field 2** | `tag_uid` | The unique ID of the RFID tag | `A3:B7:C2:D1` |
| **Field 3** | `medicine_id` | The ID assigned to that medicine | `medicine_001` |

---

## 3. Sample Arduino C Code (ESP32)

Use the following snippet to post data whenever an RFID tag is detected.

```cpp
#include <WiFi.h>
#include <HTTPClient.h>

// --- Configuration ---
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
String writeApiKey = "YOUR_THINGSPEAK_WRITE_API_KEY";

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
}

/**
 * Sends a medication scan event to ThingSpeak.
 * @param event "present" if picked up, "absent" if returned.
 * @param tagUid The Hex UID from the RC522 reader.
 * @param medId The ID of the medicine (default: medicine_001).
 */
void postToThingSpeak(String event, String tagUid, String medId) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    
    // Construct the API Update URL
    String url = "http://api.thingspeak.com/update?api_key=" + writeApiKey;
    url += "&field1=" + event;
    url += "&field2=" + tagUid;
    url += "&field3=" + medId;
    
    Serial.println("Sending: " + url);
    
    http.begin(url);
    int httpCode = http.GET(); // ThingSpeak uses GET for updates
    
    if (httpCode > 0) {
      Serial.println("Success! Response code: " + String(httpCode));
    } else {
      Serial.println("Error on HTTP request: " + String(httpCode));
    }
    http.end();
  }
}

void loop() {
  // --- Your RFID Detection Logic Here ---
  // Example trigger:
  // if (rfidDetected) {
  //    postToThingSpeak("present", "A3:B7:C2:D1", "medicine_001");
  // }
  
  delay(10000); // Wait 10s between checks
}
```

---

## 4. Hardware Handoff

Once the hardware is running and sending data, provide the following to the **Software/Python** team:

1.  **Channel ID**
2.  **Read API Key** (NOT the Write Key)

They will update the `config.json` in the `med_monitor` folder to start the live ML analysis.
