#include <stdio.h>
#include <time.h>

#define MESSAGE_SIZE 512

float read_temperature()
{
    return 23.7; //fake temp for now... need read_temp() function
}

long get_timestamp()
{
    return time(NULL); // for current time?
}

void create_temperature_response_message(
    const char *requestId,
    int arduinoId,
    float temperature,
    long timestamp,
    char *responseMessage
)
{
    sprintf(
        responseMessage,
        "{"
            "\"requestId\":\"%s\","
            "\"arduinoId\":%d,"
            "\"sensorReading\":{"
                "\"value\":%.2f,"
                "\"type\":\"temp\","
                "\"timestamp\":%ld"
            "},"
            "\"status\":{"
                "\"success\":true,"
                "\"message\":\"Temperature reading successful\""
            "}"
        "}",
        requestId,
        arduinoId,
        temperature,
        timestamp
    );
}

int main()
{
    // just fake sent message from RabbitMQ.. later something like sensor.request?
   
    const char *requestId = "test-request-001";
    int arduinoId = 1;

    float temperature = read_temperature();
    long timestamp = get_timestamp();

    char responseMessage[MESSAGE_SIZE];

    create_temperature_response_message(
        requestId,
        arduinoId,
        temperature,
        timestamp,
        responseMessage
    );

    printf("Temperature response message:\n");
    printf("%s\n", responseMessage);

    return 0;
}