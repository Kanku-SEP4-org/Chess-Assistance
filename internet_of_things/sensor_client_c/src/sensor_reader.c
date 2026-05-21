#ifdef _WIN32
  #include <windows.h>
  #define usleep(x) Sleep((x)/1000)
#else
  // This covers Linux, even during Unit Testing
  #include <fcntl.h>
  #include <unistd.h>
  #include <termios.h>
#endif

#include "sensor_reader.h"
#include <stdio.h>
#include <string.h>

#define SERIAL_PORT "/dev/ttyACM0"

// 1. Wrap the Serial Setup logic
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
    // Windows dummy return
    return 1;
#endif
}

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
    if (temp_pos)
        sscanf(temp_pos, "TEMP:%f", temperature);

    return 1;
#else
    // --- WINDOWS CLOUD MOCK ---
    // This allows testing the Message Builder/RabbitMQ without an Arduino
    *temperature = 23.5f;
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

    write(serial, "5\n", 2);

    usleep(500000);

    read(serial, buffer, sizeof(buffer) - 1);

    close(serial);

    char *light_pos = strstr(buffer, "LIG:");
    if (light_pos)
        sscanf(light_pos, "LIG:%hd", light);

    return 1;
#else
    // --- WINDOWS CLOUD MOCK ---
    // This allows testing the Message Builder/RabbitMQ without an Arduino
    *light = 500;
    return 1;
#endif
}

int fill_cup(int *success)
{
#if !defined(_WIN32) && !defined(UNIT_TESTING)
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

write(serial, "7\n", 2);

usleep(500000);

read(serial, buffer, sizeof(buffer) - 1);

close(serial);

if (strstr(buffer, "PUMP:DONE"))
{
    *success = 1;
    return 1;
}

if (strstr(buffer, "PUMP:FAIL"))
{
    *success = 0;
    return 1;
}

return 0;
#else
    // Windows / testing mock
    *success =1;
    printf("Mock: Fill cup command sent to Arduino\n");
    return 1;
#endif
}

// int read_pump_status(int *success)
// {
// #if !defined(_WIN32) && !defined(UNIT_TESTING)
//     int serial = open(SERIAL_PORT, O_RDWR | O_NOCTTY);
//     if (serial == -1)
//     {
//         printf("open_port: Unable to open\n");
//         return -1;
//     }

//     setup_serial(serial);

//     char buffer[100] = {0};

//     sleep(2);
//     tcflush(serial, TCIOFLUSH);

//     write(serial, "7\n", 2);

//     usleep(500000);

//     read(serial, buffer, sizeof(buffer) - 1);

//     close(serial);

//     if (strstr(buffer, "PUMP:DONE"))
//     {
//         *success = 1;
//         return 1;
//     }

//     if (strstr(buffer, "PUMP:FAIL"))
//     {
//         *success = 0;
//         return 1;
//     }

//     return 0;
// #else
//     *success = 1;
//     return 1;
// #endif
// }

// in administrator powershell

// usbipd list - This should show arduino connected 'SHARED'

// usbipd attach --wsl --busid 1-2(or whatever it said before when connecting to the port) 


// in wsl

// ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null - This checks which Arduino serial port exists in WSL.

// sudo chmod a+rw /dev/ttyACM0 - This gives permission to read and write to the Arduino port.

