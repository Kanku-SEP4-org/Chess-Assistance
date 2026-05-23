/**
 * @file communication.c
 * @brief Memory-safe communication layer with isolated runtime buffers.
 */

#include "communication.h"
#include "wifi.h"
#include "uart_stdio.h"
#include <stdio.h>
#include <string.h>
#include <util/delay.h>

#define TCP_BUFF_SIZE 128

static comm_mode_t current_mode = COMM_SERIAL;

// Separate memory arrays to prevent pointer collisions and connection drops
static char tcp_receive_buffer[TCP_BUFF_SIZE] = {0};
static char tcp_setup_ip_buffer[32] = {0};
static volatile bool new_tcp_packet_ready = false;

// Staging declaration linking communication.c back to the main processing core
extern void process_system_command(char command, uint16_t total_bytes, const char* full_buffer);

static void internal_wifi_packet_callback(void) {
    new_tcp_packet_ready = true;
}

void communication_init(void) {
    wifi_init();
    current_mode = COMM_SERIAL;
}

void communication_dev_autoconnect(const char* developer_name) {
    printf("Initializing auto-connect sequence for profile: %s...\n", developer_name);

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

    if (strcmp(developer_name, "ana") == 0) {
        transmit_data("NETWORK: ESP-01 adaptive link active. Connecting socket...\n");

        // Isolate the setup target parameters cleanly
        strcpy(tcp_setup_ip_buffer, "192.168.121.81");

        status = wifi_command_create_TCP_connection_n(
            tcp_setup_ip_buffer,
            23,
            internal_wifi_packet_callback,
            tcp_receive_buffer, // Isolated target destination data pointer array
            TCP_BUFF_SIZE
        );

        if (status != WIFI_OK) {
            transmit_data("NETWORK: Fresh TCP skipped. Forcing full credential handshake...\n");

            wifi_command_set_mode_to_1();
            _delay_ms(200);

            status = wifi_command_join_AP("Galley-fray", "elena276");
            _delay_ms(500);

            if (status == WIFI_OK) {
                status = wifi_command_create_TCP_connection_n(
                    tcp_setup_ip_buffer,
                    23,
                    internal_wifi_packet_callback,
                    tcp_receive_buffer,
                    TCP_BUFF_SIZE
                );
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
        // Echo a local trace down the YAT monitor lines for visibility
        printf("[TCP Inbound]: %s\n", tcp_receive_buffer);

        // Extract the first network character token as our instruction command
        char network_command = tcp_receive_buffer[0];

        // Inject the character directly into the central switch-case processor!
        process_system_command(network_command, strlen(tcp_receive_buffer), tcp_receive_buffer);

        // Clear flags and flush buffer for the next transaction
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
    char ssid[32] = {0};
    char password[32] = {0};
    char server_ip[32] = {0};

    int parsed_fields = sscanf(config_string, "%31[^,],%31[^,],%31[^\r\n]", ssid, password, server_ip);

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

    WIFI_ERROR_MESSAGE_t status = wifi_command_join_AP(ssid, password);
    _delay_ms(500);

    if (status == WIFI_OK) {
        strcpy(tcp_setup_ip_buffer, server_ip);
        status = wifi_command_create_TCP_connection_n(
            tcp_setup_ip_buffer,
            23,
            internal_wifi_packet_callback,
            tcp_receive_buffer,
            TCP_BUFF_SIZE
        );
    }

    if (status == WIFI_OK) {
        current_mode = COMM_WIFI;
        tcp_receive_buffer[0] = '\0';
        transmit_data("WIFI:CONNECTED\n");
    } else {
        current_mode = COMM_SERIAL;
        transmit_data("ERROR:WIFI_CONNECTION_FAILED\n");
    }
}