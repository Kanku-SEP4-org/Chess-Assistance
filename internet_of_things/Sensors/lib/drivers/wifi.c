/**
 * @file wifi.h
 * @author Laurits Ivar / Erland Larsen
 * @brief ESP8266 WiFi module interface using UART.
 * @version 0.9
 * @date 2023-08-23
 * Revision history: 0.1 - Initial version
 *                   0.9 - 2026-03-01 Refactored to use common uart driver
 * 
 * @copyright Copyright (c) 2026
 * 
 */
#include "wifi.h"
#include <string.h>
#include <stdbool.h>
#include <stdio.h>
#include <util/delay.h>
#include "uart.h"

#define WIFI_DATABUFFERSIZE 128
static uint8_t wifi_dataBuffer[WIFI_DATABUFFERSIZE];
static uint8_t wifi_dataBufferIndex;
static uint32_t wifi_baudrate;
static void (*_callback)(uint8_t byte);

static void wifi_TCP_callback(uint8_t byte);

static void wifi_callback(uint8_t received_byte)
{
    if(NULL != _callback)
        _callback(received_byte);
}
static void wifi_command_callback(uint8_t received_byte)
{
    wifi_dataBuffer[wifi_dataBufferIndex] = received_byte;
    wifi_dataBufferIndex++;
}

void wifi_init()
{
    wifi_baudrate = 115200;
    uart_init(UART2_ID, wifi_baudrate, wifi_callback, 0);
}

void static wifi_clear_databuffer_and_index()
{
    for (uint16_t i = 0; i < WIFI_DATABUFFERSIZE; i++)
        wifi_dataBuffer[i] = 0;
    wifi_dataBufferIndex = 0;
}

WIFI_ERROR_MESSAGE_t wifi_command(const char *str, uint16_t timeOut_s)
{
    void* callback_state = _callback;
    _callback = wifi_command_callback;

    char sendbuffer[128];
    strcpy(sendbuffer, str);

    uart_send_string_blocking(UART2_ID, strcat(sendbuffer, "\r\n"));

    for (uint16_t i = 0; i < timeOut_s * 100UL; i++) // timeout after 20 sec
    {
        _delay_ms(10);
        if (strstr((char *)wifi_dataBuffer, "OK\r\n") != NULL)
            break;
    }

    WIFI_ERROR_MESSAGE_t error;

    if (wifi_dataBufferIndex == 0)
        error=WIFI_ERROR_NOT_RECEIVING;
    else if (strstr((char *)wifi_dataBuffer, "OK") != NULL)
        error=WIFI_OK;
    else if (strstr((char *)wifi_dataBuffer, "ERROR") != NULL)
        error= WIFI_ERROR_RECEIVED_ERROR;
    else if (strstr((char *)wifi_dataBuffer, "FAIL") != NULL)
        error= WIFI_FAIL;
    else
        error= WIFI_ERROR_RECEIVING_GARBAGE;
    
    wifi_clear_databuffer_and_index();
    _callback = callback_state;
    return error; 
}

WIFI_ERROR_MESSAGE_t wifi_command_AT()
{
    return wifi_command("AT", 1);
}

WIFI_ERROR_MESSAGE_t wifi_command_join_AP(char *ssid, char *password)
{
   /* WIFI_ERROR_MESSAGE_t error = wifi_command_AT();
    if (error != WIFI_OK)
        return error;*/

    char sendbuffer[128];
    strcpy(sendbuffer, "AT+CWJAP=\"");
    strcat(sendbuffer, ssid);
    strcat(sendbuffer, "\",\"");
    strcat(sendbuffer, password);
    strcat(sendbuffer, "\"");

    return wifi_command(sendbuffer, 20);
}

WIFI_ERROR_MESSAGE_t wifi_command_disable_echo()
{
    return wifi_command("ATE0", 1);
}

WIFI_ERROR_MESSAGE_t wifi_command_get_ip_from_URL(char * url, char *ip_address){
    char sendbuffer[128];
    strcpy(sendbuffer, "AT+CIPDOMAIN=\"");
    strcat(sendbuffer, url);
    strcat(sendbuffer, "\"");
    
    uint16_t timeOut_s = 5;

    void* callback_state = _callback;
    _callback = wifi_command_callback;

    uart_send_string_blocking(UART2_ID, strcat(sendbuffer, "\r\n"));

    for (uint16_t i = 0; i < timeOut_s * 100UL; i++) // timeout after 20 sec
    {
        _delay_ms(10);
        if (strstr((char *)wifi_dataBuffer, "OK\r\n") != NULL)
            break;
    }

    WIFI_ERROR_MESSAGE_t error;

    if (wifi_dataBufferIndex == 0)
        error=WIFI_ERROR_NOT_RECEIVING;
    else if (strstr((char *)wifi_dataBuffer, "OK") != NULL)
        error=WIFI_OK;
    else if (strstr((char *)wifi_dataBuffer, "ERROR") != NULL)
        error= WIFI_ERROR_RECEIVED_ERROR;
    else if (strstr((char *)wifi_dataBuffer, "FAIL") != NULL)
        error= WIFI_FAIL;
    else
        error= WIFI_ERROR_RECEIVING_GARBAGE;
    
   
    char *ipStart = strstr((char *)wifi_dataBuffer, "CIPDOMAIN:");
    if (ipStart != NULL) {
        // Move the pointer to the start of the IP address
        ipStart += strlen("CIPDOMAIN:");

        // Find the end of the IP address (assuming it ends with a newline)
        char * ipEnd = strchr(ipStart, '\r');
        if (ipEnd != NULL && (ipEnd - ipStart) < 16) {
            // Copy the IP address into the buffer
            strncpy(ip_address, ipStart, ipEnd - ipStart);
            ip_address[ipEnd - ipStart] = '\0';
            
        } }

    wifi_clear_databuffer_and_index();
    _callback = callback_state;
    return error; 
}


