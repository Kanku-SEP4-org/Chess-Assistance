#pragma once
#ifndef SENSORS_COMMUNICATION_H
#define SENSORS_COMMUNICATION_H


#include <stdbool.h>
#include <stdint.h>

/********************
 * @brief Communication utilities for the project.
 * This file provides functions for UART communication, including sending commands to the WiFi module and handling responses.
 * It also defines a callback mechanism for processing incoming data from the WiFi module.
 ********************/
// Runtime communication modes
typedef enum {
    COMM_SERIAL,
    COMM_WIFI
} comm_mode_t;

// Set up the network state and primary hardware buffers
//default comm_serial
void communication_init(void);

// Automatically hook up specified developer testing profiles
// if successful, mode switches to comm_wifi
void communication_dev_autoconnect(const char* developer_name);

// Non-blocking background worker to poll for incoming TCP data packets
//handles interrupts when messages arrive, while leaving the sensors to their work
void communication_poll_network(void);

// Master data transmission pipeline
void transmit_data(const char* str);

// Process a raw configuration string pushed down from sensor_client_c
void communication_connect_wifi(const char *config_string);


#endif