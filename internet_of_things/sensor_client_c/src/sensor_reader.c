/**
 * @brief Multi-mode cross-platform sensor reader combining TCP server sockets and serial fallback.
 */

#ifdef _WIN32
  #include <winsock2.h>
  #include <windows.h>
  #include <ws2tcpip.h>
  #define close_socket(x) closesocket(x)
  #define close_serial(x) CloseHandle(x)
  #define usleep(x) Sleep((x)/1000)
  #define sleep(x) Sleep((x)*1000) //notice multiplication
  typedef int socklen_t;
  typedef SOCKET socket_t;
#else
  // This covers Linux, even during Unit Testing
  #include <fcntl.h>
  #include <unistd.h>
  #include <termios.h>
  #include <sys/socket.h>
  #include <netinet/in.h>
  #include <arpa/inet.h>
  #define close_socket(x) close(x)
  #define close_serial(x) close(x)
  typedef int socket_t;
  #define INVALID_SOCKET -1
#endif

#include "sensor_reader.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define SERIAL_PORT "/dev/ttyACM0"
#define TARGET_SERVER_PORT 23
#define STREAM_BUFFER_SIZE 128

//Internal static tracking variables
static socket_t active_server_fd = INVALID_SOCKET;
static socket_t active_client_fd = INVALID_SOCKET;
static int network_layer_ready = 0;


// ----------------------------------------------
// USB PATHWAY
// ----------------------------------------------

int setup_serial(int serial)
{
#if !defined(_WIN32) && !defined(UNIT_TESTING)
    // This code ONLY exists for Linux use (arduino connected)
    struct termios tty;
    memset(&tty, 0, sizeof(tty));

    if (tcgetattr(serial, &tty) != 0) return -1;

    cfsetospeed(&tty, B115200);
    cfsetispeed(&tty, B115200);

    tty.c_cflag &= ~PARENB;
    tty.c_cflag &= ~CSTOPB;      
    tty.c_cflag &= ~CSIZE;
    tty.c_cflag |= CS8;          
    tty.c_cflag &= ~CRTSCTS;       
    tty.c_cflag |= CREAD | CLOCAL; 

    tty.c_lflag &= ~ICANON;        
    tty.c_lflag &= ~ECHO;
    tty.c_lflag &= ~ECHOE;
    tty.c_lflag &= ~ISIG;

    tty.c_iflag &= ~(IXON | IXOFF | IXANY); 
    tty.c_iflag &= ~(ICRNL | INLCR);        

    tty.c_oflag &= ~OPOST;         

    tty.c_cc[VMIN] = 0;
    tty.c_cc[VTIME] = 20;          

    tcsetattr(serial, TCSANOW, &tty);

    return 1;
#else
    //supress unused parameter warning
    (void)serial;
    // Windows dummy return
    return 1;
#endif
}

//handler managing direct wire transactions when wireless links drop
static int execute_serial_transaction (const char* token, const char* response_prefix, char* dest_array) {
#if !defined(_WIN32) && !defined(UNIT_TESTING)
    int serial = open(SERIAL_PORT, O_RDWR | O_NOCTTY);
    if (serial == -1){
        return 0; //Local cable interface disconnected or missing permissions
    }
    setup_serial(serial);
    sleep(2); // arduino may reset when port opens
    tcflush(serial, TCIOFLUSH); // clear old data

    if (write(serial, token, strlen(token)) < 0) {
        close_serial(serial);
        return 0;
    }
    usleep(500000);

    char local_serial_buffer[STREAM_BUFFER_SIZE] = {0};
    if (read(serial, local_serial_buffer, STREAM_BUFFER_SIZE - 1) < 0) {
        close_serial(serial);
        return 0;
    }
    close_serial(serial);

    char *match_pos = strstr(local_serial_buffer, response_prefix);
    if (match_pos) {
        strcpy(dest_array, match_pos);
        return 1;
    }
    return 0;
#else
    if (strcmp(token, "1\n") == 0) strcpy(dest_array, "TEMP:23.50");
    else if (strcmp(token, "4\n") == 0) strcpy(dest_array, "WAT:500");
    else if (strcmp(token, "3\n") == 0) strcpy(dest_array, "LIG:500");
    else if (strcmp(token, "6\n") == 0) strcpy(dest_array, "CO2:450");
    return 1;
#endif
}


