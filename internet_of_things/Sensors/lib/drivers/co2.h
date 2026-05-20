/***********************************************
 * co2.h
 *  CO2 sensor interface for the sensor model MH-Z19B, 
 *  which communicates over UART3. The sensor sends CO2 concentration
 *  in ppm as a 16-bit value (2 bytes).
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-03-27
 *  Project: SPE4_API
 **********************************************/
#pragma once
#include <stdint.h>

typedef enum {
    CO2_OK,
    CO2_ERROR
} co2_status_t;

typedef void (*co2_callback_t)(uint16_t co2_ppm);

co2_status_t co2_init(co2_callback_t callback);
co2_status_t co2_start_measure();