WIFI_ERROR_MESSAGE_t wifi_command_quit_AP(){

    return wifi_command("AT+CWQAP", 5);
}

WIFI_ERROR_MESSAGE_t wifi_command_set_mode_to_1()
{
    return wifi_command("AT+CWMODE=1", 1);
}

WIFI_ERROR_MESSAGE_t wifi_command_set_to_single_Connection()
{
    return wifi_command("AT+CIPMUX=0", 1);
}

WIFI_ERROR_MESSAGE_t wifi_command_close_TCP_connection()
{
    return wifi_command("AT+CIPCLOSE", 5);
}


#define BUF_SIZE 128
#define IPD_PREFIX "+IPD,"
#define PREFIX_LENGTH 5

WIFI_TCP_Callback_t callback_when_message_received_static;
char *received_message_buffer_static_pointer;
static void  wifi_TCP_callback(uint8_t byte)
{
    static enum { IDLE, MATCH_PREFIX, LENGTH, DATA } state = IDLE;
    static int length = 0, index = 0, prefix_index = 0;

    switch(state) {
        case IDLE:
            if(byte == IPD_PREFIX[0]) {
                state = MATCH_PREFIX;
                prefix_index = 1;
            }
            break;

        case MATCH_PREFIX:
            if(byte == IPD_PREFIX[prefix_index]) {
                if(prefix_index == PREFIX_LENGTH - 1) {
                    state = LENGTH;
                } else {
                    prefix_index++;
                }
            } else {
                // not the expected character, reset to IDLE
                state = IDLE;
                prefix_index = 0;
            }
            break;

        case LENGTH:
            if(byte >= '0' && byte <= '9') {
                length = length * 10 + (byte - '0');
            } else if(byte == ':') {
                state = DATA;
                index = 0; // reset index to start storing data
            } else {
                // not the expected character, reset to IDLE
                state = IDLE;
                length = 0;
            }
            break;

        case DATA:
            if(index < length) {
                received_message_buffer_static_pointer[index++] = byte;
            }
            if(index == length) {
                // message is complete, null terminate the string
                received_message_buffer_static_pointer[index] = '\0';

                // reset to IDLE
                state = IDLE;
                length = 0;
                index = 0;

            wifi_clear_databuffer_and_index();
            callback_when_message_received_static();
            }
            break;
    }
  
}

WIFI_ERROR_MESSAGE_t wifi_command_create_TCP_connection(char *IP, uint16_t port, WIFI_TCP_Callback_t callback_when_message_received, char *received_message_buffer)
{
    received_message_buffer_static_pointer = received_message_buffer;
    callback_when_message_received_static = callback_when_message_received;
    char sendbuffer[128];
    char portString[7];

    strcpy(sendbuffer, "AT+CIPSTART=\"TCP\",\"");
    
    strcat(sendbuffer, IP);
    strcat(sendbuffer, "\",");
    sprintf(portString, "%u", port);
    strcat(sendbuffer, portString);

    WIFI_ERROR_MESSAGE_t errorMessage = wifi_command(sendbuffer, 20);
    if (errorMessage != WIFI_OK)
        return errorMessage;
    else
        _callback = wifi_TCP_callback;

    wifi_clear_databuffer_and_index();
    return errorMessage;
}

WIFI_ERROR_MESSAGE_t wifi_command_TCP_transmit(uint8_t * data, uint16_t length)
{
    char sendbuffer[128];
    char portString[7];
    strcpy(sendbuffer, "AT+CIPSEND=");
    sprintf(portString, "%u", length);
    strcat(sendbuffer, portString);

    WIFI_ERROR_MESSAGE_t errorMessage = wifi_command(sendbuffer, 20);
    if (errorMessage != WIFI_OK)
        return errorMessage;
    
    uart_write_bytes(UART2_ID, data, length);
    return WIFI_OK;
}