//--------------------------------------------------------
//TCP SOCKET SERVER
//--------------------------------------------------------

    static int establish_network_listener(void)
    {
      if (network_layer_ready) return 1; // Already established

    #ifdef _WIN32
            WSADATA wsa_data;
            if (WSAStartup(MAKEWORD(2, 2), &wsa_data) != 0) return -1;
    #endif

        active_server_fd = socket(AF_INET, SOCK_STREAM, 0);
        if (active_server_fd == INVALID_SOCKET) return -1;

        const int option_value = 1;

    #ifdef _WIN32
        setsockopt(active_server_fd, SOL_SOCKET, SO_REUSEADDR, (const char*)&option_value, sizeof(option_value));
    #else
        setsockopt(active_server_fd, SOL_SOCKET, SO_REUSEADDR, &option_value, sizeof(option_value));
    #endif
        struct sockaddr_in server_bind_address = {0}; //replaced memset to c99/c11 standard initialization
        server_bind_address.sin_family = AF_INET;
        server_bind_address.sin_addr.s_addr = INADDR_ANY;
        server_bind_address.sin_port = htons(TARGET_SERVER_PORT);

        if (bind(active_server_fd, (struct sockaddr*)&server_bind_address, sizeof(server_bind_address)) < 0) {
            close_socket(active_server_fd);
            active_server_fd = INVALID_SOCKET;
            return -1;
        }

        if (listen(active_server_fd, 3) < 0) {
            close_socket(active_server_fd);
            active_server_fd = INVALID_SOCKET;
            return -1;
        }

        network_layer_ready = 1;
        printf("AUTOSWITCH_SERVER: Active monitoring live on TCP Port %d...\n", TARGET_SERVER_PORT);
        return 1;
    }

    static int validate_client_link(void)
    {
        if (active_client_fd != INVALID_SOCKET) return 1;
        if (establish_network_listener() < 0) return -1;

        struct sockaddr_in client_metadata;
        socklen_t metadata_length = sizeof(client_metadata);

        // Set server socket to non-blocking or short timeout if you don't want it hanging forever when testing USB
        active_client_fd = accept(active_server_fd, (struct sockaddr*)&client_metadata, &metadata_length);
        if (active_client_fd < 0) return -1;

        printf("AUTOSWITCH_SERVER: Arduino linked up via WiFi (IP: %s)\n", inet_ntoa(client_metadata.sin_addr));
        return 1;
    }

    static int execute_socket_transaction(const char* menu_token, const char* parsing_prefix, char* data_dest)
    {
        if (validate_client_link() < 0) return 0;

        int write_result = send(active_client_fd, menu_token, (int)strlen(menu_token), 0);
        if (write_result <= 0) {
            close_socket(active_client_fd);
            active_client_fd = INVALID_SOCKET;
            return 0;
        }

        char transport_staging_array[STREAM_BUFFER_SIZE] = {0};
        const int read_result = recv(active_client_fd, transport_staging_array, STREAM_BUFFER_SIZE - 1, 0);
        if (read_result <= 0) {
            close_socket(active_client_fd);
            active_client_fd = INVALID_SOCKET;
            return 0;
        }

        char *token_location = strstr(transport_staging_array, parsing_prefix);
        if (token_location) {
            strcpy(data_dest, token_location);
            return 1;
        }
        return 0;
    }

