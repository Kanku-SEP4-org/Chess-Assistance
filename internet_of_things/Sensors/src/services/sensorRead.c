#include "sensorRead.h"
#include "dht11.h"
#include "light.h"
#include "soil.h"
#include "communication.h"
#include "co2.h"
#include <stdio.h>
#include <stddef.h>
#include "pump.h"
#include <util/delay.h>
#include <avr/interrupt.h>

static volatile uint16_t latest_co2_ppm = 0; // Global variable to store the latest CO2 reading
//volatile to mark that it can change unexpectedly (16-bit can be corrupted by an interrupt, so this accounts for that)

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

void fill_and_report_done(void)
{
    //start pump, wait briefly, stop pump, then report done.
    //safe for relay testing without real pump power connected.
    pump_start();
    _delay_ms(2000);
    pump_stop();

    transmit_data("PUMP:DONE\n");
}

void co2_incoming_data_handler(uint16_t ppm) {
    latest_co2_ppm = ppm;
}

void get_and_report_co2(void) {
    
    char buffer[50];
    uint16_t co2_local_copy;
    uint8_t data_received = 0;

    for (int timeout = 0; timeout <15; timeout++) {
        // ATOMIC BLOCK: Guard the 16-bit multi-byte copy operation for safe reading
        cli(); // Clear Global Interrupts - stops the UART ISR from firing
        co2_local_copy = latest_co2_ppm; // Safe 2-byte read transaction
        sei(); // Re-enable Global Interrupts

        if (co2_local_copy > 0) {
            data_received = 1;
            break; // Exit the loop if we have valid data
        }
        _delay_ms(10);//giving the sensor time to read
    }
    //result handling
    if (data_received) {
        sprintf(buffer, "CO2:%u\n", co2_local_copy);
        transmit_data(buffer);
    } else {
        transmit_data("ERROR:CO2_READ_FAIL\n");
    }
    // ATOMIC BLOCK: Reset the global variable back to 0
    // so the next request starts with a clean slate.
    cli();
    latest_co2_ppm = 0;
    sei();
}
