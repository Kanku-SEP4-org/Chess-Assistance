#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdio.h>
#include <util/delay.h>

#include "uart_stdio.h"

#include "services/sensorRead.h" // access interface
#include "services/communication.h"

#include "light.h"
#include "soil.h"
#include "co2.h"

#include "wifi.h" // Include WiFi driver
#define USE_WIFI_COMM 0 // Change this to 1 when ready to use WiFi

int main(void) {
    char input; // has to be one character if using case switches
    
    uart_stdio_init(115200);

    // WiFi Setup (Future-Proofing)
    #if USE_WIFI_COMM
        wifi_init();
        // Add your credentials here when ready
        // wifi_command_join_AP("SSID", "PASSWORD"); 
        // wifi_command_create_TCP_connection("192.168.1.XX", 23, NULL, NULL);
    #endif
    sei();

    //initialize ADC sensors
    ADC_Error_t light = light_init();
    ADC_Error_t water = soil_init(ADC_PK0);
    if (co2_init(co2_incoming_data_handler) == CO2_OK) {
        // CO2 Initialized successfully!
        transmit_data("CO2:OK\n");
    } else {
        transmit_data("CO2:INIT_FAIL\n");
    }


    while (1) {
        // Wait for a prompt from the PC/RabbitMQ Producer
        //" %c" allows us to skip any whitespace characters, including newlines (note the space before %c)
        if (scanf(" %c", &input) == 1) {
            switch (input)
            {
            case '1':
                get_and_report_temperature();
                break;
            case '2':
                get_and_report_humidity();
                break;
            case '3':
                get_and_report_light(light);
                break;
            case '4':
                get_and_report_water(water);
                break;
            case '5':
                //your code here
                transmit_data("Not yet implemented");
                break;
            case '6':
                co2_start_measure();
                get_and_report_co2();
                break;

            default:
                transmit_data("Invalid input. Please enter 1 - 6.\n");
                break;
            }
        }
    }
}