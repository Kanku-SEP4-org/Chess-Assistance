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

/**
 * @brief Starts the pump briefly and reports that filling is done.
 * Current implementation is a simple placeholder using the pump driver.
 * Format: "PUMP:DONE"
 */
void fill_and_report_done(void);

/**
 * @brief Handles message transmission for the CO2 function,
 * accounting for the case where data is not yet ready from the sensor.
 * If data is available, it should print the latest CO2 reading in a machine-friendly format.
 */
void get_and_report_co2(void);

/**
 * @brief data handling function that is called by the CO2 driver when new data is received from the sensor.
 * This function should store the latest CO2 reading in a global variable,
 * which can then be accessed by the get_and_report_co2() function to print the latest CO2 reading when requested.
 * @param ppm
 * must be visible for testing but also for main.c to initialize the sensor
 */
void co2_incoming_data_handler(uint16_t ppm);
