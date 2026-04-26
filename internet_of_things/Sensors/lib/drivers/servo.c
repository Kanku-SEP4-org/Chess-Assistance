/***********************************************
 * servo.c
 *  Servo motor implementation. Supports up to 2 channels of PWM on Timer 3.
 *  PWM frequency is fixed at 50Hz, and duty cycle can be set to achieve
 *  approximately +/-90 degrees of rotation.
 * *  Note: Only PWM_A is accessable on the shield (connector marked ~5)
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-03-06
 *  Project: SPE4_API
 **********************************************/

#include <avr/io.h>
#include "servo.h"

// Hardware abstraction for Timer 3 and its associated pins. 
// This allows for easier porting to other timers or microcontrollers by just changing
#define DDRx   DDRE
#define CHANNEL_A PE3
#define CHANNEL_B PE4
#define TCCRxA TCCR3A
#define TCCRxB TCCR3B
#define OCRxA  OCR3A
#define OCRxB  OCR3B
#define OCRxC  OCR3C
#define ICRx   ICR3
#define COMxA1 COM3A1
#define COMxA0 COM3A0
#define COMxB1 COM3B1
#define COMxB0 COM3B0
#define COMxC1 COM3C1
#define COMxC0 COM3C0
#define WGMx3  WGM33
#define WGMx2  WGM32
#define WGMx1  WGM31
#define WGMx0  WGM30
#define CSx2   CS32
#define CSx1   CS31
#define CSx0   CS30

#define TOP_50HZ (39999+1)	// 50Hz @F_CPU=16MHz (+1 => less error on position)

// Initialize servo. Use Timer 4
void servo_init(pwmMode_t mode)
{
	// Set Timer to mode 14, Fast PWM
	TCCRxA |= _BV(WGMx1);
	TCCRxB |= _BV(WGMx2) | _BV(WGMx3);
	
	// Set OCx pins mode
	TCCRxA |= _BV(COMxA1) | _BV(COMxB1);
	if(mode==PWM_INVERTED)
	{
		TCCRxA |= _BV(COMxA0) | _BV(COMxB0);
	}
	
	// Set PWM frequency
	ICRx = TOP_50HZ;
	
	// Set all channels to middle position (1.5ms)
	OCRxA = OCRxB = 3000;
	
	// Enable OCx output pins
	DDRx |= _BV(CHANNEL_A) | _BV(CHANNEL_B);
}

void servo_start()
{
	// Start prescaler at F_CPU/8
	TCCRxB |= _BV(CSx1);	
}

void servo_stop()
{
	// Stop prescaler
	TCCRxB &= ~(_BV(CSx0) | _BV(CSx1) | _BV(CSx2));
}


// servo_setAngle. Position +/-90 degrees
uint16_t servo_setAngle(pwmChannel_t channel, int8_t position)
{
uint16_t _ocr = 0;

	if ((position>=-90) && (position <=90))
	{
		// Duty Cycle between 1ms (-90) and 2ms (+90)
		//	_ocr = (uint16_t)((TOP_50HZ/20)+(position+90)*TOP_50HZ/(20*180));

		// The datasheet timing does not give more then +/-45 degrees
		// The following is found by experiment
		_ocr = (uint16_t)(1100+(position+90)*21);
	
		switch (channel)
		{
			case PWM_A:
				OCRxA = _ocr;
				break;
			case PWM_B:
				OCRxB = _ocr;
				break;
		}
	}
	return _ocr;
}

