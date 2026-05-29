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
                "\"value\": 0.00"
            "}",
            timestamp
        );
    }
}

void create_water_message(char *responseMessage)
{
    int water = 0;
    long timestamp = get_timestamp();

    if (read_water(&water))
    {
        sprintf(
            responseMessage,
            "{"
                "\"arduinoId\":1,"
                "\"type\":\"water\","
                "\"value\":%d,"
                "\"timestamp\":%ld"
            "}",
            water,
            timestamp
        );
    }
    else {
        sprintf(
            responseMessage,
            "{\"arduinoId\":1,\"type\":\"water\",\"value\":0,\"timestamp\":%ld}",
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
                "\"type\":\"light\","
                "\"value\":%d,"
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
                "\"value\": 0.00,"
                "\"timestamp\":%ld"
            "}",
            timestamp
        );
    }
}

void create_co2_message(char *message)
{
    int co2 = 0;
    long timestamp = get_timestamp();

    if (read_co2(&co2))
    {
        sprintf(
            message,
            "{"
                "\"arduinoId\":1,"
                "\"type\":\"co2\","
                "\"value\":%d,"
                "\"timestamp\":%ld"
            "}",
            co2,
            timestamp
        );
    }
    else
    {
        sprintf(
            message,
            "{"
                "\"arduinoId\":1,"
                "\"type\":\"co2\","
                "\"timestamp\":%ld,"
                "\"value\": 0.00"
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
                "\"value\":\"%d\","
                "\"timestamp\":%ld"
            "}",
            success,
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
                "\"value\":-1,"
                "\"timestamp\":%ld"
            "}",
            timestamp
        );
    }
}