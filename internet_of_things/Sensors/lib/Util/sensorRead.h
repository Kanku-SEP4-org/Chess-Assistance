#pragma once // Prevents the file from being included twice

#include <stdint.h>
#include "adc.h"

/**
 * @brief Reads temperature from DHT11 and prints it to UART in a machine-friendly format.
 * Format: "TEMP:24.5"
 */
void get_and_report_temperature(void);

/**
 * @brief Reads temperature from DHT11 and prints it to UART in JSON.
 * Format: "{"temperature":24.5}"
 */
void get_and_report_temp_json(void);

/**
 * @brief Reads humidity from DHT11 and prints it to UART in a machine-friendly format.
 * Format: "HUM:24.5"
 */
void get_and_report_humidity(void);

/**
 * @brief Reads humidity from DHT11 and prints it to UART in JSON.
 * Format: "{"humidity":24.5}"
 */
void get_and_report_hum_json(void);

/**
 * @brief Reads light from light sensor KY-018 and prints it to UART in a machine-friendly format.
 * Contains values between 0 and 1023
 * Format: "LIG:431"
 */
void get_and_report_light(ADC_Error_t light_sensor);

/**
 * @brief Reads light from light sensor KY-018 and prints it to UART in JSON.
 * Contains values between 0 and 1023
 * Format: "{"light":431}"
 */

void get_and_report_light_json(ADC_Error_t light_sensor);
/**
 * @brief Starts the pump briefly and reports that filling is done.
 * Current implementation is a simple placeholder using the pump driver.
 * Format: "PUMP:DONE"
 */
void fill_and_report_done(void);