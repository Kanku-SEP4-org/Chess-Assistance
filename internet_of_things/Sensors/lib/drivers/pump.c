#include "pump.h"
#include <avr/io.h>

void pump_init(void)
{
    DDRC |= (1 << PC7);    // Set PC7 as output
    PORTC &= ~(1 << PC7);  // Ensure pump is off by default
}

void pump_start(void)
{
    PORTC |= (1 << PC7);   // HIGH = pump on
}

void pump_stop(void)
{
    PORTC &= ~(1 << PC7);  // LOW = pump off
}

bool pump_is_running(void)
{
    return (PORTC & (1 << PC7)) != 0;
}