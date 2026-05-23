/**
 * @file communication.c
 * @brief Secure communication provisioning layer with persistent EEPROM caching.
 */

#include "credentials_private.h" //git-ignored configuration layer

#include "communication.h"
#include "wifi.h"
#include "uart_stdio.h"
#include <stdio.h>
#include <string.h>
#include <util/delay.h>
#include <avr/eeprom.h>          // Native AVR flash storage engine

#define TCP_BUFF_SIZE 128

static comm_mode_t current_mode = COMM_SERIAL;
static char tcp_receive_buffer[TCP_BUFF_SIZE] = {0};
static char tcp_setup_ip_buffer[32] = {0};
static volatile bool new_tcp_packet_ready = false;
static int port = 23; //localized for easy edit and DRY compliance

// EEPROM Memory Mapping Structure
// for user stable connection
typedef struct {
    uint16_t magic;
    char ssid[EEPROM_STR_LEN];
    char password[EEPROM_STR_LEN];
    char server_ip[EEPROM_STR_LEN];
} user_credentials_t;

// static memory block inside the physical EEPROM space
user_credentials_t EEMEM eeprom_storage;

extern void process_system_command(char command, uint16_t total_bytes, const char* full_buffer);

static void internal_wifi_packet_callback(void) {
    new_tcp_packet_ready = true;
}

void communication_init(void) {
    wifi_init();
    current_mode = COMM_SERIAL;
}

void communication_dev_autoconnect(const char* developer_name) {
    printf("Booting communication layer. Checking network provisions...\n");

    for (uint8_t i = 0; i < 4; i++) {
        _delay_ms(1000);
    }

    uint8_t garbage_flush;
    while (uart_read_byte(UART2_ID, &garbage_flush) == UART_OK);
    wifi_command_disable_echo();
    _delay_ms(200);
    wifi_command_close_TCP_connection();
    _delay_ms(500);

    WIFI_ERROR_MESSAGE_t status = WIFI_ERROR_NOT_RECEIVING;
    user_credentials_t runtime_config;

    // SCENARIO A: Look for user-saved credentials in the EEPROM first
    eeprom_read_block(&runtime_config, &eeprom_storage, sizeof(user_credentials_t));

    if (runtime_config.magic == EEPROM_MAGIC_NUM) {
        transmit_data("NETWORK: Saved user profile located in EEPROM. Loading cached links...\n");
        strcpy(tcp_setup_ip_buffer, runtime_config.server_ip);

        // Attempt immediate connection utilizing the ESP-01 hardware auto-link background state
        status = wifi_command_create_TCP_connection_n(tcp_setup_ip_buffer, port, internal_wifi_packet_callback, tcp_receive_buffer, TCP_BUFF_SIZE);

        if (status != WIFI_OK) {
            transmit_data("NETWORK: Cached TCP failed. Re-authenticating credentials...\n");
            wifi_command_set_mode_to_1();
            _delay_ms(200);
            status = wifi_command_join_AP(runtime_config.ssid, runtime_config.password);
            _delay_ms(500);
            if (status == WIFI_OK) {
                status = wifi_command_create_TCP_connection_n(tcp_setup_ip_buffer, port, internal_wifi_packet_callback, tcp_receive_buffer, TCP_BUFF_SIZE);
            }
        }
    }
    // If no user credentials found, fallback safely to git-ignored developer macro flags
    else if (strcmp(developer_name, DEV_PROFILE_NAME) == 0) {
        transmit_data("NETWORK: No active user profile. Loading private developer profile...\n");
        strcpy(tcp_setup_ip_buffer, DEV_SERVER_IP);

        status = wifi_command_create_TCP_connection_n(tcp_setup_ip_buffer, port, internal_wifi_packet_callback, tcp_receive_buffer, TCP_BUFF_SIZE);

        if (status != WIFI_OK) {
            wifi_command_set_mode_to_1();
            _delay_ms(200);
            status = wifi_command_join_AP(DEV_WIFI_SSID, DEV_WIFI_PASS);
            _delay_ms(500);
            if (status == WIFI_OK) {
                status = wifi_command_create_TCP_connection_n(tcp_setup_ip_buffer, port, internal_wifi_packet_callback, tcp_receive_buffer, TCP_BUFF_SIZE);
            }
        }
    }

    if (status == WIFI_OK) {
        current_mode = COMM_WIFI;
        tcp_receive_buffer[0] = '\0';
        transmit_data("SYSTEM_STATUS:WIFI_TCP_ONLINE\n");
    } else {
        printf("Auto-connect failed with error code: %d. Falling back to USB Serial.\n", status);
        current_mode = COMM_SERIAL;
    }
}

void communication_poll_network(void) {
    if (new_tcp_packet_ready) {
        printf("[TCP Inbound]: %s\n", tcp_receive_buffer);
        char network_command = tcp_receive_buffer[0];
        process_system_command(network_command, strlen(tcp_receive_buffer), tcp_receive_buffer);
        new_tcp_packet_ready = false;
        tcp_receive_buffer[0] = '\0';
    }
}

void transmit_data(const char* str) {
    if (current_mode == COMM_WIFI) {
        wifi_command_TCP_transmit((uint8_t*)str, strlen(str));
    } else {
        printf("%s", str);
    }
}

void communication_connect_wifi(const char *config_string) {
    user_credentials_t new_config;
    new_config.magic = EEPROM_MAGIC_NUM;

    // Parse incoming user configurations safely into the memory block layout
    int parsed_fields = sscanf(config_string, "%31[^,],%31[^,],%31[^\r\n]", new_config.ssid, new_config.password, new_config.server_ip);

    if (parsed_fields != 3) {
        transmit_data("ERROR:WIFI_PAYLOAD_PARSE_FAILED\n");
        return;
    }

    uint8_t garbage_flush;
    while (uart_read_byte(UART2_ID, &garbage_flush) == UART_OK);
    wifi_command_disable_echo();
    _delay_ms(200);
    wifi_command_close_TCP_connection();
    _delay_ms(500);

    wifi_command_set_mode_to_1();
    _delay_ms(200);

    WIFI_ERROR_MESSAGE_t status = wifi_command_join_AP(new_config.ssid, new_config.password);
    _delay_ms(500);

    if (status == WIFI_OK) {
        strcpy(tcp_setup_ip_buffer, new_config.server_ip);
        status = wifi_command_create_TCP_connection_n(tcp_setup_ip_buffer, port, internal_wifi_packet_callback, tcp_receive_buffer, TCP_BUFF_SIZE);
    }

    if (status == WIFI_OK) {
        // CRITICAL STEP: Write parsed values into internal EEPROM memory blocks permanently
        eeprom_write_block(&new_config, &eeprom_storage, sizeof(user_credentials_t));

        current_mode = COMM_WIFI;
        tcp_receive_buffer[0] = '\0';
        transmit_data("WIFI:CONNECTED_AND_SAVED_TO_EEPROM\n");
    } else {
        current_mode = COMM_SERIAL;
        transmit_data("ERROR:WIFI_CONNECTION_FAILED\n");
    }
}