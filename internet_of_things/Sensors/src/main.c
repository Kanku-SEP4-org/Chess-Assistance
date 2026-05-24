#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdio.h>
#include <util/delay.h>

#include "uart_stdio.h"
#include "services/sensorRead.h"
#include "services/communication.h"

#include "light.h"
#include "soil.h"
#include "co2.h"
#include "wifi.h"

// Hardware descriptor for the soil moisture sensor pin
static ADC_Error_t water_sensor_pin;
static ADC_Error_t light_sensor_pin;

/**
 * @brief Unified command processing center.
 * Evaluates instructions identically whether they originate from USB or Wi-Fi TCP.
 */
void process_system_command(char command, uint16_t total_bytes, const char* full_buffer) {
    // Filter out blank spacing arrays safely
    if (command == '\r' || command == '\n' || command == ' ') {
        return;
    }

    switch (command)
    {
        case '1':
            get_and_report_temperature();
            break;
        case '2':
            get_and_report_humidity();
            break;
        case '3':
            get_and_report_light(light_sensor_pin);
            break;
        case '4':
            get_and_report_water(water_sensor_pin);
            break;
        case '5': {
        //add function here
            transmit_data("Not implemented\n");
            break;
        }
        case '6':
            co2_start_measure();
            get_and_report_co2();
            break;
        case '7':
            if (total_bytes > 1) {
                // Pass the offset pointer safely bypassing token index 0
                // !!! message sent from server must be like:
                // 7SSID,PASSWORD,SERVER_IP
                communication_connect_wifi(&full_buffer[1]);
            } else {
                transmit_data("ERROR:MISSING_WIFI_CREDENTIALS\n");
            }
            break;

        default: {
            char unknown_msg[40];
            sprintf(unknown_msg, "Invalid input '%c'. Please enter 1 - 7.\n", command);
            transmit_data(unknown_msg);
            break;
        }
    }
}

int main(void) {
    char serial_input_buffer[96] = {0};

    uart_stdio_init(115200);
    sei(); // Enable background interrupt queues early

    communication_init();
    communication_dev_autoconnect("dev");

    // Flush any power-on junk characters out of your stdio buffer
    char boot_flush[32];
    _delay_ms(100);
    while(gets_nonblocking(boot_flush, sizeof(boot_flush)) > 0 || uart_read_byte(UART0_ID, (uint8_t*)boot_flush) == UART_OK);

    // Initialize ADC drivers
    light_sensor_pin = light_init();
    water_sensor_pin = soil_init(ADC_PK0);

    if (co2_init(co2_incoming_data_handler) == CO2_OK) {
        transmit_data("CO2_INIT:OK\n");
    } else {
        transmit_data("CO2_INIT:INIT_FAIL\n");
    }

    while (1) {
        // Continuous non-blocking background network polling processing
        communication_poll_network();

        // Non-blocking check: See if a command line arrived from the USB terminal link
        uint16_t bytes_read = gets_nonblocking(serial_input_buffer, sizeof(serial_input_buffer));

        if (bytes_read > 0) {
            // Process the USB input command locally
            process_system_command(serial_input_buffer[0], bytes_read, serial_input_buffer);
        }
    }
    return 0; //outside while loop so that the loop is constant but also main can still return 0
}