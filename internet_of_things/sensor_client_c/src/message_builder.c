#include "message_builder.h"
#include "sensor_reader.h"
#include <stdio.h>
#include <time.h>

long get_timestamp()
{
    return time(NULL);
}

void create_temperature_message(char *message)
{
    float temperature = 0.0; // creates variable for real temp
    long timestamp = get_timestamp();

    if (read_temperature(&temperature)) // &temperature - function can access variable to change its value
    {
        sprintf(
            message,
            "{"
                "\"ArduinoId\":1,"
                "\"Value\":%.2f,"
                "\"Type\":\"temp\","
                "\"Timestamp\":%ld"
            "}",
            temperature,
            timestamp
        );
    }
    else // no temp from arduino - send error - failure
    {
        sprintf(
            message,
            "{"
                "\"ArduinoId\":1,"
                "\"Type\":\"temp\","
                "\"Timestamp\":%ld,"
                "\"Value\": 0.00"
            "}",
            timestamp
        );
    }
}

void create_light_message(char *message)
{
    short light = 0;
    long timestamp = get_timestamp();

    if (read_light(&light))
    {
        sprintf(
            message,
            "{"
                "\"ArduinoId\":1,"
                "\"Value\":%d,"
                "\"Type\":\"light\","
                "\"Timestamp\":%ld"
            "}",
            light,
            timestamp
        );
    }
    else
    {
        sprintf(
            message,
            "{"
                "\"ArduinoId\":1,"
                "\"Type\":\"light\","
                "\"Timestamp\":%ld,"
                "\"Value\": 0.00"
            "}",
            timestamp
        );
    }
}