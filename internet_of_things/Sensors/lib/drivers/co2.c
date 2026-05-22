/***********************************************
 * co2.c
 *  CO2 sensor implementation for the sensor model MH-Z19B, 
 *  which communicates over UART3. The sensor sends CO2 concentration
 *  in ppm as a 16-bit value (2 bytes).
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-03-27
 *  Project: SPE4_API
 **********************************************/
#include "co2.h"
#include "uart.h"

static co2_callback_t co2_callback = NULL;

void co2_uart_rx_callback(uint8_t byte)
{
    static uint8_t byte_count = 0;
    static uint8_t response[9]; // Buffer to store the response from the sensor
    uint16_t co2_ppm = 0;
    uint8_t calculated_checksum = 0;

    response[byte_count++] = byte; // Store the received byte in the response buffer
    if(9 == byte_count) // We have received the full response (9 bytes)
    {
        // Validate the response (e.g., check start byte, command byte, and checksum)
        if (response[0] == 0xFF && response[1] == 0x86) // Check for valid start and command bytes
        {
            for (size_t i = 1; i < 8; i++) // Calculate checksum from bytes 1 to 7
            {
                calculated_checksum += response[i];
            }
            calculated_checksum = (0xFF-calculated_checksum) + 1; // Finalize checksum calculation

            if (calculated_checksum == response[8]) // Check if checksum matches
            {
                co2_ppm = ((uint16_t)response[2] << 8) | response[3]; // Combine bytes to get CO2 ppm value
                if (NULL != co2_callback)
                {
                    co2_callback(co2_ppm); // Call the registered callback with the CO2 ppm value
                }
            }
        }
        byte_count = 0; // Reset byte count for the next response
        for(int i = 0; i < 9; i++) // Clear the response buffer
        {
            response[i] = 0;
        }
    }
}

co2_status_t co2_init(co2_callback_t callback)
{
    if( NULL != callback )
    {
        if(UART_OK == uart_init(UART3_ID, 9600, co2_uart_rx_callback, 0)) // Initialize UART3 for CO2 sensor communication
        {
            co2_callback = callback; // Store the user-provided callback
            return CO2_OK;
        }
    }
    return CO2_ERROR;
}

co2_status_t co2_start_measure()
{
    uart_t status = UART_OK;
    // Send command to start measurement
    uint8_t start_command[] = {0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79}; // Example command to start measurement
    for (size_t i = 0; i < sizeof(start_command); i++)    
    {
        status |= uart_write_byte(UART3_ID, start_command[i]);
    }
    return (UART_OK == status) ? CO2_OK : CO2_ERROR;
}
