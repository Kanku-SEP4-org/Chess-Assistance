#include "sensorRead.h"
#include "dht11.h"
#include <stdio.h>
#include <stddef.h>

void get_and_report_temperature(void) {
    uint8_t h_int, h_dec, t_int, t_dec;

    // Call the temperature and humidity driver
    if (dht11_get(&h_int, &h_dec, &t_int, &t_dec) == DHT11_OK) {
        // Clear, consistent output for the C# app
        printf("TEMP:%d.%d\n", t_int, t_dec);
    } else {
        printf("ERROR:DHT11_READ_FAIL\n");
    }
}

void get_and_report_temp_json(void) {
    uint8_t h_int, h_dec, t_int, t_dec;

    if (dht11_get(&h_int, &h_dec, &t_int, &t_dec) == DHT11_OK) {
        // We use escaped quotes \" to create a valid JSON string
        printf("{\"temperature\": %d.%d, \"humidity\": %d.%d}\n", 
                t_int, t_dec, h_int, h_dec);
    } else {
        printf("{\"error\": \"DHT11_READ_FAIL\"}\n");
    }
}

void get_and_report_humidity(void) {
    uint8_t h_int, h_dec, t_int, t_dec;

    // Call the temperature and humidity driver
    if (dht11_get(&h_int, &h_dec, &t_int, &t_dec) == DHT11_OK) {
        // Clear, consistent output for the C# app
        printf("HUM:%d.%d\n", h_int, h_dec);
    } else {
        printf("ERROR:DHT11_READ_FAIL\n");
    }
}

void get_and_report_hum_json(void) {
    uint8_t h_int, h_dec, t_int, t_dec;

    if (dht11_get(&h_int, &h_dec, &t_int, &t_dec) == DHT11_OK) {
        // We use escaped quotes \" to create a valid JSON string
        printf("{\"temperature\": %d.%d, \"humidity\": %d.%d}\n", 
                t_int, t_dec, h_int, h_dec);
    } else {
        printf("{\"error\": \"DHT11_READ_FAIL\"}\n");
    }
}