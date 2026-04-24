#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdio.h>
#include "uart_stdio.h"

#include "sensorRead.h" // access interface

int main(void) {
    char input;
    
    uart_stdio_init(115200);
    sei();

    while (1) {
        // Wait for a prompt from the PC/RabbitMQ Producer
        if (scanf("%c", &input) == 1) {
            if (input == 't') {
                get_and_report_temperature();
            }
            if (input == 'h') {
                get_and_report_humidity();
            } //added since it's the same 'movement'
            //for json output
            if (input == 'tj') {
                get_and_report_temp_json();
            }
            if (input == 'hj') {
                get_and_report_hum_json();
            }
        }
    }
}