#pragma once // Prevents the file from being included twice

#include <stdint.h>
#include "adc.h"

/**
 * @brief Reads temperature from DHT11 and prints it to UART in a machine-friendly format.
 * Format: "TEMP:24.5"
 */
void get_and_report_temperature(void);

/**
 * @brief Reads humidity from DHT11 and prints it to UART in a machine-friendly format.
 * Format: "HUM:24.5"
 */
void get_and_report_humidity(void);

/**
 * @brief Reads light from light sensor KY-018 and prints it to UART in a machine-friendly format.
 * Contains values between 0 and 1023
 * Format: "LIG:431"
 */
void get_and_report_light(ADC_Error_t light_sensor);

/**
 * @brief Reads moisture from soil sensor and prints it to UART in a machine-friendly format.
 * Contains values between 0 and 1023
 * Format: "WAT:431"
 */
void get_and_report_water(ADC_Error_t water_sensor);