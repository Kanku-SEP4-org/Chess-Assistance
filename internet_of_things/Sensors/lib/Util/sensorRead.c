#include "sensorRead.h"
#include "dht11.h"
#include "communication.h"
#include <stdio.h>
#include <stddef.h>

void get_and_report_temperature(void) {
    uint8_t h_int, h_dec, t_int, t_dec;

    // Call the temperature and humidity driver
    if (dht11_get(&h_int, &h_dec, &t_int, &t_dec) == DHT11_OK) {
        // Clear, consistent output for the C# app
       char buffer[50];
        sprintf(buffer,"TEMP:%d.%d\n", t_int, t_dec);
        transmit_data(buffer);
    } else {
        transmit_data("ERROR:DHT11_READ_FAIL\n");
    }
}

void get_and_report_temp_json(void) {
    uint8_t h_int, h_dec, t_int, t_dec;

    if (dht11_get(&h_int, &h_dec, &t_int, &t_dec) == DHT11_OK) {
        // escaped quotes \" to create a valid JSON string
        char buffer[50];
        sprintf(buffer, "{\"temperature\": %d.%d}", 
                t_int, t_dec);
        transmit_data(buffer);
    } else {
        transmit_data("{\"error\": \"DHT11_READ_FAIL\"}\n");
    }
}

void get_and_report_humidity(void) {
    uint8_t h_int, h_dec, t_int, t_dec;

    // Call the temperature and humidity driver
    if (dht11_get(&h_int, &h_dec, &t_int, &t_dec) == DHT11_OK) {
        // Clear, consistent output for the C# app
        char buffer[50];
        sprintf(buffer,"HUM:%d.%d\n", h_int, h_dec);
        transmit_data(buffer);
    } else {
        transmit_data("ERROR:DHT11_READ_FAIL\n");
    }
}

void get_and_report_hum_json(void) {
    uint8_t h_int, h_dec, t_int, t_dec;

    if (dht11_get(&h_int, &h_dec, &t_int, &t_dec) == DHT11_OK) {
        // We use escaped quotes \" to create a valid JSON string
        char buffer[100];
        sprintf(buffer, "{\"humidity\": %d.%d}\n", 
                h_int, h_dec);
        transmit_data(buffer);
    } else {
        transmit_data("{\"error\": \"DHT11_READ_FAIL\"}\n");
    }
}