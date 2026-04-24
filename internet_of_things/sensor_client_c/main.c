#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include <amqp.h>
#include <amqp_tcp_socket.h>

#define HOSTNAME "localhost"
#define PORT 5672
#define USERNAME "guest"
#define PASSWORD "guest"

#define REQUEST_QUEUE "sensor.requests"
#define RESPONSE_QUEUE "sensor.responses"

#define MESSAGE_SIZE 512

void fail_on_amqp_error(amqp_rpc_reply_t reply, const char *message)
{
    if (reply.reply_type == AMQP_RESPONSE_NORMAL)
    {
        return;
    }

    printf("RabbitMQ error: %s\n", message);
    exit(1);
}

void fail_on_error(int status, const char *message)
{
    if (status < 0)
    {
        printf("Error: %s\n", message);
        exit(1);
    }
}

float read_temperature()
{
    return 23.7; //fake temp for now... need read_temp() function
}

long get_timestamp()
{
    return time(NULL);
}

void create_temperature_response_message(char *responseMessage)
{
    float temperature = read_temperature();
    long timestamp = get_timestamp();

    /*
        This response is based on the proto structure:

        TempRes
        - sensorReading
          - value
          - type
          - timestamp
        - status
          - success
          - message
    */

    sprintf(
        responseMessage,
        "{"
            "\"arduinoId\":1,"
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
        temperature,
        timestamp
    );
}

void send_response(amqp_connection_state_t connection, const char *message)
{
    amqp_basic_properties_t properties;
    properties._flags = AMQP_BASIC_CONTENT_TYPE_FLAG;
    properties.content_type = amqp_cstring_bytes("application/json");

    int publishStatus = amqp_basic_publish(
        connection,
        1,
        amqp_cstring_bytes(""),
        amqp_cstring_bytes(RESPONSE_QUEUE),
        0,
        0,
        &properties,
        amqp_cstring_bytes(message)
    );

    fail_on_error(publishStatus, "Could not publish response message");

    printf("Sent response to queue '%s':\n%s\n", RESPONSE_QUEUE, message);
}

int main()
{
    amqp_connection_state_t connection;
    amqp_socket_t *socket = NULL;
    amqp_rpc_reply_t loginReply;

    printf("Starting C sensor RabbitMQ client...\n");

    connection = amqp_new_connection();

    socket = amqp_tcp_socket_new(connection);
    if (!socket)
    {
        printf("Could not create TCP socket\n");
        return 1;
    }

    int socketStatus = amqp_socket_open(socket, HOSTNAME, PORT);
    fail_on_error(socketStatus, "Could not open TCP socket");

    loginReply = amqp_login(
        connection,
        "/",
        0,
        131072,
        0,
        AMQP_SASL_METHOD_PLAIN,
        USERNAME,
        PASSWORD
    );

    fail_on_amqp_error(loginReply, "Could not log in to RabbitMQ");

    amqp_channel_open(connection, 1);
    fail_on_amqp_error(
        amqp_get_rpc_reply(connection),
        "Could not open RabbitMQ channel"
    );

    amqp_queue_declare(
        connection,
        1,
        amqp_cstring_bytes(REQUEST_QUEUE),
        0,
        0,
        0,
        0,
        amqp_empty_table
    );

    fail_on_amqp_error(
        amqp_get_rpc_reply(connection),
        "Could not declare request queue"
    );

    amqp_queue_declare(
        connection,
        1,
        amqp_cstring_bytes(RESPONSE_QUEUE),
        0,
        0,
        0,
        0,
        amqp_empty_table
    );

    fail_on_amqp_error(
        amqp_get_rpc_reply(connection),
        "Could not declare response queue"
    );

    amqp_basic_consume(
        connection,
        1,
        amqp_cstring_bytes(REQUEST_QUEUE),
        amqp_empty_bytes,
        0,
        1,
        0,
        amqp_empty_table
    );

    fail_on_amqp_error(
        amqp_get_rpc_reply(connection),
        "Could not start consuming request queue"
    );

    printf("Waiting for messages from queue '%s'...\n", REQUEST_QUEUE);

    while (1)
    {
        amqp_envelope_t envelope;

        amqp_maybe_release_buffers(connection);

        amqp_rpc_reply_t consumeReply = amqp_consume_message(
            connection,
            &envelope,
            NULL,
            0
        );

        if (consumeReply.reply_type != AMQP_RESPONSE_NORMAL)
        {
            printf("Could not consume message\n");
            break;
        }

        printf("\nReceived request from queue '%s':\n", REQUEST_QUEUE);
        printf("%.*s\n", (int)envelope.message.body.len, (char *)envelope.message.body.bytes);

        char responseMessage[MESSAGE_SIZE];
        create_temperature_response_message(responseMessage);

        send_response(connection, responseMessage);

        amqp_destroy_envelope(&envelope);
    }

    amqp_channel_close(connection, 1, AMQP_REPLY_SUCCESS);
    amqp_connection_close(connection, AMQP_REPLY_SUCCESS);
    amqp_destroy_connection(connection);

    return 0;
}