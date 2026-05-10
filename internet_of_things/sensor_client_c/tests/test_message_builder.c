#include <string.h>

#include "unity.h"
#include "message_builder.h"

//Run before every test
void setUp(void){}

//Runs after every test
void tearDown(void){}

void test_create_temperature_response_message(void)
{
    char responseMessage[512];
    create_temperature_response_message(responseMessage);
    TEST_ASSERT_NOT_NULL(responseMessage);
    TEST_ASSERT_TRUE(strlen(responseMessage) > 0);
    // Since the Windows mock returns 23.50, check for that
    TEST_ASSERT_NOT_NULL(strstr(responseMessage, "\"value\":23.50"));
    TEST_ASSERT_NOT_NULL(strstr(responseMessage, "\"type\":\"temp\""));
    TEST_ASSERT_NOT_NULL(strstr(responseMessage, "\"arduinoId\":1"));
}

int main(void)
{
    UNITY_BEGIN();
    RUN_TEST(test_create_temperature_response_message);
    return UNITY_END();
}