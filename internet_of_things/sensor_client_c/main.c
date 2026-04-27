#include <stdio.h>
#include "rabbitmq_client.h"
#include "message_builder.h"

#define MESSAGE_SIZE 512

int main()
{
    printf("Starting C sensor RabbitMQ client...\n");
    printf("RabbitMQ Management UI: http://localhost:15672\n");

    amqp_connection_state_t connection = connect_to_rabbitmq();

    setup_rabbitmq_queues(connection);

    printf("Waiting for messages from queue '%s'...\n", REQUEST_QUEUE);

    while (1)
    {
        if (!wait_for_request(connection))
        {
            break;
        }

        char responseMessage[MESSAGE_SIZE];

        create_temperature_response_message(responseMessage);

        send_response(connection, responseMessage);
    }

    close_rabbitmq(connection);

    return 0;
}