#include <stdio.h>
#include <inttypes.h>
#include "sdkconfig.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_chip_info.h"
#include "esp_flash.h"
#include "esp_system.h"

/* New Include */
#include "DHT.h"

typedef struct{
    uint64_t time_ms;
    float temperature;
    float humidity;
} SensorData_T;

typedef struct {
    float tempOffset;
    float humidityOffset;
} CalibrationData_T;

// void app_main(void)
// {




// }