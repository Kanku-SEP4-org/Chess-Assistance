#include "unity.h"
#include "message_builder.h"
#include <string.h>

//Mock values 
static int mock_temp_result;
static float mock_temp_value;

static int mock_water_result;
static int mock_water_value;

static int mock_pump_result;
static int mock_pump_success;

// If the temp_value is true, it returns success and writes the test value. Else, it will simulate a failed sensor read
// int read_temperature(float *temperature)
// {
//     if (mock_temp_result)
//     {
//         *temperature = mock_temp_value;
//         return 1;
//     }
//     return 0;
// }

//If water_value is true, it returns success and writes the test value.
// int read_water(int *water)
// {
//     if (mock_water_result)
//     {
//         *water = mock_water_value;
//         return 1;
//     }
//     return 0;
// }

int read_pump_status(int *success)
{
    if (mock_pump_result)
    {
        *success = mock_pump_success;
        return 1;
    }
    return 0;
}
// It runs before each test. It resets each value so ever test starts from a clean known state
void setUp(void)
{
    // mock_temp_result = 1;
    // mock_temp_value = 23.5f;

    // mock_water_result = 1;
    // mock_water_value = 512;
    mock_pump_result = 1;
    mock_pump_success = 1;
}

// It runs AFTER each test and it does not require any cleanup. The function is required by unity.
void tearDown(void)
{
}

//Tests if a valid temp reading creates the correct JSON message containing the expected ARDUINO values(type, value, etc)
void test_create_temperature_message_success(void)
{
    char buffer[512] = {0};

    create_temperature_message(buffer);

    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"arduinoId\":1"));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"type\":\"temp\""));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"value\":23.50"));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"timestamp\":"));
}

// Test that a failed temperature read creates a fallback JSON message with type temp and value set to null
void test_create_temperature_message_failure(void)
{
    char buffer[512] = {0};
    mock_temp_result = 0;

    create_temperature_message(buffer);

    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"arduinoId\":1"));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"type\":\"temp\""));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"value\": null"));
}

//Tests that the valid water reading creates the correct JSON message where we can verify the arduinoID, water type, value
void test_create_water_message_success(void)
{
    char buffer[512] = {0};

    create_water_message(buffer);

    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"arduinoId\":1"));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"type\":\"water\""));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"value\":512"));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"timestamp\":"));
}

//Tests that we get a fallback JSON message from a failed water read and the type water and value are set to null
void test_create_water_message_failure(void)
{
    char buffer[512] = {0};
    mock_water_result = 0;

    create_water_message(buffer);

    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"arduinoId\":1"));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"type\":\"water\""));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"value\": null"));
}
/* Tests pump success JSON */
void test_create_pump_response_message_done(void)
{
    char buffer[512] = {0};
    mock_pump_result = 1;
    mock_pump_success = 1;

    create_pump_response_message(buffer);

    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"arduinoId\":1"));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"type\":\"pump\""));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"status\":\"done\""));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"timestamp\":"));
}

/* Tests pump fail JSON */
void test_create_pump_response_message_fail(void)
{
    char buffer[512] = {0};
    mock_pump_result = 1;
    mock_pump_success = 0;

    create_pump_response_message(buffer);

    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"arduinoId\":1"));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"type\":\"pump\""));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"status\":\"fail\""));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"timestamp\":"));
}

/* Tests pump error JSON */
void test_create_pump_response_message_error(void)
{
    char buffer[512] = {0};
    mock_pump_result = 0;

    create_pump_response_message(buffer);

    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"arduinoId\":1"));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"type\":\"pump\""));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"status\":\"error\""));
    TEST_ASSERT_NOT_NULL(strstr(buffer, "\"timestamp\":"));
}
//The main Unity test runner
int main(void)
{
    UNITY_BEGIN();

    // RUN_TEST(test_create_temperature_message_success);
    // RUN_TEST(test_create_temperature_message_failure);
    // RUN_TEST(test_create_water_message_success);
    // RUN_TEST(test_create_water_message_failure);
    // RUN_TEST(test_create_pump_response_message_done);
    // RUN_TEST(test_create_pump_response_message_fail);
    // RUN_TEST(test_create_pump_response_message_error);
    return UNITY_END();
}