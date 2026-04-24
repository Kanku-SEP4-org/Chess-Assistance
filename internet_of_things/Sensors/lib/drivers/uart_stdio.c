/***********************************************
 * uart_stdio.c
 *  Low-level UART stdio implementation
 *  Author:  Erland Larsen
 *  Date:    2026-01-30
 *  Project: SPE4_API
 **********************************************/
#include "uart_stdio.h"
#include <avr/io.h>
#include <stdio.h>
#include <stdbool.h>

static int uart0_putchar(char c, FILE *stream);
static int uart0_getchar(FILE *stream);

static bool _line_received = false;

// Stream-objekt for stdio
static FILE uart0_stream;

static void _uart0_line_callback(uint8_t b)
{
    _line_received = true;
}

uart_t uart_stdio_init(uint32_t baud)
{
    uart_t result;

    #ifdef UART_STDIO_RX_BUFFER_SIZE
    {
    result = uart_init(UART0_ID, baud, _uart0_line_callback, UART_STDIO_RX_BUFFER_SIZE);
    }
    #else
    result = uart_init(UART0_ID, baud, NULL, 0);
    #endif

    if (UART_OK == result)
    {
        // Bind stdio to UART
        fdev_setup_stream(&uart0_stream, uart0_putchar, uart0_getchar, _FDEV_SETUP_RW);
        stdin = &uart0_stream;
        stdout = &uart0_stream;
        stderr = &uart0_stream;
    }
    return result;
}

uint8_t gets_nonblocking(char *buffer, uint8_t max_length)
{
    uart_t result;
    uint8_t index = 0;
    uint8_t c;

    if(_line_received) 
    {
        while ((result = uart_read_byte(UART0_ID, &c)) == UART_OK && c != '\n' && index < max_length - 1) 
        {
            buffer[index++] = c;
        }
        buffer[index] = '\0'; // Null-terminate the string
        _line_received = false; // Reset flag for next line
    }
    return index; // Return number of characters read
}

static int uart0_putchar(char c, FILE *stream)
{
    (void)stream;

    // Many terminals expect CRLF
    if (c == '\n') {
        uart_write_byte(UART0_ID, '\r');
    }
    uart_write_byte(UART0_ID, (uint8_t)c);
    return 0;
}

static int uart0_getchar(FILE *stream)
{
    (void)stream;
    uint8_t c;
    uart_t result;

    #ifdef UART_STDIO_RX_BUFFER_SIZE
    do
    {
        result = uart_read_byte(UART0_ID, &c);
    } while(UART_OK != result); // Wait until a byte is available in the ring buffer
    #else
        result = uart_read_byte_blocking(UART0_ID, &c);
        if (UART_OK != result) 
        {
            return EOF;
        }
    #endif

    // Convert CR to NL (makes enter key work as expected)
    if (c == '\r') c = '\n';

    return (int)c;
}
