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
            message,
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

void create_light_message(char *message)
{
    short light = 0;
    long timestamp = get_timestamp();

    if (read_light(&light))
    {
        sprintf(
            message,
            "{"
                "\"arduinoId\":1,"
                "\"value\":%d,"
                "\"type\":\"light\","
                "\"timestamp\":%ld"
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
                "\"arduinoId\":1,"
                "\"type\":\"light\","
                "\"timestamp\":%ld,"
                "\"value\": null"
            "}",
            timestamp
        );
    }
}

void create_pump_response_message(char *message)
{
    int success = 0;
    long timestamp = get_timestamp();

    if (fill_cup(&success))    {
        sprintf(
            message,
            "{"
                "\"arduinoId\":1,"
                "\"type\":\"pump\","
                "\"status\":\"%s\","
                "\"timestamp\":%ld"
            "}",
            success ? "done" : "fail",
            timestamp
        );
    }
    else
    {
        sprintf(
            message,
            "{"
                "\"arduinoId\":1,"
                "\"type\":\"pump\","
                "\"status\":\"error\","
                "\"timestamp\":%ld"
            "}",
            timestamp
        );
    }
}