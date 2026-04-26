/***********************************************
 * led.h
 *  LED interface. Control functions for the four LEDs on the shield.
 *  * Note: Uses software timers (timer.c) for blinking functionality.
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-01-30
 *  Project: SPE4_API
 **********************************************/
#pragma once
#include <stdint.h>

typedef enum {
    LED_OK = 0,
    LED_ERROR_INVALID_LED_NO = -1,
    LED_ERROR_INVALID_PERIOD = -2, 
    LED_ERROR_NO_RESOURCES = -3
} led_status_t;

// initialize the LED’s to be output. 
void led_init(void);

// Turn on LED. Valid numbers [1..4]
led_status_t led_on(int8_t led_no);

// Turn off LED. Valid numbers [1..4]
led_status_t led_off(int8_t led_no);
 
// Toggle LED state. Valid numbers [1..4]
led_status_t led_toggle(int8_t led_no);

// Blink LED number [1..4], with period given in ms. 
// Valid period range [10..60000]
led_status_t led_blink(int8_t led_no, uint16_t period_ms);
