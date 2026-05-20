#include <unity.h>
#include <string.h>
#include "sensorRead.h"

static char transmitted_buffer[128];

void transmit_data(const char *data)
{
    strncpy(transmitted_buffer, data, sizeof(transmitted_buffer) - 1);
    transmitted_buffer[sizeof(transmitted_buffer) - 1] = '\0';
}

void setUp(void)
{
    memset(transmitted_buffer, 0, sizeof(transmitted_buffer));
}

void tearDown(void)
{
}

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