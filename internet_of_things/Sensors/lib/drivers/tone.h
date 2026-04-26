/***********************************************
 * tone.h
 *  Interface for the speaker/buzzer driver
 *  connected to the microcontroller. 
 *  This driver uses Timer2 to generate square waves 
 *  at the desired frequency for the specified duration.
 * 
 *  Author:  Unknown
 *  Date:    Unknown
 * 
 *  Refactored by: Erland Larsen
 *  Date:    2026-03-15
 *  Project: SPE4_API
 **********************************************/
#pragma once

#include <stdint.h>
void tone_play(uint16_t frequency, uint16_t duration);
void tone_play_starwars();// by Domonkos Gellert Papp
