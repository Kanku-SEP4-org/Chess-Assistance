/***********************************************
 * buzzer.c
 *  Buzzer driver implementation
 * 
 *  Author:  Laurits Ivar / Erland Larsen
 *  Date:    2024
 *  Project: SPE4_API
 *  Revision history: 
 * 			 0.1 - Initial version for SEP4_DRIVERS (Laurits Ivar)
 * 			 0.9 - 2026-03-06 Beep duration increased and integrated 
 *                  into SPE4_API (Erland Larsen)
 **********************************************/
#include "buzzer.h"
#include <avr/io.h>
#include <util/delay.h>

#define BUZ_BIT PE5
#define BUZ_DDR DDRE
#define BUZ_PORT PORTE

void buzzer_beep(){

    BUZ_DDR |= (1<<BUZ_BIT); //init to be an output
    BUZ_PORT&=~(1<<BUZ_BIT); //Turn On (Active low)
    _delay_ms(25);
    BUZ_PORT|=(1<<BUZ_BIT); //Turn Off (Active low)
}