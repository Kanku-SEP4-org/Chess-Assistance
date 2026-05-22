

#include "communication.h"
#include "wifi.h"
#include "uart_stdio.h"
#include <stdio.h>
#include <string.h>
#include <util/delay.h>

#define TCP_BUFF_SIZE 128
#define CONFIG_BUFF_SIZE 32

// Configuration states for end-users
typedef enum {
    STATE_READY,
    STATE_REQ_SSID,
    STATE_REQ_PASS,
    STATE_REQ_IP
} config_state_t;

static comm_mode_t current_mode = COMM_SERIAL;
static char tcp_received_payload[TCP_BUFF_SIZE] = {0};
static volatile bool new_tcp_packet_ready = false;

// Internal callback that fires immediately when the ESP8266 completes a TCP packet stream
static void internal_wifi_packet_callback(void) {
    new_tcp_packet_ready = true;
}

void communication_init(void) {
    wifi_init(); // Initialize UART2 under the hood at 115200 baud
    current_mode = COMM_SERIAL;
}

void communication_dev_autoconnect(const char* developer_name) {
    printf("Initializing auto-connect sequence for profile: %s...\n", developer_name);

    WIFI_ERROR_MESSAGE_t status = WIFI_FAIL;

    if (strcmp(developer_name, "ana") == 0) {
        wifi_command_join_AP("Galley-fray", "elena276");
        status = wifi_command_create_TCP_connection("192.168.206.81", 23, internal_wifi_packet_callback, tcp_received_payload);
    }
    if (strcmp(developer_name, "dawid") == 0) {
        wifi_command_join_AP("SSID", "PASSWORD");
        status = wifi_command_create_TCP_connection("192.168.1.XX", 23, internal_wifi_packet_callback, tcp_received_payload);
    }
    if (strcmp(developer_name, "natalia") == 0) {
        wifi_command_join_AP("SSID", "PASSWORD");
        status = wifi_command_create_TCP_connection("192.168.1.XX", 23, internal_wifi_packet_callback, tcp_received_payload);
    }
    if (strcmp(developer_name, "vanessa") == 0) {
        wifi_command_join_AP("SSID", "PASSWORD");
        status = wifi_command_create_TCP_connection("192.168.1.XX", 23, internal_wifi_packet_callback, tcp_received_payload);
    }

    if (status == WIFI_OK) {
        current_mode = COMM_WIFI;
        transmit_data("SYSTEM_STATUS:WIFI_TCP_ONLINE\n");
    } else {
        printf("Auto-connect failed with error code: %d. Falling back to USB Serial.\n", status);
        current_mode = COMM_SERIAL;
    }
}

void communication_poll_network(void) {
    // Check if the background ISR has flipped the network processing flag
    if (new_tcp_packet_ready) {
        // Echo the packet back or handle remote commands here
        printf("[TCP Inbound]: %s\n", tcp_received_payload);

        // Clear flags and flush buffer for the next transaction
        new_tcp_packet_ready = false;
        tcp_received_payload[0] = '\0';
    }
}

void transmit_data(const char* str) {
    if (current_mode == COMM_WIFI) {
        // Transmit data seamlessly over the TCP socket buffer via UART2
        wifi_command_TCP_transmit((uint8_t*)str, strlen(str));
    } else {
        // Standard system fallback directly out to the USB terminal via UART0
        printf("%s", str);
    }
}

//USER function
void communication_connect_wifi(const char *config_string) {
    char ssid[32] = {0};
    char password[32] = {0};
    char server_ip[32] = {0};

    // Parse the comma-separated string format: "SSID,PASSWORD,SERVER_IP"
    int parsed_fields = sscanf(config_string, "%31[^,],%31[^,],%31[^\r\n]", ssid, password, server_ip);

    // If the computer sent a partial or broken string, reject it immediately
    if (parsed_fields != 3) {
        transmit_data("ERROR:WIFI_PAYLOAD_PARSE_FAILED\n");
        return;
    }

    // Pass the parsed variables directly into your underlying WiFi driver
    wifi_command_join_AP(ssid, password);
    WIFI_ERROR_MESSAGE_t status = wifi_command_create_TCP_connection(server_ip, 23, internal_wifi_packet_callback, tcp_received_payload);

    if (status == WIFI_OK) {
        current_mode = COMM_WIFI;
        transmit_data("WIFI:CONNECTED\n");
    } else {
        current_mode = COMM_SERIAL;
        transmit_data("ERROR:WIFI_CONNECTION_FAILED\n");
    }
}