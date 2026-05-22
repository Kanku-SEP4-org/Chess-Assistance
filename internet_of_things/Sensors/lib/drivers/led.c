/***********************************************
 * led.c
 *  LED implementation. Control functions for the four LEDs on the shield.
 *  * Note: Uses software timers (timer.c) for blinking functionality.
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-01-30
 *  Project: SPE4_API
 **********************************************/
#include "led.h"
#include <avr/io.h>
#include "timer.h"

#define LED_BIT1 PB7
#define LED_BIT2 PB6
#define LED_BIT3 PB5
#define LED_BIT4 PB4
#define LED_MAX_LEDS 4
#define LED_DDR DDRB
#define LED_PORT PORTB

static int8_t led_timer_id[LED_MAX_LEDS] = {0};

void led_init(void)
{
  LED_DDR |= (1<<LED_BIT1)|(1<<LED_BIT2)|(1<<LED_BIT3)|(1<<LED_BIT4); //Output
  LED_PORT |= (1<<LED_BIT1)|(1<<LED_BIT2)|(1<<LED_BIT3)|(1<<LED_BIT4); //turnOff (Active Low)
}

led_status_t led_on(int8_t led_no)
{ // Active low
    switch (led_no)
    {
    case 1:
        LED_PORT &= ~((1 << LED_BIT1));
        break;
    case 2:
        LED_PORT &= ~((1 << LED_BIT2));
        break;
    case 3:
        LED_PORT &= ~((1 << LED_BIT3));
        break;
    case 4:
        LED_PORT &= ~((1 << LED_BIT4));
        break;
    default:
        return LED_ERROR_INVALID_LED_NO;
    }
    return LED_OK;
}

led_status_t led_off(int8_t led_no)
{ // active low
    switch (led_no)
    {
    case 1:
        if(led_timer_id[0] != 0)
        {
            timer_delete(led_timer_id[0]);
            led_timer_id[0] = 0;
        }
        LED_PORT |= ((1 << LED_BIT1));
        break;
    case 2:
        if(led_timer_id[1] != 0)
        {
            timer_delete(led_timer_id[1]);
            led_timer_id[1] = 0;
        }
        LED_PORT |= ((1 << LED_BIT2));
        break;
    case 3:
        if(led_timer_id[2] != 0)
        {
            timer_delete(led_timer_id[2]);
            led_timer_id[2] = 0;
        }
        LED_PORT |= ((1 << LED_BIT3));
        break;
    case 4:
        if(led_timer_id[3] != 0)
        {
            timer_delete(led_timer_id[3]);
            led_timer_id[3] = 0;
        }
        LED_PORT |= ((1 << LED_BIT4));
        break;
    default:
        return LED_ERROR_INVALID_LED_NO;
    }
    return LED_OK;
}

led_status_t led_toggle(int8_t led_no)
{
    switch (led_no)
    {
    case 1:
        LED_PORT ^= ((1 << LED_BIT1));
        break;
    case 2:
        LED_PORT ^= ((1 << LED_BIT2));
        break;
    case 3:
        LED_PORT ^= ((1 << LED_BIT3));
        break;
    case 4:
        LED_PORT ^= ((1 << LED_BIT4));
        break;
    default:
        return LED_ERROR_INVALID_LED_NO;
    }
    return LED_OK;
}

static void led_blink_callback(uint8_t id)
{
    for (int8_t led_no = 0; led_no < LED_MAX_LEDS; led_no++)
    {
        if (led_timer_id[led_no] == id)
        {
            led_toggle(led_no+1);
            break;
        }
    }
}

led_status_t led_blink(int8_t led_no, uint16_t period_ms)
{
    if(led_no < 1 || led_no > LED_MAX_LEDS)
    {
        return LED_ERROR_INVALID_LED_NO;
    }
    if (period_ms >= 10 && period_ms <= 60000)
    {
        if ((led_timer_id[led_no - 1] = timer_create_sw(led_blink_callback, period_ms / 2)) < 0)
        {
            return LED_ERROR_NO_RESOURCES;
        }
    }
    else
    {
        return LED_ERROR_INVALID_PERIOD;
    }
    return LED_OK;
}
