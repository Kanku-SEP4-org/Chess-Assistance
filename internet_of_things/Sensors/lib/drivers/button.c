/***********************************************
 * button.c
 *  Button implementation. Functions for the three buttons on the shield.
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-01-30
 *  Project: SPE4_API
 **********************************************/
#include <avr/io.h>
#include <stdbool.h>

#define BUTTON_COUNT 3
#define B_1 PF1
#define B_2 PF2
#define B_3 PF3

#define B_DDR DDRF
#define B_PORT PORTF
#define B_PIN PINF

void button_init()
{
    B_DDR&=~((1<<B_1) | (1<<B_2) | (1<<B_3)) ; // Make them 3 buttons to be input. 
    B_PORT|=((1<<B_1) | (1<<B_2) | (1<<B_3)) ; // enable the pullup resistor. 
}


bool button_get(uint8_t button_no)
{
	switch(button_no)
	{
		case 1:
			return (B_PIN & _BV(B_1)) == 0;
		case 2:
			return (B_PIN & _BV(B_2)) == 0;
		case 3:
			return (B_PIN & _BV(B_3)) == 0;
	}
	return 0;
}

uint8_t button_scan()
{
	for(int i=1; i<=BUTTON_COUNT; i++)
	{
		if(button_get(i))
		{
			return i;
		}
	}
	return 0;
}