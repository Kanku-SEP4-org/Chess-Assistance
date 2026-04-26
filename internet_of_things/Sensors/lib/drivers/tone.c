/***********************************************
 * tone.c
 *  Implementation for the speaker/buzzer driver
 *  connected to the microcontroller. 
 *  This driver uses Timer2 to generate square waves 
 *  at the desired frequency for the specified duration.
 * 
 *  Author:  Unknown
 *  Date:    Unknown
 * 
 *  Refactored by: Erland Larsen
 *  Date:    2026-03-17
 *  Project: SPE4_API
 **********************************************/
#include "tone.h"
#include <avr/io.h>
//#include <util/delay.h>

#define BUZ_BIT PA7
#define BUZ_DDR DDRA
#define BUZ_PORT PORTA

void tone_play(uint16_t frequency, uint16_t duration) 
{
    uint8_t prescaler_bits = 0;
    uint16_t prescaler_value = 0;
    uint16_t num_ticks = 0;

    // Set BUZ_BIT as output
    BUZ_DDR|=(1<<BUZ_BIT);

    // Calculate the half-period delay in microseconds
    uint16_t delay_us = 500000 / frequency;

    // Calculate the number of cycles needed for the specified duration
    uint16_t duration_loop = (uint16_t) ((uint32_t) duration * 1000 / (2 * delay_us));

    // Initialize Timer in normal mode
    TCCR2A = 0;
    TCCR2B = 0;

    // Choose prescaler based on delay
    if (delay_us > 4000) 
    {
        prescaler_bits = (1 << CS22) | (1 << CS21) | (1 << CS20); // 1024
        prescaler_value = 1024;
    } 
    else if (delay_us > 2000) 
    {
        prescaler_bits = (1 << CS22) | (1 << CS21); // 256
        prescaler_value = 256;
    } 
    else if (delay_us > 1000) 
    {
        prescaler_bits = (1 << CS22) | (1 << CS20); // 128
        prescaler_value = 128;
    } 
    else if (delay_us >500) 
    {
        prescaler_bits = (1 << CS22); // 64
        prescaler_value = 64;
    } 
    else if (delay_us >125) 
    {
        prescaler_bits = (1 << CS21)| (1 << CS20); //32
        prescaler_value = 32;
    }
    else
    {
       prescaler_bits = (1 << CS21) ; // 8
       prescaler_value = 8;
    }

    // Set the prescaler
    TCCR2B = prescaler_bits;

    // Calculate the number of timer ticks needed for the specified delay
    num_ticks = (F_CPU / 1000000UL) * delay_us / prescaler_value;

    // Generate the tone
    for (uint16_t i = 0; i < duration_loop; i++) 
    {
        // Set BUZ_BIT high
        BUZ_PORT |= (1 << BUZ_BIT);
        // Reset the timer counter
        TCNT2 = 0;

        // Wait until the timer counter reaches the required ticks
        while (TCNT2 < num_ticks) 
        {
            // Busy-wait
        }

        // Set BUZ_BIT low
        BUZ_PORT &= ~(1 << BUZ_BIT);
        // Reset the timer counter
        TCNT2 = 0;

        // Wait until the timer counter reaches the required ticks
        while (TCNT2 < num_ticks) 
        {
            // Busy-wait
        }
    }
    // Stop the timer
    TCCR2B = 0;

    // Set BUZ_BIT as input to turn off the buzzer
    BUZ_DDR&=~(1<<BUZ_BIT);
}

void tone_play_starwars()
{
    tone_play(392, 500);  // G4 for 500 ms
    tone_play(392, 500);  // G4 for 500 ms
    tone_play(392, 500);  // G4 for 500 ms
    tone_play(311, 350);  // E♭4 for 350 ms
    tone_play(466, 150);  // B4 for 150 ms
    tone_play(392, 500);  // G4 for 500 ms
    tone_play(311, 350);  // E♭4 for 350 ms
    tone_play(466, 150);  // B4 for 150 ms
    tone_play(392, 1000); // G4 for 1000 ms

    tone_play(587, 500);  // D5 for 500 ms
    tone_play(587, 500);  // D5 for 500 ms
    tone_play(587, 500);  // D5 for 500 ms
    tone_play(622, 350);  // D#5 for 350 ms
    tone_play(466, 150);  // B4 for 150 ms
    tone_play(370, 500);  // F#4 for 500 ms
    tone_play(311, 350);  // Eb4 for 350 ms
    tone_play(466, 150);  // B4 for 150 ms
    tone_play(392, 1000); // G4 for 1000 ms
}
