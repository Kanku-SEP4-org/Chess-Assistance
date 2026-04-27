/***********************************************
 * soil.h
 *  Interface for the Soil Moisture Sensor driver.
 *  NOTE: The soil moisture sensor is connected to an ADC channel on the
 *        microcontroller and is a wrapper around the ADC functions.
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-03-10
 *  Project: SPE4_API
 **********************************************/
#pragma once

#include "adc.h"
#include <stdint.h>

// Initialize the soil moisture sensor. This is a wrapper around adc_create()
// for the specific channel and reference used by the soil moisture sensor.
// Parameters: channel - the ADC channel to initialize. Chose an available
// ADC channel (e.g. ADC_PK0) that you have connected the soil moisture sensor to.
// More than one soil moisture sensor can be used by initializing multiple channels.
// Returns ADC_Error_t indicating success or the type of error that occurred.
ADC_Error_t soil_init(ADC_Channel_t channel);

// Read the current soil moisture level from the sensor.
// Returns a value between 0 and 1023 (10-bit resolution).
// Low values = dry, high values = wet.
// On error (e.g. invalid channel or reference), returns UINT16_MAX.
uint16_t soil_measure_raw(ADC_Channel_t channel);
