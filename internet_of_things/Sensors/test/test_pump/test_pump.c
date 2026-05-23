#include <unity.h>
#include <string.h>
#include "sensorRead.h"

static char transmitted_buffer[128];

//Mock transmit_data() used by fill_and_report_done().
//Instead of sending over UART, it stores the message in a local buffer.

void transmit_data(const char *data)
{
    strncpy(transmitted_buffer, data, sizeof(transmitted_buffer) - 1);
    transmitted_buffer[sizeof(transmitted_buffer) - 1] = '\0';
}

// Runs before each test.
// Clears the fake transmit buffer.

void setUp(void)
{
    memset(transmitted_buffer, 0, sizeof(transmitted_buffer));
}


//Runs after each test.
//No cleanup needed, but Unity requires the function.
 
void tearDown(void)
{
}

//Test that the dummy pump function reports a successful fill response.
//Expected serial output: PUMP:DONE
 
void test_fill_and_report_done_sends_pump_done(void)
{
    fill_and_report_done();

    TEST_ASSERT_EQUAL_STRING("PUMP:DONE\n", transmitted_buffer);
}

int main(void)
{
    UNITY_BEGIN();

    RUN_TEST(test_fill_and_report_done_sends_pump_done);

    return UNITY_END();
}