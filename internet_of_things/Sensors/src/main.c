#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdio.h>

#include "uart_stdio.h"

#include "services/sensorRead.h" // access interface
#include "services/communication.h"

#include "light.h"
#include "soil.h"
#include "co2.h"

//#include "wifi.h" // Include WiFi driver
//#define USE_WIFI_COMM 0 // Change this to 1 when ready to use WiFi
//no longer needed here

int main(void) {
    char input; // has to be one character if using case switches
    // Buffer to hold incoming serial commands non-blockingly (replaces input)
    char serial_input_buffer[96] = {0};

    uart_stdio_init(115200);

    //new unified communication control layer
    communication_init();
    communication_dev_autoconnect("ana"); // Temporary auto-connect for development, can be removed when wifi_connect() is ready for user setting

    // WiFi Setup (deprecated)
    //#if USE_WIFI_COMM
    //    wifi_init();
        //dev_connect("ana"); // Temporary function to connect to wifi without user input, can be removed when wifi_connect() is ready
        // Add your credentials here when ready
        // wifi_command_join_AP("SSID", "PASSWORD"); 
        // wifi_command_create_TCP_connection("192.168.1.XX", 23, NULL, NULL);
    //#endif

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
        communication_poll_network(); //process bg network events without blocking
        // Wait for a prompt from the PC/RabbitMQ Producer
        //" %c" allows us to skip any whitespace characters, including newlines (note the space before %c)

        // 2. Non-blocking check: See if sensor_client_c has sent a full command line
        uint16_t bytes_read = gets_nonblocking(serial_input_buffer, sizeof(serial_input_buffer));

       // if (scanf(" %c", &input) == 1) {
        //no longer using input
        if (bytes_read > 0) {
            // The first character is the switch case menu command identifier
            char command = serial_input_buffer[0];

            switch (command)
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
                case '7':
                    // Pass the string *starting after the '7'* directly to the Wi-Fi connector.
                    // points cleanly to "MySSID,Pass,192.168.1.1"
                    //!!! make sure they are separated by commas, to avoid confussions thanks to IP nature, for example
                    communication_connect_wifi(&serial_input_buffer[1]);
                    break;


                default:
                    transmit_data("Invalid input. Please enter 1 - 7.\n");
                    break;
                }
        }
    }
}