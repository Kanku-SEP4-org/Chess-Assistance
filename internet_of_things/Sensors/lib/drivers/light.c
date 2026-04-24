/***********************************************
 * light.c
 *  Implementation of the Light Sensor driver.
 *  Functions for the light sensor (KY-018).
 *  NOTE: The light sensor is connected to the ADC channel PK7 on the
 *        microcontroller and is a wrapper around the ADC functions.
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-03-10
 *  Project: SPE4_API
 **********************************************/
#include "adc.h"
#include <stdint.h>

// Initialize the light sensor. This is a wrapper around adc_create()
// for the specific channel and reference used by the light sensor.
// Returns ADC_Error_t indicating success or the type of error that occurred.
ADC_Error_t light_init()
{
    return adc_create(ADC_PK7, ADC_REF_5V);
}

// Read the current light level from the sensor.
// The KY-018 light sensor outputs a low value for bright light
// and a high value for darkness. To make it more intuitive, we invert
// the value so that low values = dark and high values = bright.
uint16_t light_measure_raw()
{
    uint16_t raw_value = adc_measure(ADC_PK7);
    if(raw_value > 1023) 
    {
        return raw_value; // Return error value
    }
    else
    {
        return 1023 - raw_value; // Invert the value for intuitive readings
    }
}
