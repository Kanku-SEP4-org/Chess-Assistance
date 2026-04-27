#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <fcntl.h>
#include <unistd.h>
// #include <termios.h>

#include <amqp.h>
#include <amqp_tcp_socket.h>

#define HOSTNAME "localhost"
#define PORT 5672
#define USERNAME "guest"
#define PASSWORD "guest"

#define REQUEST_QUEUE "sensor.requests"
#define RESPONSE_QUEUE "sensor.responses"

#define MESSAGE_SIZE 512

#define SERIAL_PORT "/dev/ttyACM0"
//#define SERIAL_PORT "/dev/ttyUSB0"

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

// settings for linux to talk to arduino
// int setup_serial(int serial)
// {
//     struct termios tty;
//     memset(&tty, 0, sizeof(tty));

//     if (tcgetattr(serial, &tty) != 0)
//     {
//         return 0;
//     }

//     cfsetospeed(&tty, B115200);
//     cfsetispeed(&tty, B115200);

//     tty.c_cflag = CS8 | CLOCAL | CREAD;
//     tty.c_iflag = 0;
//     tty.c_oflag = 0;
//     tty.c_lflag = 0;

//     tty.c_cc[VMIN] = 0;
//     tty.c_cc[VTIME] = 20; // waiting 2 sec for arduino response

//     if (tcsetattr(serial, TCSANOW, &tty) != 0)
//     {
//         return 0;
//     }

//     return 1;
// }

int read_temperature(float *temperature)
{
    int serial = open(SERIAL_PORT, O_RDWR | O_NOCTTY);

    // if (serial < 0)
    // {
    //     printf("Could not open Arduino serial port: %s\n", SERIAL_PORT);
    //     return 0; // as it failed
    // }
    
    // this functions is for linux to know how to corrrectly communicate with arduino through serial
    // if (!setup_serial(serial))
    // {
    //     printf("Could not configure Arduino serial port\n");
    //     close(serial);
    //     return 0;
    // }

    char buffer[100] = {0};

    write(serial, "1\n", 2); // asks Arduino for temperature

    int bytesRead = read(serial, buffer, sizeof(buffer) - 1);

    close(serial);

    if (bytesRead <= 0)
    {
        printf("No response from Arduino\n");
        return 0; // failed arduino temperature
    }

    printf("Arduino response: %s\n", buffer);

    if (sscanf(buffer, "TEMP:%f", temperature) == 1) // gets the number 1 case, stores it inside temperature
    {
        return 1; // success
    }

    printf("Could not read temperature from response\n");
    return 0; // failed
}

long get_timestamp()
{
    return time(NULL);
}

void create_temperature_response_message(char *responseMessage)
{
    /*This could have stayed if we would return fake temperature fx -99.0 when failing. 
    error would be harder to spot since JSON reposne would give us some temp.

        float temperature = read_temperature();
        long timestamp = get_timestamp();

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
    */

    // for success and failure JSON message

    //if arduino gives temp - sends value - success
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

// RabbitMQ - http://localhost:15672