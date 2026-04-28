#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdio.h>
#include "uart_stdio.h"

#include "sensorRead.h" // access interface
#include "communication.h"

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
                get_and_report_temp_json();
                break;
            case '4':
                get_and_report_hum_json();
                break;

            default:
                transmit_data("Invalid input. Please enter 1, 2, 3, or 4.\n");
                break;
            }
        }
    }
}