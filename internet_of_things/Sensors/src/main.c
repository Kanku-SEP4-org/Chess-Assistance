/*****************************************************************************
 * main.c
 *  Main application file for the IoT hardware drivers demo.
 *  This file initializes all the hardware drivers and demonstrates their
 *  functionality.
 *  Push button 2 on the shield during reset to enter continious sensor
 *  reading mode. Otherwise the program will run an interactive demo that
 *  allows you to test each driver individually by sending commands over UART.
 *  See interactive.c for details.
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-03-17
 *  Project: SPE4_API
 *****************************************************************************/
#include <avr/io.h>
#include <util/delay.h>
#include <avr/interrupt.h>
#include <stdio.h>
#include "interactive.h"
#include "button.h"
#include "uart_stdio.h"
#include "led.h"
#include "pir.h"
#include "display.h"
#include "wifi.h"
#include "button.h"
#include "buzzer.h"
#include "dht11.h"
#include "proximity.h"
#include "servo.h"
#include "adc.h"
#include "light.h"
#include "soil.h"
#include "tone.h"
//#include "adxl345.h"
#include "timer.h"
//#include "adxl345.h"


uint8_t humidity_integer, humidity_decimal, temperature_integer, temperature_decimal;
static int8_t _led_no = 0;
//static int16_t _x, _y, _z;

void timer_callback(uint8_t id)
{
    led_toggle((_led_no%4) + 1); // Toggle LEDs in sequence 1-4
    _led_no++;
}

int main(void)
{
    led_init();
    button_init();
    display_init();
    proximity_init();
    light_init();
    soil_init(ADC_PK0);
    pir_init(pir_callback);
   // tone_init();
    wifi_init();
    servo_init(PWM_NORMAL);
    //adxl345_init();

    if (UART_OK != uart_stdio_init(115200))
    {
        led_on(4); // Turn on LED4 to indicate error
        while (1)
            ;
    }
    sei(); // Enable global interrupts
    printf("VIA UNIVERSITY COLLEGE SEP4 IoT Hardware DRIVERS DEMO\n");
    if(!button_get(2))
    {
        interactive_demo();
    }

    timer_create_sw(timer_callback, 1000); // Create a timer that toggles an LED every 1 second

    tone_play_starwars();

    // Test servo by sweeping from -90 to +90 degrees and back
    servo_start();
    for(int i=-90; i<=90; i+=10)
    {
        servo_setAngle(PWM_A, (int8_t)i);
        printf("Servo set to %d degrees.\n", i);
        _delay_ms(100);
    }
    servo_stop();

    // Test WiFi by sending AT command and printing response
    if(WIFI_OK == wifi_command_AT())
    {
        printf("WiFi module responded to AT command.\n");
    }
    else
    {
        printf("WiFi module did not respond to AT command.\n");
    }

    buzzer_beep();

    // Continuous sensor readings
    while (1)
    {
        dht11_get(&humidity_integer, &humidity_decimal, &temperature_integer, &temperature_decimal);
        printf("Temperature: %d.%d°C, Humidity: %d.%d%%", temperature_integer, temperature_decimal, humidity_integer, humidity_decimal);
        display_setDecimals(1);
        display_int(temperature_integer*10 + temperature_decimal);
        printf(" Light: %d ", light_measure_raw());
        printf(" Soil: %d", soil_measure_raw(ADC_PK0));
        printf(" Distance: %d mm", proximity_measure());
        // adxl345_read_xyz(&_x, &_y, &_z);
        // printf(" Accel: X=%d Y=%d Z=%d", _x, _y, _z);
        printf(" Motion: %s", (pir_get_state() == PIR_NO_MOTION) ? "No" : "Yes");
       puts("");
        _delay_ms(2000);
    }
}
