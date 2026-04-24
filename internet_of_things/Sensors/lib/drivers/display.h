/***********************************************
 * display.h
 *  4 digit 7-segment display interface
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-01-30
 *  Project: SPE4_API
 *  NOTICE:  The display driver uses Timer1 and 
 *           its interrupt. The Global Interrupt
 *           flag must be enabled in main.c
 *           after display_init() is called.
 **********************************************/
#pragma once
#include <stdint.h>
/**
 * @brief Initialize the 4-digit 7-segment display.
 * 
 */
void display_init(void);

/**
 * @brief 
 * 
 * @param seg should be a number from 0-17. 0-15 corrospond to the hex-digit, 16 is '-' and 17 is whitespace ' '
 */
void display_setValues(int8_t seg1, int8_t seg2, int8_t seg3, int8_t seg4 );

/**
 * @brief Can show an integer. 
 * 
 * @param value between -999 to 9999
 */
void display_int(int16_t value);

/**
 * @brief Set comma position. 
 * 
 * @param value between 0-3. 0 is no comma, 1 is one decimal place, etc.
 *
 */
void display_setDecimals(uint8_t value);
