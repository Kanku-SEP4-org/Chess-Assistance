#include "sensorRead.h"
#include "dht11.h"
#include "light.h"
#include "soil.h"
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

void get_and_report_light(ADC_Error_t light_sensor){
    char buffer[50];

    if(light_sensor == ADC_OK){
        uint16_t light_level = light_measure_raw();

        sprintf(buffer,"LIG:%d\n", light_level);
    }else if (light_sensor == ADC_ERROR_INVALID_CHANNEL){
        sprintf(buffer, "ERROR:ADC_ERROR_INVALID_CHANNEL");
    }else if (light_sensor == ADC_ERROR_INVALID_REFERENCE){
        sprintf(buffer, "ERROR:ADC_ERROR_INVALID_REFERENCE");
    }
    
    transmit_data(buffer);
}

void get_and_report_water(ADC_Error_t water_sensor){
    char buffer[50];

    if(water_sensor == ADC_OK){
        uint16_t water_level = soil_measure_raw(ADC_PK0);

        sprintf(buffer,"WAT:%d\n", water_level);
    }else if (water_sensor == ADC_ERROR_INVALID_CHANNEL){
        sprintf(buffer, "ERROR:ADC_ERROR_INVALID_CHANNEL");
    }else if (water_sensor == ADC_ERROR_INVALID_REFERENCE){
        sprintf(buffer, "ERROR:ADC_ERROR_INVALID_REFERENCE");
    }
    
    transmit_data(buffer);
}