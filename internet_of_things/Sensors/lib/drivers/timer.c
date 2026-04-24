/***********************************************
 * timer.c
 *  Software timer implementation. Supports up to TIMER_MAX_TIMERS concurrent 
 *  timers with millisecond resolution.
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-03-06
 *  Project: SPE4_API
 **********************************************/
#include "timer.h"
#include <avr/io.h>
#include <avr/interrupt.h>
#include <stddef.h>

typedef struct {
    void (*callback)(uint8_t id);
    uint16_t interval_ms;
    uint16_t elapsed_ms;
    int8_t active;
} software_timer_t;

static software_timer_t software_timers[TIMER_MAX_TIMERS];
static int8_t timer_count = 0;

int8_t timer_create_sw(void (*callback)(uint8_t id), uint16_t interval_ms)
{
    if (interval_ms == 0 || interval_ms > TIMER_MAX_INTERVAL_MS) 
    {
        return TIMER_ERROR_INVALID_INTERVAL;
    }

    if(timer_count >= TIMER_MAX_TIMERS) 
    {
        return TIMER_ERROR_NO_RESOURCES;
    }

    if(callback == NULL) 
    {
        return TIMER_ERROR_NO_RESOURCES;
    }

    // Initialize Timer0 if this is the first timer
    if(timer_count == 0)
    {
        // Set up Timer0 for CTC mode (Clear Timer on Compare Match)
        TCCR0A |= (1 << WGM01);

        // Set the compare value for 1 ms interrupt
        OCR0A = (int8_t)(F_CPU / 64UL / 1000UL) - 1;

        // Enable the Timer0 compare match A interrupt
        TIMSK0 |= (1 << OCIE0A);

        // Set the prescaler to 64
        TCCR0B |= (1 << CS01) | (1 << CS00);
    }

    // Find an empty slot
    for (int8_t i = 0; i < TIMER_MAX_TIMERS; i++) 
    {
        if (software_timers[i].callback == NULL) 
        {
            software_timers[i].callback = callback;
            software_timers[i].interval_ms = interval_ms;
            software_timers[i].elapsed_ms = 0;
            software_timers[i].active = 1;
            timer_count++;
            return i + 1; // Timer IDs are 1-based
        }
    }   

    return TIMER_ERROR_NO_RESOURCES;
}

int8_t timer_get_state(int8_t timer_id)
{
    if(timer_id > 0 && timer_id <= TIMER_MAX_TIMERS) 
    {
        return software_timers[timer_id - 1].active;
    }
    return TIMER_INVALID_ID;
}

int8_t timer_pause(int8_t timer_id)
{
    if(timer_id > 0 && timer_id <= TIMER_MAX_TIMERS) 
    {
        software_timers[timer_id - 1].active = 0;
        return TIMER_OK;
    }
    return TIMER_INVALID_ID;
}

int8_t timer_resume(int8_t timer_id)
{
    if(timer_id > 0 && timer_id <= TIMER_MAX_TIMERS) 
    {
        software_timers[timer_id - 1].active = 1;
        software_timers[timer_id - 1].elapsed_ms = 0; // Reset elapsed time
        return TIMER_OK;
    }
    return TIMER_INVALID_ID;
}

int8_t timer_delete(int8_t timer_id)
{
    if(timer_id > 0 && timer_id <= TIMER_MAX_TIMERS) 
    {
        software_timers[timer_id - 1].callback = NULL;
        software_timers[timer_id - 1].interval_ms = 0;
        software_timers[timer_id - 1].elapsed_ms = 0;
        software_timers[timer_id - 1].active = 0;
        timer_count--;
        return TIMER_OK;
    }
    return TIMER_INVALID_ID;
}

ISR(TIMER0_COMPA_vect)
{
    for (int8_t i = 0; i < TIMER_MAX_TIMERS; i++) 
    {
        if (software_timers[i].callback != NULL && software_timers[i].active) 
        {
            software_timers[i].elapsed_ms++;
            if (software_timers[i].elapsed_ms >= software_timers[i].interval_ms) 
            {
                software_timers[i].elapsed_ms = 0;
                software_timers[i].callback(i + 1); // Call with timer ID
            }
        }
    }
}
