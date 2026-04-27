/***********************************************
 * button.h
 *  Button interface. Functions for the three buttons on the shield.
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-01-30
 *  Project: SPE4_API
 **********************************************/
#pragma once

#include <stdint.h>
#include <stdbool.h>

// Initialize buttons. Sets up necessary pins and pull-ups.
void button_init();

// Get the state of a button. Returns true if pressed, false if not pressed.
// Valid button numbers are [1..3].
bool button_get(uint8_t button_no);

// Scan buttons and return the number of the first button found to be pressed. 
// Returns 0 if no buttons are pressed. Valid button numbers are [1..3].
uint8_t button_scan();

