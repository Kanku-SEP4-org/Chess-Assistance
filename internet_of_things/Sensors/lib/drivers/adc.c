/***********************************************
 * adc.c
 *  Implementation of the Analog to Digital Converter (ADC) driver.
 *  Functions for reading values from the ADC channels on the shield.
 *  ADC channels are connected to the PK0-PK7 pins on the microcontroller.
 *
 *  Author:  Erland Larsen
 *  Date:    2026-03-10
 *  Project: SPE4_API
 **********************************************/

#include "adc.h"
#include <avr/io.h>
#include <stdbool.h>

// Static variables to track initialized channels and their references
static bool adc_hw_initialized = false;
static bool channel_initialized[8] = {false};
static ADC_Reference_t channel_references[8] = {ADC_REF_5V, ADC_REF_5V, ADC_REF_5V, ADC_REF_5V, ADC_REF_5V, ADC_REF_5V, ADC_REF_5V, ADC_REF_5V};

// Initialize the ADC. Sets up necessary pins and reference voltage.
// You can call this function multiple times to initialize multiple
// channels if needed.
// Parameters: channel - the ADC channel to initialize. Chose ADC_PK0 if you
//                       have connected a sensor to PK0 pin on the MCU.
//             reference - the reference voltage to use.
// Return: ADC_Error_t indicating success or the type of error that occurred.
ADC_Error_t adc_create(ADC_Channel_t channel, ADC_Reference_t reference)
{
    // Validate if channel is available and not already in use
    if (channel < ADC_PK0 || channel > ADC_PK7 || (channel_initialized[channel] == true))
    {
        return ADC_ERROR_INVALID_CHANNEL;
    }

    // Validate reference
    if (reference < ADC_REF_5V || reference > ADC_REF_1V1)
    {
        return ADC_ERROR_INVALID_REFERENCE;
    }

    // Initialize ADC hardware if not already done
    if (!adc_hw_initialized)
    {
        // Enable ADC, set prescaler to 128 for 10-bit resolution
        ADCSRA = (1 << ADEN) | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0);

        // Enable channels ADC8-ADC15 (PK0-PK7) by setting MUX5 bit in ADCSRB
        ADCSRB |= (1 << MUX5);

        // Disable digital input buffers on ADC pins to reduce power consumption
        DIDR2 |= (1 << channel);
        
        adc_hw_initialized = true;
    }

    // Store the reference for this channel
    channel_references[channel] = reference;
    channel_initialized[channel] = true;

    return ADC_OK;
}

// Read the current value from the ADC channel. Returns a value between 0 and 1023 (10-bit resolution).
// Returns UINT16_MAX if an error occurs (e.g. invalid channel or reference).
// NOTE: This function is blocking. Conversion time is typically around 200 microseconds.
//       ADC Clock is set to F_CPU/128 to obtain 10-bit resolution. Make sure to call adc_create() before calling this function.
uint16_t adc_measure(ADC_Channel_t channel)
{
    // Validate channel
    if (channel < ADC_PK0 || channel > ADC_PK7)
    {
        return UINT16_MAX;
    }

    // Check if channel is initialized
    if (!channel_initialized[channel])
    {
        return UINT16_MAX;
    }

    // Set the ADC channel and reference voltage
    ADMUX = (channel_references[channel] << REFS0) | (channel & 0x07);

    // Start the conversion
    ADCSRA |= (1 << ADSC);

    // Wait for the conversion to complete
    while (ADCSRA & (1 << ADSC));

    // Return the ADC value
    return ADC;
}