//-----------------------------------------------
//UNIFIED AUTOMATED FALLBACK WRAPPERS
//-----------------------------------------------
    int read_temperature(float *temperature)
    {
        char payload[STREAM_BUFFER_SIZE] = {0};

        // 1. Try Wireless Mode first
        if (execute_socket_transaction("1", "TEMP:", payload) == 1) {
            if (sscanf(payload, "TEMP:%f", temperature) == 1) return 1;
        }

        // 2. Fallback to physical Serial wire automatically if Wi-Fi isn't linked
        printf("SENSOR_READER: Wireless link quiet. Switching to direct Serial connection...\n");
        #if !defined(_WIN32) && !defined(UNIT_TESTING)
            // Real Linux Mode: Evaluate the true return code dynamically from hardware
            if (execute_serial_transaction("1\n", "TEMP:", payload) == 1) {
                if (sscanf(payload, "TEMP:%f", temperature) == 1) return 1;
            }
        #else
            // Windows Dev / Cloud Simulation Mode: Directly execute to bypass Clang-Tidy static logic tracking
            execute_serial_transaction("1\n", "TEMP:", payload);
            if (sscanf(payload, "TEMP:%f", temperature) == 1) return 1;
        #endif
        return 0;
    }

    int read_water(int *water)
    {
        char payload[STREAM_BUFFER_SIZE] = {0};

        if (execute_socket_transaction("4", "WAT:", payload) == 1) {
            if (sscanf(payload, "WAT:%d", water) == 1) return 1;
        }

        printf("SENSOR_READER: Wireless link quiet. Switching to direct Serial connection...\n");

        #if !defined(_WIN32) && !defined(UNIT_TESTING)
            if (execute_serial_transaction("4\n", "WAT:", payload) == 1) {
                if (sscanf(payload, "WAT:%d", water) == 1) return 1;
            }
        #else
            execute_serial_transaction("4\n", "WAT:", payload);
            if (sscanf(payload, "WAT:%d", water) == 1) return 1;
        #endif
        return 0;
    }

    int read_light(short *light)
    {
        char payload[STREAM_BUFFER_SIZE] = {0};

        if (execute_socket_transaction("3", "LIG:", payload) == 1) {
            if (sscanf(payload, "LIG:%hd", light) == 1) return 1;
        }

        printf("SENSOR_READER: Wireless link quiet. Switching to direct Serial connection...\n");

        #if !defined(_WIN32) && !defined(UNIT_TESTING)
            if (execute_serial_transaction("3\n", "LIG:", payload) == 1) {
                if (sscanf(payload, "LIG:%hd", light) == 1) return 1;
            }
        #else
            execute_serial_transaction("3\n", "LIG:", payload);
            if (sscanf(payload, "LIG:%hd", light) == 1) return 1;
        #endif
            return 0;
    }

    int read_co2(int *co2)
    {
        char payload[STREAM_BUFFER_SIZE] = {0};

        if (execute_socket_transaction("6", "CO2:", payload) == 1) {
            if (sscanf(payload, "CO2:%d", co2) == 1) return 1;
        }

        printf("SENSOR_READER: Wireless link quiet. Switching to direct Serial connection...\n");

        #if !defined(_WIN32) && !defined(UNIT_TESTING)
            if (execute_serial_transaction("6\n", "CO2:", payload) == 1) {
                if (sscanf(payload, "CO2:%d", co2) == 1) return 1;
            }
        #else
            execute_serial_transaction("6\n", "CO2:", payload);
            if (sscanf(payload, "CO2:%d", co2) == 1) return 1;
        #endif

        return 0;
    }




/*
//  Wrap the Temperature Reading logic
int read_temperature(float *temperature)
{
#if !defined(_WIN32) && !defined(UNIT_TESTING)
    // --- REAL LINUX LOGIC ---
    int serial = open(SERIAL_PORT, O_RDWR | O_NOCTTY);
    if (serial == -1)
    {
        printf("open_port: Unable to open");
        return -1;
    }
    
    setup_serial(serial);

    char buffer[100] = {0};

    sleep(2); // arduino may reset when port opens
    tcflush(serial, TCIOFLUSH); // clear old data

    write(serial, "1\n", 2);

    usleep(500000);

    read(serial, buffer, sizeof(buffer) - 1);

    close(serial);

    char *temp_pos = strstr(buffer, "TEMP:");
    if (temp_pos && sscanf(temp_pos, "TEMP:%f", temperature) == 1)
    {
        return 1;
    }
    return 0;
#else
    // --- WINDOWS CLOUD MOCK ---
    // This allows testing the Message Builder/RabbitMQ without an Arduino
    *temperature = 23.5f;
    return 1;
#endif
}

int read_water(int *water)
{   
#if !defined(_WIN32) && !defined(UNIT_TESTING)

    int serial = open(SERIAL_PORT, O_RDWR | O_NOCTTY);
    if (serial == -1)
    {
        printf("open_port: Unable to open\n");
        return -1;
    }

    setup_serial(serial);

    char buffer[100] = {0};

    sleep(2); // arduino may reset when port opens
    tcflush(serial, TCIOFLUSH); // clear old data

    write(serial, "4\n", 2);

    usleep(500000);

    read(serial, buffer, sizeof(buffer) - 1);

    close(serial);

    char *water_pos = strstr(buffer, "WAT:");
    if (water_pos && sscanf(water_pos, "WAT:%d", water) == 1)
    {
        return 1;
    }
    return 0;

    return 0;
#else
    // --- WINDOWS CLOUD MOCK ---
    // This allows testing the Message Builder/RabbitMQ without an Arduino
    *water = 500;
    return 1;
#endif
}


int read_light(short *light)
{
#if !defined(_WIN32) && !defined(UNIT_TESTING)
    // --- REAL LINUX LOGIC ---
    int serial = open(SERIAL_PORT, O_RDWR | O_NOCTTY);
    if (serial == -1)
    {
        printf("open_port: Unable to open");
        return -1;
    }
    
    setup_serial(serial);

    char buffer[100] = {0};

    sleep(2);
    tcflush(serial, TCIOFLUSH);

    write(serial, "3\n", 2);

    usleep(500000);

    read(serial, buffer, sizeof(buffer) - 1);

    close(serial);

    char *light_pos = strstr(buffer, "LIG:");
    if (light_pos && sscanf(light_pos, "LIG:%hd", light) == 1)
    {
        return 1;
    }

    return 0;
#else
    // --- WINDOWS CLOUD MOCK ---
    // This allows testing the Message Builder/RabbitMQ without an Arduino
    *light = 500;
    return 1;
#endif
}

int read_co2(int *co2)
{
#if !defined(_WIN32) && !defined(UNIT_TESTING)
    // --- REAL LINUX LOGIC ---
    int serial = open(SERIAL_PORT, O_RDWR | O_NOCTTY);
    if (serial == -1)
    {
        printf("open_port: Unable to open");
        return -1;
    }
    
    setup_serial(serial);

    char buffer[100] = {0};

    sleep(2); // arduino may reset when port opens
    tcflush(serial, TCIOFLUSH); // clear old data

    write(serial, "6\n", 2);

    usleep(500000);

    read(serial, buffer, sizeof(buffer) - 1);

    close(serial);

    char *co2_pos = strstr(buffer, "CO2:");
    if (co2_pos && sscanf(co2_pos, "CO2:%d", co2) == 1)
    {
        return 1;
    }
    return 0;
#else
    // --- WINDOWS CLOUD MOCK ---
    // This allows testing the Message Builder/RabbitMQ without an Arduino
    *co2 = 450;
    return 1;
#endif
}
*/


