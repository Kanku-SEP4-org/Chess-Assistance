/********************************************************************
 * uart.h
 *  Serial port interface (UART)
 *  Author:  Erland Larsen
 *  Date:    2026-02-06
 *  Project: SPE4_API
 *  NOTICE:  Only support for 8 databit, 1 stop bit and no parity.
 *           Baud Rates supported: 2400, 4800, 9600, 14400, 19200,
 *           28800, 38400, 57600, 115200.
 *  Reservations:
 *           UART0: stdin, stdout, stderr are connected to UART0.
 *                  Do not use UART0 for other purposes if you want 
 *                  to use stdio functions for PC terminal.
 *           UART2: Used for WIFI module in AT-command mode.
 * 
  *******************************************************************/
#pragma once
#include <stdint.h>
#include "ringbuffer.h"

typedef enum {
    UART_OK = 0,
    UART_ERROR_INVALID_BAUD_RATE = -1,
    UART_ERROR_INIT_FAILED = -2,
    UART_ERROR_INVALID_ID = -3,
    UART_NO_DATA_AVAILABLE = -4
} uart_t;

typedef enum {
    UART0_ID = 0,
    UART1_ID = 1,
    UART2_ID = 2,
    UART3_ID = 3
} uart_id_t;

typedef void (*rx_callback_t)(uint8_t byte);

// Initialize UART with the specified baud rate (4800 - 115200). Fixed 8 data bit, 1 stop bit, no parity.
// PARAMETERS: uart_id:     UART0_ID, UART1_ID, UART2_ID or UART3_ID
//             baud_rate:   2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, 115200
//                          Notice: Fixed 8 data bit, 1 stop bit, no parity.
//             buffer_size: Size of ringbuffer to create for RX. Set to 0 to disable RX buffer.
//             callback:    Function to call when a byte is received. If NULL, no callback will be used 
//                          but if buffer_size > 0 rx-interrupt is enabled and stores received bytes in
//                          ringbuffer. If non-NULL, callback will be called with received byte as 
//                          argument when a byte is received. See table below.
//                          NOTE: If using stdio, use uart_stdio_init(...) to initializes UART0 and binds it to stdio.
//
//                          buffer_size | callback | Behavior
//                          --------------------------------------------------------------------------------
//                          0           | NULL     | No RX interrupt, no ringbuffer, no callback. use 
//                                      |          | uart_read_byte_blocking to read bytes directly from UART registers.
//                          0           | non-NULL | RX interrupt enabled, no ringbuffer. callback will be called with
//                                      |          | received byte as argument when a byte is received.
//                          >0          | NULL     | RX interrupt enabled, ringbuffer of specified size created for
//                                      |          | incoming bytes. Use uart_read_byte to read bytes from ringbuffer.
//                          >0          | non-NULL | RX interrupt enabled, ringbuffer of specified size created for
//                                      |          | incoming bytes. Callback on receipt of '\n'.
//                          ---------------------------------------------------------------------------------
// RETURNS: UART_OK on success, or negative error code on failure.
uart_t uart_init(uart_id_t uart_id, uint32_t baud_rate, rx_callback_t rx_callback, uint8_t buffer_size);

uart_t uart_write_bytes(uart_id_t uart_id, uint8_t* data, uint8_t length);
uart_t uart_write_byte(uart_id_t uart_id, uint8_t b);
uart_t uart_read_byte(uart_id_t uart_id, uint8_t *byte);
uart_t uart_read_byte_blocking(uart_id_t uart_id, uint8_t *byte);

uart_t uart_send_string_blocking(uart_id_t uart_id, const char* str);
