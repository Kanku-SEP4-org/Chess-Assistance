/***********************************************
 * pir.c
 *  PIR sensor implementation
 *  Author:  Erland Larsen
 *  Date:    2026-01-30
 *  Project: SPE4_API
 **********************************************/
#include "pir.h"
#include <avr/io.h>
#include <stddef.h>
#include <avr/interrupt.h>


static pir_callback_t pir_callback = NULL;

#ifndef WINDOWS_TEST
ISR(INT2_vect) 
{
    pir_callback();
}
#endif

void pir_init(pir_callback_t callback) 
{
    // Set Port-bit PD2 as input.
    DDRD &= ~(1 << PD2);

    if (callback != NULL)           // Check if Interrupts should be used
    {
        // Enable interrupt
        EICRA |= (1 << ISC20);      // Set INT2 to trigger on any edge
        EIMSK |= (1 << INT2);       // Enable external interrupt INT2

        // Set the callback
        pir_callback = callback;
    }
}

pir_state_t pir_get_state(void)
{
    return (PIND & (1 << PD2)) ? PIR_MOTION_DETECTED : PIR_NO_MOTION;
}