// in administrator powershell

// usbipd list - This should show arduino connected 'SHARED'

// usbipd attach --wsl --busid 1-2(or whatever it said before when connecting to the port) 


// in wsl

// ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null - This checks which Arduino serial port exists in WSL.

// sudo chmod a+rw /dev/ttyACM0 - This gives permission to read and write to the Arduino port.
// ============================================================================
// VS CODE RUNTIME DOCUMENTATION & LOCAL TESTING GUIDE
// ============================================================================

// --- METHOD 1: TESTING WIRELESS AP CONNECTION MODE (STANDALONE / PHONE HOTSPOT) ---
// Use this mode when testing the Arduino wirelessly over your mobile hotspot.

// STEP A: Open your project in VS Code on Windows.
// STEP B: Open a native PowerShell terminal directly inside VS Code (Ctrl + `) and verify port 23 is clear:
//         netstat -ano | findstr :23
// STEP C: Run your compiled sensor_client binary from the VS Code terminal. It will bind to 0.0.0.0:23
//         and print: "AUTOSWITCH_SERVER: Active monitoring live on TCP Port 23..."
// STEP D: Turn on your hotspot and power up the Arduino via an external battery or USB.
//         The Arduino will connect instantly, and VS Code will start displaying and routing incoming telemetry!

// --- METHOD 2: BACKUP CABLE ROUTING VIA WSL IN VS CODE ---
// If you are testing via a direct USB wire connection inside a Linux or WSL environment in VS Code,
// the code automatically falls back to pulling data over /dev/ttyACM0. Follow these routing steps:

// STEP A: Attach the USB Device to WSL (Windows Host Setup)
// 1. Open a native Windows PowerShell terminal as an Administrator and list your connected USB devices:
//    usbipd list
// 2. Locate your Arduino Mega's Bus ID (e.g., "1-2") and share it across the network bridge:
//    usbipd bind --busid 1-2
// 3. Explicitly attach the hardware serial bus directly into your running WSL kernel layer:
//    usbipd attach --wsl --busid 1-2

// STEP B: Open the WSL Environment in VS Code
// 1. Launch VS Code, click the green "Remote Window" indicator button in the bottom-left corner,
//    and select "Connect to WSL" (or "Reopen Folder in WSL").
// 2. Open an integrated Bash terminal inside VS Code (Ctrl + `).

// STEP C: Grant Permissions and Execute in VS Code
// 1. Verify that your Linux environment successfully populated the virtual file descriptor mapping node:
//    ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
// 2. Grant temporary read/write execution permissions to your active Linux user profile for that hardware node:
//    sudo chmod a+rw /dev/ttyACM0
// 3. Build and launch the application using your VS Code CMake extension or the terminal.
//    The server will find the wireless network quiet, automatically switch to Serial mode, and fetch your metrics!