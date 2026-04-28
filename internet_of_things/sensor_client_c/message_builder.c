#include "message_builder.h"
#include "sensor_reader.h"
#include <stdio.h>
#include <time.h>

long get_timestamp()
{
    return time(NULL);
}

void create_temperature_response_message(char *responseMessage)
{
    float temperature = 0.0; // creates variable for real temp
    long timestamp = get_timestamp();

    if (read_temperature(&temperature)) // &temperature - function can access variable to change its value
    {
        sprintf(
            responseMessage,
            "{"
                "\"arduinoId\":1,"
                "\"value\":%.2f,"
                "\"type\":\"temp\","
                "\"timestamp\":%ld"
            "}",
            temperature,
            timestamp
        );
    }
    else // no temp from arduino - send error - failure
    {
        sprintf(
            responseMessage,
            "{"
                "\"arduinoId\":1,"
                "\"type\":\"temp\","
                "\"timestamp\":%ld,"
                "\"value\": null"
            "}",
            timestamp
        );
    }
}