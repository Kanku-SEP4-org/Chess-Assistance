#include <amqp.h>
#include <amqp_tcp_socket.h>
#include "rabbitmq_client.h"
#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>


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

amqp_connection_state_t connect_to_rabbitmq()
{
    amqp_connection_state_t connection;
    amqp_socket_t *socket = NULL;
    amqp_rpc_reply_t loginReply;

    connection = amqp_new_connection();

    socket = amqp_tcp_socket_new(connection);
    if (!socket)
    {
        printf("Could not create TCP socket\n");
        exit(1);
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

    return connection;
}

void setup_rabbitmq_queues(amqp_connection_state_t connection)
{
    amqp_queue_declare(
        connection,
        1,
        amqp_cstring_bytes(REQUEST_QUEUE),
        0,
        1,
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
        1,
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
        1,
        0,
        0,
        amqp_empty_table
    );

    fail_on_amqp_error(
        amqp_get_rpc_reply(connection),
        "Could not start consuming request queue"
    );
}

int wait_for_request(amqp_connection_state_t connection)
{
    amqp_envelope_t envelope;

    amqp_maybe_release_buffers(connection);

    struct timeval timeout;
    timeout.tv_sec = 0;
    timeout.tv_usec = 100000; // wait max 0.1 second

    amqp_rpc_reply_t consumeReply = amqp_consume_message(
        connection,
        &envelope,
        &timeout,
        0
    );

    if (consumeReply.reply_type != AMQP_RESPONSE_NORMAL)
    {
        return 0;
    }

    printf("\nReceived request from queue '%s':\n", REQUEST_QUEUE);
    printf("%.*s\n", (int)envelope.message.body.len, (char *)envelope.message.body.bytes);

    amqp_destroy_envelope(&envelope);

    return 1;
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

void close_rabbitmq(amqp_connection_state_t connection)
{
    amqp_channel_close(connection, 1, AMQP_REPLY_SUCCESS);
    amqp_connection_close(connection, AMQP_REPLY_SUCCESS);
    amqp_destroy_connection(connection);
}