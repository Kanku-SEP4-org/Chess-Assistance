/********************************************************************
 * uart.c
 *  Serial port implementation (UART)
 *  Author:  Erland Larsen
 *  Date:    2026-02-06
 *  Project: SPE4_API
 *  NOTICE:  stdin, stdout, stderr are connected to UART0.
 *           Do not use UART0 for other purposes if you want
 *           to use stdio functions.
 *           This version only works with 8 databit, 1 stop bit and
 *           no parity.
 *******************************************************************/
#include "uart.h"
#include "ringbuffer.h"
#include <stddef.h>
#include <avr/io.h>
#include <avr/interrupt.h>

static ringbuffer_t uart0_rx_buffer = NULL;
static ringbuffer_t uart1_rx_buffer = NULL;
static ringbuffer_t uart2_rx_buffer = NULL;
static ringbuffer_t uart3_rx_buffer = NULL;
static rx_callback_t uart0_rx_callback = NULL;
static rx_callback_t uart1_rx_callback = NULL;
static rx_callback_t uart2_rx_callback = NULL;
static rx_callback_t uart3_rx_callback = NULL;


static inline uint16_t ubrr_from_baud(uint32_t baud)
{
    // Double speed (U2X0=1): UBRR = F_CPU/(8*baud) - 1
    return (uint16_t)((F_CPU / (8UL * baud)) - 1UL);
}

uart_t uart_init(uart_id_t uart_id, uint32_t baud, rx_callback_t rx_callback, uint8_t buffer_size)
//uart_t uart_init(uart_id_t uart_id, uint32_t baud, uint8_t buffer_size)
{
    uint16_t ubrr = ubrr_from_baud(baud);

    switch (uart_id)
    {
    case 0:
        // Baudrate
        UBRR0H = (int8_t)(ubrr >> 8);
        UBRR0L = (int8_t)(ubrr & 0xFF);

        UCSR0A = (1 << U2X0);                   // Enable double speed
        UCSR0B = (1 << RXEN0) | (1 << TXEN0);   // Enable RX + TX
        UCSR0C = (1 << UCSZ01) | (1 << UCSZ00); // 8N1

        if(buffer_size > 0) 
        {
            if(NULL != uart0_rx_buffer) 
            {
                ringbuffer_destroy(uart0_rx_buffer); // Destroy existing buffer if it exists (e.g., re-initialization)
                uart0_rx_buffer = NULL;
            }
            uart0_rx_buffer = ringbuffer_create(buffer_size, sizeof(uint8_t));
            if (!uart0_rx_buffer) 
            {
                return UART_ERROR_INIT_FAILED;
            }
        }
        if((NULL != rx_callback) || (buffer_size > 0)) 
        {
            uart0_rx_callback = rx_callback;
            UCSR0B |= (1 << RXCIE0);            // Enable RX Complete Interrupt
        }
        break;
    case 1:
        // Baudrate
        UBRR1H = (int8_t)(ubrr >> 8);
        UBRR1L = (int8_t)(ubrr & 0xFF);

        UCSR1A = (1 << U2X0);                   // Enable double speed
        UCSR1B = (1 << RXEN1) | (1 << TXEN1);   // Enable RX + TX
        UCSR1C = (1 << UCSZ11) | (1 << UCSZ10); // 8N1

        if(buffer_size > 0) 
        {
            if(NULL != uart1_rx_buffer) 
            {
                ringbuffer_destroy(uart1_rx_buffer); // Destroy existing buffer if it exists (e.g., re-initialization)
                uart1_rx_buffer = NULL;
            }
            uart1_rx_buffer = ringbuffer_create(buffer_size, sizeof(uint8_t));
            if (!uart1_rx_buffer) 
            {
                return UART_ERROR_INIT_FAILED;
            }
        }
        if((NULL != rx_callback) || (buffer_size > 0)) 
        {
            uart1_rx_callback = rx_callback;
            UCSR1B |= (1 << RXCIE1);            // Enable RX Complete Interrupt
        }
        break;
    case 2:
        // Baudrate
        UBRR2H = (int8_t)(ubrr >> 8);
        UBRR2L = (int8_t)(ubrr & 0xFF);

        UCSR2A = (1 << U2X0);                   // Enable double speed
        UCSR2B = (1 << RXEN2) | (1 << TXEN2);   // Enable RX + TX
        UCSR2C = (1 << UCSZ21) | (1 << UCSZ20); // 8N1

        if(buffer_size > 0) 
        {
            if(NULL != uart2_rx_buffer) 
            {
                ringbuffer_destroy(uart2_rx_buffer); // Destroy existing buffer if it exists (e.g., re-initialization)
                uart2_rx_buffer = NULL;
            }
            uart2_rx_buffer = ringbuffer_create(buffer_size, sizeof(uint8_t));
            if (!uart2_rx_buffer) 
            {
                return UART_ERROR_INIT_FAILED;
            }
        }
        if((NULL != rx_callback) || (buffer_size > 0)) 
        {
            uart2_rx_callback = rx_callback;
            UCSR2B |= (1 << RXCIE2);            // Enable RX Complete Interrupt
        }
        break;
    case 3:
        // Baudrate
        UBRR3H = (int8_t)(ubrr >> 8);
        UBRR3L = (int8_t)(ubrr & 0xFF);

        UCSR3A = (1 << U2X0);                   // Enable double speed
        UCSR3B = (1 << RXEN3) | (1 << TXEN3);   // Enable RX + TX
        UCSR3C = (1 << UCSZ31) | (1 << UCSZ30); // 8N1
        
        if(buffer_size > 0) 
        {
            if(NULL != uart3_rx_buffer) 
            {
                ringbuffer_destroy(uart3_rx_buffer); // Destroy existing buffer if it exists (e.g., re-initialization)
                uart3_rx_buffer = NULL;
            }
            uart3_rx_buffer = ringbuffer_create(buffer_size, sizeof(uint8_t));
            if (!uart3_rx_buffer) 
            {
                return UART_ERROR_INIT_FAILED;
            }
        }
        if((NULL != rx_callback) || (buffer_size > 0)) 
        {
            uart3_rx_callback = rx_callback;
            UCSR3B |= (1 << RXCIE3);            // Enable RX Complete Interrupt
        }
        break;
    default:
        return UART_ERROR_INIT_FAILED; // Invalid UART ID
    }
    return UART_OK;
}

