/***********************************************
 * uart_stdio.h
 *  Low-level UART stdio interface
 *  Author:  Erland Larsen
 *  Date:    2026-01-30
 *  Project: SPE4_API
 **********************************************/

#pragma once
#include "uart.h"
#include <stdint.h>

// Buffer size for incoming bytes on stdio (UART0).
#define UART_STDIO_RX_BUFFER_SIZE 32

// Initialize USART0 and bind stdin/stdout/stderr to it
uart_t uart_stdio_init(uint32_t baud);

// Optional: direct send/receive (can be used without stdio)
void uart0_write_byte(int8_t b);
int8_t uart0_read_byte_blocking(void);

uint8_t gets_nonblocking(char *buffer, uint8_t max_length);
