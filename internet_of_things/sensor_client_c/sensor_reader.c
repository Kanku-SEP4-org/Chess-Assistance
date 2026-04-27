#include "sensor_reader.h"
#include <stdio.h>
#include <string.h>
// #include <fcntl.h>
// #include <unistd.h>
// #include <termios.h>

#define SERIAL_PORT "/dev/ttyACM0"
// #define SERIAL_PORT "/dev/ttyUSB0"

/* settings for Linux to talk to Arduino



int setup_serial(int serial)
{
    struct termios tty;
    memset(&tty, 0, sizeof(tty));

    if (tcgetattr(serial, &tty) != 0)
    {
        return 0;
    }

    cfsetospeed(&tty, B115200);
    cfsetispeed(&tty, B115200);

    tty.c_cflag = CS8 | CLOCAL | CREAD;
    tty.c_iflag = 0;
    tty.c_oflag = 0;
    tty.c_lflag = 0;

    tty.c_cc[VMIN] = 0;
    tty.c_cc[VTIME] = 20;

    if (tcsetattr(serial, TCSANOW, &tty) != 0)
    {
        return 0;
    }

    return 1;
}
*/

int read_temperature(float *temperature)
{
    // int serial = open(SERIAL_PORT, O_RDWR | O_NOCTTY);

    // setup_serial(serial);

    FILE *sensorOutput = popen("../mock_sensor_c/mock-sensor", "r");

    char buffer[100] = {0};

    fgets(buffer, sizeof(buffer), sensorOutput);

    pclose(sensorOutput);

    // write(serial, "1\n", 2); // asks Arduino for temperature

    // read(serial, buffer, sizeof(buffer) - 1);

    // close(serial);

    sscanf(buffer, "TEMP:%f", temperature);

    return 1;
}