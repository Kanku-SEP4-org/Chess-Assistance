#ifndef PUMP_H
#define PUMP_H

#include <stdbool.h>

/**
 * @brief Initializes the pump control pin.
 * Sets PC7 as output and ensures pump is off by default.
 */
void pump_init(void);

/**
 * @brief Starts the pump.
 * Sets PC7 HIGH.
 */
void pump_start(void);

/**
 * @brief Stops the pump.
 * Sets PC7 LOW.
 */
void pump_stop(void);

/**
 * @brief Returns whether the pump output is currently active.
 * @return true if pump is on, false otherwise.
 */
bool pump_is_running(void);

#endif