/***********************************************
 * servo.h
 *  Servo motor interface. Supports up to 2 channels of PWM on Timer 3.
 *  PWM frequency is fixed at 50Hz, and duty cycle can be set to achieve
 *  approximately +/-90 degrees of rotation.
 * *  Note: Only PWM_A is accessable on the shield (connector marked ~5)
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-03-06
 *  Project: SPE4_API
 **********************************************/

#pragma once

#include <stdint.h>

typedef enum {PWM_NORMAL, PWM_INVERTED} pwmMode_t;
typedef enum {PWM_A, PWM_B} pwmChannel_t;

// Initialize servo. Use Timer 4
void servo_init(pwmMode_t mode);

// Start PWM (all channels)
void servo_start();

// Stop PWM (all channels)
void servo_stop();

// servo_setAngle. Position +/-90 degrees
uint16_t servo_setAngle(pwmChannel_t channel, int8_t position);

