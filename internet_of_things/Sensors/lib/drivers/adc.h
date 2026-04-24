/***********************************************
 * adc.h
 *  Interface for the Analog to Digital Converter (ADC) driver. 
 *  Functions for reading values from the ADC channels on the shield.
 *  ADC channels are connected to the PK0-PK7 pins on the microcontroller.
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-03-10
 *  Project: SPE4_API
 **********************************************/
#pragma once

typedef enum
{
    ADC_PK0 = 0,
    ADC_PK1 = 1,
    ADC_PK2 = 2,
    ADC_PK3 = 3,
    ADC_PK4 = 4,
    ADC_PK5 = 5,    // NOTE: PK5 is shared with the accelerometer INT1 pin, so it may not work if the accelerometer is mounted
    ADC_PK6 = 6,    // NOTE: PK6 is shared with the accelerometer INT2 pin, so it may not work if the accelerometer is mounted
    ADC_PK7 = 7
} ADC_Channel_t;

typedef enum
{
    ADC_REF_5V = 1,   // Use VCC as reference voltage (default)
    ADC_REF_1V1 = 2,  // Use internal reference voltage (1.1V)
    ADC_REF_2V56 = 3  // Use internal reference voltage (2.56V)
} ADC_Reference_t;

typedef enum
{
    ADC_OK = 0,
    ADC_ERROR_INVALID_CHANNEL = -1,
    ADC_ERROR_INVALID_REFERENCE = -2
} ADC_Error_t;

#include <stdint.h>

// Initialize the ADC. Sets up necessary pins and reference voltage.
// You can call this function multiple times to initialize multiple
// channels if needed.
// Parameters: channel - the ADC channel to initialize. Chose ADC_PK0 if you
//                       have connected a sensor to PK0 pin on the MCU.
//             reference - the reference voltage to use.
// Return: ADC_Error_t indicating success or the type of error that occurred.
ADC_Error_t adc_create(ADC_Channel_t channel, ADC_Reference_t reference);

// Read the current value from the ADC channel. Returns a value between 0 and 1023 (10-bit resolution).
// Returns UINT16_MAX if an error occurs (e.g. invalid channel or reference).
// NOTE: This function is blocking. Conversion time is typically around 200 microseconds.
//       ADC Clock is set to F_CPU/128 to obtain 10-bit resolution. Make sure to call adc_create() before calling this function.
uint16_t adc_measure(ADC_Channel_t channel); 
