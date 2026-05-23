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

    printf("Reading sensor data and listening for requests\n");

    while (1)
    {
        char lightMessage[MESSAGE_SIZE];
        char tempMessage[MESSAGE_SIZE];
        char waterMessage[MESSAGE_SIZE];
        char pumpMessage[MESSAGE_SIZE];
        char co2Message[MESSAGE_SIZE];     

        int requestReceived = wait_for_request(connection);

        if (requestReceived == 1)
        {
            printf("Fill-cup request received.\n");
            
            create_pump_response_message(pumpMessage);
            printf("Pump message: %s\n", pumpMessage);
            send_response(connection, pumpMessage);

        }

        create_light_message(lightMessage);
        send_response(connection, lightMessage);

        create_temperature_message(tempMessage);
        send_response(connection, tempMessage);

        create_water_message(waterMessage);
        send_response(connection, waterMessage);

        create_co2_message(co2Message);
        send_response(connection, co2Message);
        sleep(5);
    }

    close_rabbitmq(connection);

    return 0;
}