uart_t uart_write_bytes(uart_id_t uart_id, uint8_t *data, uint8_t length)
{
    for(uint8_t i = 0; i < length; i++) 
    {
        uart_write_byte(uart_id, data[i]);
    }
    return UART_OK;
}


uart_t uart_write_byte(uart_id_t uart_id, uint8_t b)
{
    switch (uart_id)
    {
    case UART0_ID:
        while (!(UCSR0A & (1 << UDRE0))) { }  // vent til buffer tom
        UDR0 = b;
        break;
    case UART1_ID:
        while (!(UCSR1A & (1 << UDRE1))) { }  // vent til buffer tom
        UDR1 = b;
        break;
    case UART2_ID:
        while (!(UCSR2A & (1 << UDRE2))) { }  // vent til buffer tom
        UDR2 = b;
        break;
    case UART3_ID:
        while (!(UCSR3A & (1 << UDRE3))) { }  // vent til buffer tom
        UDR3 = b;
        break;
    default:
        return UART_ERROR_INVALID_ID; // Invalid UART ID
    }
    return UART_OK;
}

uart_t uart_read_byte_blocking(uart_id_t uart_id, uint8_t *byte)
{
    switch (uart_id)
    {
    case UART0_ID:
        while (!(UCSR0A & (1 << RXC0))) { }   // vent på modtaget byte
        *byte = UDR0;
        return UART_OK;
    case UART1_ID:
        while (!(UCSR1A & (1 << RXC1))) { }   // vent på modtaget byte
        *byte = UDR1;
        return UART_OK;
    case UART2_ID:
        while (!(UCSR2A & (1 << RXC2))) { }   // vent på modtaget byte
        *byte = UDR2;
        return UART_OK;
    case UART3_ID:
        while (!(UCSR3A & (1 << RXC3))) { }   // vent på modtaget byte
        *byte = UDR3;
        return UART_OK;
    }
    return UART_ERROR_INVALID_ID;
}

