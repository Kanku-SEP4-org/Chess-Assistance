#ifndef RABBITMQ_CLIENT_H
#define RABBITMQ_CLIENT_H

#include <amqp.h>

#define HOSTNAME "localhost"
#define PORT 5672
#define USERNAME "guest"
#define PASSWORD "guest"

#define REQUEST_QUEUE "sensor.requests"
#define RESPONSE_QUEUE "sensor.responses"

amqp_connection_state_t connect_to_rabbitmq();
void setup_rabbitmq_queues(amqp_connection_state_t connection);
int wait_for_request(amqp_connection_state_t connection);
void send_response(amqp_connection_state_t connection, const char *message);
void close_rabbitmq(amqp_connection_state_t connection);

#endif