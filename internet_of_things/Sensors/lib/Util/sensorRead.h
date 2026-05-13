#pragma once // Prevents the file from being included twice

#include <stdint.h>

/**
 * @brief Reads temperature from DHT11 and prints it to UART in a machine-friendly format.
 * Format: "TEMP:24.5"
 */
void get_and_report_temperature(void);
void get_and_report_temp_json(void);
void get_and_report_humidity(void);
void get_and_report_hum_json(void);
void get_and_report_water(void);