uart_t uart_read_byte(uart_id_t uart_id, uint8_t *byte)
{
    switch (uart_id)
    {
    case UART0_ID:
        if(!ringbuffer_pop(uart0_rx_buffer, byte)) 
        {
            return UART_NO_DATA_AVAILABLE;
        }
        break;
    case UART1_ID:
        if(!ringbuffer_pop(uart1_rx_buffer, byte)) 
        {
            return UART_NO_DATA_AVAILABLE;
        }
        break;
    case UART2_ID:
        if(!ringbuffer_pop(uart2_rx_buffer, byte)) 
        {
            return UART_NO_DATA_AVAILABLE;
        }
        break;
    case UART3_ID:
        if(!ringbuffer_pop(uart3_rx_buffer, byte)) 
        {
            return UART_NO_DATA_AVAILABLE;
        }
        break;
    default:
        return UART_ERROR_INVALID_ID;
    }
    return UART_OK;
}

uart_t uart_send_string_blocking(uart_id_t uart_id, const char* str)
{
    while(*str) 
    {
        uart_write_byte(uart_id, (uint8_t)(*str));
        str++;
    }
    return UART_OK;
}

ISR(USART0_RX_vect)
{
    uint8_t byte = UDR0;
    if(uart0_rx_buffer == NULL) 
    {
        // No ring buffer, just call callback if exists
        if(uart0_rx_callback != NULL) 
        {
            uart0_rx_callback(byte);
        }
    }
    else
    {
        // Push received byte into ring buffer.
        ringbuffer_push(uart0_rx_buffer, &byte);
        if(((byte == '\r') || (byte == '\n')) && (uart0_rx_callback != NULL)) 
        {
            uart0_rx_callback(byte); // Call callback on receipt of '\n'
        }
    }
}

ISR(USART1_RX_vect)
{
    uint8_t byte = UDR1;
    if(uart1_rx_buffer == NULL) 
    {
        // No ring buffer, just call callback if exists
        if(uart1_rx_callback != NULL) 
        {
            uart1_rx_callback(byte);
        }
    }
    else
    {
        // Push received byte into ring buffer.
        ringbuffer_push(uart1_rx_buffer, &byte);
        if((byte == '\n') && (uart1_rx_callback != NULL)) 
        {
            uart1_rx_callback(byte); // Call callback on receipt of '\n'
        }
    }
}

ISR(USART2_RX_vect)
{
    uint8_t byte = UDR2;
    if(uart2_rx_buffer == NULL) 
    {
        // No ring buffer, just call callback if exists
        if(uart2_rx_callback != NULL) 
        {
            uart2_rx_callback(byte);
        }
    }
    else
    {
        // Push received byte into ring buffer.
        ringbuffer_push(uart2_rx_buffer, &byte);
        if((byte == '\n') && (uart2_rx_callback != NULL)) 
        {
            uart2_rx_callback(byte); // Call callback on receipt of '\n'
        }
    }
}

ISR(USART3_RX_vect)
{
    uint8_t byte = UDR3;
    if(uart3_rx_buffer == NULL) 
    {
        // No ring buffer, just call callback if exists
        if(uart3_rx_callback != NULL) 
        {
            uart3_rx_callback(byte);
        }
    }
    else
    {
        // Push received byte into ring buffer.
        ringbuffer_push(uart3_rx_buffer, &byte);
        if((byte == '\n') && (uart3_rx_callback != NULL)) 
        {
            uart3_rx_callback(byte); // Call callback on receipt of '\n'
        }
    }
}
