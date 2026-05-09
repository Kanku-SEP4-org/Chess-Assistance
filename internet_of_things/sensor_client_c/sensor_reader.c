#include "sensor_reader.h"
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <termios.h>

#define SERIAL_PORT "/dev/ttyACM0"
// #define SERIAL_PORT "/dev/ttyUSB0"

// settings for Linux to talk to Arduino

int setup_serial(int serial)
{
    struct termios tty;
    memset(&tty, 0, sizeof(tty));

    tcgetattr(serial, &tty);

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
}

int read_temperature(float *temperature)
{
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
}

int read_light(int *light)
{
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

    write(serial, "1\n", 5);

    usleep(500000);

    read(serial, buffer, sizeof(buffer) - 1);

    close(serial);

    char *light_pos = strstr(buffer, "LIG:");
    if (light_pos)
        sscanf(light_pos, "TEMP:%f", light);

    return 1;
}


// in administrator powershell

// usbipd list - This should show arduino connected 'SHARED'

// usbipd attach --wsl --busid 1-2(or whatever it said before when connecting to the port) 


// in wsl

// ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null - This checks which Arduino serial port exists in WSL.

// sudo chmod a+rw /dev/ttyACM0 - This gives permission to read and write to the Arduino port.

