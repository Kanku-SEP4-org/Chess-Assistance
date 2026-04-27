/***********************************************
 * light.h
 *  Interface for the Light Sensor driver.
 *  Functions for the light sensor (KY-018).
 *  NOTE: The light sensor is connected to the ADC channel PK7 on the
 *        microcontroller and is a wrapper around the ADC functions.
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-03-10
 *  Project: SPE4_API
 **********************************************/
#pragma once

#include "adc.h"
#include <stdint.h>

// Initialize the light sensor. This is a wrapper around adc_create()
// for the specific channel and reference used by the light sensor.
// Returns ADC_Error_t indicating success or the type of error that occurred.
ADC_Error_t light_init();

// Read the current light level from the sensor.
// Returns a value between 0 and 1023 (10-bit resolution).
// Low values = dark, high values = bright.
uint16_t light_measure_raw();
