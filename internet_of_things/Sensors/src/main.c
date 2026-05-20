#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdio.h>
#include "uart_stdio.h"

#include "services/sensorRead.h" // access interface
#include "light.h"
#include "services/communication.h"

#include "wifi.h" // Include WiFi driver
#include "wifi_config.h"
#include "soil.h"
#define USE_WIFI_COMM 0 // Change this to 1 when ready to use WiFi

int main(void) {
    char input; // has to be one character if using case switches
    
    uart_stdio_init(115200);

    // WiFi Setup (Future-Proofing)
    #if USE_WIFI_COMM
        wifi_init();
        printf("[WIFI] Waiting for module...\n");
        delay(4000);

        // check if wifi responsive
        printf("[WIFI] Sending AT...\n");
        while (wifi_command_AT() != WIFI_OK)
        {
            delay(1000);
        }
        printf("[WIFI] Module OK\n");

        // disable echo
        wifi_command_disable_echo();

        // set mode to connecting to an access point
        wifi_command_set_mode_to_1();


        // use credentials provided in wifi_config.h
        printf("[WIFI] Connecting to %s...\n", WIFI_SSID);
        while (wifi_command_join_AP(WIFI_SSID, WIFI_PASS) != WIFI_OK)
        {
            printf("[WIFI] Retrying...\n");
            delay(1000);
        }
        printf("[WIFI] Connected\n");

        wifi_command_set_to_single_Connection();
    #endif
    sei();

    //initialize ADC sensors
    ADC_Error_t light = light_init();
    ADC_Error_t water = soil_init(ADC_PK0);

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

            default:
                transmit_data("Invalid input. Please enter 1 - 4.\n");
                break;
            }
        }
    }
}