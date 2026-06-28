#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>

// --- USER CONFIGURATION ---
const char *ssid = "YOUR_WIFI_NAME";
const char *password = "YOUR_WIFI_PASSWORD";
const char *serverName = "http://192.168.1.45:5000/scan";

// --- SERVO HARDWARE CONFIGURATION ---
#define SERVO_PIN 13

// The ESP32 LEDC subsystem in Core v3.x handles channels automatically
const int servoFreq = 50;       // Servo standard: 50Hz frequency
const int servoResolution = 16; // 16-bit resolution (0 to 65535)

// Math: At 50Hz and 16-bit resolution:
// 1.0ms pulse (0 degrees / Locked)  = roughly 3276 duty cycle
// 2.0ms pulse (180 degrees/ Unlock) = roughly 6553 duty cycle
const int dutyLocked = 3300;
const int dutyUnlocked = 6500;

// --- AI-THINKER CAMERA PIN MAP ---
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27
#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22

void setup()
{
    Serial.begin(115200);

    // --- 1. INITIALIZE HARDWARE PWM (The Flex Point) ---
    // Core 3.0 API: ledcAttach(pin, frequency, resolution)
    ledcAttach(SERVO_PIN, servoFreq, servoResolution);

    // Set initial state to LOCKED
    ledcWrite(SERVO_PIN, dutyLocked);

    // --- 2. INITIALIZE NETWORK ---
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi Connected!");

    // --- 3. INITIALIZE CAMERA DMA PIPELINE ---
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 15;
    config.fb_count = 1;

    // --- DIAGNOSTIC ERROR CHECK ---
    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK)
    {
        Serial.printf("CRITICAL ERROR: Camera init failed with error 0x%x\n", err);
        Serial.println("Fix 1: Push the golden camera ribbon cable firmly into the connector.");
        Serial.println("Fix 2: Go to Tools -> PSRAM -> Enabled in Arduino IDE.");
        return; // Stop the program here so it doesn't freeze later
    }
    Serial.println("Camera Hardware Initialized Successfully!");
}

void loop()
{
    Serial.println("\nCapturing frame to PSRAM...");

    // Snap photo using Direct Memory Access (DMA)
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb)
    {
        Serial.println("Camera capture failed");
        return;
    }

    if (WiFi.status() == WL_CONNECTED)
    {
        HTTPClient http;
        http.begin(serverName);
        http.addHeader("Content-Type", "image/jpeg");

        // Transmit PSRAM buffer payload
        int httpResponseCode = http.POST(fb->buf, fb->len);

        if (httpResponseCode == 200)
        {
            Serial.println("Laptop Auth: PASS. Adjusting PWM Duty Cycle to UNLOCK.");

            // Swing arm to 180 degrees
            ledcWrite(SERVO_PIN, dutyUnlocked);

            // Wait for user to open the door
            delay(4000);

            Serial.println("Timeout: Adjusting PWM Duty Cycle to LOCK.");
            // Swing arm back to 0 degrees
            ledcWrite(SERVO_PIN, dutyLocked);
        }
        else
        {
            Serial.print("Laptop Auth: FAIL. HTTP Code: ");
            Serial.println(httpResponseCode);
        }
        http.end();
    }

    // CRITICAL: Free the PSRAM heap allocation to prevent Kernel Panic
    esp_camera_fb_return(fb);
    delay(6000); // Polling delay
}