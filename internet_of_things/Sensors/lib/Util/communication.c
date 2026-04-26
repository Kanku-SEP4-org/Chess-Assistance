#include "communication.h"
#include "wifi.h"

void transmit_data(char* str) {
    #ifdef USE_WIFI
        wifi_command_TCP_transmit((uint8_t*)str, strlen(str)); // Send data over WiFi
    #else
        printf("%s", str); // Default to USB/Serial
    #endif
}