/***********************************************
 * proximity.c
 *  Proximity sensor implementation. Supports HC-SR04 ultrasonic sensor
 *  using Timer 5 for timing the echo pulse.
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-03-06
 *  Project: SPE4_API
 **********************************************/
#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>
#include <stdint.h>
#include <stdbool.h>
#include "proximity.h"


//Trigger
#define DDR_Trig  DDRL
#define P_Trig    PL7
#define PORT_trig PORTL

//Echo
#define PIN_Echo  PINL
#define P_Echo    PL6

volatile static bool _timeout = false;
static uint16_t _last_distance = 0;

uint16_t proximity_get_distance()
{
    return _last_distance;
}

void proximity_init()
{
    // Timer 5 init
    TCCR5A = 0;
    TCCR5B = (1<<WGM52); // CTC mode
    OCR5A = 12500;  // 50 ms
    TIMSK5 |= (1<<OCIE5A);  // Enable Interrupt for Timeout

    //Trigger
    DDR_Trig |= (1 << P_Trig);
}

uint16_t proximity_measure()
{
    uint32_t cnt;
    bool done;

    // Send Trigger pulse, 10us to start measurement
    PORT_trig |= (1 << P_Trig);
    _delay_us(10);
    PORT_trig &= ~(1 << P_Trig);

    cnt = 0;
    done = false;
    _timeout = false;
    TCCR5B |= (1<<CS51) | (1<<CS50); // Start Timer. F_CPU/64

    // Wait for start of Echo pulse. Timeout if no connection
    while(!_timeout && !(PIN_Echo & (1 << P_Echo)))
    {
       ; // Do nothing!
    }

    // Measure Echo pulse duration
    TCNT5 = 0;  // Reset time counter
    while (!_timeout && !done)
    {
        // When P_Echo goes low again we have a measurement
        if(0 == (PIN_Echo & (1 << P_Echo)))
        {
            cnt = (uint32_t)TCNT5;
            done = true;
        }
    }
    if(_timeout)
    {
        _last_distance = UINT16_MAX;
    }
    else
    {
        _last_distance = (uint16_t)(cnt * 343ul / 500ul); // Distance in mm. See note below.
    }
    TCCR5B &= ~((1<<CS51) | (1<<CS50)); // Stop Timer
    return _last_distance;

    /*
    The number of clock cycles it took is the prescaler (here 64) times the counter value.
    64*cnt
    To get the time, it should be divided with the clock frequency which is 16000000Hz
    cnt*64/16000000
    This is the time it takes for the ultrasound signal to travel to the target and back.
    To get the time to the target, this time should be divided by 2.
    time to target = cnt*64/(16000000*2)
    To get the distance we should multiply with the speed of sound. This is 343m/s or 343000mm/s
    Distance = cnt*64/(16000000*2) * 343000
    To ensure that we keep the calculation in a nice uint16 range (no floating point in target), the
    constant that cnt should me multiplied with is calculated: 64/(16000000*2) * 343000 = 
    64/32000 * 343 = 1/500 * 343 = 343/500
    */
}

ISR(TIMER5_COMPA_vect)
{
    _timeout = true;
}