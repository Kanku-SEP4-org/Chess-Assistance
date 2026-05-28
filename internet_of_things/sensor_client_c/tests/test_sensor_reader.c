//
// Created by ana on 10-May-26.
//

#include "unity.h"
#include "sensor_reader.h"

void setUp(void) {}
void tearDown(void) {}

void test_read_temperature_should_return_mock_value_on_windows(void) {
    float temp = 0.0f;
    int status = read_temperature(&temp);

    // Verify the function transaction reports success
    TEST_ASSERT_EQUAL_INT(1, status);

#ifdef _WIN32
    // Use a delta assertion to account for fractional float parsing transitions
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 23.5f, temp);
#else
    // On Linux checking live telemetry ranges
    TEST_ASSERT_FLOAT_WITHIN(50.0f, 25.0f, temp);
#endif
}

int main(void) {
    UNITY_BEGIN();
    RUN_TEST(test_read_temperature_should_return_mock_value_on_windows);
    return UNITY_END();
}
