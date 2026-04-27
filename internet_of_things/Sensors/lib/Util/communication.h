#pragma once 

#include <stdint.h>

/********************
 * @brief Communication utilities for the project.
 * This file provides functions for UART communication, including sending commands to the WiFi module and handling responses.
 * It also defines a callback mechanism for processing incoming data from the WiFi module.
 ********************/
void transmit_data(char* str);