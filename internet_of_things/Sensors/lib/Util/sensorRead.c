#include "sensorRead.h"
#include "dht11.h"
#include "light.h"
#include "communication.h"
#include <stdio.h>
#include <stddef.h>

void get_and_report_temperature(void) {
    uint8_t h_int, h_dec, t_int, t_dec;

    // Call the temperature and humidity driver
    if (dht11_get(&h_int, &h_dec, &t_int, &t_dec) == DHT11_OK) {
        // Clear, consistent output for the C# app
       char buffer[50];
        sprintf(buffer,"TEMP:%d.%d\n", t_int, t_dec); //TEMP:20.5
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
        sprintf(buffer, "{\"temperature\": %d.%d}", //{"temperature":20.5}
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

void get_and_report_light(ADC_Error_t light_sensor){
    char buffer[50];

    if(light_sensor == ADC_OK){
        uint16_t light_level = light_measure_raw();

        sprintf(buffer,"LIG:%d\n", light_level);
    }else if (light_sensor == ADC_ERROR_INVALID_CHANNEL){
        sprintf(buffer, "Invalid channel for light sensor");
    }else if (light_sensor == ADC_ERROR_INVALID_REFERENCE){
        sprintf(buffer, "Invalid reference for light sensor");
    }
    
    transmit_data(buffer);
}

void get_and_report_light_json(ADC_Error_t light_sensor){
    char buffer[100];

    if(light_sensor == ADC_OK){
        uint16_t light_level = light_measure_raw();

        sprintf(buffer,"{\"light\":%d}\n", light_level);
    }else if (light_sensor == ADC_ERROR_INVALID_CHANNEL){
        sprintf(buffer, "Invalid channel for light sensor");
    }else if (light_sensor == ADC_ERROR_INVALID_REFERENCE){
        sprintf(buffer, "Invalid reference for light sensor");
    }

    transmit_data(buffer);
}