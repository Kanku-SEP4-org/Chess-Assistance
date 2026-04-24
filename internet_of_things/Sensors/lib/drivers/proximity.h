/***********************************************
 * proximity.h
 *  Proximity sensor interface. Supports HC-SR04 ultrasonic sensor
 *  using Timer 5 for timing the echo pulse.
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-03-06
 *  Project: SPE4_API
 **********************************************/
#pragma once
#include <stdint.h>

// Initialize proximity sensor. Sets up Timer and necessary pins.
void proximity_init();

// Trigger a measurement and return the distance in mm. Returns UINT16_MAX on timeout (no object detected within range).
uint16_t proximity_measure();

// Get the last measured distance in mm. Returns UINT16_MAX if the last measurement timed out.
uint16_t proximity_get_distance();

