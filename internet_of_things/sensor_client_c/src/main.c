#include <stdio.h>
#include <unistd.h>

#include "rabbitmq_client.h"
#include "message_builder.h"
#include "sensor_reader.h"

#define MESSAGE_SIZE 512

int main()
{
    printf("Starting C sensor RabbitMQ client...\n");
    printf("RabbitMQ Management UI: http://localhost:15672\n");

    amqp_connection_state_t connection = connect_to_rabbitmq();

    setup_rabbitmq_queues(connection);

    printf("Producing temperature and light messages and listening for fill-cup requests...\n");

    while (1)
    {
        char lightMessage[MESSAGE_SIZE];
        char tempMessage[MESSAGE_SIZE];

        int requestReceived = wait_for_request(connection);

        if (requestReceived == 1)
        {
            printf("Fill-cup request received.\n");

            if (fill_cup())
            {
                printf("Arduino was prompted to fill the cup.\n");
            }
            else
            {
                printf("Failed to prompt Arduino to fill the cup.\n");
            }
        }

        create_light_message(lightMessage);
        send_response(connection, lightMessage);

        create_temperature_message(tempMessage);
        send_response(connection, tempMessage);

        sleep(5);
    }

    close_rabbitmq(connection);

    return 0;
}