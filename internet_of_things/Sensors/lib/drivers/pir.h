/***********************************************
 * pir.h
 *  PIR sensor interface
 *  Author:  Erland Larsen
 *  Date:    2026-01-30
 *  Project: SPE4_API
 **********************************************/
#pragma once

typedef void (*pir_callback_t)(void);
typedef enum {
    PIR_NO_MOTION = 0,
    PIR_MOTION_DETECTED
} pir_state_t;

// Initialize PIR sensor. Two modes exist:
//   if callback is NULL, no interrupts are used and the user must poll the sensor state using pir_get_state().
//   if callback is not NULL, it is called on any change in motion detection via interrupt.
//      The callback can use pir_get_state() to read the current state.
//      The callback must be as fast as possible and should not perform blocking operations.
void pir_init(pir_callback_t callback);

// Get the current state of the PIR sensor.
// Returns PIR_NO_MOTION or PIR_MOTION_DETECTED.
pir_state_t pir_get_state(void);
