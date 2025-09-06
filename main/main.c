#include <stdio.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include "esp_system.h"
#include "freertos/event_groups.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "DHT.h"
#include "nvs_flash.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "protocol_examples_common.h"
#include "mqtt_client.h"
#define MQTT_TOPIC "iot/esp32-01/telemetry/dht"

static const char *TAG = "Project: NodeMCU-32S-Iot";

static esp_mqtt_client_handle_t g_mqtt = NULL;
static volatile bool g_mqtt_connected = false;

void DHT_task(void *pvParameter)
{
    setDHTgpio(GPIO_NUM_25);
    ESP_LOGI(TAG, "Starting DHT Task\n\n");

    while (1)
    {
        ESP_LOGI(TAG, "=== Reading DHT ===\n");
        int ret = readDHT();

        errorHandler(ret);

        float hum = getHumidity();
        float tmp = getTemperature();
        ESP_LOGI(TAG, "Hum: %.1f Tmp: %.1f", hum, tmp);

        char ts[32];
        time_t now = time(NULL);
        struct tm tm_utc;
        gmtime_r(&now, &tm_utc);
        strftime(ts, sizeof(ts), "%Y-%m-%dT%H:%M:%SZ", &tm_utc);

        char payload[160];
        int n = snprintf(payload, sizeof(payload),
                         "{\"ts\":\"%s\",\"temp_c\":%.2f,\"hum_pct\":%.2f,\"seq\":%u}",
                         ts, tmp, hum, seq++);

        if (g_mqtt && g_mqtt_connected && n > 0) {
            int msg_id = esp_mqtt_client_publish(
                g_mqtt, MQTT_TOPIC, payload, 0,
                /*QoS*/1, /*retain*/0);
            ESP_LOGI(TAG, "MQTT publish [%s] id=%d payload=%s", MQTT_TOPIC, msg_id, payload);
        } else {
            ESP_LOGW(TAG, "MQTT not connected, skip publish");
        }     

        // The interval of whole process must be beyond 2 seconds !!
        vTaskDelay(2000 / portTICK_PERIOD_MS);
    }
}

static void mqtt_event_handler(void *args, esp_event_base_t base, int32_t id, void *data) {
    esp_mqtt_event_handle_t e = (esp_mqtt_event_handle_t)data;
    switch (id) {
        case MQTT_EVENT_CONNECTED:
            g_mqtt_connected = true;
            ESP_LOGI(TAG, "MQTT connected");
            break;
        case MQTT_EVENT_DISCONNECTED:
            g_mqtt_connected = false;
            ESP_LOGW(TAG, "MQTT disconnected");
            break;
        default:
            break;
    }
}

static void mqtt_start(void) {
    const esp_mqtt_client_config_t cfg = {
        .broker.address.uri = CONFIG_BROKER_URL,
        .session.protocol_ver = MQTT_PROTOCOL_V_5,
        .network.disable_auto_reconnect = true,
    };
    g_mqtt = esp_mqtt_client_init(&cfg);
    esp_mqtt_client_register_event(g_mqtt, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(g_mqtt);
}



void app_main()
{
    ESP_LOGI(TAG, "Startup...");
    ESP_LOGI(TAG, "Free memory: %" PRIu32 " bytes", esp_get_free_heap_size());



    esp_log_level_set("*", ESP_LOG_INFO);
    esp_log_level_set("mqtt_client", ESP_LOG_VERBOSE);
    esp_log_level_set("mqtt_example", ESP_LOG_VERBOSE);

    ESP_ERROR_CHECK(nvs_flash_init());
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    ESP_ERROR_CHECK(example_connect()); 

    mqtt_start();
    xTaskCreate(&DHT_task, "DHT_task", 2048, NULL, 5, NULL);
}

