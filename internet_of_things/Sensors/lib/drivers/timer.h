/***********************************************
 * timer.h
 *  Software timer interface. Supports up to TIMER_MAX_TIMERS concurrent 
 *  timers with millisecond resolution.
 * 
 *  Author:  Erland Larsen
 *  Date:    2026-03-06
 *  Project: SPE4_API
 **********************************************/
#pragma once
#include <stdint.h>

#define TIMER_INVALID_ID -1
#define TIMER_ERROR_INVALID_INTERVAL -2
#define TIMER_ERROR_NO_RESOURCES -3
#define TIMER_OK 0
#define TIMER_MAX_TIMERS 5
#define TIMER_MAX_INTERVAL_MS 60000

// Create a software timer that calls 'callback' every 'interval_ms' milliseconds
// interval_ms must be between 1 and TIMER_MAX_INTERVAL_MS ms
// NOTICE: Callback function must be short and non-blocking! Called with timer ID as argument.
// Returns a Timer ID [1..TIMER_MAX_TIMERS] on success, or a negative error code on failure.
int8_t timer_create_sw(void (*callback)(uint8_t id), uint16_t interval_ms); 

// Get the state of a timer (active or paused). Returns 1 if active, 0 if paused, or negative error code if invalid ID.
int8_t timer_get_state(int8_t timer_id);

// Pause a timer. Returns TIMER_OK on success, or negative error code if invalid ID.
int8_t timer_pause(int8_t timer_id);

// Resume a paused timer. Returns TIMER_OK on success, or negative error code if invalid ID.
int8_t timer_resume(int8_t timer_id);

// Delete a timer. Returns TIMER_OK on success, or negative error code if invalid ID.
int8_t timer_delete(int8_t timer_id);
