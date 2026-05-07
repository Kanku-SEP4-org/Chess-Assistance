#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdio.h>
#include "uart_stdio.h"

#include "sensorRead.h" // access interface
#include "communication.h"

#include "wifi.h" // Include WiFi driver
#include "uart_stdio.h"
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
        get_and_report_temp_json();
        _delay_ms(5000);
        
    }
}